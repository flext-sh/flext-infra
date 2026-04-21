"""CLI registration for the github domain."""

from __future__ import annotations

from flext_core import r

from flext_infra import FlextInfraCliGroupBase, c, m, p, t, u


class FlextInfraCliGithub(FlextInfraCliGroupBase):
    """Owns github CLI route declarations."""

    @staticmethod
    def _sync_github_workflows(
        params: m.Infra.GithubWorkflowSyncRequest,
    ) -> p.Result[m.Infra.GithubWorkflowSyncReport]:
        return u.Infra.github_sync_workflows(params)

    @staticmethod
    def _lint_github_workflows(
        params: m.Infra.GithubWorkflowLintRequest,
    ) -> p.Result[m.Infra.GithubWorkflowLintOutcome]:
        return u.Infra.github_lint_workflows(params)

    @staticmethod
    def _run_github_pull_request(
        params: m.Infra.GithubPullRequestRequest,
    ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
        result = u.Infra.github_run_pull_request(
            repo_root=params.repo_root_path,
            workspace_root=params.repo_root_path,
            request=params,
        )
        if result.success and result.value.exit_code != 0:
            return r[m.Infra.GithubPullRequestOutcome].fail(
                f"PR operation exited with code {result.value.exit_code}",
            )
        return result

    @staticmethod
    def _run_github_workspace_pull_requests(
        params: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]:
        return u.Infra.github_run_workspace_pull_requests(params)

    routes = (
        FlextInfraCliGroupBase.route(
            name="workflows",
            help_text="Sync GitHub workflow files across workspace",
            model_cls=m.Infra.GithubWorkflowSyncRequest,
            handler=_sync_github_workflows,
        ),
        FlextInfraCliGroupBase.route(
            name=c.Infra.LINT_SECTION,
            help_text="Lint GitHub workflow files",
            model_cls=m.Infra.GithubWorkflowLintRequest,
            handler=_lint_github_workflows,
        ),
        FlextInfraCliGroupBase.route(
            name=c.Infra.PR,
            help_text="Manage pull requests for a single project",
            model_cls=m.Infra.GithubPullRequestRequest,
            handler=_run_github_pull_request,
        ),
        FlextInfraCliGroupBase.route(
            name="pr-workspace",
            help_text="Manage pull requests across workspace projects",
            model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
            handler=_run_github_workspace_pull_requests,
        ),
    )

    def register_github(self, app: t.Cli.CliApp) -> None:
        """Register github routes."""
        FlextInfraCliGithub.register_routes(app)


__all__: list[str] = ["FlextInfraCliGithub"]
