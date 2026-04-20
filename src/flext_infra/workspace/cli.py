"""CLI registration for the workspace domain."""

from __future__ import annotations

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.typings import t
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.sync import FlextInfraSyncService


class FlextInfraCliWorkspace(FlextInfraCliGroupBase):
    """Owns workspace CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="detect",
            help_text="Detect workspace or standalone mode",
            model_cls=FlextInfraWorkspaceDetector,
            handler=FlextInfraWorkspaceDetector.execute_command,
            failure_message="detection failed",
        ),
        FlextInfraCliGroupBase.route(
            name="sync",
            help_text="Sync base.mk to project root",
            model_cls=FlextInfraSyncService,
            handler=FlextInfraSyncService.execute_command,
            failure_message="sync failed",
        ),
        FlextInfraCliGroupBase.route(
            name="orchestrate",
            help_text="Run make verb across projects",
            model_cls=FlextInfraOrchestratorService,
            handler=FlextInfraOrchestratorService.execute_command,
            failure_message="orchestration failed",
        ),
        FlextInfraCliGroupBase.route(
            name="migrate",
            help_text="Migrate workspace projects to flext_infra tooling",
            model_cls=FlextInfraProjectMigrator,
            handler=FlextInfraProjectMigrator.execute_command,
            failure_message="migration failed",
        ),
    )

    def register_workspace(self, app: t.Cli.CliApp) -> None:
        """Register workspace routes."""
        FlextInfraCliWorkspace.register_routes(app)


__all__: list[str] = ["FlextInfraCliWorkspace"]
