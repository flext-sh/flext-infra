from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import t

from flext_core import r
from flext_infra import (
    FlextInfraModels as m,
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceMode,
    main as infra_main,
)


def workspace_main(argv: list[str] | None = None) -> int:
    args = ["workspace"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


class TestRunDetect:
    @pytest.mark.parametrize(
        ("result", "expected_success"),
        [
            (r[FlextInfraWorkspaceMode].ok(FlextInfraWorkspaceMode.WORKSPACE), True),
            (r[FlextInfraWorkspaceMode].fail("Detection failed"), False),
        ],
    )
    def test_detect(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        result: r[FlextInfraWorkspaceMode],
        expected_success: bool,
    ) -> None:
        def _detect_stub(
            _self: FlextInfraWorkspaceDetector,
            project_root: Path,
        ) -> r[FlextInfraWorkspaceMode]:
            del _self, project_root
            return result

        monkeypatch.setattr(FlextInfraWorkspaceDetector, "detect", _detect_stub)
        handle_result = FlextInfraWorkspaceDetector.execute_command(
            FlextInfraWorkspaceDetector(workspace=tmp_path),
        )
        tm.that(handle_result.is_success, eq=expected_success)


class TestRunSync:
    @pytest.mark.parametrize(
        ("result", "expected_success"),
        [
            (
                r[m.Infra.SyncResult].ok(
                    m.Infra.SyncResult(
                        files_changed=1,
                        source=Path(),
                        target=Path(),
                    ),
                ),
                True,
            ),
            (r[m.Infra.SyncResult].fail("Sync failed"), False),
        ],
    )
    def test_sync(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        result: r[m.Infra.SyncResult],
        expected_success: bool,
    ) -> None:
        def _execute_stub(
            _self: FlextInfraSyncService,
        ) -> r[m.Infra.SyncResult]:
            del _self
            return result

        monkeypatch.setattr(FlextInfraSyncService, "execute", _execute_stub)
        handle_result = FlextInfraSyncService.execute_command(
            FlextInfraSyncService(workspace=tmp_path),
        )
        tm.that(handle_result.is_success, eq=expected_success)


class TestRunOrchestrate:
    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_success(
            _self: FlextInfraOrchestratorService,
            projects: t.StrSequence,
            verb: str,
            fail_fast: bool = False,
            make_args: t.StrSequence | None = None,
        ) -> r[Sequence[m.Infra.CommandOutput]]:
            del _self, projects, verb, fail_fast, make_args
            return r[Sequence[m.Infra.CommandOutput]].ok([
                m.Infra.CommandOutput(stdout="", stderr="", exit_code=0, duration=0.0),
                m.Infra.CommandOutput(stdout="", stderr="", exit_code=0, duration=0.0),
            ])

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "orchestrate",
            _orchestrate_success,
        )
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(verb="check", projects="p-a,p-b"),
        )
        tm.that(handle_result.is_success, eq=True)

    def test_preserves_make_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_make_args: list[str] = []

        def _orchestrate_success(
            _self: FlextInfraOrchestratorService,
            projects: t.StrSequence,
            verb: str,
            fail_fast: bool = False,
            make_args: t.StrSequence | None = None,
        ) -> r[Sequence[m.Infra.CommandOutput]]:
            del _self, projects, verb, fail_fast
            if make_args is not None:
                captured_make_args.extend(make_args)
            return r[Sequence[m.Infra.CommandOutput]].ok([
                m.Infra.CommandOutput(stdout="", stderr="", exit_code=0, duration=0.0),
            ])

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "orchestrate",
            _orchestrate_success,
        )
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(
                verb="test",
                projects="p-a",
                make_arg=["FILES=a b c.py", "VERBOSE=1"],
            ),
        )
        tm.that(handle_result.is_success, eq=True)
        tm.that(captured_make_args, eq=["FILES=a b c.py", "VERBOSE=1"])

    def test_rejects_unknown_verb(self) -> None:
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(verb="legacy-check", projects="p-a"),
        )
        tm.fail(handle_result, has="unsupported orchestrate verb")

    def test_no_projects(self) -> None:
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(verb="check", projects=""),
        )
        tm.that(handle_result.is_failure, eq=True)

    def test_with_failures(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_partial(
            _self: FlextInfraOrchestratorService,
            projects: t.StrSequence,
            verb: str,
            fail_fast: bool = False,
            make_args: t.StrSequence | None = None,
        ) -> r[Sequence[m.Infra.CommandOutput]]:
            del _self, projects, verb, fail_fast, make_args
            return r[Sequence[m.Infra.CommandOutput]].ok([
                m.Infra.CommandOutput(stdout="", stderr="", exit_code=0, duration=0.0),
                m.Infra.CommandOutput(stdout="", stderr="", exit_code=1, duration=0.0),
            ])

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "orchestrate",
            _orchestrate_partial,
        )
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(verb="check", projects="p-a,p-b"),
        )
        tm.that(handle_result.is_failure, eq=True)

    def test_orchestration_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_failure(
            _self: FlextInfraOrchestratorService,
            projects: t.StrSequence,
            verb: str,
            fail_fast: bool = False,
            make_args: t.StrSequence | None = None,
        ) -> r[Sequence[m.Infra.CommandOutput]]:
            del _self, projects, verb, fail_fast, make_args
            return r[Sequence[m.Infra.CommandOutput]].fail("Orchestration failed")

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "orchestrate",
            _orchestrate_failure,
        )
        handle_result = FlextInfraOrchestratorService.execute_command(
            FlextInfraOrchestratorService(verb="check", projects="p-a"),
        )
        tm.that(handle_result.is_failure, eq=True)


class TestRunMigrate:
    @pytest.mark.parametrize(
        ("result", "expected_success"),
        [
            (
                r[Sequence[m.Infra.MigrationResult]].ok([
                    m.Infra.MigrationResult(
                        project="test",
                        errors=[],
                        changes=[],
                    ),
                ]),
                True,
            ),
            (r[Sequence[m.Infra.MigrationResult]].fail("Migration failed"), False),
        ],
    )
    def test_success_or_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        result: r[Sequence[m.Infra.MigrationResult]],
        expected_success: bool,
    ) -> None:
        def _migrate_stub(
            _self: FlextInfraProjectMigrator,
            workspace_root: Path,
            dry_run: bool,
        ) -> r[Sequence[m.Infra.MigrationResult]]:
            del _self, workspace_root, dry_run
            return result

        monkeypatch.setattr(FlextInfraProjectMigrator, "migrate", _migrate_stub)
        handle_result = FlextInfraProjectMigrator.execute_command(
            FlextInfraProjectMigrator(workspace=tmp_path, apply=True),
        )
        tm.that(handle_result.is_success, eq=expected_success)

    def test_with_project_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mrs: Sequence[m.Infra.MigrationResult] = [
            m.Infra.MigrationResult(
                project="p1",
                errors=["Error 1"],
                changes=[],
            ),
            m.Infra.MigrationResult(project="p2", errors=[], changes=[]),
        ]

        def _migrate_with_errors(
            _self: FlextInfraProjectMigrator,
            workspace_root: Path,
            dry_run: bool,
        ) -> r[Sequence[m.Infra.MigrationResult]]:
            del _self, workspace_root, dry_run
            return r[Sequence[m.Infra.MigrationResult]].ok(mrs)

        monkeypatch.setattr(
            FlextInfraProjectMigrator,
            "migrate",
            _migrate_with_errors,
        )
        handle_result = FlextInfraProjectMigrator.execute_command(
            FlextInfraProjectMigrator(workspace=tmp_path, apply=True),
        )
        tm.that(handle_result.is_success, eq=True)
        tm.that(handle_result.value[0].errors, eq=["Error 1"])


def _ok_stub(
    _params: m.Infra.WorkspaceDetectInput
    | m.Infra.WorkspaceSyncInput
    | FlextInfraOrchestratorService
    | FlextInfraProjectMigrator,
) -> r[bool]:
    return r[bool].ok(True)


class TestMainCli:
    def test_detect(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraWorkspaceDetector,
            "execute_command",
            _ok_stub,
        )
        tm.that(workspace_main(["detect", "--workspace", str(tmp_path)]), eq=0)

    def test_sync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraSyncService,
            "execute_command",
            _ok_stub,
        )
        tm.that(workspace_main(["sync", "--workspace", str(tmp_path)]), eq=0)

    def test_orchestrate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "execute_command",
            _ok_stub,
        )
        tm.that(
            workspace_main([
                "orchestrate",
                "--verb",
                "check",
                "--projects",
                "p-a",
            ]),
            eq=0,
        )

    def test_orchestrate_repeats_make_arg(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: list[FlextInfraOrchestratorService] = []

        def _capture_orchestrate(
            params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            captured.append(params)
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraOrchestratorService,
            "execute_command",
            _capture_orchestrate,
        )
        tm.that(
            workspace_main([
                "orchestrate",
                "--verb",
                "test",
                "--projects",
                "p-a",
                "--make-arg",
                "FILES=a b c.py",
                "--make-arg",
                "VERBOSE=1",
            ]),
            eq=0,
        )
        tm.that(captured[0].make_arg, eq=["FILES=a b c.py", "VERBOSE=1"])

    def test_migrate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraProjectMigrator,
            "execute_command",
            _ok_stub,
        )
        tm.that(workspace_main(["migrate", "--workspace", str(tmp_path)]), eq=0)

    def test_no_command(self) -> None:
        tm.that(workspace_main([]), eq=1)
