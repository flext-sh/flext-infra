# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codemod.rules.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .apply_renames import FlextInfraApplyRenames
__all__: tuple[str, ...] = ("FlextInfraApplyRenames",)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({".apply_renames": ("FlextInfraApplyRenames",)}),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
