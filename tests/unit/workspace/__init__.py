# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_main": ("TestsFlextInfraWorkspaceMain",),
        ".test_makefile_dry_run": ("TestsFlextInfraWorkspaceMakefileDryRun",),
        ".test_makefile_generator": ("TestsFlextInfraWorkspaceMakefileGenerator",),
        ".test_propagate": ("TestsFlextInfraWorkspacePropagator",),
        ".test_sync": ("TestsFlextInfraWorkspaceSync",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
