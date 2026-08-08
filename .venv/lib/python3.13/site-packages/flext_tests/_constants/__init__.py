# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .data_cases import FlextTestsConstantsDataCases as FlextTestsConstantsDataCases
    from .docker import FlextTestsConstantsDocker as FlextTestsConstantsDocker
    from .files import FlextTestsConstantsFiles as FlextTestsConstantsFiles
    from .make import FlextTestsConstantsMake as FlextTestsConstantsMake
    from .matcher import FlextTestsConstantsMatcher as FlextTestsConstantsMatcher
    from .validator import FlextTestsConstantsValidator as FlextTestsConstantsValidator

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".data_cases": ("FlextTestsConstantsDataCases",),
    ".docker": ("FlextTestsConstantsDocker",),
    ".files": ("FlextTestsConstantsFiles",),
    ".make": ("FlextTestsConstantsMake",),
    ".matcher": ("FlextTestsConstantsMatcher",),
    ".validator": ("FlextTestsConstantsValidator",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsConstantsDataCases",
    "FlextTestsConstantsDocker",
    "FlextTestsConstantsFiles",
    "FlextTestsConstantsMake",
    "FlextTestsConstantsMatcher",
    "FlextTestsConstantsValidator",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
