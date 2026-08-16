# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers.smells package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import (
        FlextInfraSmellFixer,
        auto_fixable_smell_tags,
        register_smell_fixer,
        smell_fixer_for,
    )
    from .boolean_logic import FlextInfraBooleanLogicFixer
__all__: tuple[str, ...] = (
    "FlextInfraBooleanLogicFixer",
    "FlextInfraSmellFixer",
    "auto_fixable_smell_tags",
    "register_smell_fixer",
    "smell_fixer_for",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".base": (
                    "FlextInfraSmellFixer",
                    "auto_fixable_smell_tags",
                    "register_smell_fixer",
                    "smell_fixer_for",
                ),
                ".boolean_logic": ("FlextInfraBooleanLogicFixer",),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
