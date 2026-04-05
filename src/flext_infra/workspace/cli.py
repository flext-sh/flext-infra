"""CLI mixin for workspace commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    m,
    t,
)


class FlextInfraCliWorkspace:
    """Workspace CLI group — composed into FlextInfraCli via MRO."""

    def register_workspace(self, app: t.Cli.CliApp) -> None:
        """Register workspace commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="detect",
                    help_text="Detect workspace or standalone mode",
                    model_cls=m.Infra.WorkspaceDetectInput,
                    handler=FlextInfraWorkspaceDetector.execute_command,
                    failure_message="detection failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="sync",
                    help_text="Sync base.mk to project root",
                    model_cls=m.Infra.WorkspaceSyncInput,
                    handler=FlextInfraSyncService.execute_command,
                    failure_message="sync failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="orchestrate",
                    help_text="Run make verb across projects",
                    model_cls=m.Infra.WorkspaceOrchestrateInput,
                    handler=FlextInfraOrchestratorService.execute_command,
                    failure_message="orchestration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="migrate",
                    help_text="Migrate workspace projects to flext_infra tooling",
                    model_cls=m.Infra.WorkspaceMigrateInput,
                    handler=FlextInfraProjectMigrator.execute_command,
                    failure_message="migration failed",
                ),
            ],
        )


__all__ = ["FlextInfraCliWorkspace"]
