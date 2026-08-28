"""Public workspace CLI and facade tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import c


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
        workspace_root.mkdir()
        (workspace_root / ".gitmodules").write_text("", encoding="utf-8")
        member_root = workspace_root / "child"
        _write_project(member_root, "demo-project")

        result = FlextInfraWorkspaceDetector(
            workspace_root=member_root, apply_changes=False
        ).execute()

        tm.ok(result)
        tm.that(result.value, eq=c.Infra.WorkspaceMode.STANDALONE)

    def test_workspace_main_detect_accepts_explicit_workspace_root(
        self, tmp_path: Path
    ) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        member_root = workspace_root / "child"
        _write_project(member_root, "demo-project")

        tm.that(workspace_main(["detect", "--workspace", str(member_root)]), eq=0)

    def test_workspace_main_detect_runs_public_command(self, tmp_path: Path) -> None:
        """``workspace detect`` runs as a public CLI command."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        exit_code = workspace_main(["detect", "--workspace", str(project_root)])

        tm.that(exit_code, eq=0)

    def test_workspace_main_without_command_returns_failure(self) -> None:
        tm.that(workspace_main([]), eq=1)
