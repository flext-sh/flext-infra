"""Centralized CLI registration and handlers for release commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import FlextInfraReleaseOrchestrator, m, t


class FlextInfraCliRelease:
    """Release CLI group — composed into the centralized infra CLI."""

    def register_release(self, app: t.Cli.TyperApp) -> None:
        """Register release commands on the given application."""
        orchestrator = FlextInfraReleaseOrchestrator()
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="run",
                    help_text="Run release orchestration CLI flow",
                    model_cls=m.Infra.ReleaseRunInput,
                    handler=orchestrator.execute_command,
                    failure_message="Release failed",
                    success_message="Release completed successfully",
                ),
            ],
        )


__all__ = ["FlextInfraCliRelease"]
