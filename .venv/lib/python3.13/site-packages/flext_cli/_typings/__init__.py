# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli. Typings package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextCliTypesBase as FlextCliTypesBase
    from .domain import FlextCliTypesDomain as FlextCliTypesDomain
    from .pipeline import FlextCliTypesPipeline as FlextCliTypesPipeline
    from .xlsx import FlextCliTypesXlsx as FlextCliTypesXlsx

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextCliTypesBase",),
    ".domain": ("FlextCliTypesDomain",),
    ".pipeline": ("FlextCliTypesPipeline",),
    ".xlsx": ("FlextCliTypesXlsx",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCliTypesBase",
    "FlextCliTypesDomain",
    "FlextCliTypesPipeline",
    "FlextCliTypesXlsx",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
