# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".base": ("s",),
        ".cli": ("main",),
        ".maintenance": ("maintenance",),
        ".protocols": ("p",),
        ".refactor": ("refactor",),
        ".release": ("release",),
        ".transformers": ("transformers",),
        ".typings": ("t",),
        ".utilities": ("u",),
        ".validate": ("validate",),
        ".workspace": ("workspace",),
    },
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS_PART_02"]
