# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Semantic Cutover package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .alias_cst import FlextInfraUtilitiesSemanticCutoverAliasCst
    from .aliases import FlextInfraUtilitiesSemanticCutoverAliases
    from .base import FlextInfraUtilitiesSemanticCutoverBase
    from .edits import FlextInfraUtilitiesSemanticCutoverEdits
    from .family_flatten import FlextInfraUtilitiesSemanticFamilyFlatten
    from .family_references import FlextInfraUtilitiesSemanticFamilyReferences
    from .nesting import FlextInfraUtilitiesSemanticCutoverNesting
    from .nesting_cst import FlextInfraUtilitiesSemanticCutoverNestingCst
    from .nesting_references import FlextInfraUtilitiesSemanticCutoverNestingReferences
    from .private_import_cst import FlextInfraUtilitiesSemanticCutoverPrivateImportCst
    from .private_imports import FlextInfraUtilitiesSemanticCutoverPrivateImports


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesSemanticCutoverAliasCst",
    "FlextInfraUtilitiesSemanticCutoverAliases",
    "FlextInfraUtilitiesSemanticCutoverBase",
    "FlextInfraUtilitiesSemanticCutoverEdits",
    "FlextInfraUtilitiesSemanticCutoverNesting",
    "FlextInfraUtilitiesSemanticCutoverNestingCst",
    "FlextInfraUtilitiesSemanticCutoverNestingReferences",
    "FlextInfraUtilitiesSemanticCutoverPrivateImportCst",
    "FlextInfraUtilitiesSemanticCutoverPrivateImports",
    "FlextInfraUtilitiesSemanticFamilyFlatten",
    "FlextInfraUtilitiesSemanticFamilyReferences",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".alias_cst": ("FlextInfraUtilitiesSemanticCutoverAliasCst",),
            ".aliases": ("FlextInfraUtilitiesSemanticCutoverAliases",),
            ".base": ("FlextInfraUtilitiesSemanticCutoverBase",),
            ".edits": ("FlextInfraUtilitiesSemanticCutoverEdits",),
            ".family_flatten": ("FlextInfraUtilitiesSemanticFamilyFlatten",),
            ".family_references": ("FlextInfraUtilitiesSemanticFamilyReferences",),
            ".nesting": ("FlextInfraUtilitiesSemanticCutoverNesting",),
            ".nesting_cst": ("FlextInfraUtilitiesSemanticCutoverNestingCst",),
            ".nesting_references": (
                "FlextInfraUtilitiesSemanticCutoverNestingReferences",
            ),
            ".private_import_cst": (
                "FlextInfraUtilitiesSemanticCutoverPrivateImportCst",
            ),
            ".private_imports": ("FlextInfraUtilitiesSemanticCutoverPrivateImports",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
