"""CLI mixin for github commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import FlextInfraGithubService, c, m, t


class FlextInfraCliGithub:
    """GitHub CLI group — composed into FlextInfraCli via MRO."""

    def register_github(self, app: t.Cli.TyperApp) -> None:
        """Register github commands on the given Typer app."""
        service = FlextInfraGithubService()
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="workflows",
                    help_text="Sync GitHub workflow files across workspace",
                    model_cls=m.Infra.GithubWorkflowsInput,
                    handler=service.execute_workflows,
                    failure_message="Workflow sync failed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.LINT_SECTION,
                    help_text="Lint GitHub workflow files",
                    model_cls=m.Infra.GithubLintInput,
                    handler=service.execute_lint,
                    failure_message="Workflow lint failed",
                ),
                m.Cli.ResultCommandRoute(
                    name=c.Infra.PR,
                    help_text="Manage pull requests for a single project",
                    model_cls=m.Infra.GithubPrInput,
                    handler=service.execute_pr,
                    failure_message="PR operation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="pr-workspace",
                    help_text="Manage pull requests across workspace projects",
                    model_cls=m.Infra.GithubPrWorkspaceInput,
                    handler=service.execute_pr_workspace,
                    failure_message="PR workspace orchestration failed",
                ),
            ],
        )


__all__ = ["FlextInfraCliGithub"]
