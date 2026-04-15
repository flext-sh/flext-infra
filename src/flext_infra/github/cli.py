"""CLI mixin for github commands."""

from __future__ import annotations

from typing import Protocol

from flext_cli import cli
from flext_infra import c, m, p, t


class _GithubCliHandlers(Protocol):
    def sync_github_workflows(
        self,
        params: m.Infra.GithubWorkflowSyncRequest,
    ) -> p.Result[m.Infra.GithubWorkflowSyncReport]: ...

    def lint_github_workflows(
        self,
        params: m.Infra.GithubWorkflowLintRequest,
    ) -> p.Result[m.Infra.GithubWorkflowLintOutcome]: ...

    def run_github_pull_request(
        self,
        params: m.Infra.GithubPullRequestRequest,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]: ...

    def run_github_workspace_pull_requests(
        self,
        params: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]: ...


class FlextInfraCliGithub:
    """GitHub CLI group — composed into FlextInfraCli via MRO."""

    def register_github(self: _GithubCliHandlers, app: t.Cli.CliApp) -> None:
        """Register github commands on the given Typer app."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="workflows",
                    help_text="Sync GitHub workflow files across workspace",
                    model_cls=m.Infra.GithubWorkflowSyncRequest,
                    handler=self.sync_github_workflows,
                    failure_message="Workflow sync failed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.LINT_SECTION,
                    help_text="Lint GitHub workflow files",
                    model_cls=m.Infra.GithubWorkflowLintRequest,
                    handler=self.lint_github_workflows,
                    failure_message="Workflow lint failed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.PR,
                    help_text="Manage pull requests for a single project",
                    model_cls=m.Infra.GithubPullRequestRequest,
                    handler=self.run_github_pull_request,
                    failure_message="PR operation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="pr-workspace",
                    help_text="Manage pull requests across workspace projects",
                    model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
                    handler=self.run_github_workspace_pull_requests,
                    failure_message="PR workspace orchestration failed",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliGithub"]
