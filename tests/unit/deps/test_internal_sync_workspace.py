from __future__ import annotations

import os
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from flext_infra import FlextInfraInternalDependencySyncService
from tests import u


@contextmanager
def temporary_env(**updates: str | None) -> Generator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def create_git_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    u.Infra.Tests.initialize_git_repo(repo)
    return repo


def create_workspace_with_submodule(tmp_path: Path) -> tuple[Path, Path]:
    child = create_git_repo(tmp_path, "child")
    workspace = create_git_repo(tmp_path, "workspace")
    subprocess.run(
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
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "add submodule"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    return workspace, workspace / "deps" / "child"


def test_workspace_root_from_env_returns_none_when_env_is_missing(
    tmp_path: Path,
) -> None:
    with temporary_env(FLEXT_WORKSPACE_ROOT=None):
        result = FlextInfraInternalDependencySyncService().workspace_root_from_env(
            tmp_path,
        )

    assert result is None


def test_workspace_root_from_env_returns_valid_parent(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with temporary_env(FLEXT_WORKSPACE_ROOT=str(tmp_path)):
        result = FlextInfraInternalDependencySyncService().workspace_root_from_env(
            project,
        )

    assert result == tmp_path


def test_workspace_root_from_env_rejects_invalid_or_unrelated_paths(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    project = tmp_path / "other" / "project"
    project.mkdir(parents=True)

    with temporary_env(FLEXT_WORKSPACE_ROOT="/nonexistent/path"):
        missing_result = (
            FlextInfraInternalDependencySyncService().workspace_root_from_env(
                project,
            )
        )
    with temporary_env(FLEXT_WORKSPACE_ROOT=str(workspace)):
        unrelated_result = (
            FlextInfraInternalDependencySyncService().workspace_root_from_env(
                project,
            )
        )

    assert missing_result is None
    assert unrelated_result is None


def test_workspace_root_from_parents_finds_gitmodules(tmp_path: Path) -> None:
    (tmp_path / ".gitmodules").touch()
    project = tmp_path / "sub" / "project"
    project.mkdir(parents=True)

    result = FlextInfraInternalDependencySyncService.workspace_root_from_parents(
        project,
    )

    assert result == tmp_path


def test_workspace_root_from_parents_returns_none_when_missing(tmp_path: Path) -> None:
    project = tmp_path / "isolated"
    project.mkdir()

    result = FlextInfraInternalDependencySyncService.workspace_root_from_parents(
        project,
    )

    assert result is None


def test_is_workspace_mode_respects_standalone_env(tmp_path: Path) -> None:
    with temporary_env(FLEXT_STANDALONE="1", FLEXT_WORKSPACE_ROOT=None):
        is_workspace, root = (
            FlextInfraInternalDependencySyncService().is_workspace_mode(
                tmp_path,
            )
        )

    assert is_workspace is False
    assert root is None


def test_is_workspace_mode_uses_workspace_root_env(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with temporary_env(FLEXT_STANDALONE="", FLEXT_WORKSPACE_ROOT=str(tmp_path)):
        is_workspace, root = (
            FlextInfraInternalDependencySyncService().is_workspace_mode(
                project,
            )
        )

    assert is_workspace is True
    assert root == tmp_path


def test_is_workspace_mode_detects_real_git_superproject(tmp_path: Path) -> None:
    workspace, submodule = create_workspace_with_submodule(tmp_path)

    with temporary_env(FLEXT_STANDALONE="", FLEXT_WORKSPACE_ROOT=None):
        is_workspace, root = (
            FlextInfraInternalDependencySyncService().is_workspace_mode(
                submodule,
            )
        )

    assert is_workspace is True
    assert root == workspace


def test_is_workspace_mode_falls_back_to_gitmodules_heuristic(tmp_path: Path) -> None:
    (tmp_path / ".gitmodules").touch()
    project = tmp_path / "sub"
    project.mkdir()

    with temporary_env(FLEXT_STANDALONE="", FLEXT_WORKSPACE_ROOT=None):
        is_workspace, root = (
            FlextInfraInternalDependencySyncService().is_workspace_mode(
                project,
            )
        )

    assert is_workspace is True
    assert root == tmp_path


def test_is_workspace_mode_returns_false_for_isolated_project(tmp_path: Path) -> None:
    project = tmp_path / "isolated"
    project.mkdir()

    with temporary_env(FLEXT_STANDALONE="", FLEXT_WORKSPACE_ROOT=None):
        is_workspace, root = (
            FlextInfraInternalDependencySyncService().is_workspace_mode(
                project,
            )
        )

    assert is_workspace is False
    assert root is None
