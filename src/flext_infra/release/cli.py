"""Centralized CLI registration and handlers for release commands."""

from __future__ import annotations

from flext_cli.api import cli as cli_service
from flext_infra import (
    FlextInfraReleaseOrchestrator,
    FlextInfraServiceReleaseMixin,
    m,
    t,
)


class FlextInfraCliRelease(FlextInfraServiceReleaseMixin):
    """Release CLI group — composed into the centralized infra CLI."""

    def register_release(self, app: t.Cli.CliApp) -> None:
        """Register release commands on the given application."""
        routes = (
            m.Cli.ResultCommandRoute(
                name="run",
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=self.run_release,
                failure_message="Release failed",
                success_message="Release completed successfully",
            ),
        )
        cli_service.register_result_routes(
            app,
            routes,
        )


__all__ = ["FlextInfraCliRelease"]
