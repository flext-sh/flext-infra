"""Real public semantic publication, identity and rollback contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, infra, m, p, r
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import tm, u

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraSemanticPublication:
    """All files remain recoverable until the semantic consumer accepts them."""

    @staticmethod
    def test_joint_phases_reconcile_an_unchanged_initializer_later_owned_by_lazy_init(
        mod_workspace: Path,
    ) -> None:
        """Keep the historical initializer proof while consuming declared exports."""
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        original = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().lower()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        declaration.write_text(original, encoding=c.DEFAULT_ENCODING)
        initializer = package / c.Infra.INIT_PY
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (declaration, initializer)
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=(
                    original.replace(".lower()", ".upper()").encode(c.DEFAULT_ENCODING)
                    if state.path == declaration
                    else state.content
                ),
                desired_mode=state.mode,
                source_states=states,
            )
            for state in states
        )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
            ),
        )
        output = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    f"from {mod_workspace.name} import DeclaredService; "
                    "assert DeclaredService.normalize(' live ') == 'LIVE'",
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True)

    def test_same_byte_foreign_replacement_of_unchanged_destination_is_rejected(
        self,
        mod_workspace: Path,
    ) -> None:
        """An unchanged plan never authorizes a foreign inode with equal bytes."""
        first, second = self._plans(mod_workspace)
        unchanged = second.model_copy(
            update={"desired_content": second.before.content},
        )
        foreign = second.path.with_suffix(".foreign")
        foreign.write_bytes(tm.not_none(second.before.content))
        foreign.chmod(tm.not_none(second.before.mode))
        foreign.replace(second.path)
        foreign_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(second.path, required=True),
        )
        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, unchanged),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(second.path, required=True)),
            eq=foreign_state,
        )

    def test_foreign_unchanged_destination_after_append_rejects_final_receipt(
        self,
        mod_workspace: Path,
    ) -> None:
        """A real accepted phase never authorizes a later foreign identical inode."""
        first, second = self._plans(mod_workspace)
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=plan.path,
                before=plan.before,
                desired_content=(
                    plan.desired_content
                    if plan.path == first.path
                    else plan.before.content
                ),
                desired_mode=plan.desired_mode,
            )
            for plan in (first, second)
        )
        inputs = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(plan.path, required=True))
            for plan in plans
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            files=plans,
            inputs=inputs,
        )
        project = u.build_project_metadata(
            mod_workspace,
            u.read_project_document_cached(mod_workspace),
        )
        roots = {f"@{project.project.name}": mod_workspace}
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=mod_workspace),
        )
        foreign_state: m.Cli.AtomicFileState | None = None

        def apply(
            session: m.Infra.CodegenTransactionSession,
        ) -> p.Result[t.VariadicTuple[Path]]:
            nonlocal foreign_state
            published = transaction.append_phase_locked(
                session, analysis.phase, plans,
            )
            if published.failure:
                return r[t.VariadicTuple[Path]].from_failure(published)
            foreign = second.path.with_suffix(".foreign")
            foreign.write_bytes(tm.not_none(second.before.content))
            foreign.chmod(tm.not_none(second.before.mode))
            foreign.replace(second.path)
            foreign_state = tm.ok(
                u.Cli.atomic_read_binary_file_state(second.path, required=True),
            )
            return transaction.commit_locked(
                published.value,
                lambda: transaction.validate_phase_analysis_locked(
                    analysis, session=published.value,
                ),
            )

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            prepared = transaction.begin_files_locked(scope_root, roots, inputs)
            if prepared.failure:
                return r[t.VariadicTuple[Path]].from_failure(prepared)
            return transaction.publish_prepared_locked(prepared.value, apply)

        tm.fail(
            transaction.run_files_locked(roots, publish),
        )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(second.path, required=True)),
            eq=tm.not_none(foreign_state),
        )

    @staticmethod
    @pytest.mark.parametrize("foreign_parent", [False, True])
    def test_artifact_publication_owns_declared_absent_parent_chain(
        mod_workspace: Path,
        *,
        foreign_parent: bool,
    ) -> None:
        """Create missing parents through the journal or refuse a foreign owner."""
        package = mod_workspace / "src" / mod_workspace.name
        target = package / "relocated" / "nested" / "service.py"
        chain = tm.ok(u.Cli.atomic_plan_directory_chain(target.parent))
        source = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().upper()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        plan = m.Infra.CodegenFilePlan(
            project=mod_workspace,
            path=target,
            before=chain,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=package.stat().st_mode & 0o666,
        )
        foreign = target.parent / "foreign.txt"
        if foreign_parent:
            tm.ok(u.Cli.ensure_dir(target.parent))
            foreign.write_text("foreign owner\n", encoding=c.DEFAULT_ENCODING)
        result = FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            (plan,),
            repository_root=mod_workspace,
            projection_roots=(mod_workspace,),
        )
        if foreign_parent:
            tm.fail(result, has="parent chain changed")
            tm.that(target.exists(), eq=False)
            tm.that(foreign.read_text(encoding=c.DEFAULT_ENCODING), eq="foreign owner\n")
        else:
            tm.ok(result)
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        f"from {mod_workspace.name}.relocated.nested import "
                        "DeclaredService; "
                        "assert DeclaredService.normalize(' live ') == 'LIVE'",
                    ),
                    cwd=mod_workspace,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)},
                    ),
                ),
            )
            tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)
            tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_preflight_and_commit_accept_the_real_published_consumer(
        self,
        mod_workspace: Path,
    ) -> None:
        """Original input checks precede effects; consumers see the desired bytes."""
        plans = self._plans(mod_workspace)

        def preflight() -> p.Result[bool]:
            return u.Cli.atomic_verify_binary_file_states(
                tuple(
                    plan.before
                    for plan in plans
                    if isinstance(plan.before, m.Cli.AtomicFileState)
                ),
            )

        def validate() -> p.Result[bool]:
            return u.Cli.run_raw((
                sys.executable,
                "-I",
                "-c",
                "import runpy, sys; "
                "assert all(runpy.run_path(path)['value'] == 'after' "
                "for path in sys.argv[1:])",
                *(str(plan.path) for plan in plans),
            )).map(lambda output: u.Cli.process_succeeded(output.outcome))

        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                preflight=preflight,
                validator=validate,
            ),
        )

    @pytest.mark.parametrize("stage", ["preflight", "commit"])
    def test_transaction_rejects_changed_source_scope_or_catalog(
        self,
        mod_workspace: Path,
        stage: str,
    ) -> None:
        """A foreign input introduced inside the transaction cannot be accepted."""
        plans = self._plans(mod_workspace)
        scope = tuple(u.Infra.ast_grep_scan_targets(mod_workspace))
        catalog = mod_workspace / c.Infra.CODEMOD_CONFIG_RELPATH
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text("ruleDirs: []\n", encoding=c.DEFAULT_ENCODING)
        state = tm.ok(u.Cli.atomic_read_binary_file_state(catalog, required=True))
        added = mod_workspace / "concurrent_consumer.py"

        def verify_inputs() -> p.Result[bool]:
            if tuple(u.Infra.ast_grep_scan_targets(mod_workspace)) != scope:
                return r[bool].fail("public source scope changed")
            return u.Cli.atomic_verify_binary_file_states((state,))

        def preflight() -> p.Result[bool]:
            if stage == "preflight":
                added.write_text(
                    '"""Concurrent public consumer."""\n',
                    encoding=c.DEFAULT_ENCODING,
                )
            return verify_inputs()

        def validate() -> p.Result[bool]:
            consumer = u.Cli.run_raw((
                sys.executable,
                "-I",
                "-c",
                "import runpy, sys; "
                "assert all(runpy.run_path(path)['value'] == 'after' "
                "for path in sys.argv[1:])",
                *(str(plan.path) for plan in plans),
            ))
            if consumer.failure:
                return r[bool].from_failure(consumer)
            if not u.Cli.process_succeeded(consumer.value.outcome):
                return r[bool].fail(consumer.value.stderr)
            catalog.write_text(
                "ruleDirs: []\n# concurrent catalog edit\n",
                encoding=c.DEFAULT_ENCODING,
            )
            return verify_inputs()

        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                preflight=preflight,
                validator=validate,
            ),
        )
        if stage == "preflight":
            tm.that(added.is_file(), eq=True)
            for plan in plans:
                tm.that(plan.path.read_bytes(), eq=plan.before.content)
        else:
            tm.that(
                catalog.read_text(encoding=c.DEFAULT_ENCODING),
                has="concurrent catalog edit",
            )

    @staticmethod
    def test_no_effect_publication_requires_true_acceptance(
        mod_workspace: Path,
    ) -> None:
        """A successful false result rejects publication without filesystem effects."""
        before = tuple(
            (path, path.stat().st_mode, path.read_bytes() if path.is_file() else None)
            for path in sorted(mod_workspace.rglob("*"))
        )
        calls = 0
        accepted = False

        def validate() -> p.Result[bool]:
            nonlocal calls
            calls += 1
            return r[bool].ok(accepted)

        rejected = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            validator=validate,
        )
        tm.that(calls, eq=1)
        accepted = True
        published = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            validator=validate,
        )
        tm.that(calls, eq=2)
        tm.that(
            tuple(
                (
                    path,
                    path.stat().st_mode,
                    path.read_bytes() if path.is_file() else None,
                )
                for path in sorted(mod_workspace.rglob("*"))
            ),
            eq=before,
        )
        tm.that(tm.ok(published), eq=())
        tm.fail(rejected)

    @staticmethod
    @pytest.mark.parametrize("raises", [False, True])
    def test_no_effect_publication_retains_validator_failure(
        mod_workspace: Path,
        *,
        raises: bool,
    ) -> None:
        """An explicit consumer rejection cannot become a no-effect success."""
        path = mod_workspace / "consumer.py"
        source = 'raise RuntimeError("consumer rejected")\n'
        path.write_text(source, encoding="utf-8")
        failure = RuntimeError("consumer rejected")

        def reject() -> p.Result[bool]:
            consumer = tm.ok(u.Cli.run_raw((sys.executable, str(path))))
            tm.that(u.Cli.process_succeeded(consumer.outcome), eq=False)
            if raises:
                raise failure
            return r[bool].fail(str(failure), exception=failure)

        if raises:
            with pytest.raises(RuntimeError) as raised:
                FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (),
                    repository_root=mod_workspace,
                    validator=reject,
                )
            tm.that(raised.value is failure, eq=True)
        else:
            rejected = FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                validator=reject,
            )
            tm.fail(rejected, has=str(failure))
            tm.that(rejected.exception is failure, eq=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("rejected", [False, True])
    def test_unchanged_semantic_entry_validates_generated_public_consumer(
        tmp_path: Path,
        *,
        rejected: bool,
    ) -> None:
        """The real semantic entry cannot accept stale exports without its gates."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        notice = u.Infra.copyright_notice(root)
        path = package / "service.py"
        source = (
            f'"""Public candidate service.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n\n"
            "class FlextTestProjectService:\n"
            '    """Execute the fixture consumer contract."""\n\n'
            "    @staticmethod\n"
            "    def execute() -> bool:\n"
            '        """Return the fixture service health.\n\n'
            "        Returns:\n"
            "            Whether the fixture service is healthy.\n\n"
            '        """\n'
            "        return True\n\n\n"
            + ('raise RuntimeError("consumer rejected")\n\n' if rejected else "")
            + '__all__ = ["FlextTestProjectService"]\n'
        )
        path.write_text(source, encoding="utf-8")
        initializer = package / "__init__.py"
        original = initializer.read_bytes()
        report = m.Infra.ModScanReport(
            findings=0,
            actionable=0,
            detection_only=0,
            non_actionable_with_fix=0,
            files=frozenset(),
            entries=(),
        )
        with infra.rope_workspace(root) as rope:
            result = FlextInfraCodemodSemanticApply.apply(root, report, rope)
        if rejected:
            tm.fail(result, has="quality")
            tm.that(initializer.read_bytes(), eq=original)
        else:
            tm.ok(result)
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {package.name} import FlextTestProjectService; "
                            "assert FlextTestProjectService.execute()"
                        ),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)},
                    ),
                ),
            )
            tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("accepted", [False, True])
    def test_projection_only_candidate_validates_real_public_consumer(
        mod_workspace: Path,
        *,
        accepted: bool,
    ) -> None:
        """Generate declared exports before acceptance without changing authored WIP."""
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        source = "class DeclaredService:\n    pass\n\n__all__ = ['DeclaredService']\n"
        declaration.write_text(source, encoding="utf-8")
        initializer = package / "__init__.py"
        original = initializer.read_bytes()

        def validate() -> p.Result[bool]:
            consumer = u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {mod_workspace.name} import DeclaredService; "
                        "assert isinstance(DeclaredService(), DeclaredService)"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            )
            tm.ok(consumer)
            tm.that(u.Cli.process_succeeded(consumer.value.outcome), eq=True)
            return r[bool].ok(True) if accepted else r[bool].fail("consumer rejected")

        published = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            projection_roots=(mod_workspace,),
            validator=validate,
        )
        if accepted:
            tm.ok(published)
            tm.that(initializer.read_bytes() != original, eq=True)
        else:
            tm.fail(published, has="consumer rejected")
            tm.that(initializer.read_bytes(), eq=original)
        tm.that(declaration.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def _plans(root: Path) -> t.VariadicTuple[m.Infra.SemanticFilePlan]:
        plans: list[m.Infra.SemanticFilePlan] = []
        for name in ("first.py", "second.py"):
            path = root / name
            u.Cli.atomic_write_text_file(path, 'value = "before"\n').unwrap()
            before = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=root,
                    path=path,
                    before=before,
                    desired_content=b'value = "after"\n',
                    desired_mode=before.mode,
                    changes=("publication contract",),
                ),
            )
        return tuple(plans)

    @pytest.mark.parametrize("raises", [False, True])
    def test_rejected_semantic_acceptance_rolls_back_every_file(
        self,
        mod_workspace: Path,
        *,
        raises: bool,
    ) -> None:
        """Test rejected semantic acceptance rolls back every file."""
        plans = self._plans(mod_workspace)
        failure = RuntimeError("semantic acceptance rejected")

        def reject() -> p.Result[bool]:
            for plan in plans:
                tm.that(plan.path.read_bytes(), eq=plan.desired_content)
            if raises:
                raise failure
            return r[bool].fail(str(failure))

        if raises:
            with pytest.raises(RuntimeError) as raised:
                FlextInfraSemanticPublication.publish_semantic_file_plans(
                    plans,
                    repository_root=mod_workspace,
                    validator=reject,
                )
            tm.that(raised.value is failure, eq=True)
        else:
            tm.fail(
                FlextInfraSemanticPublication.publish_semantic_file_plans(
                    plans,
                    repository_root=mod_workspace,
                    validator=reject,
                ),
                has=str(failure),
            )
        for plan in plans:
            tm.that(plan.path.read_bytes(), eq=plan.before.content)
        # Recovery leaves the same public operation available, not a poisoned journal.
        fresh = tuple(
            plan.model_copy(
                update={
                    "before": u.Cli.atomic_read_binary_file_state(
                        plan.path,
                        required=True,
                    ).unwrap(),
                },
            )
            for plan in plans
        )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                fresh,
                repository_root=mod_workspace,
            ),
        )

    @pytest.mark.parametrize("linked", [False, True])
    def test_changed_later_identity_prevents_earlier_publication(
        self,
        mod_workspace: Path,
        *,
        linked: bool,
    ) -> None:
        """Test changed later identity prevents earlier publication."""
        first, second = self._plans(mod_workspace)
        if linked:
            actual = second.path.with_suffix(".actual")
            second.path.rename(actual)
            second.path.symlink_to(actual)
        else:
            u.Cli.atomic_write_text_file(second.path, 'value = "concurrent"\n').unwrap()
        observed = second.path.read_bytes()
        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, second),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(second.path.read_bytes(), eq=observed)

    def test_generated_later_plan_rejects_authored_earlier_plan(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test generated later plan rejects authored earlier plan."""
        first, second = self._plans(mod_workspace)
        u.Cli.atomic_write_text_file(
            second.path,
            f'{c.Infra.AUTOGEN_HEADERS[0]}\nvalue = "before"\n',
        ).unwrap()
        generated = second.model_copy(
            update={
                "before": u.Cli.atomic_read_binary_file_state(
                    second.path,
                    required=True,
                ).unwrap(),
            },
        )
        tm.fail(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, generated),
                repository_root=mod_workspace,
            ),
            has="canonical generator repair",
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    def test_none_content_preserves_the_file(self, mod_workspace: Path) -> None:
        """Test none content preserves the file."""
        first, _ = self._plans(mod_workspace)
        noop = first.model_copy(update={"desired_content": None, "desired_mode": None})
        tm.that(
            tm.ok(
                FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (noop,),
                    repository_root=mod_workspace,
                ),
            ),
            eq=(),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    @staticmethod
    def test_declared_template_input_is_not_its_generated_projection(
        mod_workspace: Path,
    ) -> None:
        """Test declared template input is not its generated projection."""
        template_root = mod_workspace / "templates"
        template_root.mkdir()
        declared = template_root / "declared.j2"
        arbitrary = template_root / "arbitrary.j2"
        projection = mod_workspace / "projection.py"
        content = f"{c.Infra.AUTOGEN_HEADERS[0]}\nbefore\n"
        for path in (declared, arbitrary, projection):
            path.write_text(content, encoding="utf-8")
        entry = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.source is not None
        )
        policy = config.Infra.codegen.model_copy(
            update={
                "templates": config.Infra.codegen.templates.model_copy(
                    update={
                        "root": template_root,
                        "entries": (
                            entry.model_copy(update={"source": Path(declared.name)}),
                        ),
                    },
                ),
            },
        )
        plans = tuple(
            m.Infra.SemanticFilePlan(
                project=mod_workspace,
                path=path,
                before=tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True)),
                desired_content=content.replace("before", "after").encode(),
                desired_mode=path.stat().st_mode & 0o7777,
            )
            for path in (declared, arbitrary, projection)
        )
        for denied in plans[1:]:
            tm.fail(
                FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (plans[0], denied),
                    repository_root=mod_workspace,
                    codegen=policy,
                ),
                has="canonical generator repair",
            )
            tm.that(declared.read_text(), eq=content)
            tm.that(denied.path.read_text(), eq=content)
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (plans[0],),
                repository_root=mod_workspace,
                codegen=policy,
            ),
        )
        rendered = tm.ok(
            u.Cli.template_render(declared, m.Infra.StaticTextRenderSpec()),
        )
        tm.that(rendered, has="after")
        tm.that(arbitrary.read_text(), eq=content)
        tm.that(projection.read_text(), eq=content)

    def test_real_formatter_rejects_later_source_before_any_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test real formatter rejects later source before any publication."""
        plans = self._plans(mod_workspace)
        edits = tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=plan.path,
                original_source=plan.path.read_text(),
                updated_source='value="after"\n' if index == 0 else "value = (\n",
                changes=("formatter preflight",),
            )
            for index, plan in enumerate(plans)
        )
        with pytest.raises(RuntimeError, match="failed"):
            FlextInfraCodemodSemanticApply.apply_transaction_paths(mod_workspace, edits)
        for plan in plans:
            tm.that(plan.path.read_bytes(), eq=plan.before.content)

    def test_real_semantic_caller_commits_normalized_source_idempotently(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test real semantic caller commits normalized source idempotently."""
        first, _ = self._plans(mod_workspace)
        edit = m.Infra.SemanticMigrationEdit(
            file_path=first.path,
            original_source=first.path.read_text(),
            updated_source='value="after"\n',
            changes=("semantic normalization",),
        )
        FlextInfraCodemodSemanticApply.apply_transaction_paths(mod_workspace, (edit,))
        published = first.path.read_text()
        tm.that(published, has="after")
        tm.that(published, lacks="before")
        repeated = edit.model_copy(
            update={"original_source": published, "updated_source": published},
        )
        FlextInfraCodemodSemanticApply.apply_transaction_paths(
            mod_workspace,
            (repeated,),
        )
        tm.that(first.path.read_text(), eq=published)
