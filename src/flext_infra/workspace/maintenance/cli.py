"""CLI mixin for maintenance commands."""

from __future__ import annotations

from typing import Protocol

from flext_cli import cli
from flext_infra import FlextInfraPythonVersionEnforcer, m, r, t


class _FlextInfraMaintenanceFacade(Protocol):
    """Public maintenance API surface consumed by the CLI mixin."""

    def enforce_python_version(
        self,
        params: FlextInfraPythonVersionEnforcer,
    ) -> r[int]:
        """Run Python version enforcement through the public facade."""
        ...


class FlextInfraCliMaintenance:
    """Maintenance CLI group — composed into FlextInfraCli via MRO."""

    def register_maintenance(
        self: _FlextInfraMaintenanceFacade,
        app: t.Cli.CliApp,
    ) -> None:
        """Register maintenance commands on the given Typer app."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="run",
                    help_text="Enforce Python version constraints",
                    model_cls=FlextInfraPythonVersionEnforcer,
                    handler=self.enforce_python_version,
                    failure_message="Maintenance failed",
                    success_message="Maintenance completed",
                ),
            ],
        )


__all__ = ["FlextInfraCliMaintenance"]
