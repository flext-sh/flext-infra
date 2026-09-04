"""Documentation, GitHub, maintenance, and validation CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.server import FlextInfraDocServer
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_infra.maintenance.clean import FlextInfraCleanService
from flext_infra.maintenance.python_version import FlextInfraPythonVersionEnforcer
from flext_infra.services.cli_routes_validate_commands import ValidationCommandRoutes


class ValidationRoutes(ValidationCommandRoutes):
    """Own documentation, GitHub, maintenance, and validation routes."""

    @staticmethod
    def _require_successful_pull_request_workspace(
        report: m.Infra.GithubPullRequestWorkspaceReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Fail the CLI boundary when any repository operation failed."""
        if report.fail:
            return r.fail(report.message)
        return r.ok(report)

    @staticmethod
    def _run_github_workspace_pull_requests(
        params: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> p.Result[t.Cli.ResultValue]:
        """Run the workspace PR owner and reject a report containing failures."""
        return u.Infra.run_github_workspace_pull_requests(params).flat_map(
            ValidationRoutes._require_successful_pull_request_workspace
        )

    validation_routes: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        c.Infra.CLI_GROUP_DOCS: tuple(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=ValidationCommandRoutes.result_handler(
                    model_cls.execute_command
                ),
                success_message=success_message,
            )
            for route_name, help_text, model_cls, success_message in (
                (
                    "audit",
                    "Audit documentation for broken links and forbidden terms",
                    FlextInfraDocAuditor,
                    "Audit completed successfully",
                ),
                (
                    "fix",
                    "Fix documentation issues",
                    FlextInfraDocFixer,
                    "Fix completed successfully",
                ),
                (
                    "build",
                    "Build MkDocs sites",
                    FlextInfraDocBuilder,
                    "Build completed successfully",
                ),
                (
                    "generate",
                    "Generate project docs",
                    FlextInfraDocGenerator,
                    "Generate completed successfully",
                ),
                (
                    "serve",
                    "Serve one MkDocs site in dev mode (blocking preview)",
                    FlextInfraDocServer,
                    "Serve completed successfully",
                ),
                (
                    "validate",
                    "Validate documentation",
                    FlextInfraDocValidator,
                    "Validate completed successfully",
                ),
            )
        ),
        c.Infra.CLI_GROUP_GITHUB: (
            m.Cli.ResultCommandRoute(
                name="workflows",
                help_text="Sync GitHub workflow files across workspace",
                model_cls=m.Infra.GithubWorkflowSyncRequest,
                handler=u.Infra.sync_github_workflows,
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.LINT_SECTION,
                help_text="Lint GitHub workflow files",
                model_cls=m.Infra.GithubWorkflowLintRequest,
                handler=u.Infra.lint_github_workflows,
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.PR,
                help_text="Manage pull requests for a single project",
                model_cls=m.Infra.GithubPullRequestRequest,
                handler=ValidationCommandRoutes.result_handler(
                    u.Infra.run_github_pull_request
                ),
            ),
            m.Cli.ResultCommandRoute(
                name="pr-workspace",
                help_text="Manage pull requests across workspace projects",
                model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
                handler=_run_github_workspace_pull_requests,
            ),
        ),
        c.Infra.CLI_GROUP_MAINTENANCE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Enforce Python version constraints",
                model_cls=FlextInfraPythonVersionEnforcer,
                handler=FlextInfraPythonVersionEnforcer.execute_command,
                success_message="Maintenance completed",
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_CLEAN,
                help_text="Report or remove disposable build artifacts",
                model_cls=FlextInfraCleanService,
                handler=FlextInfraCleanService.execute_command,
                success_message="Clean completed",
            ),
        ),
        c.Infra.CLI_GROUP_VALIDATE: ValidationCommandRoutes.validate_command_routes,
    }


__all__: list[str] = ["ValidationRoutes"]
