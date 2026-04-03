"""CLI mixin for basemk commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import FlextInfraBaseMkGenerator, m, u

if TYPE_CHECKING:
    import typer

_R = u.Infra.route  # shorthand


class FlextInfraCliBasemk:
    """Basemk CLI group — composed into FlextInfraCli via MRO."""

    def register_basemk(self, app: typer.Typer) -> None:
        """Register basemk commands on the given Typer app."""
        u.Infra.register_routes(
            app,
            [
                _R(
                    "generate",
                    "Generate base.mk from templates",
                    m.Infra.BaseMkGenerateInput,
                    FlextInfraBaseMkGenerator().execute_command,
                    fail_msg="base.mk generation failed",
                    success_msg="base.mk generated",
                ),
            ],
        )
