"""CLI mixin for basemk commands."""

from __future__ import annotations

from flext_cli import cli as cli_service, m, t
from flext_infra import FlextInfraBaseMkGenerator


class FlextInfraCliBasemk:
    """Basemk CLI group — composed into FlextInfraCli via MRO."""

    def register_basemk(self, app: t.Cli.CliApp) -> None:
        """Register basemk commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="generate",
                    help_text="Generate base.mk from templates",
                    model_cls=FlextInfraBaseMkGenerator,
                    handler=FlextInfraBaseMkGenerator.execute_command,
                    failure_message="base.mk generation failed",
                    success_message="base.mk generated",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliBasemk"]
