"""CLI registration for the maintenance domain."""

from __future__ import annotations

from flext_infra import FlextInfraCliGroupBase, FlextInfraPythonVersionEnforcer, t


class FlextInfraCliMaintenance(FlextInfraCliGroupBase):
    """Owns maintenance CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="run",
            help_text="Enforce Python version constraints",
            model_cls=FlextInfraPythonVersionEnforcer,
            handler=FlextInfraPythonVersionEnforcer.execute_command,
            success_message="Maintenance completed",
        ),
    )

    def register_maintenance(self, app: t.Cli.CliApp) -> None:
        """Register maintenance routes."""
        FlextInfraCliMaintenance.register_routes(app)


__all__: list[str] = ["FlextInfraCliMaintenance"]
