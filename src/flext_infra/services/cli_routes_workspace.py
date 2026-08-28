"""Workspace and release CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, m, p, t
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.services.cli_routes_refactor import RefactorRoutes
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.flext_binding import FlextInfraFlextBindingService
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService


class WorkspaceRoutes(RefactorRoutes):
    """Own refactor, release, and workspace routes."""

    @staticmethod
    def _apply_flext_binding(
        params: m.Infra.FlextBindingRequest,
    ) -> p.Result[t.Cli.ResultValue]:
        """Apply the typed binding request through its service owner."""
        return FlextInfraFlextBindingService.apply(
            consumer_root=params.workspace_root,
            flext_root=params.flext_root,
            python=params.python,
        ).map(CliRouteBase.as_route_value)

    workspace_routes: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        c.Infra.CLI_GROUP_REFACTOR: RefactorRoutes.refactor_routes,
        c.Infra.CLI_GROUP_RELEASE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=FlextInfraReleaseOrchestrator.execute_command,
                success_message="Release completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_WORKSPACE: (
            m.Cli.ResultCommandRoute(
                name="verify-environment",
                help_text="Verify live workspace editable provenance",
                model_cls=m.Infra.WorkspaceEnvironmentRequest,
                handler=FlextInfraWorkspaceEnvironmentProvenance.execute_request,
                success_message="workspace editable provenance verified",
            ),
            m.Cli.ResultCommandRoute(
                name="flext-binding",
                help_text="Bind this project onto a flext worktree for the session",
                model_cls=m.Infra.FlextBindingRequest,
                handler=_apply_flext_binding,
                success_message="flext worktree binding applied",
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=model_cls.execute_command,
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
                )
            ),
        ),
    }


__all__: list[str] = ["WorkspaceRoutes"]
