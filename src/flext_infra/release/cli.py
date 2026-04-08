"""Centralized CLI registration and handlers for release commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli as cli_service
from flext_infra import FlextInfraReleaseOrchestrator, m, t

if TYPE_CHECKING:
    from flext_infra import FlextInfra


class FlextInfraCliRelease:
    """Release CLI group — composed into the centralized infra CLI."""

    def register_release(self: FlextInfra, app: t.Cli.CliApp) -> None:
        """Register release commands on the given application."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="run",
                    help_text="Run release orchestration CLI flow",
                    model_cls=FlextInfraReleaseOrchestrator,
                    handler=self.run_release,
                    failure_message="Release failed",
                    success_message="Release completed successfully",
                ),
            ],
        )


__all__ = ["FlextInfraCliRelease"]
