# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".cli": ("FlextInfraCliWorkspace",),
        ".detector": ("FlextInfraWorkspaceDetector",),
        ".migrator": ("FlextInfraProjectMigrator",),
        ".orchestrator": ("FlextInfraOrchestratorService",),
        ".project_makefile": ("FlextInfraProjectMakefileUpdater",),
        ".sync": ("FlextInfraSyncService",),
        ".workspace_makefile": ("FlextInfraWorkspaceMakefileGenerator",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
