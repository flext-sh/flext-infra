"""Workspace and release CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import FlextInfraWorkService, c, m
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService


class WorkspaceRoutes(CliRouteBase):
    """Own workspace routes without loading release or refactor services."""

    workspace_routes: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
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
                        "work",
                        "Unified bead/GitFlow/worktree/PR lane saga",
                        FlextInfraWorkService,
                    ),
                )
            ),
        ),
    }


__all__: list[str] = ["WorkspaceRoutes"]
