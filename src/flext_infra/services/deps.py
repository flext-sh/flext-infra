"""Public dependency service mixin for the infra API facade."""

from __future__ import annotations

from flext_infra import (
    FlextInfraDependencyDetectorRuntime,
    FlextInfraExtraPathsManager,
    FlextInfraInternalDependencySyncService,
    FlextInfraModelsDeps,
    FlextInfraPyprojectModernizer,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraUtilitiesDependencyPathSync,
    p,
    r,
    t,
)


class FlextInfraServiceDepsMixin:
    """Expose dependency operations through the public infra facade."""

    def detect_dependencies(
        self,
        params: FlextInfraModelsDeps.DetectCommand,
    ) -> p.Result[bool]:
        """Run dependency detection through the public facade."""
        detector = FlextInfraRuntimeDevDependencyDetector()
        runtime = FlextInfraDependencyDetectorRuntime(
            detector=detector,
            workspace_report_factory=FlextInfraModelsDeps.WorkspaceDependencyReport,
            dependency_limits_factory=FlextInfraModelsDeps.DependencyLimitsInfo,
            pip_check_factory=FlextInfraModelsDeps.PipCheckReport,
        )
        return runtime.run(params)

    def sync_extra_paths(
        self,
        params: FlextInfraModelsDeps.ExtraPathsCommand,
    ) -> p.Result[bool]:
        """Synchronize pyright and mypy extra paths."""
        manager = FlextInfraExtraPathsManager(workspace_root=params.workspace_path)
        result = manager.sync_extra_paths(
            dry_run=params.dry_run,
            project_dirs=[
                params.workspace_path / project_name
                for project_name in (params.project_names or [])
            ]
            or None,
        )
        if result.failure:
            return r[bool].fail(result.error or "sync failed")
        return r[bool].ok(True)

    def sync_internal_dependencies(
        self,
        params: FlextInfraModelsDeps.InternalSyncCommand,
    ) -> p.Result[bool]:
        """Synchronize internal FLEXT dependencies."""
        service = FlextInfraInternalDependencySyncService()
        result = service.sync(params.workspace_path)
        if result.failure:
            return r[bool].fail(result.error or "internal dependency sync failed")
        return r[bool].ok(True)

    def modernize_pyproject(
        self,
        params: FlextInfraModelsDeps.ModernizeCommand,
    ) -> p.Result[bool]:
        """Modernize workspace pyproject files."""
        service = FlextInfraPyprojectModernizer(workspace_root=params.workspace_path)
        exit_code = service.run(params)
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)

    def sync_dependency_paths(
        self,
        params: FlextInfraModelsDeps.PathSyncCommand,
    ) -> p.Result[bool]:
        """Rewrite internal dependency paths."""
        service = FlextInfraUtilitiesDependencyPathSync()
        exit_code = service.execute(params)
        if exit_code != 0:
            return r[bool].fail("dependency path sync failed")
        return r[bool].ok(True)


__all__: t.StrSequence = ("FlextInfraServiceDepsMixin",)
