"""Workspace and release CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, m
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.services.cli_routes_refactor import RefactorRoutes
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


class WorkspaceRoutes(RefactorRoutes):
    """Own refactor, release, and workspace routes."""

    workspace_routes: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        c.Infra.CLI_GROUP_REFACTOR: RefactorRoutes.refactor_routes,
        c.Infra.CLI_GROUP_RELEASE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
                success_message="Release completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_WORKSPACE: (
            m.Cli.ResultCommandRoute(
                name="detect",
                help_text="Detect workspace or standalone mode",
                model_cls=FlextInfraWorkspaceDetector,
                handler=FlextInfraWorkspaceDetector.execute_command,
            ),
        ),
    }


__all__: list[str] = ["WorkspaceRoutes"]
