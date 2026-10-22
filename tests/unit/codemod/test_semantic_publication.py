"""Real public semantic publication, identity and fix-forward contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import codegen, codemod, infra, refactor, services, transformers
from tests import c, m, tm, u

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraSemanticPublication:
    """Preserve successful effects and report each unsafe semantic target."""

    @staticmethod
    def _rename_artifact(
        tmp_path: Path,
        *,
        kind: str = "callable",
        external_consumers: int = 0,
        executable: bool = False,
    ) -> t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]:
        """Build a native artifact against an independent physical runtime.

        Returns:
            The captured source candidate and its separate driver identity.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        driver = root / c.Infra.REPORTS_DIR_NAME / "native" / "rename.artifact"
        driver.parent.mkdir(parents=True, exist_ok=True)
        notice = u.Infra.copyright_notice(root)
        source = package / "service.py"
        source.write_text(
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
        if executable:
            source.chmod(stat.S_IMODE(source.stat().st_mode) | stat.S_IXUSR)
        consumer_roots: list[Path] = []
        for index in range(external_consumers):
            receiver, receiver_package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=f"native-receiver-{index}",
                package_name=f"native_receiver_{index}",
            )
            u.Tests.provision_checkout(receiver)
            u.Tests.provision_runtime_environment(receiver)
            (receiver_package / "consumer.py").write_text(
                consumer.read_text(encoding=c.DEFAULT_ENCODING),
                encoding=c.DEFAULT_ENCODING,
            )
            consumer_roots.append(receiver)
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    root,
                    workspace,
                    m.Infra.SemanticRenameSelections(
                        decisions=(
                            m.Infra.SemanticRenameSelection(
                                qualified_name=(
                                    f"{package.name}.service"
                                    + (
                                        ".FlextSemanticService"
                                        if kind != "module"
                                        else ""
                                    )
                                    + (".predicate" if kind == "callable" else "")
                                ),
                                replacement_name="FlextMeaningfulService"
                                if kind == "class"
                                else "meaningful",
                                reason="Reviewed callable domain contract",
                            ),
                        ),
                        consumer_roots=tuple(consumer_roots),
                    ),
                )
            )
        tm.ok(consumer in artifact.candidate.updates)
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        captured = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        hydrated = m.Infra.SemanticRenamePlan.model_validate_json(
            tm.not_none(captured.content)
        )
        tm.that(
            hydrated.model_dump(mode="python"),
            eq=artifact.model_dump(mode="python"),
        )
        return hydrated, captured

    @pytest.mark.parametrize("kind", ["class", "module"])
    def test_mod_composes_native_cross_root_effects_and_is_idempotent(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """Public mod composes one native candidate across roots, idempotently."""
        u.Tests.run_native_callable(self._scenario_cross_root_mod, tmp_path, kind)

    @staticmethod
    def _scenario_cross_root_mod(tmp_path: Path, kind: str) -> None:
        """The normal public mod action consumes one coordinated native candidate."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path,
            kind=kind,
            external_consumers=2,
            executable=kind == "module",
        )
        root = (artifact.candidate.workspaces or (artifact.candidate.workspace,))[0]
        for receiver in artifact.consumer_roots:
            inventory = next(
                item
                for item in artifact.source_directories
                if item.root.path == receiver
            )
            tm.ok(
                any(
                    entry.name == c.Infra.TRANSACTION_STATE_DIRNAME
                    and entry.kind == "directory"
                    for entry in inventory.entries
                )
            )
        source = next(
            state
            for state in artifact.candidate.inputs
            if state.path.name == "service.py"
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".git" / "persisted-plan-metadata", "metadata\n"
            )
        )
        with infra.rope_workspace(root) as workspace:
            rebuilt = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    root,
                    workspace,
                    codemod.FlextInfraCodemodSemanticApply.rename_selections(artifact),
                    source_plan=artifact,
                )
            )
        tm.ok(any(effect.source_states for effect in rebuilt.candidate.declared_files))
        tm.ok(
            all(
                not effect.source_states for effect in artifact.candidate.declared_files
            )
        )
        for original, retained in zip(
            artifact.source_directories, rebuilt.source_directories, strict=True
        ):
            tm.that(retained is original, truth=True)
        tm.that(
            rebuilt.model_dump(mode="python"), eq=artifact.model_dump(mode="python")
        )
        if kind == "class":
            tm.ok(root != artifact.candidate.workspace)
            preview = tm.ok(
                infra.source_preview(root).preview_sources(
                    artifact.candidate.workspace,
                    artifact.candidate.updates,
                    lambda view_root, _paths: (
                        codemod.FlextInfraModGateEngine.scan_candidate(
                            root, view_root, artifact.candidate
                        ).unwrap()
                    ),
                    options=m.Infra.CodegenSourcePreviewOptions(
                        inputs=artifact.candidate.inputs,
                        workspaces=artifact.candidate.workspaces,
                        modes=artifact.candidate.modes,
                        runtime_check=False,
                    ),
                )
            )
            source_states = tm.not_none(preview.source_states)
            tm.ok(any(state.path == source.path for state in source_states))
            tm.ok(all(state.path.is_relative_to(root) for state in source_states))
            tm.ok(u.Cli.atomic_verify_binary_file_states(artifact.candidate.inputs))
            tm.ok(
                codegen.FlextInfraStagedPackage.source_inputs_current(
                    artifact.candidate
                )
            )
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    rename_plan=driver.path,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            )
        )
        if kind == "module":
            origin, target = artifact.moves[0]
            tm.fail(origin.exists())
            tm.that(stat.S_IMODE(target.stat().st_mode), eq=source.mode)
        for receiver in artifact.consumer_roots:
            package = next(
                layout.package_name
                for layout in artifact.candidate.layouts
                if layout.project_root == receiver
            )
            tm.that(
                u.Tests.run_lazy_init_probe(
                    f"from {package}.consumer import VALUE\nprint(VALUE)\n",
                    python_paths=tuple(
                        str(layout.src_dir) for layout in artifact.candidate.layouts
                    ),
                ),
                eq=["True"],
            )
        published = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for scope in (root, *artifact.consumer_roots)
            for path in u.Infra.discover_python_files(
                scope, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(published))
        tm.that(driver.path.read_bytes(), eq=driver.content)

    @pytest.mark.parametrize(
        "drift", ["edits", "membership", "identity", "foreign-directory"]
    )
    def test_mod_rejects_changed_persisted_rename_payload(
        self, tmp_path: Path, drift: str
    ) -> None:
        """A persisted rename payload that drifted from its plan is rejected.

        Drift covers edits, membership, identity and a foreign directory.

        """
        u.Tests.run_native_callable(self._scenario_payload_drift, tmp_path, drift)

    @staticmethod
    def _scenario_payload_drift(tmp_path: Path, drift: str) -> None:
        """Ephemeral receipt exclusion never permits a different persisted edit plan."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path,
            kind="class",
            external_consumers=1 if drift == "foreign-directory" else 0,
        )
        tm.that(artifact.edits, empty=False)
        changed = artifact.model_copy(update={"edits": ()})
        tm.ok(u.Cli.atomic_write_text_file(driver.path, changed.model_dump_json()))
        observed_driver = tm.ok(
            u.Cli.atomic_read_binary_file_state(driver.path, required=True)
        )
        root = (artifact.candidate.workspaces or (artifact.candidate.workspace,))[0]
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".git" / "persisted-plan-metadata", "metadata\n"
            )
        )
        source = next(
            state for state in artifact.source_states if state.path.name == "service.py"
        )
        expected_error = "fields=edits"
        if drift == "membership":
            (source.path.parent / "new_consumer.py").write_text(
                "VALUE = 1\n", encoding=c.DEFAULT_ENCODING
            )
            expected_error = str(source.path.parent)
        elif drift == "identity":
            replacement = source.path.with_suffix(".replacement")
            replacement.write_bytes(tm.not_none(source.content))
            replacement.chmod(tm.not_none(source.mode))
            replacement.replace(source.path)
            expected_error = str(source.path)
        elif drift == "foreign-directory":
            receiver = artifact.consumer_roots[0]
            foreign = receiver / "foreign-controller"
            foreign.mkdir()
            expected_error = str(receiver)
            tm.fail(
                codegen.FlextInfraStagedPackage.source_inputs_current(
                    artifact.candidate
                ),
                has=expected_error,
            )
        tm.fail(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    apply=True,
                    rename_plan=driver.path,
                    consumer_roots=artifact.consumer_roots,
                ),
                mod_progress,
            ),
            has=expected_error,
        )
        tm.ok(
            u.Cli.atomic_verify_binary_file_states((
                *(
                    state
                    for state in (*artifact.candidate.inputs, *artifact.source_states)
                    if drift != "identity" or state.path != source.path
                ),
                observed_driver,
            ))
        )

    @pytest.mark.slow
    @pytest.mark.parametrize("needs_ast", [False, True])
    def test_source_campaign_applies_ast_without_a_rename_artifact(
        self,
        tmp_path: Path,
        *,
        needs_ast: bool,
    ) -> None:
        """A source campaign applies without a rename artifact, with or without AST.

        The repeat of the same campaign is a no-op.

        """
        u.Tests.run_native_callable(
            self._scenario_source_campaign,
            tmp_path,
            needs_ast=needs_ast,
        )

    @staticmethod
    def _scenario_source_campaign(tmp_path: Path, *, needs_ast: bool) -> None:
        """The public pipeline accepts real automatic work and its no-op repeat."""
        mod_progress = services.FlextInfraCliModProgress()
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        u.Tests.declare_codemod_rules(
            root,
            {
                "source-campaign": (
                    "id: source-campaign\n"
                    "language: Python\n"
                    "rule:\n"
                    "  pattern: 'value: int = 1'\n"
                    "fix: 'value: int = 2'\n"
                    "severity: warning\n"
                )
            },
        )
        source = package / "service.py"
        notice = u.Infra.copyright_notice(root)
        source.write_text(
            f'"""Automatic source campaign.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n"
            f"value: int = {1 if needs_ast else 2}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tm.ok(codemod.FlextInfraModGateEngine.scan(root, fix=False))
        tm.that(bool(before.actionable), eq=needs_ast)
        request = m.Infra.ModCommand(repository_root=root, apply=True)
        tm.ok(infra.mod(request, mod_progress))
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.service import value\nprint(value)\n",
                python_paths=(str(package.parent),),
            ),
            eq=["2"],
        )
        tm.that(
            tm.ok(codemod.FlextInfraModGateEngine.scan(root, fix=False)).findings, eq=0
        )
        published = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        tm.ok(infra.mod(request, mod_progress))
        tm.ok(u.Cli.atomic_verify_binary_file_states((published,)))

    @staticmethod
    @pytest.mark.parametrize("retire", [False, True])
    def test_source_effect_rejects_unpaired_content_and_mode(
        tmp_path: Path, *, retire: bool
    ) -> None:
        """A deletion clears mode; a write always declares its actual mode."""
        source = tmp_path / "source.py"
        source.write_text("value = 1\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        with pytest.raises(ValueError, match="desired bytes and mode"):
            m.Infra.CodegenFilePlan(
                project=tmp_path,
                path=source,
                before=original,
                desired_content=None if retire else original.content,
                desired_mode=original.mode if retire else None,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @pytest.mark.parametrize("drift", ["none", "source", "directory", "same-byte"])
    def test_composed_module_rename_preserves_mode_and_original_receipts(
        self, tmp_path: Path, drift: str
    ) -> None:
        """A composed module rename keeps executable mode and original receipts.

        Drifted source, directory or same-byte inputs are refused.

        """
        u.Tests.run_native_callable(self._scenario_composed_rename, tmp_path, drift)

    @staticmethod
    def _scenario_composed_rename(tmp_path: Path, drift: str) -> None:
        """Composition preserves strict rename intent, executable mode and CAS."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path, kind="module", executable=True
        )
        root = artifact.candidate.workspace
        origin, target = artifact.moves[0]
        originals = {state.path: state for state in artifact.candidate.inputs}
        composed = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.compose_candidate(
                artifact,
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                    inputs=(driver,),
                    files=(
                        m.Infra.CodegenFilePlan(
                            project=root,
                            path=target,
                            before=originals[target],
                            desired_content=tm.not_none(
                                artifact.candidate.updates[target]
                            ).encode(c.DEFAULT_ENCODING),
                            desired_mode=artifact.candidate.modes[target],
                            source_states=artifact.source_states,
                            source_directories=artifact.source_directories,
                            source_query_topology=artifact.source_query_topology,
                        ),
                    ),
                ),
            )
        )
        tm.that(composed, is_=m.Infra.SemanticRenamePlan)
        tm.that(composed.decisions, eq=artifact.decisions)
        tm.that(composed.edits, eq=artifact.edits)
        tm.that(composed.moves, eq=artifact.moves)
        tm.that(composed.candidate.modes[target], eq=originals[origin].mode)
        tm.ok(driver in composed.source_states)
        if drift == "source":
            origin.write_bytes(tm.not_none(originals[origin].content) + b"\n")
        elif drift == "directory":
            (origin.parent / "new_consumer.py").write_text(
                "value = 1\n", encoding=c.DEFAULT_ENCODING
            )
        elif drift == "same-byte":
            foreign = origin.with_suffix(".foreign")
            foreign.write_bytes(tm.not_none(originals[origin].content))
            foreign.chmod(tm.not_none(originals[origin].mode))
            foreign.replace(origin)
        observed = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path)) for path in originals
        )
        published = codemod.FlextInfraCodemodSemanticApply.publish_candidate(
            root, composed
        )
        if drift == "none":
            tm.ok(published)
            tm.fail(origin.exists())
            tm.that(stat.S_IMODE(target.stat().st_mode), eq=originals[origin].mode)
        else:
            tm.fail(published)
            tm.ok(u.Cli.atomic_verify_binary_file_states(observed))
        tm.that(driver.path.read_bytes(), eq=driver.content)

    def test_automatic_nesting_rewrites_declared_consumers_without_syntax_fanout(
        self,
        tmp_path: Path,
    ) -> None:
        """Automatic nesting rewrites declared consumers without syntax fan-out.

        The rule selects the owner while external read scope stays bounded.

        """
        u.Tests.run_native_callable(self._scenario_nesting, tmp_path)

    @staticmethod
    def _scenario_nesting(tmp_path: Path) -> None:
        """Rule authority selects the owner while external read scope stays bounded."""
        mod_progress = services.FlextInfraCliModProgress()
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="native-receiver",
            package_name="native_receiver",
        )
        for checkout in (root, receiver):
            u.Tests.provision_checkout(checkout)
            u.Tests.provision_runtime_environment(checkout)
        alias = next(
            letter
            for letter, family in u.Infra.facade_families().items()
            if family.module == "models"
        )
        source = package / f"{u.Tests.family_public_module(alias)}.py"
        source.write_text("", encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as graph:
            owner = (
                graph.convention(source).module_policy.project_prefix
                + u.Infra.facade_family_declared_by(source.name).suffix
            )
        source.write_text(
            f'class {owner}:\n    """Native public family owner."""\n\n'
            'class Payload:\n    """Native introducing declaration."""\n'
            '    VALUE = "native"\n\n'
            f'__all__ = ({owner!r}, "Payload")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.{source.stem} import Payload as Bound\n"
            "VALUE = Bound.VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        unrelated = receiver_package / "unrelated.py"
        unrelated.write_text(
            'class Payload:\n    VALUE = "local"\nVALUE = Payload.VALUE\n',
            encoding=c.DEFAULT_ENCODING,
        )
        original = tm.ok(u.Cli.atomic_read_binary_file_state(unrelated, required=True))
        tm.ok(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    consumer_roots=(receiver,),
                    apply=True,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from native_receiver.consumer import VALUE\nprint(VALUE)\n",
                python_paths=(str(package.parent), str(receiver_package.parent)),
            ),
            eq=["native"],
        )
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), has="    class Payload:")

    @pytest.mark.parametrize("failure", ["missing", "collision", "drift"])
    def test_mod_refuses_invalid_cross_root_campaign_before_source_publication(
        self,
        tmp_path: Path,
        failure: str,
    ) -> None:
        """An invalid cross-root campaign is refused before any source is published.

        Invalid means a missing scope, an occupied native name or stale epochs.

        """
        u.Tests.run_native_callable(self._scenario_invalid_campaign, tmp_path, failure)

    @staticmethod
    def _scenario_invalid_campaign(tmp_path: Path, failure: str) -> None:
        """Missing scope, occupied native name and stale epochs stay unpublished."""
        mod_progress = services.FlextInfraCliModProgress()
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path,
            kind="class",
            external_consumers=1,
        )
        root = artifact.candidate.workspaces[0]
        roots = artifact.consumer_roots
        if failure == "missing":
            roots = (*roots, tmp_path / "missing-consumer")
        elif failure == "collision":
            declaration = next(
                state.path
                for state in artifact.candidate.inputs
                if state.path.name == "service.py"
            )
            declaration.write_text(
                declaration.read_text(encoding=c.DEFAULT_ENCODING)
                + "\nclass FlextMeaningfulService:\n    pass\n",
                encoding=c.DEFAULT_ENCODING,
            )
        else:
            consumer = next(
                state.path
                for state in artifact.candidate.inputs
                if state.path.name == "consumer.py"
                and state.path.is_relative_to(roots[0])
            )
            consumer.write_bytes(
                consumer.read_bytes() + b"# a different physical epoch\n"
            )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for scope in (root, *artifact.consumer_roots)
            for path in u.Infra.discover_python_files(
                scope, workspace_excluded_top_dirs=frozenset()
            )
        )
        tm.fail(
            infra.mod(
                m.Infra.ModCommand(
                    repository_root=root,
                    consumer_roots=roots,
                    rename_plan=driver.path,
                    apply=True,
                ),
                mod_progress,
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @pytest.mark.parametrize("drift", ["none", "driver", "source", "snapshot"])
    def test_candidate_publication_keeps_driver_separate_and_authenticated(
        self, tmp_path: Path, drift: str
    ) -> None:
        """Candidate publication keeps the driver apart and authenticated.

        A drifted driver, source or snapshot is rejected.

        """
        u.Tests.run_native_callable(self._scenario_driver_identity, tmp_path, drift)

    @staticmethod
    def _scenario_driver_identity(tmp_path: Path, drift: str) -> None:
        """Native runtime acceptance never replaces source or driver snapshots."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(tmp_path)
        candidate = artifact.candidate
        tm.fail(driver.path in {state.path for state in candidate.inputs})
        tm.ok(
            refactor.FlextInfraAccessorMigrationReportMixin.validate_candidate(
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
                desired_content=tm.not_none(source).encode(c.DEFAULT_ENCODING),
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
        published = transformers.FlextInfraSemanticPublication.publish_source_candidate(
            plans, candidate=candidate, inputs=inputs
        )
        if drift == "none":
            tm.that(tm.ok(published), eq=tuple(candidate.updates))
            for path, desired in candidate.updates.items():
                tm.that(
                    path.read_bytes(),
                    eq=tm.not_none(desired).encode(c.DEFAULT_ENCODING),
                )
            before = tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(state.path))
                for state in candidate.inputs
            )
            tm.fail(
                transformers.FlextInfraSemanticPublication.publish_source_candidate(
                    plans, candidate=candidate, inputs=(driver,)
                )
            )
        elif drift == "snapshot":
            tm.fail(published, has=f"two states for {driver.path}")
        else:
            tm.fail(published)
        tm.ok(u.Cli.atomic_verify_binary_file_states(before))
        tm.that(driver.path.read_bytes(), eq=driver_bytes)

    @pytest.mark.parametrize("kind", ["callable", "class", "module"])
    def test_authenticated_rename_apply_publishes_then_rejects_stale_repeat(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """An authenticated rename applies once and rejects a stale repeat."""
        u.Tests.run_native_callable(self._scenario_stale_repeat, tmp_path, kind)

    @staticmethod
    def _scenario_stale_repeat(tmp_path: Path, kind: str) -> None:
        """The actual artifact consumer applies once and preserves its stale driver."""
        artifact, driver = TestsFlextInfraSemanticPublication._rename_artifact(
            tmp_path, kind=kind
        )
        root = artifact.candidate.workspace
        request = m.Infra.ModCommand(
            repository_root=root, rename_plan=driver.path, apply=True
        )
        with infra.rope_workspace(root) as workspace:
            tm.that(
                tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                        request, workspace, infra.source_preview(root)
                    )
                ),
                eq=True,
            )
            published = {
                path: path.read_bytes() if path.exists() else None
                for path in artifact.candidate.updates
            }
            for path, desired in artifact.candidate.updates.items():
                tm.that(
                    published[path],
                    eq=None if desired is None else desired.encode(c.DEFAULT_ENCODING),
                )
            tm.fail(
                codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                    request, workspace, infra.source_preview(root)
                )
            )
        for path, content in published.items():
            tm.that(path.read_bytes() if path.exists() else None, eq=content)
        tm.that(driver.path.read_bytes(), eq=driver.content)
        consumer = next(
            path for path in artifact.candidate.updates if path.name == "consumer.py"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {consumer.parent.name}.consumer import VALUE\nprint(VALUE)\n",
                python_paths=(str(consumer.parent.parent),),
            ),
            eq=["True"],
        )

    @pytest.mark.parametrize("kind", ["class", "module"])
    def test_native_rename_artifact_preserves_originals_and_refuses_consumer_drift(
        self,
        tmp_path: Path,
        kind: str,
    ) -> None:
        """A rename artifact preserves originals and refuses consumer drift.

        A changed external consumer epoch rejects the cut before the producer
        changes.

        """
        u.Tests.run_native_callable(self._scenario_consumer_drift, tmp_path, kind)

    @staticmethod
    def _scenario_consumer_drift(tmp_path: Path, kind: str) -> None:
        """A changed external epoch rejects the cut before the producer changes."""
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer_root, consumer_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="native-consumer",
            package_name="native_consumer",
        )
        declaration = package / "original.py"
        declaration.write_text(
            "class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        consumer = consumer_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.original import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(producer) as workspace:
            artifact = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.build_rename_plan(
                    producer,
                    workspace,
                    m.Infra.SemanticRenameSelections(
                        decisions=(
                            m.Infra.SemanticRenameSelection(
                                qualified_name=f"{package.name}.original"
                                + (".Original" if kind == "class" else ""),
                                replacement_name="Renamed"
                                if kind == "class"
                                else "renamed",
                                reason=(
                                    "Coordinated native producer and consumer "
                                    "identity cut"
                                ),
                            ),
                        ),
                        consumer_roots=(consumer_root,),
                    ),
                )
            )
            driver = producer / "native.artifact"
            tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
            before = declaration.read_bytes()
            changed = consumer.read_bytes() + b"# independent source epoch\n"
            consumer.write_bytes(changed)
            tm.fail(
                codemod.FlextInfraCodemodSemanticApply.consume_rename_plan(
                    m.Infra.ModCommand(
                        repository_root=producer, rename_plan=driver, apply=True
                    ),
                    workspace,
                    infra.source_preview(producer),
                )
            )
        tm.that(declaration.read_bytes(), eq=before)
        tm.that(consumer.read_bytes(), eq=changed)
        tm.fail(declaration.with_name("renamed.py").exists())
