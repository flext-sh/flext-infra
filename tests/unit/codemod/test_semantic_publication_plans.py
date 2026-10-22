"""Real public semantic file-plan publication, identity and rejection contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import codegen, codemod, config, infra, transformers
from tests import c, m, p, r, tm, u

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraSemanticPublicationPlans:
    """Admit complete semantic file plans and refuse stale or foreign identity."""

    def test_same_byte_foreign_replacement_of_unchanged_destination_is_rejected(
        self,
        mod_workspace: Path,
    ) -> None:
        """An unchanged plan rejects a foreign replacement with identical bytes."""
        u.Tests.run_native_callable(self._scenario_foreign_destination, mod_workspace)

    @staticmethod
    def _scenario_foreign_destination(mod_workspace: Path) -> None:
        """An unchanged plan never authorizes a foreign inode with equal bytes."""
        first, second = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
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
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
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
        """A foreign identical inode after an accepted phase is rejected."""
        u.Tests.run_native_callable(self._scenario_append_receipt, mod_workspace)

    @staticmethod
    def _scenario_append_receipt(mod_workspace: Path) -> None:
        """A real accepted phase never authorizes a later foreign identical inode."""
        first, second = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
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
        transaction = codegen.FlextInfraCodegenTransaction(
            codegen.FlextInfraCodegenMiseArtifacts(repository_root=mod_workspace),
        )
        foreign_state: m.Cli.AtomicFileState | None = None

        def apply(
            session: m.Infra.CodegenTransactionSession,
        ) -> p.Result[t.VariadicTuple[Path]]:
            nonlocal foreign_state
            published = transaction.append_phase_locked(
                session, analysis.phase, analysis.files
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
            verified = transaction.validate_phase_analysis_locked(
                analysis,
                session=published.value,
            )
            if verified.failure:
                return r[t.VariadicTuple[Path]].from_failure(verified)
            return transaction.commit_locked(published.value)

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

    def test_preflight_and_commit_accept_the_real_published_consumer(
        self,
        mod_workspace: Path,
    ) -> None:
        """Preflight and commit accept the real published consumer.

        Original input checks run before effects; the consumer then observes the
        desired bytes.

        """
        u.Tests.run_native_callable(self._scenario_preflight_commit, mod_workspace)

    @staticmethod
    def _scenario_preflight_commit(mod_workspace: Path) -> None:
        """Original input checks precede effects; consumers see the desired bytes."""
        plans = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)

        def preflight() -> p.Result[bool]:
            return u.Cli.atomic_verify_binary_file_states(
                tuple(plan.before for plan in plans),
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            return u.Cli.run_raw((
                sys.executable,
                "-I",
                "-c",
                (
                    "import runpy, sys; "
                    "assert all(runpy.run_path(path)['value'] == 'after' "
                    "for path in sys.argv[1:])"
                ),
                *(
                    str(candidate_root / plan.path.relative_to(mod_workspace))
                    for plan in plans
                ),
            )).map(lambda output: u.Cli.process_succeeded(output.outcome))

        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    source_guard=preflight, validator=validate
                ),
            ),
        )

    @pytest.mark.parametrize("stage", ["preflight", "commit"])
    def test_transaction_rejects_changed_source_scope_or_catalog(
        self,
        mod_workspace: Path,
        stage: str,
    ) -> None:
        """A changed source scope or codemod catalog is rejected in the transaction.

        The foreign input is introduced at either preflight or commit.

        """
        u.Tests.run_native_callable(self._scenario_scope_drift, mod_workspace, stage)

    @staticmethod
    def _scenario_scope_drift(mod_workspace: Path, stage: str) -> None:
        """A foreign input introduced inside the transaction cannot be accepted."""
        plans = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
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

        def validate(candidate_root: Path) -> p.Result[bool]:
            consumer = u.Cli.run_raw((
                sys.executable,
                "-I",
                "-c",
                (
                    "import runpy, sys; "
                    "assert all(runpy.run_path(path)['value'] == 'after' "
                    "for path in sys.argv[1:])"
                ),
                *(
                    str(candidate_root / plan.path.relative_to(mod_workspace))
                    for plan in plans
                ),
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
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    source_guard=preflight, validator=validate
                ),
            ),
        )
        if stage == "preflight":
            tm.ok(added.is_file())
            for plan in plans:
                tm.that(plan.path.read_bytes(), eq=plan.before.content)
        else:
            tm.that(
                catalog.read_text(encoding=c.DEFAULT_ENCODING),
                has="concurrent catalog edit",
            )

    @staticmethod
    def _plans(
        root: Path,
        names: t.StrTuple = ("first.py", "second.py"),
    ) -> t.VariadicTuple[m.Infra.SemanticFilePlan]:
        plans: list[m.Infra.SemanticFilePlan] = []
        for name in names:
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
    def test_rejected_semantic_acceptance_preserves_original_files(
        self,
        mod_workspace: Path,
        *,
        raises: bool,
    ) -> None:
        """A rejected or raising semantic acceptance preserves every original file."""
        u.Tests.run_native_callable(
            self._scenario_rejected_acceptance,
            mod_workspace,
            raises=raises,
        )

    @staticmethod
    def _scenario_rejected_acceptance(mod_workspace: Path, *, raises: bool) -> None:
        """The complete candidate is consumed before any original file changes."""
        plans = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        failure = RuntimeError("semantic acceptance rejected")

        def reject(candidate_root: Path) -> p.Result[bool]:
            for plan in plans:
                candidate = candidate_root / plan.path.relative_to(mod_workspace)
                tm.that(candidate.read_bytes(), eq=plan.desired_content)
                tm.that(plan.path.read_bytes(), eq=plan.before.content)
            consumer = tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-c",
                        (
                            "import runpy, sys; "
                            "assert all(runpy.run_path(path)['value'] == 'after' "
                            "for path in sys.argv[1:])"
                        ),
                        *(
                            str(candidate_root / plan.path.relative_to(mod_workspace))
                            for plan in plans
                        ),
                    ),
                    cwd=candidate_root,
                ),
            )
            tm.ok(u.Cli.process_succeeded(consumer.outcome))
            if raises:
                raise failure
            return r[bool].fail(str(failure))

        if raises:
            with pytest.raises(RuntimeError) as raised:
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    plans,
                    repository_root=mod_workspace,
                    options=m.Infra.SemanticPublicationOptions(validator=reject),
                )
            tm.ok(raised.value is failure)
        else:
            tm.fail(
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    plans,
                    repository_root=mod_workspace,
                    options=m.Infra.SemanticPublicationOptions(validator=reject),
                ),
                has=str(failure),
            )
        for plan in plans:
            tm.that(plan.path.read_bytes(), eq=plan.before.content)
        # A subsequent explicitly accepted operation can publish a new candidate.
        fresh = tuple(
            plan.model_copy(
                update={
                    "before": u.Cli.atomic_read_binary_file_state(
                        plan.path,
                        required=True,
                    ).unwrap(),
                    "desired_content": b'value = "accepted"\n',
                },
            )
            for plan in plans
        )
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                fresh,
                repository_root=mod_workspace,
            ),
        )

    @pytest.mark.parametrize("linked", [False, True])
    def test_changed_middle_identity_rejects_before_other_publications(
        self,
        mod_workspace: Path,
        *,
        linked: bool,
    ) -> None:
        """A changed middle-plan identity rejects the batch before any publication.

        The identity change is either a replaced file or a link.

        """
        u.Tests.run_native_callable(
            self._scenario_middle_identity,
            mod_workspace,
            linked=linked,
        )

    @staticmethod
    def _scenario_middle_identity(mod_workspace: Path, *, linked: bool) -> None:
        """Complete admission rejects stale identity before any file is changed."""
        first, second, third = TestsFlextInfraSemanticPublicationPlans._plans(
            mod_workspace,
            ("first.py", "second.py", "third.py"),
        )
        if linked:
            actual = second.path.with_suffix(".actual")
            second.path.rename(actual)
            second.path.symlink_to(actual)
        else:
            u.Cli.atomic_write_text_file(second.path, 'value = "concurrent"\n').unwrap()
        observed = second.path.read_bytes()
        tm.fail(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, second, third),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(third.path.read_bytes(), eq=third.before.content)
        tm.that(second.path.read_bytes(), eq=observed)

    def test_semantic_publication_changes_authored_initializer(
        self,
        mod_workspace: Path,
    ) -> None:
        """An explicit semantic plan changes an authored initializer."""
        u.Tests.run_native_callable(self._scenario_authored_initializer, mod_workspace)

    @staticmethod
    def _scenario_authored_initializer(mod_workspace: Path) -> None:
        """An explicit semantic plan owns its authored initializer transformation."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        initializer = package / c.Infra.INIT_PY
        source = 'VALUE = "before"\n__all__ = ("VALUE",)\n'
        initializer.write_text(source, encoding="utf-8")
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(initializer, required=True),
        )
        plan = m.Infra.SemanticFilePlan(
            project=mod_workspace,
            path=initializer,
            before=before,
            desired_content=source.replace('"before"', '"after"').encode(),
            desired_mode=before.mode,
        )
        published = tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (plan,),
                repository_root=mod_workspace,
            ),
        )
        tm.that(published, eq=(initializer,))
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    f"from {mod_workspace.name} import VALUE; assert VALUE == 'after'",
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    },
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))

    def test_generated_later_plan_rejects_authored_earlier_plan(
        self,
        mod_workspace: Path,
    ) -> None:
        """A generated later plan rejects an authored earlier plan."""
        u.Tests.run_native_callable(self._scenario_generated_plan, mod_workspace)

    @staticmethod
    def _scenario_generated_plan(mod_workspace: Path) -> None:
        """Test generated later plan rejects authored earlier plan."""
        first, second = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
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
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, generated),
                repository_root=mod_workspace,
            ),
            has="canonical generator repair",
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    def test_none_content_preserves_the_file(self, mod_workspace: Path) -> None:
        """A plan with no desired content or mode preserves the file."""
        u.Tests.run_native_callable(self._scenario_none_content, mod_workspace)

    @staticmethod
    def _scenario_none_content(mod_workspace: Path) -> None:
        """Test none content preserves the file."""
        first, _ = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        noop = first.model_copy(update={"desired_content": None, "desired_mode": None})
        tm.that(
            tm.ok(
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (noop,),
                    repository_root=mod_workspace,
                ),
            ),
            eq=(),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)

    def test_declared_template_input_is_not_its_generated_projection(
        self,
        mod_workspace: Path,
    ) -> None:
        """A declared template input is not its generated projection.

        An arbitrary template is never treated as a projection input.

        """
        u.Tests.run_native_callable(self._scenario_template_input, mod_workspace)

    @staticmethod
    def _scenario_template_input(mod_workspace: Path) -> None:
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
                transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                    (plans[0], denied),
                    repository_root=mod_workspace,
                    codegen=policy,
                ),
                has="canonical generator repair",
            )
            tm.that(declared.read_text(), eq=content)
            tm.that(denied.path.read_text(), eq=content)
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
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
        """A later source rejected by the real formatter stops the whole batch.

        No file is published.

        """
        u.Tests.run_native_callable(self._scenario_formatter_rejection, mod_workspace)

    @staticmethod
    def _scenario_formatter_rejection(mod_workspace: Path) -> None:
        """Test real formatter rejects later source before any publication."""
        plans = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
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
            codemod.FlextInfraCodemodSemanticApply.apply_transaction_paths(
                mod_workspace,
                edits,
                source_preview=infra.source_preview(mod_workspace),
            )
        for plan in plans:
            tm.that(plan.path.read_bytes(), eq=plan.before.content)

    def test_real_semantic_caller_commits_normalized_source_idempotently(
        self,
        mod_workspace: Path,
    ) -> None:
        """The real semantic caller commits normalized source idempotently.

        A repeat changes nothing further.

        """
        u.Tests.run_native_callable(self._scenario_normalized_caller, mod_workspace)

    @staticmethod
    def _scenario_normalized_caller(mod_workspace: Path) -> None:
        """Test real semantic caller commits normalized source idempotently."""
        first, _ = TestsFlextInfraSemanticPublicationPlans._plans(mod_workspace)
        edit = m.Infra.SemanticMigrationEdit(
            file_path=first.path,
            original_source=first.path.read_text(),
            updated_source='value="after"\n',
            changes=("semantic normalization",),
        )
        codemod.FlextInfraCodemodSemanticApply.apply_transaction_paths(
            mod_workspace,
            (edit,),
            source_preview=infra.source_preview(mod_workspace),
        )
        published = first.path.read_text()
        tm.that(published, has="after")
        tm.that(published, lacks="before")
        repeated = edit.model_copy(
            update={"original_source": published, "updated_source": published},
        )
        codemod.FlextInfraCodemodSemanticApply.apply_transaction_paths(
            mod_workspace,
            (repeated,),
            source_preview=infra.source_preview(mod_workspace),
        )
        tm.that(first.path.read_text(), eq=published)
