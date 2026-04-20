"""CLI registration for the deps domain."""

from __future__ import annotations

from flext_core import r

from flext_infra._utilities.deps_path_sync import FlextInfraUtilitiesDependencyPathSync
from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.models import FlextInfraModelsDeps
from flext_infra.protocols import p
from flext_infra.typings import t


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
            failure_message="dependency detection failed",
        ),
        FlextInfraCliGroupBase.route(
            name="extra-paths",
            help_text="Synchronize pyright/mypy extraPaths",
            model_cls=FlextInfraExtraPathsManager,
            handler=FlextInfraExtraPathsManager.execute_command,
            failure_message="extra-path synchronization failed",
        ),
        FlextInfraCliGroupBase.route(
            name="internal-sync",
            help_text="Synchronize internal FLEXT dependencies",
            model_cls=FlextInfraInternalDependencySyncService,
            handler=FlextInfraInternalDependencySyncService.execute_command,
            failure_message="internal dependency sync failed",
        ),
        FlextInfraCliGroupBase.route(
            name="modernize",
            help_text="Modernize workspace pyproject files",
            model_cls=FlextInfraPyprojectModernizer,
            handler=FlextInfraPyprojectModernizer.execute_command,
            failure_message="pyproject modernization failed",
        ),
        FlextInfraCliGroupBase.route(
            name="path-sync",
            help_text="Rewrite internal FLEXT dependency paths",
            model_cls=FlextInfraModelsDeps.PathSyncCommand,
            handler=_sync_dependency_paths,
            failure_message="dependency path sync failed",
        ),
    )

    def register_deps(self, app: t.Cli.CliApp) -> None:
        """Register deps routes."""
        FlextInfraCliDeps.register_routes(app)


__all__: list[str] = ["FlextInfraCliDeps"]
