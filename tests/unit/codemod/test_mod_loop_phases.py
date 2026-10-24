"""Unit tests for the mod loop's callback repair phases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, infra, m, p
from flext_infra.codegen.staged_package import FlextInfraStagedPackage
from flext_infra.codemod import (
    FlextInfraAccessorRenamePhase,
    FlextInfraApplyRenames,
    FlextInfraCodemodBatchApply,
    FlextInfraModGateEngine,
    FlextInfraNamespaceRelocationPhase,
)
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, tm, u

_SOURCE_NAME = next(iter(c.ENFORCEMENT_ACCESSOR_RENAMES))
_REPLACEMENT_NAME = c.ENFORCEMENT_ACCESSOR_RENAMES[_SOURCE_NAME][0]


class _RecordingProgress:
    """Minimal real ModProgress transport that records emissions for asserts."""

    def __init__(self) -> None:
        """Initialize an empty emission log."""
        self.messages: list[str] = []

    def emit(self, message: str) -> None:
        """Record one progress line."""
        self.messages.append(message)

    def emit_rename(self, report: m.Infra.ApplyRenamesReport) -> None:
        """Record one rename campaign summary."""
        self.messages.append(f"rename occurrences={report.occurrences}")


def _phase_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    """Build one workspace owning a protocol violation and a rename target.

    Returns ``(workspace, project, service_file, legacy_file, foreign_file)``;
    the phases are driven with ``project`` as the repository root, exactly as
    the mod loop runs inside one repository.

    Returns:
        The resulting ``tuple[Path, Path, Path, Path, Path]``.

    """
    workspace, project, pkg = u.Tests.namespace_workspace(
        tmp_path,
        package_name="flext_core",
        pyproject=(
            "[project]\nname='flext-core'\n"
            f"version='{config.Infra.initial_project_version}'\n"
        ),
    )
    _ = u.Tests.src_package(
        workspace,
        "workspace_root",
        pyproject=(
            "[project]\nname='workspace-root'\n"
            f"version='{config.Infra.initial_project_version}'\n"
        ),
    )
    u.Tests.copy_tracked_mise_seeds(project)
    service_file = pkg / "service.py"
    _ = service_file.write_text(
        "from __future__ import annotations\n"
        "from typing import Protocol\n\n"
        "class ServiceContract(Protocol):\n"
        '    """Service contract under relocation."""\n'
        "\n"
        "    def run(self) -> str:\n"
        '        """Run the contract."""\n'
        "        ...\n",
        encoding="utf-8",
    )
    legacy_file = pkg / "legacy.py"
    _ = legacy_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        f"def {_SOURCE_NAME}(flag: bool) -> bool:\n"
        "    return flag\n"
        "\n"
        "\n"
        f"value = {_SOURCE_NAME}(True)\n",
        encoding="utf-8",
    )
    foreign_pkg = project / "src" / "other_pkg"
    foreign_pkg.mkdir(parents=True, exist_ok=True)
    _ = (foreign_pkg / "__init__.py").write_text("", encoding="utf-8")
    foreign_file = foreign_pkg / "legacy.py"
    _ = foreign_file.write_text(
        "from __future__ import annotations\n"
        "\n"
        f"def {_SOURCE_NAME}(flag: bool) -> bool:\n"
        "    return flag\n",
        encoding="utf-8",
    )
    u.Tests.provision_checkout(workspace)
    return workspace, project, service_file, legacy_file, foreign_file


def _apply_accessor(project: Path, *, callback: bool) -> p.Result[bool]:
    """Exercise the same candidate through the public verb or loop callback.

    Returns:
        The real public candidate verdict without substituting its validators.

    """
    if not callback:
        return infra.accessor_migrate(
            m.Infra.AccessorMigrationInput(repository_root=project, apply=True)
        ).map(lambda report: bool(report.automated_change_count))
    with infra.rope_workspace(project) as rope:
        preflight = FlextInfraModGateEngine.scan(project, fix=False).unwrap()
        return FlextInfraAccessorRenamePhase(
            source_preview=infra.source_preview(project)
        ).apply(project, preflight, rope)


class TestsFlextInfraCodemodLoopPhases:
    """Behavior contract for test_mod_loop_phases."""

    @staticmethod
    def test_managed_scanner_keeps_resolution_outside_consumer_cwd(
        tmp_path: Path,
    ) -> None:
        """Resolve at the declared owner, then scan a tree with no Mise declaration."""
        project = u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="scan-target",
            pkg_name="scan_target",
            files={"module.py": "value = 1\n"},
        )
        owner = Path(__file__).resolve().parents[3]
        binary = tm.ok(u.Infra.managed_mise_binary("ast-grep", owner))
        tm.ok(binary.is_absolute())
        tm.fail((project / c.Infra.MISE_TOML_FILENAME).exists())
        report = tm.ok(FlextInfraModGateEngine.scan(project, fix=False))
        tm.that(
            any(entry.file.name == "module.py" for entry in report.entries), eq=True
        )

    @staticmethod
    def test_namespace_phase_relocates_from_the_loop_scan(
        tmp_path: Path,
    ) -> None:
        """The relocation callback consumes the loop's own preflight scan."""
        _workspace, project, service_file, _legacy, _foreign = _phase_fixture(
            tmp_path,
        )
        with infra.rope_workspace(project) as rope:
            preflight = FlextInfraModGateEngine.scan(project, fix=False).unwrap()
            phase = FlextInfraNamespaceRelocationPhase()
            states = tuple(
                u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in u.Infra.iter_python_files(
                    m.Infra.SourceScanRequest(project_roots=(project,)),
                ).unwrap()
            )
            sources = {
                state.path: tm.not_none(state.content).decode(c.DEFAULT_ENCODING)
                for state in states
            }
            frozen = dict(sources)
            analysis = phase.plan(
                project,
                preflight,
                rope,
                sources=sources,
                receipt=m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                    inputs=states,
                    files=(),
                ),
            ).unwrap()
            tm.that(analysis.files, empty=False)
            tm.that(analysis.issues, empty=True)
            tm.that(sources, eq=frozen)
            for state in states:
                tm.that(state.path.read_bytes(), eq=state.content)
            for plan in analysis.files:
                if plan.path in sources:
                    tm.that(
                        plan.before,
                        eq=next(state for state in states if state.path == plan.path),
                    )
                else:
                    tm.fail(plan.path.exists())
            changed = phase.apply(project, preflight, rope)

        tm.fail(changed.failure)
        tm.ok(changed.value)
        protocols_file = service_file.parent / "protocols.py"
        tm.ok(protocols_file.exists())
        tm.that(
            protocols_file.read_text(encoding="utf-8"),
            has="class ServiceContract(Protocol):",
        )

    @staticmethod
    def test_accessor_phase_renames_only_origin_owned_occurrences(
        tmp_path: Path,
    ) -> None:
        """The accessor callback keeps foreign homonyms untouched in the loop."""
        _workspace, project, _service, legacy_file, foreign_file = _phase_fixture(
            tmp_path,
        )
        with infra.rope_workspace(project) as rope:
            preflight = FlextInfraModGateEngine.scan(project, fix=False).unwrap()
            phase = FlextInfraAccessorRenamePhase(
                source_preview=infra.source_preview(project)
            )

            changed = phase.apply(project, preflight, rope)

        tm.fail(changed.failure)
        tm.ok(changed.value)
        legacy_source = legacy_file.read_text(encoding="utf-8")
        tm.that(legacy_source, has=f"def {_REPLACEMENT_NAME}(")
        tm.that(legacy_source, lacks=f"def {_SOURCE_NAME}(")
        foreign_source = foreign_file.read_text(encoding="utf-8")
        tm.that(foreign_source, has=f"def {_SOURCE_NAME}(")

    @staticmethod
    @pytest.mark.parametrize("callback", [False, True])
    def test_accessor_candidate_closes_declaration_and_consumer(
        tmp_path: Path,
        *,
        callback: bool,
    ) -> None:
        """Both public paths rename a coupled import and declaration together."""
        _workspace, project, _service, legacy, foreign = _phase_fixture(tmp_path)
        consumer = legacy.parent / "consumer.py"
        _ = consumer.write_text(
            f"from flext_core.legacy import {_SOURCE_NAME}\n\n"
            f"value = {_SOURCE_NAME}(True)\n",
            encoding="utf-8",
        )
        foreign_before = foreign.read_bytes()

        result = _apply_accessor(project, callback=callback)

        tm.fail(result.failure)
        tm.ok(result.value)
        tm.that(legacy.read_text(encoding="utf-8"), has=f"def {_REPLACEMENT_NAME}(")
        tm.that(consumer.read_text(encoding="utf-8"), lacks=_SOURCE_NAME)
        tm.that(consumer.read_text(encoding="utf-8"), has=_REPLACEMENT_NAME)
        tm.that(foreign.read_bytes(), eq=foreign_before)

    @staticmethod
    @pytest.mark.parametrize("callback", [False, True])
    def test_accessor_rejection_precedes_both_shared_mutations(
        tmp_path: Path,
        *,
        callback: bool,
    ) -> None:
        """A rename collision rejects the complete candidate, not its second file."""
        _workspace, project, _service, legacy, _foreign = _phase_fixture(tmp_path)
        with legacy.open("a", encoding="utf-8") as stream:
            _ = stream.write(
                f"\n\ndef {_REPLACEMENT_NAME}(flag: bool) -> bool:\n"
                "    return not flag\n"
            )
        consumer = legacy.parent / "consumer.py"
        _ = consumer.write_text(
            f"from flext_core.legacy import {_SOURCE_NAME}\n\n"
            f"value = {_SOURCE_NAME}(True)\n",
            encoding="utf-8",
        )
        before = {path: path.read_bytes() for path in (legacy, consumer)}

        result = _apply_accessor(project, callback=callback)

        tm.ok(result.failure)
        for path, content in before.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    @pytest.mark.parametrize("callback", [False, True])
    def test_protected_accessor_publication_returns_failure(
        tmp_path: Path,
        *,
        callback: bool,
    ) -> None:
        """Generated-owner refusal is a real failure, never an advisory success."""
        _workspace, project, _service, legacy, _foreign = _phase_fixture(tmp_path)
        source = legacy.read_text(encoding="utf-8")
        _ = legacy.write_text(
            c.Infra.AUTOGEN_HEADERS[0] + "\n" + source,
            encoding="utf-8",
        )
        consumer = legacy.parent / "consumer.py"
        _ = consumer.write_text(
            f"from flext_core.legacy import {_SOURCE_NAME}\n\n"
            f"value = {_SOURCE_NAME}(True)\n",
            encoding="utf-8",
        )
        before = {path: path.read_bytes() for path in (legacy, consumer)}

        result = _apply_accessor(project, callback=callback)

        tm.ok(result.failure)
        tm.that(
            result.error, has="generated findings require canonical generator repair"
        )
        if not callback:
            output = tm.ok(
                u.Cli.run_raw([
                    "flext-infra",
                    "refactor",
                    "accessor-migrate",
                    "--repository-root",
                    str(project),
                    "--apply",
                ])
            )
            tm.that(output.outcome.raw_return_code, eq=c.Cli.EXIT_CODE_FAILURE)
            tm.that(
                output.stdout + output.stderr,
                has="generated findings require canonical generator repair",
            )
        for path, content in before.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    def test_added_consumer_rejects_the_authenticated_batch(tmp_path: Path) -> None:
        """The final leased guard detects a new consumer before either CAS write."""
        _workspace, project, _service, legacy, _foreign = _phase_fixture(tmp_path)
        consumer = legacy.parent / "consumer.py"
        _ = consumer.write_text(
            f"from flext_core.legacy import {_SOURCE_NAME}\n\n"
            f"value = {_SOURCE_NAME}(True)\n",
            encoding="utf-8",
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (legacy, consumer)
        )
        before = {path: path.read_bytes() for path in (legacy, consumer)}
        updates = {
            path: content.decode("utf-8").replace(_SOURCE_NAME, _REPLACEMENT_NAME)
            for path, content in before.items()
        }
        candidate = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                project, updates, options=m.Infra.StageSourceOptions(inputs=states)
            )
        )
        plans = tuple(
            m.Infra.SemanticFilePlan(
                project=project,
                path=state.path,
                before=state,
                desired_content=updates[state.path].encode("utf-8"),
                desired_mode=state.mode,
                source_states=candidate.inputs,
            )
            for state in states
        )
        added = legacy.parent / "added_consumer.py"
        _ = added.write_text(consumer.read_text(encoding="utf-8"), encoding="utf-8")
        added_before = added.read_bytes()

        result = FlextInfraSemanticPublication.publish_source_candidate(
            plans,
            candidate=candidate,
        )

        tm.ok(result.failure)
        for path, content in before.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(added.read_bytes(), eq=added_before)

    @staticmethod
    @pytest.mark.slow
    def test_batch_loop_runs_callback_phases_to_the_fixed_point(
        tmp_path: Path,
    ) -> None:
        """One ``refactor mod`` loop converges with both callback phases wired."""
        _workspace, project, service_file, legacy_file, foreign_file = _phase_fixture(
            tmp_path,
        )
        progress = _RecordingProgress()
        with infra.rope_workspace(project) as rope:
            result = FlextInfraCodemodBatchApply(
                workspace_factory=infra.rope_workspace,
                source_preview=infra.source_preview(project),
                repository_root=project,
                apply_changes=True,
                check_only=False,
                dry_run=False,
                rename_runner=FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=(),
                phase_callbacks=(
                    FlextInfraNamespaceRelocationPhase(),
                    FlextInfraAccessorRenamePhase(
                        source_preview=infra.source_preview(project)
                    ),
                ),
            ).execute()

        tm.fail(result.failure)
        tm.that(
            (service_file.parent / "protocols.py").exists(),
            eq=True,
        )
        legacy_source = legacy_file.read_text(encoding="utf-8")
        tm.that(legacy_source, has=f"def {_REPLACEMENT_NAME}(")
        tm.that(
            foreign_file.read_text(encoding="utf-8"),
            has=f"def {_SOURCE_NAME}(",
        )
        tm.that(
            progress.messages,
            has="mod: phase namespace-relocations changed sources",
        )
        tm.that(
            progress.messages,
            has="mod: phase accessor-rename changed sources",
        )
