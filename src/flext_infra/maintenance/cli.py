"""CLI mixin for maintenance commands."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import (
    FlextInfraPythonVersionEnforcer,
    FlextInfraServiceWorkspaceMixin,
    m,
    t,
)


class FlextInfraCliMaintenance(FlextInfraServiceWorkspaceMixin):
    """Maintenance CLI group — composed into FlextInfraCli via MRO."""

    def register_maintenance(
        self,
        app: t.Cli.CliApp,
    ) -> None:
        """Register maintenance commands on the given Typer app."""
        route = m.Cli.ResultCommandRoute(
            name="run",
            help_text="Enforce Python version constraints",
            model_cls=FlextInfraPythonVersionEnforcer,
            handler=self.enforce_python_version,
            failure_message="Maintenance failed",
            success_message="Maintenance completed",
        )
        cli.register_result_routes(
            app,
            [
                route,
            ],
        )


__all__ = ["FlextInfraCliMaintenance"]
