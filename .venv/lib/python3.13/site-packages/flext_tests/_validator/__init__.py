# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Validator package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _types_parts as _types_parts
    from .bypass import FlextValidatorBypass as FlextValidatorBypass
    from .imports import FlextValidatorImports as FlextValidatorImports
    from .layer import FlextValidatorLayer as FlextValidatorLayer
    from .markdown import FlextValidatorMarkdown as FlextValidatorMarkdown
    from .settings import FlextValidatorSettings as FlextValidatorSettings
    from .tests import FlextValidatorTests as FlextValidatorTests
    from .types import FlextValidatorTypes as FlextValidatorTypes

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._types_parts": ("_types_parts",),
    ".bypass": ("FlextValidatorBypass",),
    ".imports": ("FlextValidatorImports",),
    ".layer": ("FlextValidatorLayer",),
    ".markdown": ("FlextValidatorMarkdown",),
    ".settings": ("FlextValidatorSettings",),
    ".tests": ("FlextValidatorTests",),
    ".types": ("FlextValidatorTypes",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextValidatorBypass",
    "FlextValidatorImports",
    "FlextValidatorLayer",
    "FlextValidatorMarkdown",
    "FlextValidatorSettings",
    "FlextValidatorTests",
    "FlextValidatorTypes",
    "_types_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
