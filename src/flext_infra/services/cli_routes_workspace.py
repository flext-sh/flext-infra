"""Workspace and release CLI route ownership."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.cli_catalog import CliCatalog
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.services.cli_routes_refactor import RefactorRoutes

if TYPE_CHECKING:
    from flext_infra import m


class WorkspaceRoutes(CliRouteBase):
    """Load only the selected refactor, release, or workspace implementation."""

    @classmethod
    def routes_for(
        cls, group: str, command: str
    ) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Build the route selected at the lightweight dispatch boundary."""
        if group == "refactor":
            return RefactorRoutes.routes_for(command)

        from flext_infra import m

        if (group, command) == ("release", "run"):
            from flext_infra.release.orchestrator import (
                FlextInfraReleaseOrchestrator,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=FlextInfraReleaseOrchestrator,
                    handler=lambda params: (
                        FlextInfraReleaseOrchestrator.execute_command(params).map(
                            CliRouteBase.as_route_value
                        )
                    ),
                    success_message="Release completed successfully",
                ),
            )

        if group != "workspace":
            return ()
        if command == "verify-environment":
            from flext_infra.workspace.environment_provenance import (
                FlextInfraWorkspaceEnvironmentProvenance,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=m.Infra.WorkspaceEnvironmentRequest,
                    handler=lambda params: (
                        FlextInfraWorkspaceEnvironmentProvenance.execute_request(
                            params
                        ).map(CliRouteBase.as_route_value)
                    ),
                    success_message="workspace editable provenance verified",
                ),
            )
        if command == "detect":
            from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

            implementation = FlextInfraWorkspaceDetector
        elif command == "sync":
            from flext_infra.workspace.sync import FlextInfraSyncService

            implementation = FlextInfraSyncService
        elif command == "orchestrate":
            from flext_infra.workspace.orchestrator import (
                FlextInfraOrchestratorService,
            )

            implementation = FlextInfraOrchestratorService
        elif command == "serialize-make":
            from flext_infra.workspace.make_serialization import (
                FlextInfraMakeSerializationService,
            )

            implementation = FlextInfraMakeSerializationService
        elif command == "migrate":
            from flext_infra.workspace.migrator import FlextInfraProjectMigrator

            implementation = FlextInfraProjectMigrator
        elif command == "worktree":
            from flext_infra import FlextInfraWorktreeService

            implementation = FlextInfraWorktreeService
        else:
            return ()

        return (
            m.Cli.ResultCommandRoute(
                name=command,
                help_text=CliCatalog.description(group, command),
                model_cls=implementation,
                handler=lambda params, mc=implementation: mc.execute_command(params),
            ),
        )


__all__: list[str] = ["WorkspaceRoutes"]
