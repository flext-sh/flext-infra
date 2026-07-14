from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_cli import cli
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def create_git_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    u.Tests.initialize_git_repo(repo)
    return repo


def create_workspace_with_submodule(tmp_path: Path) -> tuple[Path, Path]:
    child = create_git_repo(tmp_path, "child")
    workspace = create_git_repo(tmp_path, "workspace")
    cli.run_checked(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(child),
            "deps/child",
        ],
        cwd=workspace,
    )
    cli.run_checked(["git", "add", "-A"], cwd=workspace)
    cli.run_checked(["git", "commit", "-m", "add submodule"], cwd=workspace)
    return workspace, workspace / "deps" / "child"


class TestsFlextInfraDepsInternalSyncWorkspace:
    """Behavior contract for test_internal_sync_workspace."""

    # mro-wkii.4.15: environment setup uses the canonical typed test utility.

    def test_workspace_root_from_env_returns_none_when_env_is_missing(
        self, tmp_path: Path
    ) -> None:
        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().workspace_root_from_env(Path(sys.argv[1])))"
                ),
                str(tmp_path),
            ],
            remove_env_keys=("FLEXT_WORKSPACE_ROOT",),
        )

        tm.ok(result)
        tm.that(result.value, eq="None")

    def test_workspace_root_from_env_returns_valid_parent(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().workspace_root_from_env(Path(sys.argv[1])))"
                ),
                str(project),
            ],
            env={"FLEXT_WORKSPACE_ROOT": str(tmp_path)},
        )

        tm.ok(result)
        tm.that(result.value, eq=str(tmp_path))

    def test_workspace_root_from_env_rejects_invalid_or_unrelated_paths(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        project = tmp_path / "other" / "project"
        project.mkdir(parents=True)

        command = [
            sys.executable,
            "-W",
            "error",
            "-c",
            (
                "import sys; from pathlib import Path; "
                "from flext_infra.deps.internal_sync import "
                "FlextInfraInternalDependencySyncService as Service; "
                "print(Service().workspace_root_from_env(Path(sys.argv[1])))"
            ),
            str(project),
        ]
        missing_result = u.Cli.capture(
            command, env={"FLEXT_WORKSPACE_ROOT": "/nonexistent/path"}
        )
        unrelated_result = u.Cli.capture(
            command, env={"FLEXT_WORKSPACE_ROOT": str(workspace)}
        )

        tm.ok(missing_result)
        tm.that(missing_result.value, eq="None")
        tm.ok(unrelated_result)
        tm.that(unrelated_result.value, eq="None")

    def test_workspace_root_from_parents_finds_gitmodules(self, tmp_path: Path) -> None:
        (tmp_path / ".gitmodules").touch()
        project = tmp_path / "sub" / "project"
        project.mkdir(parents=True)

        result = FlextInfraInternalDependencySyncService.workspace_root_from_parents(
            project
        )

        tm.that(result, eq=tmp_path)

    def test_workspace_root_from_parents_returns_none_when_missing(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "isolated"
        project.mkdir()

        result = FlextInfraInternalDependencySyncService.workspace_root_from_parents(
            project
        )

        tm.that(result, none=True)

    def test_is_workspace_mode_respects_standalone_env(self, tmp_path: Path) -> None:
        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().is_workspace_mode(Path(sys.argv[1])))"
                ),
                str(tmp_path),
            ],
            env={"FLEXT_STANDALONE": "1"},
            remove_env_keys=("FLEXT_WORKSPACE_ROOT",),
        )

        tm.ok(result)
        tm.that(result.value, ends="(False, None)")

    def test_is_workspace_mode_uses_workspace_root_env(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().is_workspace_mode(Path(sys.argv[1])))"
                ),
                str(project),
            ],
            env={"FLEXT_STANDALONE": "", "FLEXT_WORKSPACE_ROOT": str(tmp_path)},
        )

        tm.ok(result)
        tm.that(result.value, eq=f"(True, {tmp_path!r})")

    def test_is_workspace_mode_detects_real_git_superproject(
        self, tmp_path: Path
    ) -> None:
        workspace, submodule = create_workspace_with_submodule(tmp_path)

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().is_workspace_mode(Path(sys.argv[1])))"
                ),
                str(submodule),
            ],
            env={"FLEXT_STANDALONE": ""},
            remove_env_keys=("FLEXT_WORKSPACE_ROOT",),
        )

        tm.ok(result)
        tm.that(result.value, eq=f"(True, {workspace!r})")

    def test_is_workspace_mode_falls_back_to_gitmodules_heuristic(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".gitmodules").touch()
        project = tmp_path / "sub"
        project.mkdir()

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().is_workspace_mode(Path(sys.argv[1])))"
                ),
                str(project),
            ],
            env={"FLEXT_STANDALONE": ""},
            remove_env_keys=("FLEXT_WORKSPACE_ROOT",),
        )

        tm.ok(result)
        tm.that(result.value, eq=f"(True, {tmp_path!r})")

    def test_is_workspace_mode_returns_false_for_isolated_project(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "isolated"
        project.mkdir()

        result = u.Cli.capture(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    "from flext_infra.deps.internal_sync import "
                    "FlextInfraInternalDependencySyncService as Service; "
                    "print(Service().is_workspace_mode(Path(sys.argv[1])))"
                ),
                str(project),
            ],
            env={"FLEXT_STANDALONE": ""},
            remove_env_keys=("FLEXT_WORKSPACE_ROOT",),
        )

        tm.ok(result)
        tm.that(result.value, eq="(False, None)")
