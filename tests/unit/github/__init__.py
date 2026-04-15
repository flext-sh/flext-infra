# AUTO-GENERATED FILE — Regenerate with: make gen
"""Github package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".main_cli_tests": ("main_cli_tests",),
        ".main_dispatch_tests": ("main_dispatch_tests",),
        ".main_integration_tests": ("main_integration_tests",),
        ".main_tests": ("main_tests",),
        "flext_infra": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
