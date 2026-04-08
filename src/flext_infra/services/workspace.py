"""Public workspace service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_core import r
from flext_infra import (
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraPythonVersionEnforcer,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
)


class FlextInfraServiceWorkspaceMixin:
    """Expose workspace operations through the public infra facade."""

    def detect_workspace(
        self,
        params: FlextInfraWorkspaceDetector,
    ) -> r[c.Infra.WorkspaceMode]:
        """Detect workspace mode through the public facade."""
        return params.execute()

    def sync_workspace(self, params: FlextInfraSyncService) -> r[m.Infra.SyncResult]:
        """Sync workspace files through the public facade."""
        return params.execute()

    def orchestrate_workspace(
        self,
        params: FlextInfraOrchestratorService,
    ) -> r[bool]:
        """Run workspace orchestration through the public facade."""
        return params.execute()

    def migrate_workspace(
        self,
        params: FlextInfraProjectMigrator,
    ) -> r[Sequence[m.Infra.MigrationResult]]:
        """Run workspace migration through the public facade."""
        return params.execute()

    def enforce_python_version(self, params: FlextInfraPythonVersionEnforcer) -> r[int]:
        """Run Python-version enforcement through the public facade."""
        return params.execute()


__all__: Sequence[str] = ("FlextInfraServiceWorkspaceMixin",)
