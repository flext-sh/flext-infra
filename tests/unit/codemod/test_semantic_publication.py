"""Real public semantic publication, identity and fix-forward contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import config, infra
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from flext_infra.refactor import (
    FlextInfraAccessorMigrationReportMixin,
    FlextInfraImportNormalization,
)
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, m, p, r, tm, u

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraSemanticPublication:
    """Preserve successful effects and report each unsafe semantic target."""

    @staticmethod
    def test_input_union_preserves_shared_identity_and_rejects_conflicts(
        tmp_path: Path,
    ) -> None:
        """One source authority survives repeats; neither conflicting order wins."""
        source = tmp_path / "source.py"
        source.write_bytes(b"VALUE = 1\n")
        first = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        absent = tm.ok(u.Cli.atomic_read_binary_file_state(tmp_path / "optional"))
        shared = m.Cli.AtomicFileState.model_validate_json(first.model_dump_json())
        tm.that(
            tm.ok(
                FlextInfraCodegenPreconditions.unique_states((
                    first,
                    absent,
                    shared,
                    absent,
                ))
            ),
            eq=(first, absent),
        )
        source.write_bytes(b"VALUE = 2\n")
        changed = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        for observations in ((first, changed), (changed, first)):
            tm.fail(
                FlextInfraCodegenPreconditions.unique_states(observations),
                has=str(source),
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((changed, absent)))

    @staticmethod
    def test_cold_public_cli_composes_semantic_ports_without_an_import_cycle() -> None:
        """A fresh native CLI process must finish API composition before dispatch."""
        result = tm.ok(u.Cli.run((sys.executable, "-I", "-m", "flext_infra", "--help")))
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    def test_public_workspace_factory_preserves_selected_rope_root(
        tmp_path: Path,
    ) -> None:
        """The injected factory preserves the existing scoped workspace contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = "VALUE = 1\n"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root, root) as workspace:
            tm.not_none(workspace.module(path))
            tm.that(workspace.source(path), eq=source)

    @staticmethod
    def _rename_artifact(
        tmp_path: Path,
    ) -> t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]:
        """Build a native artifact against an independent physical runtime.

        Returns:
            The captured source candidate and its separate driver identity.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        notice = u.Infra.copyright_notice(root)
        (package / "service.py").write_text(
            f'"""Public callable contract.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n\n"
            "class FlextSemanticService:\n"
            '    """Preserve predicate behavior under an explicit domain rename."""\n\n'
            "    @staticmethod\n"
            "    def predicate(value: str) -> bool:\n"
            '        """Inspect a caller value.\n\n'
            "        Returns:\n"
            "            Whether the value is nonempty.\n"
            '        """\n'
            "        return bool(value)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = package / "consumer.py"
        consumer.write_text(
            f'"""Observed callable consumer.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n"
            f"from {package.name}.service import FlextSemanticService\n\n"
            'VALUE = FlextSemanticService.predicate("domain")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root,
                    workspace,
                    m.Infra.SemanticRenameSelections(
                        decisions=(
                            m.Infra.SemanticRenameSelection(
                                qualified_name=(
                                    f"{package.name}.service.FlextSemanticService.predicate"
                                ),
                                replacement_name="meaningful",
                                reason="Reviewed callable domain contract",
                            ),
                        )
                    ),
                )
            )
        tm.that(consumer in artifact.candidate.updates, eq=True)
        driver = root / "rename.artifact"
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        captured = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        tm.that(
            m.Infra.SemanticRenamePlan.model_validate_json(
                tm.not_none(captured.content)
            ),
            eq=artifact,
        )
        return artifact, captured

    @staticmethod
    @pytest.mark.parametrize("drift", ["none", "driver", "source", "snapshot"])
    def test_candidate_publication_keeps_driver_separate_and_authenticated(
        tmp_path: Path, drift: str
    ) -> None:
        """Native runtime acceptance never replaces source or driver snapshots."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(tmp_path)
        candidate = artifact.candidate
        tm.that(driver.path in {state.path for state in candidate.inputs}, eq=False)
        tm.ok(
            FlextInfraAccessorMigrationReportMixin.validate_candidate(
                candidate,
                infra.source_preview(candidate.workspace),
                tuple(u.Infra.snapshot_lint_gates()),
            )
        )
        originals = {state.path: state for state in candidate.inputs}
        plans = tuple(
            m.Infra.SemanticFilePlan(
                project=candidate.workspace,
                path=path,
                before=originals[path],
                desired_content=source.encode(c.DEFAULT_ENCODING),
                desired_mode=originals[path].mode,
                source_states=(driver,),
            )
            for path, source in candidate.updates.items()
        )
        source = plans[0].path
        if drift in {"driver", "snapshot"}:
            driver.path.write_bytes(tm.not_none(driver.content) + b"\n")
        elif drift == "source":
            source.write_bytes(source.read_bytes() + b"\n# Shared source update\n")
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(state.path))
            for state in candidate.inputs
        )
        driver_bytes = driver.path.read_bytes()
        inputs = (
            (tm.ok(u.Cli.atomic_read_binary_file_state(driver.path, required=True)),)
            if drift == "snapshot"
            else (driver,)
        )
        published = FlextInfraSemanticPublication.publish_source_candidate(
            plans, candidate=candidate, inputs=inputs
        )
        if drift == "none":
            tm.that(tm.ok(published), eq=tuple(candidate.updates))
            for path, desired in candidate.updates.items():
                tm.that(path.read_bytes(), eq=desired.encode(c.DEFAULT_ENCODING))
            before = tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(state.path))
                for state in candidate.inputs
            )
            tm.fail(
                FlextInfraSemanticPublication.publish_source_candidate(
                    plans, candidate=candidate, inputs=(driver,)
                )
            )
        elif drift == "snapshot":
            tm.fail(published, has=f"two states for {driver.path}")
        else:
            tm.fail(published)
        tm.ok(u.Cli.atomic_verify_binary_file_states(before))
        tm.that(driver.path.read_bytes(), eq=driver_bytes)

    @staticmethod
    def test_authenticated_rename_apply_publishes_then_rejects_stale_repeat(
        tmp_path: Path,
    ) -> None:
        """The actual artifact consumer applies once and preserves its stale driver."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(tmp_path)
        root = artifact.candidate.workspace
        request = m.Infra.ModCommand(
            repository_root=root, rename_plan=driver.path, apply=True
        )
        with infra.rope_workspace(root) as workspace:
            tm.that(
                tm.ok(
                    FlextInfraCodemodSemanticApply.consume_rename_plan(
                        request, workspace, infra.source_preview(root)
                    )
                ),
                eq=True,
            )
            published = {path: path.read_bytes() for path in artifact.candidate.updates}
            for path, desired in artifact.candidate.updates.items():
                tm.that(published[path], eq=desired.encode(c.DEFAULT_ENCODING))
            tm.fail(
                FlextInfraCodemodSemanticApply.consume_rename_plan(
                    request, workspace, infra.source_preview(root)
                )
            )
        for path, content in published.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(driver.path.read_bytes(), eq=driver.content)

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
                    (
                        f"from {mod_workspace.name} import DeclaredService; "
                        "assert DeclaredService.normalize(' live ') == 'LIVE'"
                    ),
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
                session,
                analysis.phase,
                plans,
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
                    analysis,
                    session=published.value,
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
            tm.that(
                foreign.read_text(encoding=c.DEFAULT_ENCODING), eq="foreign owner\n"
            )
        else:
            tm.ok(result)
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {mod_workspace.name}.relocated.nested import "
                            "DeclaredService; "
                            "assert DeclaredService.normalize(' live ') == 'LIVE'"
                        ),
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
                (
                    "import runpy, sys; "
                    "assert all(runpy.run_path(path)['value'] == 'after' "
                    "for path in sys.argv[1:])"
                ),
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
                (
                    "import runpy, sys; "
                    "assert all(runpy.run_path(path)['value'] == 'after' "
                    "for path in sys.argv[1:])"
                ),
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

        def validate(_candidate_root: Path) -> p.Result[bool]:
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

        def reject(candidate_root: Path) -> p.Result[bool]:
            consumer = tm.ok(
                u.Cli.run_raw((
                    sys.executable,
                    str(candidate_root / path.relative_to(mod_workspace)),
                ))
            )
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
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        report = m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence](
            files=frozenset(),
            entries=(),
        )
        with infra.rope_workspace(root) as rope:
            result = FlextInfraCodemodSemanticApply.apply(
                root,
                report,
                rope,
                source_preview=infra.source_preview(root),
                workspace_factory=infra.rope_workspace,
            )
        if rejected:
            tm.fail(result)
        else:
            tm.ok(result)
        tm.that(initializer.read_bytes() != original, eq=True)
        consumer = tm.ok(
            u.Cli.run_raw(
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
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=not rejected)
        if rejected:
            tm.that(consumer.stderr, has="consumer rejected")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_publication_refreshes_warm_normalized_export_route(
        mod_workspace: Path,
    ) -> None:
        """A moved declaration routes identically in warm and fresh consumers."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous.py"
        current = package / "current.py"
        consumer_path = package / "consumer.py"
        for path, exported in ((previous, True), (current, False)):
            path.write_text(
                "class DeclaredService:\n"
                "    @staticmethod\n"
                "    def execute() -> str:\n"
                f"        return {path.stem!r}\n\n"
                f"__all__ = {['DeclaredService'] if exported else []!r}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
            ),
        )
        original_source = (
            f"from {package.name}.{previous.stem} import DeclaredService\n\n"
            "def run() -> str:\n"
            "    return DeclaredService.execute()\n"
        )
        warmed = tm.not_none(
            FlextInfraImportNormalization.normalize_source(
                project_root=mod_workspace,
                file_path=consumer_path,
                source=original_source,
            ),
        )
        tm.that(warmed, has=f"from {package.name} import DeclaredService\n")
        candidate = original_source.replace(previous.stem, current.stem)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path in (previous, current):
            before = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            outgoing = ["DeclaredService"] if path == previous else []
            incoming = [] if path == previous else ["DeclaredService"]
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=path,
                    before=before,
                    desired_content=tm
                    .not_none(before.content)
                    .decode(c.DEFAULT_ENCODING)
                    .replace(
                        f"__all__ = {outgoing!r}",
                        f"__all__ = {incoming!r}",
                    )
                    .encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                ),
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_consumer = candidate_root / consumer_path.relative_to(
                mod_workspace
            )
            normalized = tm.not_none(
                FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=candidate,
                ),
            )
            tm.that(normalized, eq=warmed)
            tm.that(
                FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=normalized,
                ),
                eq=None,
            )
            fresh = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path\n"
                            "from flext_infra.refactor import (\n"
                            "    FlextInfraImportNormalization,\n"
                            ")\n"
                            "normalized = FlextInfraImportNormalization"
                            ".normalize_source(\n"
                            f"    project_root=Path({str(candidate_root)!r}),\n"
                            f"    file_path=Path({str(candidate_consumer)!r}),\n"
                            f"    source={candidate!r},\n"
                            ")\n"
                            f"assert normalized == {normalized!r}\n"
                            f"{normalized}\n"
                            f"assert run() == {current.stem!r}\n"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root
                                / package.parent.relative_to(mod_workspace)
                            ),
                        },
                    ),
                ),
            )
            tm.that(u.Cli.process_succeeded(fresh.outcome), eq=True)
            return r[bool].ok(True)

        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
                validator=validate,
            ),
        )
        initializer = package / c.Infra.INIT_PY
        published = initializer.read_bytes()
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
                validator=validate,
            ),
        )
        tm.that(initializer.read_bytes(), eq=published)

    @staticmethod
    def test_publication_refreshes_warm_normalized_export_route(
        mod_workspace: Path,
    ) -> None:
        """A moved declaration routes identically in warm and fresh consumers."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous.py"
        current = package / "current.py"
        consumer_path = package / "consumer.py"
        for path, exported in ((previous, True), (current, False)):
            path.write_text(
                "class DeclaredService:\n"
                "    @staticmethod\n"
                "    def execute() -> str:\n"
                f"        return {path.stem!r}\n\n"
                f"__all__ = {['DeclaredService'] if exported else []!r}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
            ),
        )
        original_source = (
            f"from {package.name}.{previous.stem} import DeclaredService\n\n"
            "def run() -> str:\n"
            "    return DeclaredService.execute()\n"
        )
        warmed = tm.not_none(
            FlextInfraImportNormalization.normalize_source(
                project_root=mod_workspace,
                file_path=consumer_path,
                source=original_source,
            ),
        )
        tm.that(warmed, has=f"from {package.name} import DeclaredService\n")
        candidate = original_source.replace(previous.stem, current.stem)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path in (previous, current):
            before = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            outgoing = ["DeclaredService"] if path == previous else []
            incoming = [] if path == previous else ["DeclaredService"]
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=path,
                    before=before,
                    desired_content=tm
                    .not_none(before.content)
                    .decode(c.DEFAULT_ENCODING)
                    .replace(
                        f"__all__ = {outgoing!r}",
                        f"__all__ = {incoming!r}",
                    )
                    .encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                ),
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_consumer = candidate_root / consumer_path.relative_to(
                mod_workspace
            )
            normalized = tm.not_none(
                FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=candidate,
                ),
            )
            tm.that(normalized, eq=warmed)
            tm.that(
                FlextInfraImportNormalization.normalize_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=normalized,
                ),
                eq=None,
            )
            fresh = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path\n"
                            "from flext_infra.refactor import (\n"
                            "    FlextInfraImportNormalization,\n"
                            ")\n"
                            "normalized = FlextInfraImportNormalization"
                            ".normalize_source(\n"
                            f"    project_root=Path({str(candidate_root)!r}),\n"
                            f"    file_path=Path({str(candidate_consumer)!r}),\n"
                            f"    source={candidate!r},\n"
                            ")\n"
                            f"assert normalized == {normalized!r}\n"
                            f"{normalized}\n"
                            f"assert run() == {current.stem!r}\n"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root
                                / package.parent.relative_to(mod_workspace)
                            ),
                        },
                    ),
                ),
            )
            tm.that(u.Cli.process_succeeded(fresh.outcome), eq=True)
            return r[bool].ok(True)

        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
                validator=validate,
            ),
        )
        initializer = package / c.Infra.INIT_PY
        published = initializer.read_bytes()
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                projection_roots=(mod_workspace,),
                validator=validate,
            ),
        )
        tm.that(initializer.read_bytes(), eq=published)

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
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        command = (
            sys.executable,
            "-c",
            (
                f"from {mod_workspace.name} import DeclaredService; "
                "assert isinstance(DeclaredService(), DeclaredService)"
            ),
        )
        options = m.Cli.ProcessOptions(
            env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)},
        )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_options = options.model_copy(
                update={
                    "env": {
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            candidate_root / package.parent.relative_to(mod_workspace)
                        ),
                    },
                },
            )
            consumer = u.Cli.run(
                command,
                cwd=candidate_root,
                options=candidate_options,
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
        else:
            tm.fail(published, has="consumer rejected")
        tm.that(initializer.read_bytes() != original, eq=accepted)
        consumer = tm.ok(
            u.Cli.run(command, cwd=mod_workspace, options=options),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=accepted)
        tm.that(declaration.read_text(encoding="utf-8"), eq=source)

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
        """The complete candidate is consumed before any original file changes."""
        plans = self._plans(mod_workspace)
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
            tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)
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
            FlextInfraSemanticPublication.publish_semantic_file_plans(
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
        """Complete admission rejects stale identity before any file is changed."""
        first, second, third = self._plans(
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
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (first, second, third),
                repository_root=mod_workspace,
            ),
        )
        tm.that(first.path.read_bytes(), eq=first.before.content)
        tm.that(third.path.read_bytes(), eq=third.before.content)
        tm.that(second.path.read_bytes(), eq=observed)

    @staticmethod
    def test_semantic_publication_changes_authored_initializer(
        mod_workspace: Path,
    ) -> None:
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
            FlextInfraSemanticPublication.publish_semantic_file_plans(
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
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)

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
            FlextInfraCodemodSemanticApply.apply_transaction_paths(
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
        """Test real semantic caller commits normalized source idempotently."""
        first, _ = self._plans(mod_workspace)
        edit = m.Infra.SemanticMigrationEdit(
            file_path=first.path,
            original_source=first.path.read_text(),
            updated_source='value="after"\n',
            changes=("semantic normalization",),
        )
        FlextInfraCodemodSemanticApply.apply_transaction_paths(
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
        FlextInfraCodemodSemanticApply.apply_transaction_paths(
            mod_workspace,
            (repeated,),
            source_preview=infra.source_preview(mod_workspace),
        )
        tm.that(first.path.read_text(), eq=published)
