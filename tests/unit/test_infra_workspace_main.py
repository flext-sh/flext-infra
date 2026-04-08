from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import c, m, r, t

from flext_infra import (
    FlextInfra,
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    infra,
    main as infra_main,
)


def workspace_main(argv: t.StrSequence | None = None) -> int:
    args: t.MutableSequenceOf[str] = ["workspace"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


class TestRunDetect:
    @pytest.mark.parametrize(
        ("result", "expected_success"),
        [
            (r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.WORKSPACE), True),
            (r[c.Infra.WorkspaceMode].fail("Detection failed"), False),
        ],
    )
    def test_detect(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        result: r[c.Infra.WorkspaceMode],
        expected_success: bool,
    ) -> None:
        def _detect_stub(
            _self: FlextInfra,
            params: FlextInfraWorkspaceDetector,
        ) -> r[c.Infra.WorkspaceMode]:
            tm.that(params.workspace_root, eq=tmp_path)
            return result

        monkeypatch.setattr(FlextInfra, "detect_workspace", _detect_stub)
        handle_result = infra.detect_workspace(
            FlextInfraWorkspaceDetector(workspace=tmp_path, apply=False),
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
            _self: FlextInfra,
            params: FlextInfraSyncService,
        ) -> r[m.Infra.SyncResult]:
            tm.that(params.workspace_root, eq=tmp_path)
            return result

        monkeypatch.setattr(FlextInfra, "sync_workspace", _execute_stub)
        handle_result = infra.sync_workspace(
            FlextInfraSyncService(workspace=tmp_path, apply=False),
        )
        tm.that(handle_result.is_success, eq=expected_success)


class TestRunOrchestrate:
    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_success(
            _self: FlextInfra,
            params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            tm.that(params.verb, eq="check")
            tm.that(params.project_names, eq=["p-a", "p-b"])
            return r[bool].ok(True)

        monkeypatch.setattr(FlextInfra, "orchestrate_workspace", _orchestrate_success)
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(verb="check", projects=["p-a", "p-b"]),
        )
        tm.that(handle_result.is_success, eq=True)

    def test_preserves_make_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_make_args: t.MutableSequenceOf[str] = []

        def _orchestrate_success(
            _self: FlextInfra,
            params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            captured_make_args.extend(params.make_args)
            return r[bool].ok(True)

        monkeypatch.setattr(FlextInfra, "orchestrate_workspace", _orchestrate_success)
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(
                verb="test",
                projects=["p-a"],
                make_arg=["FILES=a b c.py", "VERBOSE=1"],
            ),
        )
        tm.that(handle_result.is_success, eq=True)
        tm.that(captured_make_args, eq=["FILES=a b c.py", "VERBOSE=1"])

    def test_rejects_unknown_verb(self) -> None:
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(verb="legacy-check", projects=["p-a"]),
        )
        tm.fail(handle_result, has="unsupported orchestrate verb")

    def test_no_projects(self) -> None:
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(verb="check", projects=[]),
        )
        tm.that(handle_result.is_failure, eq=True)

    def test_with_failures(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_partial(
            _self: FlextInfra,
            params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            tm.that(params.project_names, eq=["p-a", "p-b"])
            return r[bool].fail("orchestration completed with failures: 1")

        monkeypatch.setattr(FlextInfra, "orchestrate_workspace", _orchestrate_partial)
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(
                verb="check",
                projects=["p-a", "p-b"],
            ),
        )
        tm.that(handle_result.is_failure, eq=True)

    def test_orchestration_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _orchestrate_failure(
            _self: FlextInfra,
            _params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            return r[bool].fail("Orchestration failed")

        monkeypatch.setattr(
            FlextInfra,
            "orchestrate_workspace",
            _orchestrate_failure,
        )
        handle_result = infra.orchestrate_workspace(
            FlextInfraOrchestratorService(verb="check", projects=["p-a"]),
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
            _self: FlextInfra,
            params: FlextInfraProjectMigrator,
        ) -> r[Sequence[m.Infra.MigrationResult]]:
            tm.that(params.workspace_root, eq=tmp_path)
            return result

        monkeypatch.setattr(FlextInfra, "migrate_workspace", _migrate_stub)
        handle_result = infra.migrate_workspace(
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
            _self: FlextInfra,
            params: FlextInfraProjectMigrator,
        ) -> r[Sequence[m.Infra.MigrationResult]]:
            tm.that(params.workspace_root, eq=tmp_path)
            return r[Sequence[m.Infra.MigrationResult]].ok(mrs)

        monkeypatch.setattr(FlextInfra, "migrate_workspace", _migrate_with_errors)
        handle_result = infra.migrate_workspace(
            FlextInfraProjectMigrator(workspace=tmp_path, apply=True),
        )
        tm.that(handle_result.is_success, eq=True)
        tm.that(handle_result.value[0].errors, eq=["Error 1"])


def _ok_stub(
    _self: FlextInfra,
    _params: FlextInfraWorkspaceDetector
    | FlextInfraSyncService
    | FlextInfraOrchestratorService
    | FlextInfraProjectMigrator,
) -> r[bool]:
    return r[bool].ok(True)


class TestMainCli:
    def test_detect(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfra,
            "detect_workspace",
            _ok_stub,
        )
        tm.that(workspace_main(["detect", "--workspace", str(tmp_path)]), eq=0)

    def test_sync(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfra,
            "sync_workspace",
            _ok_stub,
        )
        tm.that(workspace_main(["sync", "--workspace", str(tmp_path)]), eq=0)

    def test_orchestrate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfra,
            "orchestrate_workspace",
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
        captured: t.MutableSequenceOf[FlextInfraOrchestratorService] = []

        def _capture_orchestrate(
            _self: FlextInfra,
            params: FlextInfraOrchestratorService,
        ) -> r[bool]:
            captured.append(params)
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfra,
            "orchestrate_workspace",
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
            FlextInfra,
            "migrate_workspace",
            _ok_stub,
        )
        tm.that(workspace_main(["migrate", "--workspace", str(tmp_path)]), eq=0)

    def test_no_command(self) -> None:
        tm.that(workspace_main([]), eq=1)
