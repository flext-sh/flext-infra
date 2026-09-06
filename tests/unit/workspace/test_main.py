"""Public workspace CLI and facade tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import c, u
from tests.unit.workspace import WorktreeFixture


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
    u.Tests.write_project_beads_config(project_root, name)
    u.Tests.initialize_git_repo(
        project_root, origin_url=u.Tests.repository_ref(name).url
    )


def _write_workspace(repository_root: Path) -> None:
    repository_root.mkdir(parents=True, exist_ok=True)
    (repository_root / "pyproject.toml").write_text(
        ('[project]\nname = "workspace"\nversion = "0.1.0"\n'), encoding="utf-8"
    )
    u.Tests.write_project_beads_config(repository_root, "workspace")
    u.Tests.initialize_git_repo(
        repository_root, origin_url=u.Tests.repository_ref("workspace").url
    )
    _write_project(repository_root / "demo-a", "demo-a")
    WorktreeFixture.write_gitmodules(repository_root, ("demo-a",))


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
        repository_root = tmp_path / "workspace"
        _write_workspace(repository_root)
        member_root = repository_root / "demo-a"

        result = FlextInfraWorkspaceDetector(
            repository_root=member_root, apply_changes=False
        ).execute()

        tm.ok(result)
        tm.that(result.value, eq=c.Infra.MakeProfile.STANDALONE)

    def test_workspace_main_detect_accepts_explicit_repository_root(
        self, tmp_path: Path
    ) -> None:
        repository_root = tmp_path / "workspace"
        _write_workspace(repository_root)
        member_root = repository_root / "demo-a"

        tm.that(workspace_main(["detect", "--workspace", str(member_root)]), eq=0)

    def test_workspace_main_detect_runs_public_command(self, tmp_path: Path) -> None:
        """``workspace detect`` runs as a public CLI command."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        exit_code = workspace_main(["detect", "--workspace", str(project_root)])

        tm.that(exit_code, eq=0)

    def test_workspace_main_orchestrate_returns_failure_for_unknown_verb(self) -> None:
        tm.that(
            (workspace_main(["orchestrate", "--verb", "legacy-check"]) == 1),
            eq=True,
        )

    def test_workspace_main_without_command_returns_failure(self) -> None:
        tm.that(workspace_main([]), eq=1)
