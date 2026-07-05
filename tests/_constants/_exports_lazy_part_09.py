# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_09 = build_lazy_import_map(
    {
        ".base": ("s",),
        ".typings": ("t",),
        ".unit": ("unit",),
        ".unit.fixtures": (
            "services_resource",
            "tool_config_document",
        ),
        ".utilities": ("u",),
        "flext_tests": (
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "x",
        ),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_09"]
