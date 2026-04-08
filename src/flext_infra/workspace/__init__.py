# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

_LAZY_IMPORTS = merge_lazy_imports(
    (".maintenance",),
    build_lazy_import_map(
        {
            ".cli": ("FlextInfraCliWorkspace",),
            ".detector": ("FlextInfraWorkspaceDetector",),
            ".migrator": ("FlextInfraProjectMigrator",),
            ".orchestrator": ("FlextInfraOrchestratorService",),
            ".project_makefile": ("FlextInfraProjectMakefileUpdater",),
            ".sync": ("FlextInfraSyncService",),
            ".workspace_makefile": ("FlextInfraWorkspaceMakefileGenerator",),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
