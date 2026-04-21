"""CLI registration for the deps domain."""

from __future__ import annotations

from flext_core import r

from flext_infra import (
    FlextInfraCliGroupBase,
    FlextInfraExtraPathsManager,
    FlextInfraInternalDependencySyncService,
    FlextInfraModelsDeps,
    FlextInfraPyprojectModernizer,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraUtilitiesDependencyPathSync,
    p,
    t,
)


class FlextInfraCliDeps(FlextInfraCliGroupBase):
    """Owns deps CLI route declarations."""

    @staticmethod
    def _sync_dependency_paths(
        params: FlextInfraModelsDeps.PathSyncCommand,
    ) -> p.Result[bool]:
        service = FlextInfraUtilitiesDependencyPathSync()
        exit_code = service.execute(params)
        if exit_code != 0:
            return r[bool].fail("dependency path sync failed")
        return r[bool].ok(True)

    routes = (
        FlextInfraCliGroupBase.route(
            name="detect",
            help_text="Detect runtime vs dev dependencies",
            model_cls=FlextInfraRuntimeDevDependencyDetector,
            handler=FlextInfraRuntimeDevDependencyDetector.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="extra-paths",
            help_text="Synchronize pyright/mypy extraPaths",
            model_cls=FlextInfraExtraPathsManager,
            handler=FlextInfraExtraPathsManager.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="internal-sync",
            help_text="Synchronize internal FLEXT dependencies",
            model_cls=FlextInfraInternalDependencySyncService,
            handler=FlextInfraInternalDependencySyncService.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="modernize",
            help_text="Modernize workspace pyproject files",
            model_cls=FlextInfraPyprojectModernizer,
            handler=FlextInfraPyprojectModernizer.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="path-sync",
            help_text="Rewrite internal FLEXT dependency paths",
            model_cls=FlextInfraModelsDeps.PathSyncCommand,
            handler=_sync_dependency_paths,
        ),
    )

    def register_deps(self, app: t.Cli.CliApp) -> None:
        """Register deps routes."""
        FlextInfraCliDeps.register_routes(app)


__all__: list[str] = ["FlextInfraCliDeps"]
