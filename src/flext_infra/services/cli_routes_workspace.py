"""Workspace and release CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import FlextInfraWorktreeService, c, m
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.release.managed_git_tool import FlextInfraManagedGitToolRelease
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.services.cli_routes_refactor import RefactorRoutes
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService


class WorkspaceRoutes(RefactorRoutes):
    """Own refactor, release, and workspace routes."""

    workspace_routes: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        c.Infra.CLI_GROUP_REFACTOR: RefactorRoutes.refactor_routes,
        c.Infra.CLI_GROUP_RELEASE: (
            m.Cli.ResultCommandRoute(
                name="managed-git-tool",
                help_text="Build and atomically activate an exact Git executable",
                model_cls=FlextInfraManagedGitToolRelease,
                handler=lambda params: FlextInfraManagedGitToolRelease.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
                success_message="Managed Git tool release completed",
            ),
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
                name="verify-environment",
                help_text="Verify live workspace editable provenance",
                model_cls=m.Infra.WorkspaceEnvironmentRequest,
                handler=lambda params: (
                    FlextInfraWorkspaceEnvironmentProvenance.execute_request(
                        params
                    ).map(CliRouteBase.as_route_value)
                ),
                success_message="workspace editable provenance verified",
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=lambda params, mc=model_cls: mc.execute_command(params),
                )
                for route_name, help_text, model_cls in (
                    (
                        "detect",
                        "Detect workspace or standalone mode",
                        FlextInfraWorkspaceDetector,
                    ),
                    (
                        "orchestrate",
                        "Run make verb across projects",
                        FlextInfraOrchestratorService,
                    ),
                    (
                        "serialize-make",
                        "Run one state-sensitive Make verb under its checkout lock",
                        FlextInfraMakeSerializationService,
                    ),
                    (
                        "worktree",
                        "Manage repository-local development worktrees",
                        FlextInfraWorktreeService,
                    ),
                )
            ),
        ),
    }


__all__: list[str] = ["WorkspaceRoutes"]
