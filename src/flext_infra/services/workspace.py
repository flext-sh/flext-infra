"""Public workspace service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraPythonVersionEnforcer,
    FlextInfraServiceCliRunnerMixin,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
    p,
    t,
)


class FlextInfraServiceWorkspaceMixin(FlextInfraServiceCliRunnerMixin):
    """Expose workspace operations through the public infra facade."""

    def detect_workspace(
        self,
        params: FlextInfraWorkspaceDetector,
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode through the public facade."""
        return self._dispatch_result(params)

    def sync_workspace(
        self, params: FlextInfraSyncService
    ) -> p.Result[m.Infra.SyncResult]:
        """Sync workspace files through the public facade."""
        return self._dispatch_result(params)

    def orchestrate_workspace(
        self,
        params: FlextInfraOrchestratorService,
    ) -> p.Result[bool]:
        """Run workspace orchestration through the public facade."""
        return self._dispatch_result(params)

    def migrate_workspace(
        self,
        params: FlextInfraProjectMigrator,
    ) -> p.Result[Sequence[m.Infra.MigrationResult]]:
        """Run workspace migration through the public facade."""
        return self._dispatch_result(params)

    def enforce_python_version(
        self, params: FlextInfraPythonVersionEnforcer
    ) -> p.Result[int]:
        """Run Python-version enforcement through the public facade."""
        return self._dispatch_result(params)


__all__: t.StrSequence = ("FlextInfraServiceWorkspaceMixin",)
