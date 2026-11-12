# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Typings package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._typings.adapters import FlextInfraTypesAdapters
    from flext_infra._typings.base import FlextInfraTypesBase
    from flext_infra._typings.collections import FlextInfraTypesCollections
    from flext_infra._typings.pytest_surface import FlextInfraTypesPytest
    from flext_infra._typings.rope import FlextInfraTypesRope
    from flext_infra._typings.rope_native import FlextInfraTypesRopeNative


__all__: tuple[str, ...] = (
    "FlextInfraTypesAdapters",
    "FlextInfraTypesBase",
    "FlextInfraTypesCollections",
    "FlextInfraTypesPytest",
    "FlextInfraTypesRope",
    "FlextInfraTypesRopeNative",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraTypesAdapters": ".adapters",
        "FlextInfraTypesBase": ".base",
        "FlextInfraTypesCollections": ".collections",
        "FlextInfraTypesPytest": ".pytest_surface",
        "FlextInfraTypesRope": ".rope",
        "FlextInfraTypesRopeNative": ".rope_native",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraTypesPytest": ("Pytest",),
        "FlextInfraTypesRope": (
            "RopeSourceMemberResolverFactory",
            "FacadeMemberScope",
            "FacadeComponentClaims",
            "Cst",
            "PythonImportNode",
            "RopeSourcePath",
            "RopeImplementationPaths",
            "RopeMutablePaths",
            "RopeCallableSignature",
            "PythonClassNode",
            "CstArgument",
            "CstStatement",
            "CstImportAlias",
            "CstModule",
            "CstClass",
            "CstImport",
            "CstMetadata",
            "RopeProject",
            "RopeResource",
            "RopeImportLookup",
            "CodemodImportWalkNode",
            "CodemodImportWalkMemo",
            "RopeFile",
            "RopeRoot",
            "RopeLocation",
            "RopeSemanticModule",
            "RopeParsedModule",
            "RopePyModule",
            "RopeSourceModule",
            "RopePyName",
            "RopeAssignedName",
            "RopePyObject",
            "RopeAstNode",
            "RopeScope",
            "RopeFromImport",
            "RopeNormalImport",
            "RopeImportInfo",
            "RopeImportStatement",
            "RopeModuleImports",
            "RopeChangeSet",
            "RopeMoveGlobal",
            "RopeOccurrence",
            "RopeOccurrenceFinder",
            "RopeOccurrenceFilter",
            "RopeTransformFn",
            "RopeMatchFilter",
            "RopeNativeCore",
            "RopeNativeObject",
            "RopeNativeProject",
            "RopeNativeImportStyle",
            "RopeNativeImportPrefs",
            "RopeNativeSourceModule",
            "RopeNativeParsedModule",
            "RopeNativeSemanticModule",
            "RopeNativeResource",
            "RopeNativeMatch",
        ),
        "FlextInfraTypesRopeNative": (
            "RopeNativeCore",
            "RopeNativeObject",
            "RopeNativeProject",
            "RopeNativeImportStyle",
            "RopeNativeImportPrefs",
            "RopeNativeSourceModule",
            "RopeNativeParsedModule",
            "RopeNativeSemanticModule",
            "RopeNativeResource",
            "RopeNativeMatch",
        ),
    },
)
