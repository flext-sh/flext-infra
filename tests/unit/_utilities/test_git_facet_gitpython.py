"""Public u.Infra Git facet — GitPython-backed behavior."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraGitService, c, m, u


class TestsFlextInfraGitFacet:
    """Exercise the public Git facade against a real repository worktree."""

    def test_repository_head_and_status_and_service(self, real_git_repo: Path) -> None:
        """Head, porcelain status, and FlextInfraGitService share one typed path."""
        head = u.Infra.git_repository_head(real_git_repo)
        assert head.success
        assert len(head.value) == 40
        status = u.Infra.git_capture(
            real_git_repo, ("status", "--porcelain", "--untracked-files=all")
        )
        assert status.success
        assert isinstance(status.value, str)
        primary = u.Infra.git_primary_worktree_root(real_git_repo)
        assert primary.success
        assert primary.value == real_git_repo.resolve()
        report = FlextInfraGitService(
            operation=c.Infra.GitOperation.PRIMARY_ROOT, workspace_root=real_git_repo
        ).execute()
        assert report.success
        assert isinstance(report.value, m.Infra.GitOperationReport)
        assert report.value.primary_root == real_git_repo.resolve()
