# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Typings package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextTestsBaseTypesMixin as FlextTestsBaseTypesMixin
    from .files import FlextTestsFilesTypesMixin as FlextTestsFilesTypesMixin
    from .guards import FlextTestsGuardsTypesMixin as FlextTestsGuardsTypesMixin
    from .make import FlextTestsMakeTypesMixin as FlextTestsMakeTypesMixin
    from .matchers import FlextTestsMatchersTypesMixin as FlextTestsMatchersTypesMixin

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextTestsBaseTypesMixin",),
    ".files": ("FlextTestsFilesTypesMixin",),
    ".guards": ("FlextTestsGuardsTypesMixin",),
    ".make": ("FlextTestsMakeTypesMixin",),
    ".matchers": ("FlextTestsMatchersTypesMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsBaseTypesMixin",
    "FlextTestsFilesTypesMixin",
    "FlextTestsGuardsTypesMixin",
    "FlextTestsMakeTypesMixin",
    "FlextTestsMatchersTypesMixin",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
