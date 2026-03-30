"""CLI mixin for basemk commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli

from flext_infra import FlextInfraBaseMkGenerator, m

if TYPE_CHECKING:
    import typer


class FlextInfraCliBasemk:
    """Basemk CLI group — composed into FlextInfraCli via MRO."""

    def register_basemk(self, app: typer.Typer) -> None:
        """Register basemk commands on the given Typer app."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="generate",
                help_text="Generate base.mk from templates",
                model_cls=m.Infra.BaseMkGenerateInput,
                handler=FlextInfraBaseMkGenerator().execute_command,
                success_message="base.mk generated",
                failure_message="base.mk generation failed",
            ),
        )
