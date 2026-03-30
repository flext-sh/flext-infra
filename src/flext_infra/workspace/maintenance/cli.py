"""CLI mixin for maintenance commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli

from flext_infra import FlextInfraPythonVersionEnforcer, m

if TYPE_CHECKING:
    import typer


class FlextInfraCliMaintenance:
    """Maintenance CLI group — composed into FlextInfraCli via MRO."""

    def register_maintenance(self, app: typer.Typer) -> None:
        """Register maintenance commands on the given Typer app."""
        service = FlextInfraPythonVersionEnforcer()
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="run",
                help_text="Enforce Python version constraints",
                model_cls=m.Infra.MaintenanceRunInput,
                handler=service.execute_command,
                success_message="Maintenance completed",
                failure_message="Maintenance failed",
            ),
        )
