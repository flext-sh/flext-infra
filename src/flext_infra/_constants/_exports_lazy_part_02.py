# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".api": ("infra",),
        ".base": ("s",),
        ".cli": ("main",),
        ".fixers": ("fixers",),
        ".gates": ("gates",),
        ".maintenance": ("maintenance",),
        ".models": ("m",),
        ".protocols": ("p",),
        ".refactor": ("refactor",),
        ".release": ("release",),
        ".transformers": ("transformers",),
        ".typings": ("t",),
        ".utilities": ("u",),
        ".validate": ("validate",),
        ".workspace": ("workspace",),
        "flext_core._root_typing_parts.facades": (
            "e",
            "h",
            "r",
            "x",
        ),
    },
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS_PART_02"]
