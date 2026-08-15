# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .custom_policy import FlextInfraCustomMkPolicy
    from .generator import FlextInfraBaseMkGenerator
    from .renderer import FlextInfraBaseMkTemplateRenderer

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".custom_policy": ("FlextInfraCustomMkPolicy",),
    ".generator": ("FlextInfraBaseMkGenerator",),
    ".renderer": ("FlextInfraBaseMkTemplateRenderer",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateRenderer",
    "FlextInfraCustomMkPolicy",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
