"""Tests for public workspace mode detection."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorkspaceDetector, c
from tests import u


class TestWorkspaceDetector:
    """Exercise workspace detection through public repo state and inputs."""

    @staticmethod
    def _setup_parent_repo(tmp_path: Path, origin_url: str | None = None) -> Path:
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=repo_root))
        if origin_url is not None:
            tm.ok(
                u.Cli.run_checked(
                    ["git", "remote", "add", "origin", origin_url],
                    cwd=repo_root,
                )
            )
        project_root = repo_root / "project"
        project_root.mkdir()
        return project_root

    def test_detects_standalone_without_parent_git(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_detects_workspace_from_gitmodules(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        (tmp_path / ".gitmodules").write_text("", encoding="utf-8")
        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_detects_standalone_without_origin(self, tmp_path: Path) -> None:
        project_root = self._setup_parent_repo(tmp_path)
        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_detects_workspace_for_flext_origin(self, tmp_path: Path) -> None:
        project_root = self._setup_parent_repo(
            tmp_path,
            "https://github.com/flext-sh/flext.git",
        )
        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_detects_standalone_for_non_flext_origin(self, tmp_path: Path) -> None:
        project_root = self._setup_parent_repo(
            tmp_path,
            "https://github.com/other-org/other-repo.git",
        )
        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_execute_uses_workspace_root(self, tmp_path: Path) -> None:
        tm.ok(
            FlextInfraWorkspaceDetector(workspace=tmp_path).execute(),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_repo_name_from_https_url(self) -> None:
        tm.that(
            FlextInfraWorkspaceDetector._repo_name_from_url(
                "https://github.com/flext-sh/flext.git",
            ),
            eq="flext",
        )

    def test_repo_name_from_ssh_url(self) -> None:
        tm.that(
            FlextInfraWorkspaceDetector._repo_name_from_url(
                "git@github.com:flext-sh/flext.git",
            ),
            eq="flext",
        )

    def test_repo_name_without_git_suffix(self) -> None:
        tm.that(
            FlextInfraWorkspaceDetector._repo_name_from_url(
                "https://github.com/flext-sh/flext",
            ),
            eq="flext",
        )

    def test_detection_failure_returns_failure_result(self) -> None:
        tm.fail(
            FlextInfraWorkspaceDetector().detect(Path("\0")),
            has="Detection failed",
        )
