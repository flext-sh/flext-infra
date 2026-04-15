"""CLI mixin for workspace commands."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
    p,
    t,
)


class FlextInfraCliWorkspace:
    """Workspace CLI group — composed into FlextInfraCli via MRO."""

    if TYPE_CHECKING:
        detect_workspace: Callable[
            [FlextInfraWorkspaceDetector],
            p.Result[c.Infra.WorkspaceMode],
        ]
        sync_workspace: Callable[[FlextInfraSyncService], p.Result[m.Infra.SyncResult]]
        orchestrate_workspace: Callable[[FlextInfraOrchestratorService], p.Result[bool]]
        migrate_workspace: Callable[
            [FlextInfraProjectMigrator],
            p.Result[Sequence[m.Infra.MigrationResult]],
        ]

    def register_workspace(self, app: t.Cli.CliApp) -> None:
        """Register workspace commands on the given Typer app."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="detect",
                    help_text="Detect workspace or standalone mode",
                    model_cls=FlextInfraWorkspaceDetector,
                    handler=self.detect_workspace,
                    failure_message="detection failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="sync",
                    help_text="Sync base.mk to project root",
                    model_cls=FlextInfraSyncService,
                    handler=self.sync_workspace,
                    failure_message="sync failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="orchestrate",
                    help_text="Run make verb across projects",
                    model_cls=FlextInfraOrchestratorService,
                    handler=self.orchestrate_workspace,
                    failure_message="orchestration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="migrate",
                    help_text="Migrate workspace projects to flext_infra tooling",
                    model_cls=FlextInfraProjectMigrator,
                    handler=self.migrate_workspace,
                    failure_message="migration failed",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliWorkspace"]
