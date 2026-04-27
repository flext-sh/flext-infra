from __future__ import annotations

import os
import subprocess
from collections.abc import (
    Generator,
)
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
    u.Tests.initialize_git_repo(repo)
    return repo


def add_origin(repo_root: Path, remote_url: str) -> None:
    subprocess.run(
        ["git", "remote", "add", "origin", remote_url],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


class TestsFlextInfraDepsInternalSyncResolve:
    """Behavior contract for test_internal_sync_resolve."""

    def test_resolve_ref_prefers_github_head_ref(self, tmp_path: Path) -> None:
        with temporary_env(
            GITHUB_ACTIONS="true",
            GITHUB_HEAD_REF="feature/test",
            GITHUB_REF_NAME="main",
        ):
            result = FlextInfraInternalDependencySyncService().resolve_ref(tmp_path)

        assert result == "feature/test"

    def test_resolve_ref_uses_github_ref_name_when_head_ref_is_empty(
        self,
        tmp_path: Path,
    ) -> None:
        with temporary_env(
            GITHUB_ACTIONS="true",
            GITHUB_HEAD_REF="",
            GITHUB_REF_NAME="main",
        ):
            result = FlextInfraInternalDependencySyncService().resolve_ref(tmp_path)

        assert result == "main"

    def test_resolve_ref_uses_current_git_branch(self, tmp_path: Path) -> None:
        repo = create_git_repo(tmp_path, "repo")
        assert u.Cli.run_checked(["git", "checkout", "-B", "develop"], cwd=repo).success

        result = FlextInfraInternalDependencySyncService().resolve_ref(repo)

        assert result == "develop"

    def test_resolve_ref_uses_exact_tag_on_detached_head(self, tmp_path: Path) -> None:
        repo = create_git_repo(tmp_path, "repo")
        assert u.Cli.run_checked(
            ["git", "tag", "-a", "v1.0.0", "-m", "release"],
            cwd=repo,
        ).success
        assert u.Cli.run_checked(["git", "checkout", "v1.0.0"], cwd=repo).success

        result = FlextInfraInternalDependencySyncService().resolve_ref(repo)

        assert result == "v1.0.0"

    def test_resolve_ref_falls_back_to_main_for_non_repo(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()

        with temporary_env(
            GITHUB_ACTIONS=None,
            GITHUB_HEAD_REF=None,
            GITHUB_REF_NAME=None,
        ):
            result = FlextInfraInternalDependencySyncService().resolve_ref(project)

        assert result == "main"

    def test_infer_owner_from_origin_reads_real_remote(self, tmp_path: Path) -> None:
        repo = create_git_repo(tmp_path, "repo")
        add_origin(repo, "git@github.com:flext-sh/flext-core.git")

        result = FlextInfraInternalDependencySyncService().infer_owner_from_origin(repo)

        assert result == "flext-sh"

    def test_infer_owner_from_origin_returns_none_without_remote(
        self, tmp_path: Path
    ) -> None:
        repo = create_git_repo(tmp_path, "repo")

        result = FlextInfraInternalDependencySyncService().infer_owner_from_origin(repo)

        assert result is None

    def test_synthesized_repo_map_builds_public_urls(self) -> None:
        result = FlextInfraInternalDependencySyncService().synthesized_repo_map(
            "flext-sh",
            {"flext-core", "flext-api"},
        )

        assert result["flext-core"].ssh_url == "git@github.com:flext-sh/flext-core.git"
        assert (
            result["flext-api"].https_url == "https://github.com/flext-sh/flext-api.git"
        )
