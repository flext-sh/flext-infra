"""CLI registration and compatibility entry points for ``flext-infra deps``."""

from __future__ import annotations

from collections.abc import Sequence

from flext_cli import cli as cli_service, m as cli_models
from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraServiceDepsMixin,
    FlextInfraUtilitiesCliDispatch,
    t,
)


class FlextInfraCliDeps(FlextInfraServiceDepsMixin):
    """Dependency CLI group registered on the canonical flext-infra app."""

    def register_deps(self, app: t.Cli.CliApp) -> None:
        """Register dependency commands on the canonical Typer application."""
        cli_service.register_result_routes(
            app,
            [
                cli_models.Cli.ResultCommandRoute(
                    name="detect",
                    help_text="Detect runtime vs dev dependencies",
                    model_cls=FlextInfraModelsDeps.DetectCommand,
                    handler=self.detect_dependencies,
                    failure_message="dependency detection failed",
                ),
                cli_models.Cli.ResultCommandRoute(
                    name="extra-paths",
                    help_text="Synchronize pyright/mypy extraPaths",
                    model_cls=FlextInfraModelsDeps.ExtraPathsCommand,
                    handler=self.sync_extra_paths,
                    failure_message="extra-path synchronization failed",
                ),
                cli_models.Cli.ResultCommandRoute(
                    name="internal-sync",
                    help_text="Synchronize internal FLEXT dependencies",
                    model_cls=FlextInfraModelsDeps.InternalSyncCommand,
                    handler=self.sync_internal_dependencies,
                    failure_message="internal dependency sync failed",
                ),
                cli_models.Cli.ResultCommandRoute(
                    name="modernize",
                    help_text="Modernize workspace pyproject files",
                    model_cls=FlextInfraModelsDeps.ModernizeCommand,
                    handler=self.modernize_pyproject,
                    failure_message="pyproject modernization failed",
                ),
                cli_models.Cli.ResultCommandRoute(
                    name="path-sync",
                    help_text="Rewrite internal FLEXT dependency paths",
                    model_cls=FlextInfraModelsDeps.PathSyncCommand,
                    handler=self.sync_dependency_paths,
                    failure_message="dependency path sync failed",
                ),
            ],
        )

    @staticmethod
    def run(args: Sequence[str] | None = None) -> int:
        """Run the canonical ``deps`` group."""
        return FlextInfraUtilitiesCliDispatch.run_group("deps", args)
