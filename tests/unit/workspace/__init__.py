# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".make_constants_tests": ("make_constants_tests",),
        ".resolve_what_tests": ("resolve_what_tests",),
        ".test_main": ("TestsFlextInfraWorkspaceMain",),
        ".test_makefile_dry_run": ("TestsFlextInfraWorkspaceMakefileDryRun",),
        ".test_makefile_generator": ("TestsFlextInfraWorkspaceMakefileGenerator",),
        ".test_sync": ("TestsFlextInfraWorkspaceSync",),
        "flext_tests": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
