# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_engine": ("test_engine",),
        ".test_generator": ("test_generator",),
        ".test_generator_edge_cases": ("test_generator_edge_cases",),
        ".test_init": ("test_init",),
        ".test_main": ("test_main",),
        ".test_make_contract": ("test_make_contract",),
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
