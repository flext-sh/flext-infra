# AUTO-GENERATED FILE — Regenerate with: make gen
"""Smells package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.transformers.smells.base import FlextInfraSmellFixer
    from flext_infra.transformers.smells.boolean_logic import (
        FlextInfraBooleanLogicFixer,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": (
            "FlextInfraSmellFixer",
            "auto_fixable_smell_tags",
            "register_smell_fixer",
            "smell_fixer_for",
        ),
        ".boolean_logic": ("FlextInfraBooleanLogicFixer",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
