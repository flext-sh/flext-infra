"""CLI mixin for maintenance commands."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import FlextInfraPythonVersionEnforcer, m, t


class FlextInfraCliMaintenance:
    """Maintenance CLI group — composed into FlextInfraCli via MRO."""

    def register_maintenance(self, app: t.Cli.CliApp) -> None:
        """Register maintenance commands on the given Typer app."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="run",
                    help_text="Enforce Python version constraints",
                    model_cls=FlextInfraPythonVersionEnforcer,
                    handler=FlextInfraPythonVersionEnforcer.execute_command,
                    failure_message="Maintenance failed",
                    success_message="Maintenance completed",
                ),
            ],
        )


__all__ = ["FlextInfraCliMaintenance"]
