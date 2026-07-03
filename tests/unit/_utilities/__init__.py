# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesdiscoveryconsolidated",
        ),
        ".test_formatting": ("TestsFlextInfraUtilitiesformatting",),
        ".test_protected_edit": ("TestsFlextInfraUtilitiesProtectedEdit",),
        ".test_rope_analysis": ("TestsFlextInfraRopeAnalysis",),
        ".test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
        ".test_safety": ("TestsFlextInfraUtilitiessafety",),
        ".test_scanning": ("TestsFlextInfraUtilitiesscanning",),
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
