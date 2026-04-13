"""Public GitHub service mixin for the infra API facade."""

from __future__ import annotations

from flext_core import p, r
from flext_infra import m, u


class FlextInfraServiceGithubMixin:
    """Expose GitHub operations through the public infra facade."""

    def sync_github_workflows(
        self,
        params: m.Infra.GithubWorkflowSyncRequest,
    ) -> p.Result[m.Infra.GithubWorkflowSyncReport]:
        """Sync workspace workflows through the public facade."""
        return u.Infra.github_sync_workflows(params)

    def lint_github_workflows(
        self,
        params: m.Infra.GithubWorkflowLintRequest,
    ) -> p.Result[m.Infra.GithubWorkflowLintOutcome]:
        """Lint workspace workflows through the public facade."""
        return u.Infra.github_lint_workflows(params)

    def run_github_pull_request(
        self,
        params: m.Infra.GithubPullRequestRequest,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        """Run single-repository PR automation through the public facade."""
        result = u.Infra.github_run_pull_request(
            repo_root=params.repo_root_path,
            workspace_root=params.repo_root_path,
            request=params,
        )
        if result.failure:
            return result
        if result.value.exit_code != 0:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                f"PR operation exited with code {result.value.exit_code}",
            )
        return result

    def run_github_workspace_pull_requests(
        self,
        params: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]:
        """Run workspace PR automation through the public facade."""
        return u.Infra.github_run_workspace_pull_requests(params)


__all__: list[str] = ["FlextInfraServiceGithubMixin"]
