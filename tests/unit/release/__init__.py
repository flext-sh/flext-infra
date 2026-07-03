# AUTO-GENERATED FILE — Regenerate with: make gen
"""Release package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".flow_tests": ("flow_tests",),
        ".main_tests": ("main_tests",),
        ".orchestrator_git_tests": ("orchestrator_git_tests",),
        ".orchestrator_helpers_tests": ("orchestrator_helpers_tests",),
        ".orchestrator_publish_tests": ("orchestrator_publish_tests",),
        ".orchestrator_tests": ("orchestrator_tests",),
        ".test_release_dag": ("TestsFlextInfraReleaseDag",),
        ".version_resolution_tests": ("version_resolution_tests",),
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
