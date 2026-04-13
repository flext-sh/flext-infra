"""Public workspace CLI and facade tests."""

from __future__ import annotations

from pathlib import Path

from flext_core import p, r
from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    infra,
    main as infra_main,
)
from tests import c, m, t


def _write_project(project_root: Path, name: str) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            f'name = "{name}"\n'
            'version = "0.1.0"\n'
            'description = "Demo project"\n'
            'requires-python = ">=3.13"\n'
        ),
        encoding="utf-8",
    )


def _write_workspace(workspace_root: Path) -> None:
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / ".gitmodules").write_text(
        '[submodule "demo-a"]\n\tpath = demo-a\n\turl = https://example.invalid/demo-a.git\n',
        encoding="utf-8",
    )
    (workspace_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "workspace-root"\n'
            'version = "0.1.0"\n'
            "\n"
            "[tool.flext.workspace]\n"
            'members = ["demo-a"]\n'
        ),
        encoding="utf-8",
    )
    _write_project(workspace_root / "demo-a", "demo-a")


def _cmd_out(exit_code: int = 0) -> m.Cli.CommandOutput:
    return m.Cli.CommandOutput(
        stdout="",
        stderr="",
        exit_code=exit_code,
        duration=0.0,
    )


def _install_successful_orchestration(
    orchestrator: FlextInfraOrchestratorService,
    *,
    project_root: Path,
) -> None:
    project = m.Infra.ProjectInfo(
        name="flext-demo",
        path=project_root,
        stack="python",
    )

    def _resolved_projects(
        self: FlextInfraOrchestratorService,
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
        del self
        return r[t.SequenceOf[m.Infra.ProjectInfo]].ok([project])

    def _prepare_projects(
        self: FlextInfraOrchestratorService,
        projects: t.SequenceOf[m.Infra.ProjectInfo],
        *,
        workspace_root: Path,
    ) -> p.Result[bool]:
        _ = (self, projects, workspace_root)
        return r[bool].ok(True)

    def _run_project(
        self: FlextInfraOrchestratorService,
        project_name: str,
        verb: str,
        _index: int,
        *,
        make_args: t.StrSequence,
    ) -> p.Result[m.Cli.CommandOutput]:
        _ = (self, project_name, verb, _index, make_args)
        return r[m.Cli.CommandOutput].ok(_cmd_out())

    orchestrator._resolved_projects = _resolved_projects.__get__(
        orchestrator,
        FlextInfraOrchestratorService,
    )
    orchestrator._prepare_projects = _prepare_projects.__get__(
        orchestrator,
        FlextInfraOrchestratorService,
    )
    orchestrator._run_project = _run_project.__get__(
        orchestrator,
        FlextInfraOrchestratorService,
    )


def workspace_main(argv: list[str] | None = None) -> int:
    args = ["workspace"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


def test_detect_workspace_returns_workspace_mode(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    _write_workspace(workspace_root)
    member_root = workspace_root / "demo-a"

    result = infra.detect_workspace(
        FlextInfraWorkspaceDetector(workspace=member_root, apply=False),
    )

    assert result.success, result.error
    assert result.value == c.Infra.WorkspaceMode.WORKSPACE


def test_sync_workspace_returns_sync_result(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")

    result = infra.sync_workspace(
        FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace=project_root,
            apply=False,
        ),
    )

    assert result.success, result.error
    assert result.value.files_changed >= 1


def test_orchestrate_workspace_rejects_unknown_verb() -> None:
    result = infra.orchestrate_workspace(
        FlextInfraOrchestratorService(verb="legacy-check", projects=["p-a"]),
    )

    assert result.failure
    assert "unsupported orchestrate verb" in (result.error or "")


def test_orchestrate_workspace_defaults_to_current_project() -> None:
    orchestrator = FlextInfraOrchestratorService(verb="check", projects=[])
    _install_successful_orchestration(orchestrator, project_root=Path.cwd())
    result = infra.orchestrate_workspace(orchestrator)

    assert result.success, result.error


def test_workspace_main_detect_accepts_explicit_workspace_root(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_workspace(workspace_root)
    member_root = workspace_root / "demo-a"

    assert workspace_main(["detect", "--workspace", str(member_root)]) == 0


def test_workspace_main_sync_runs_public_command(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")

    exit_code = workspace_main([
        "sync",
        "--workspace",
        str(project_root),
        "--canonical-root",
        str(project_root.parent),
    ])

    assert exit_code == 0
    assert (project_root / "Makefile").exists()
    assert (project_root / "base.mk").exists()


def test_workspace_main_orchestrate_returns_failure_for_unknown_verb() -> None:
    assert (
        workspace_main([
            "orchestrate",
            "--verb",
            "legacy-check",
            "--projects",
            "p-a",
        ])
        == 1
    )


def test_workspace_main_without_command_returns_failure() -> None:
    assert workspace_main([]) == 1
