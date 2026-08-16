# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .custom_policy import FlextInfraCustomMkPolicy
    from .generator import FlextInfraBaseMkGenerator
    from .renderer import FlextInfraBaseMkTemplateRenderer
__all__: tuple[str, ...] = (
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateRenderer",
    "FlextInfraCustomMkPolicy",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".custom_policy": ("FlextInfraCustomMkPolicy",),
            ".generator": ("FlextInfraBaseMkGenerator",),
            ".renderer": ("FlextInfraBaseMkTemplateRenderer",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
