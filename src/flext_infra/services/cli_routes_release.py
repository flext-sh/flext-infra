"""Release CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import c, m
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.services.cli_route_base import CliRouteBase


class ReleaseRoutes(CliRouteBase):
    """Own release routes without loading workspace or refactor owners."""

    release_routes: ClassVar[tuple[m.Cli.ResultCommandRoute, ...]] = (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Run release orchestration CLI flow",
            model_cls=FlextInfraReleaseOrchestrator,
            handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                params
            ).map(CliRouteBase.as_route_value),
            success_message="Release completed successfully",
        ),
    )


__all__: list[str] = ["ReleaseRoutes"]
