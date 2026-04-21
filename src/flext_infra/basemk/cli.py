"""CLI registration for the basemk domain."""

from __future__ import annotations

from flext_infra import FlextInfraBaseMkGenerator, FlextInfraCliGroupBase, t


class FlextInfraCliBasemk(FlextInfraCliGroupBase):
    """Owns basemk CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="generate",
            help_text="Generate base.mk from templates",
            model_cls=FlextInfraBaseMkGenerator,
            handler=FlextInfraBaseMkGenerator.execute_command,
            success_message="base.mk generated",
        ),
    )

    def register_basemk(self, app: t.Cli.CliApp) -> None:
        """Register basemk routes."""
        FlextInfraCliBasemk.register_routes(app)


__all__: list[str] = ["FlextInfraCliBasemk"]
