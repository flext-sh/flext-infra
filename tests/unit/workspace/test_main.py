"""Public workspace CLI and facade tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, main as infra_main
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import c, u


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
    u.Tests.write_standalone_workspace_manifest(project_root, name)
    u.Tests.initialize_git_repo(project_root)


def _write_workspace(workspace_root: Path) -> None:
    workspace_root.mkdir(parents=True, exist_ok=True)
    provider = config.Infra.codegen.providers[0]
    (workspace_root / ".gitmodules").write_text(
        (
            '[submodule "demo-a"]\n'
            "\tpath = demo-a\n"
            f"\turl = {provider.base_url.rstrip('/')}/demo-a.git\n"
            f"\tbranch = {provider.branch}\n"
        ),
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
    config_dir = workspace_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "workspace.yaml").write_text(
        (
            "version: 3\n"
            "name: workspace-root\n"
            "repository:\n"
            "  name: workspace-root\n"
            "  distribution: workspace-root\n"
            f"  provider: {provider.name}\n"
            f"  url: {provider.base_url.rstrip('/')}/workspace-root.git\n"
            f"  branch: {provider.branch}\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            "members:\n"
            "  - name: demo-a\n"
            "    distribution: demo-a\n"
            f"    provider: {provider.name}\n"
            f"    url: {provider.base_url.rstrip('/')}/demo-a.git\n"
            f"    branch: {provider.branch}\n"
            "    path: demo-a\n"
            "    role: workspace-member\n"
            "    state: active\n"
            "    checkout: submodule\n"
            "    codegen: conform\n"
            "    package: true\n"
            "    editable: true\n"
            "    read_only: false\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
    _write_project(workspace_root / "demo-a", "demo-a")


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

    def test_workspace_main_detect_accepts_explicit_workspace_root(
        self, tmp_path: Path
    ) -> None:
        workspace_root = tmp_path / "workspace"
        _write_workspace(workspace_root)
        member_root = workspace_root / "demo-a"

        tm.that(workspace_main(["detect", "--workspace", str(member_root)]), eq=0)

    def test_workspace_main_detect_runs_public_command(self, tmp_path: Path) -> None:
        """``workspace detect`` runs as a public CLI command."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        exit_code = workspace_main(["detect", "--workspace", str(project_root)])

        tm.that(exit_code, eq=0)

    def test_workspace_main_orchestrate_returns_failure_for_unknown_verb(self) -> None:
        tm.that(
            (
                workspace_main([
                    "orchestrate",
                    "--verb",
                    "legacy-check",
                    "--projects",
                    "p-a",
                ])
                == 1
            ),
            eq=True,
        )

    def test_workspace_main_without_command_returns_failure(self) -> None:
        tm.that(workspace_main([]), eq=1)
