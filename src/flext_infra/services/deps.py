"""Public dependency service mixin for the infra API facade."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from flext_core import r
from flext_infra import (
    FlextInfraDependencyDetectorRuntime,
    FlextInfraExtraPathsManager,
    FlextInfraInternalDependencySyncService,
    FlextInfraModelsDeps,
    FlextInfraPyprojectModernizer,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraUtilitiesCli,
    FlextInfraUtilitiesDependencyPathSync,
)


class FlextInfraServiceDepsMixin:
    """Expose dependency operations through the public infra facade."""

    def detect_dependencies(
        self,
        params: FlextInfraModelsDeps.DetectCommand,
    ) -> r[bool]:
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
    ) -> r[bool]:
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
        if result.is_failure:
            return r[bool].fail(result.error or "sync failed")
        return r[bool].ok(True)

    def sync_internal_dependencies(
        self,
        params: FlextInfraModelsDeps.InternalSyncCommand,
    ) -> r[bool]:
        """Synchronize internal FLEXT dependencies."""
        service = FlextInfraInternalDependencySyncService()
        result = service.sync(params.workspace_path)
        if result.is_failure:
            return r[bool].fail(result.error or "internal dependency sync failed")
        return r[bool].ok(True)

    def modernize_pyproject(
        self,
        params: FlextInfraModelsDeps.ModernizeCommand,
    ) -> r[bool]:
        """Modernize workspace pyproject files."""
        service = FlextInfraPyprojectModernizer(workspace_root=params.workspace_path)
        namespace = argparse.Namespace(
            audit=params.audit,
            check=params.check,
            dry_run=params.dry_run,
            skip_check=params.skip_check,
            skip_comments=params.skip_comments,
        )
        cli_payload = FlextInfraUtilitiesCli.CliArgs(
            workspace=params.workspace_path,
            apply=params.apply,
            check=params.check,
            projects=list(params.project_names or []),
        )
        exit_code = service.run(
            namespace,
            cli_payload,
        )
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)

    def sync_dependency_paths(
        self,
        params: FlextInfraModelsDeps.PathSyncCommand,
    ) -> r[bool]:
        """Rewrite internal dependency paths."""
        service = FlextInfraUtilitiesDependencyPathSync()
        cli_payload = FlextInfraUtilitiesCli.CliArgs(
            workspace=params.workspace_path,
            apply=params.apply,
            projects=list(params.project_names or []),
        )
        exit_code = service.execute(
            cli=cli_payload,
            mode=params.mode,
        )
        if exit_code != 0:
            return r[bool].fail("dependency path sync failed")
        return r[bool].ok(True)


__all__: Sequence[str] = ("FlextInfraServiceDepsMixin",)
