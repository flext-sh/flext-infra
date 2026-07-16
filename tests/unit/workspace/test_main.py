"""Public workspace CLI and facade tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import r, tm

from flext_infra import main as infra_main
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.sync import FlextInfraSyncService
from tests import c
from tests import m
from tests import t
from tests import u

from tests import p



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


def _cmd_out(exit_code: int = 0) -> p.Cli.CommandOutput:
    return m.Cli.CommandOutput(stdout="", stderr="", exit_code=exit_code, duration=0.0)


def _install_successful_orchestration(
    orchestrator: FlextInfraOrchestratorService, *, project_root: Path
) -> None:
    project = m.Infra.ProjectInfo(name="flext-demo", path=project_root, stack="python")

    def _resolved_projects(
        self: FlextInfraOrchestratorService,
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        del self
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok([project])

    def _prepare_projects(
        self: FlextInfraOrchestratorService,
        projects: t.SequenceOf[p.Infra.ProjectInfo],
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
    ) -> p.Result[p.Cli.CommandOutput]:
        _ = (self, project_name, verb, _index, make_args)
        return r[p.Cli.CommandOutput].ok(_cmd_out())

    orchestrator._resolved_projects = _resolved_projects.__get__(
        orchestrator, FlextInfraOrchestratorService
    )
    orchestrator._prepare_projects = _prepare_projects.__get__(
        orchestrator, FlextInfraOrchestratorService
    )
    orchestrator._run_project = _run_project.__get__(
        orchestrator, FlextInfraOrchestratorService
    )


def workspace_main(argv: list[str] | None = None) -> int:
    args = ["workspace"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


class TestsFlextInfraWorkspaceMain:
    """Behavior contract for test_main."""

    def test_unattached_child_does_not_infer_workspace_from_ancestor(
        self, tmp_path: Path
    ) -> None:
        workspace_root = tmp_path / "workspace"
        _write_workspace(workspace_root)
        member_root = workspace_root / "demo-a"

        result = FlextInfraWorkspaceDetector(
            workspace_root=member_root, apply_changes=False
        ).execute()

        tm.ok(result)
        tm.that(result.value, eq=c.Infra.WorkspaceMode.STANDALONE)

    def test_sync_workspace_returns_sync_result(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=False,
        ).execute()

        tm.ok(result)
        assert result.value.files_changed >= 1

    def test_orchestrate_workspace_rejects_unknown_verb(self) -> None:
        result = FlextInfraOrchestratorService(
            verb="legacy-check", selected_projects=["p-a"]
        ).execute()

        tm.fail(result)
        tm.that((result.error or ""), has="unsupported orchestrate verb")

    def test_orchestrate_workspace_defaults_to_current_project(self) -> None:
        orchestrator = FlextInfraOrchestratorService(verb="check", selected_projects=[])
        _install_successful_orchestration(orchestrator, project_root=Path.cwd())
        result = orchestrator.execute()

        tm.ok(result)

    def test_orchestrate_project_target_accepts_external_sibling(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "flext"
        external = tmp_path / ".ai-hub"
        workspace.mkdir()
        external.mkdir()
        project = m.Infra.ProjectInfo(
            name="ai-hub", path=external, stack="python/flext"
        )

        target = FlextInfraOrchestratorService._project_target(
            project, workspace_root=workspace
        )

        tm.that(target, eq=str(external.resolve()))

    def test_orchestrate_project_log_filename_stays_under_reports(self) -> None:
        filename = FlextInfraOrchestratorService._project_log_filename("../.ai-hub")

        tm.that(filename, eq=".ai-hub.log")

    def test_orchestrate_workspace_forwards_fail_fast_to_project_make(self) -> None:
        tm.that(
            FlextInfraOrchestratorService._normalize_fail_fast_make_args(
                (), fail_fast=True
            ),
            eq=("FAIL_FAST=1",),
        )

    def test_workspace_main_detect_accepts_explicit_workspace_root(
        self, tmp_path: Path
    ) -> None:
        workspace_root = tmp_path / "workspace"
        _write_workspace(workspace_root)
        member_root = workspace_root / "demo-a"

        tm.that(workspace_main(["detect", "--workspace", str(member_root)]), eq=0)

    def test_workspace_main_sync_runs_public_command(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        u.Tests.initialize_git_repo(project_root)

        exit_code = workspace_main([
            "sync",
            "--workspace",
            str(project_root),
            "--canonical-root",
            str(project_root.parent),
            "--apply",
        ])

        tm.that(exit_code, eq=0)
        assert (project_root / "Makefile").exists()
        assert not (project_root / "base.mk").exists()

    def test_workspace_main_orchestrate_returns_failure_for_unknown_verb(self) -> None:
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

    def test_workspace_main_without_command_returns_failure(self) -> None:
        tm.that(workspace_main([]), eq=1)
