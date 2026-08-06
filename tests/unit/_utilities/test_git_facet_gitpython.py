"""Public u.Infra Git facet — GitPython-backed behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraGitService, c, m, u


class TestsFlextInfraGitFacet:
    """Exercise the public Git facade against a real repository worktree."""

    def test_repository_head_and_status_and_service(self, real_git_repo: Path) -> None:
        """Head, porcelain status, and FlextInfraGitService share one typed path."""
        head = u.Infra.git_repository_head(
            m.Infra.GitRepoRequest(repo_root=real_git_repo)
        )
        assert head.success
        assert len(head.value.oid) == 40
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=real_git_repo))
        assert status.success
        assert isinstance(status.value.porcelain, str)
        assert status.value.dirty is False
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=real_git_repo)
        )
        assert primary.success
        assert primary.value.primary_root == real_git_repo.resolve()
        report = FlextInfraGitService(workspace_root=real_git_repo).execute()
        assert report.success
        assert isinstance(report.value, m.Infra.GitStatusReport)
        assert report.value.repo_root == real_git_repo.resolve()
        assert report.value.dirty is False

    def test_git_init_bare_on_non_repo_cwd(self, tmp_path: Path) -> None:
        """cwd-bound execute must allow git init --bare outside a worktree."""
        bare_root = tmp_path / "bare"
        bare_root.mkdir()
        init_result = u.Cli.run_checked([c.Infra.GIT, "init", "--bare"], cwd=bare_root)
        assert init_result.success
        assert (bare_root / "HEAD").is_file()
        captured = u.Cli.capture([c.Infra.GIT, "rev-parse", "--git-dir"], cwd=bare_root)
        assert captured.success
        assert captured.value.strip() in {".", str(bare_root.resolve())}

    def test_service_status_reports_dirty_tree(self, real_git_repo: Path) -> None:
        """The status-only service flips dirty when the worktree changes."""
        clean = FlextInfraGitService(workspace_root=real_git_repo).execute()
        assert clean.success
        assert clean.value.dirty is False
        (real_git_repo / "dirty.txt").write_text("x", encoding="utf-8")
        dirty = FlextInfraGitService(workspace_root=real_git_repo).execute()
        assert dirty.success
        assert dirty.value.dirty is True
        assert "dirty.txt" in dirty.value.porcelain

    def test_missing_git_binary_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing git on PATH must Result.fail without raising."""
        monkeypatch.setattr(
            "flext_infra._utilities._git.repo.shutil.which", lambda _name: None
        )
        result = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=tmp_path))
        assert result.failure
        assert result.error is not None
        assert "git executable not found" in result.error
