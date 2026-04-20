"""CLI registration for the basemk domain."""

from __future__ import annotations

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.typings import t


class FlextInfraCliBasemk(FlextInfraCliGroupBase):
    """Owns basemk CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="generate",
            help_text="Generate base.mk from templates",
            model_cls=FlextInfraBaseMkGenerator,
            handler=FlextInfraBaseMkGenerator.execute_command,
            failure_message="base.mk generation failed",
            success_message="base.mk generated",
        ),
    )

    def register_basemk(self, app: t.Cli.CliApp) -> None:
        """Register basemk routes."""
        FlextInfraCliBasemk.register_routes(app)


__all__: list[str] = ["FlextInfraCliBasemk"]
