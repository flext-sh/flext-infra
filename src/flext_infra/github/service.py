"""GitHub command service for centralized CLI execution."""

from __future__ import annotations

from flext_core import r
from flext_infra import m, u


class FlextInfraGithubService:
    """Direct command service for GitHub CLI operations."""

    def execute_workflow_sync(
        self,
        request: m.Infra.GithubWorkflowSyncRequest,
    ) -> r[m.Infra.GithubWorkflowSyncReport]:
        """Sync GitHub workflow files across the workspace."""
        return u.Infra.github_sync_workflows(request)

    def execute_workflow_lint(
        self,
        request: m.Infra.GithubWorkflowLintRequest,
    ) -> r[m.Infra.GithubWorkflowLintOutcome]:
        """Lint GitHub workflow files across the workspace."""
        return u.Infra.github_lint_workflows(request)

    def execute_pull_request(
        self,
        request: m.Infra.GithubPullRequestRequest,
    ) -> r[m.Infra.GithubPullRequestOutcome]:
        """Manage pull requests for a single repository."""
        result = u.Infra.github_run_pull_request(
            repo_root=request.repo_root_path,
            workspace_root=request.repo_root_path,
            request=request,
        )
        if result.is_failure:
            return result
        if result.value.exit_code != 0:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                f"PR operation exited with code {result.value.exit_code}",
            )
        return result

    def execute_workspace_pull_requests(
        self,
        request: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
        """Manage pull requests across workspace projects."""
        return u.Infra.github_run_workspace_pull_requests(request)


__all__ = ["FlextInfraGithubService"]
