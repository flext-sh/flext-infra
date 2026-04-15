"""CLI group registration for ``flext-infra deps``."""

from __future__ import annotations

from flext_cli import cli, m
from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraServiceDepsMixin,
    t,
)


class FlextInfraCliDeps(FlextInfraServiceDepsMixin):
    """Dependency CLI group registered on the canonical flext-infra app."""

    def register_deps(self, app: t.Cli.CliApp) -> None:
        """Register dependency commands on the canonical Typer application."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="detect",
                    help_text="Detect runtime vs dev dependencies",
                    model_cls=FlextInfraModelsDeps.DetectCommand,
                    handler=self.detect_dependencies,
                    failure_message="dependency detection failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="extra-paths",
                    help_text="Synchronize pyright/mypy extraPaths",
                    model_cls=FlextInfraModelsDeps.ExtraPathsCommand,
                    handler=self.sync_extra_paths,
                    failure_message="extra-path synchronization failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="internal-sync",
                    help_text="Synchronize internal FLEXT dependencies",
                    model_cls=FlextInfraModelsDeps.InternalSyncCommand,
                    handler=self.sync_internal_dependencies,
                    failure_message="internal dependency sync failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="modernize",
                    help_text="Modernize workspace pyproject files",
                    model_cls=FlextInfraModelsDeps.ModernizeCommand,
                    handler=self.modernize_pyproject,
                    failure_message="pyproject modernization failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="path-sync",
                    help_text="Rewrite internal FLEXT dependency paths",
                    model_cls=FlextInfraModelsDeps.PathSyncCommand,
                    handler=self.sync_dependency_paths,
                    failure_message="dependency path sync failed",
                ),
            ],
        )
