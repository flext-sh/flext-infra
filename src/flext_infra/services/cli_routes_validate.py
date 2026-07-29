"""Documentation, GitHub, and maintenance lazy CLI loaders."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import p, t


class ValidationRoutes(CliRouteBase):
    """Load exactly one docs, GitHub, or maintenance implementation."""

    @staticmethod
    def load_audit(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation audit."""
        from flext_infra.docs.auditor import FlextInfraDocAuditor

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocAuditor,
            FlextInfraDocAuditor.execute_command,
            success_message="Audit completed successfully",
        )

    @staticmethod
    def load_fix(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation fixer."""
        from flext_infra.docs.fixer import FlextInfraDocFixer

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocFixer,
            FlextInfraDocFixer.execute_command,
            success_message="Fix completed successfully",
        )

    @staticmethod
    def load_build(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation builder."""
        from flext_infra.docs.builder import FlextInfraDocBuilder

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocBuilder,
            FlextInfraDocBuilder.execute_command,
            success_message="Build completed successfully",
        )

    @staticmethod
    def load_generate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation generator."""
        from flext_infra.docs.generator import FlextInfraDocGenerator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocGenerator,
            FlextInfraDocGenerator.execute_command,
            success_message="Generate completed successfully",
        )

    @staticmethod
    def load_serve(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation server."""
        from flext_infra.docs.server import FlextInfraDocServer

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocServer,
            FlextInfraDocServer.execute_command,
            success_message="Serve completed successfully",
        )

    @staticmethod
    def load_validate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected documentation validator."""
        from flext_infra.docs.validator import FlextInfraDocValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraDocValidator,
            FlextInfraDocValidator.execute_command,
            success_message="Validate completed successfully",
        )

    @staticmethod
    def load_workflows(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected GitHub workflow sync."""
        from flext_infra import m, u

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.GithubWorkflowSyncRequest,
            lambda params: u.Infra.sync_github_workflows(params).map(
                CliRouteBase.as_route_value
            ),
        )

    @staticmethod
    def load_lint(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected GitHub workflow lint."""
        from flext_infra import m, u

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.GithubWorkflowLintRequest,
            lambda params: u.Infra.lint_github_workflows(params).map(
                CliRouteBase.as_route_value
            ),
        )

    @staticmethod
    def load_pr(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected single-project PR route."""
        from flext_infra import m, u

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.GithubPullRequestRequest,
            lambda params: u.Infra.run_github_pull_request(params).map(
                CliRouteBase.as_route_value
            ),
        )

    @staticmethod
    def load_pr_workspace(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace PR route."""
        from flext_core import r
        from flext_infra import m, u

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.GithubPullRequestWorkspaceRequest,
            lambda params: u.Infra.run_github_workspace_pull_requests(params).flat_map(
                lambda report: r.fail(report.message) if report.fail else r.ok(report)
            ),
        )

    @staticmethod
    def load_run(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected Python-version enforcement route."""
        from flext_infra.maintenance.python_version import (
            FlextInfraPythonVersionEnforcer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraPythonVersionEnforcer,
            FlextInfraPythonVersionEnforcer.execute_command,
            success_message="Maintenance completed",
        )


__all__: list[str] = ["ValidationRoutes"]
