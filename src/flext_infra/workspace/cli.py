"""CLI registration for the workspace domain."""

from __future__ import annotations

from flext_infra import (
    FlextInfraCliGroupBase,
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    t,
)


class FlextInfraCliWorkspace(FlextInfraCliGroupBase):
    """Owns workspace CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="detect",
            help_text="Detect workspace or standalone mode",
            model_cls=FlextInfraWorkspaceDetector,
            handler=FlextInfraWorkspaceDetector.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="sync",
            help_text="Sync base.mk to project root",
            model_cls=FlextInfraSyncService,
            handler=FlextInfraSyncService.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="orchestrate",
            help_text="Run make verb across projects",
            model_cls=FlextInfraOrchestratorService,
            handler=FlextInfraOrchestratorService.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="migrate",
            help_text="Migrate workspace projects to flext_infra tooling",
            model_cls=FlextInfraProjectMigrator,
            handler=FlextInfraProjectMigrator.execute_command,
        ),
    )

    def register_workspace(self, app: t.Cli.CliApp) -> None:
        """Register workspace routes."""
        FlextInfraCliWorkspace.register_routes(app)


__all__: list[str] = ["FlextInfraCliWorkspace"]
