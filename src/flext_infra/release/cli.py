"""CLI registration for the release domain."""

from __future__ import annotations

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.typings import t


class FlextInfraCliRelease(FlextInfraCliGroupBase):
    """Owns release CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="run",
            help_text="Run release orchestration CLI flow",
            model_cls=FlextInfraReleaseOrchestrator,
            handler=FlextInfraReleaseOrchestrator.execute_command,
            success_message="Release completed successfully",
        ),
    )

    def register_release(self, app: t.Cli.CliApp) -> None:
        """Register release routes."""
        FlextInfraCliRelease.register_routes(app)


__all__: list[str] = ["FlextInfraCliRelease"]
