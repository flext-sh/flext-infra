"""Documentation, GitHub, maintenance, and validation CLI route ownership."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.services.cli_routes_validate_commands import ValidationCommandRoutes

if TYPE_CHECKING:
    from flext_infra import m, p, t


class ValidationRoutes(CliRouteBase):
    """Load only the selected documentation or validation implementation."""

    descriptions: ClassVar[Mapping[str, Mapping[str, str]]] = MappingProxyType({
        "docs": MappingProxyType({
            "audit": "Audit documentation for broken links and forbidden terms",
            "fix": "Fix documentation issues",
            "build": "Build MkDocs sites",
            "generate": "Generate project docs",
            "serve": "Serve one MkDocs site in dev mode (blocking preview)",
            "validate": "Validate documentation",
        }),
        "github": MappingProxyType({
            "workflows": "Sync GitHub workflow files across workspace",
            "lint": "Lint GitHub workflow files",
            "pr": "Manage pull requests for a single project",
            "pr-workspace": "Manage pull requests across workspace projects",
        }),
        "maintenance": MappingProxyType({"run": "Enforce Python version constraints"}),
        "validate": ValidationCommandRoutes.descriptions,
    })

    @classmethod
    def command_descriptions(cls, group: str) -> Mapping[str, str]:
        """Return this route family's declarative command descriptors."""
        return cls.descriptions[group]

    @staticmethod
    def _require_successful_pull_request_workspace(
        report: m.Infra.GithubPullRequestWorkspaceReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Fail the CLI boundary when any repository operation failed."""
        from flext_core import r

        if report.fail:
            return r.fail(report.message)
        return r.ok(report)

    @classmethod
    def routes_for(
        cls, group: str, command: str
    ) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Build the route selected at the lightweight dispatch boundary."""
        if group == "validate":
            return ValidationCommandRoutes.routes_for(command)

        from flext_infra import m

        if group == "docs":
            if command == "audit":
                from flext_infra.docs.auditor import FlextInfraDocAuditor

                implementation = FlextInfraDocAuditor
                success_message = "Audit completed successfully"
            elif command == "fix":
                from flext_infra.docs.fixer import FlextInfraDocFixer

                implementation = FlextInfraDocFixer
                success_message = "Fix completed successfully"
            elif command == "build":
                from flext_infra.docs.builder import FlextInfraDocBuilder

                implementation = FlextInfraDocBuilder
                success_message = "Build completed successfully"
            elif command == "generate":
                from flext_infra.docs.generator import FlextInfraDocGenerator

                implementation = FlextInfraDocGenerator
                success_message = "Generate completed successfully"
            elif command == "serve":
                from flext_infra.docs.server import FlextInfraDocServer

                implementation = FlextInfraDocServer
                success_message = "Serve completed successfully"
            elif command == "validate":
                from flext_infra.docs.validator import FlextInfraDocValidator

                implementation = FlextInfraDocValidator
                success_message = "Validate completed successfully"
            else:
                return ()
            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[group][command],
                    model_cls=implementation,
                    handler=lambda params, mc=implementation: mc.execute_command(
                        params
                    ),
                    success_message=success_message,
                ),
            )

        if group == "github":
            from flext_infra import u

            if command == "workflows":
                return (
                    m.Cli.ResultCommandRoute(
                        name=command,
                        help_text=cls.descriptions[group][command],
                        model_cls=m.Infra.GithubWorkflowSyncRequest,
                        handler=lambda params: u.Infra.sync_github_workflows(
                            params
                        ).map(CliRouteBase.as_route_value),
                    ),
                )
            if command == "lint":
                return (
                    m.Cli.ResultCommandRoute(
                        name=command,
                        help_text=cls.descriptions[group][command],
                        model_cls=m.Infra.GithubWorkflowLintRequest,
                        handler=lambda params: u.Infra.lint_github_workflows(
                            params
                        ).map(CliRouteBase.as_route_value),
                    ),
                )
            if command == "pr":
                return (
                    m.Cli.ResultCommandRoute(
                        name=command,
                        help_text=cls.descriptions[group][command],
                        model_cls=m.Infra.GithubPullRequestRequest,
                        handler=lambda params: u.Infra.run_github_pull_request(
                            params
                        ).map(CliRouteBase.as_route_value),
                    ),
                )
            if command == "pr-workspace":
                return (
                    m.Cli.ResultCommandRoute(
                        name=command,
                        help_text=cls.descriptions[group][command],
                        model_cls=m.Infra.GithubPullRequestWorkspaceRequest,
                        handler=lambda params: (
                            u.Infra.run_github_workspace_pull_requests(params).flat_map(
                                ValidationRoutes._require_successful_pull_request_workspace
                            )
                        ),
                    ),
                )
            return ()

        if (group, command) == ("maintenance", "run"):
            from flext_infra.maintenance.python_version import (
                FlextInfraPythonVersionEnforcer,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[group][command],
                    model_cls=FlextInfraPythonVersionEnforcer,
                    handler=FlextInfraPythonVersionEnforcer.execute_command,
                    success_message="Maintenance completed",
                ),
            )
        return ()


__all__: list[str] = ["ValidationRoutes"]
