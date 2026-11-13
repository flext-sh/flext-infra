"""Rope-specific type aliases for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from ast import ClassDef, Import, ImportFrom
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra._protocols import FlextInfraProtocolsRopeRuntime
from flext_infra._typings import FlextInfraTypesRopeNative


class FlextInfraTypesRope(FlextInfraTypesRopeNative):
    """Rope type aliases — accessed via t.Infra.*."""

    type RopeSourceMemberResolverFactory = Callable[
        [], FlextInfraProtocolsRopeRuntime.RopeSourceMemberResolver
    ]

    type FacadeMemberScope = tuple[
        Callable[[], FlextInfraProtocolsRopeRuntime.RopeSourceMemberResolver],
        FlextInfraProtocolsRopeRuntime.RopeProject,
        Mapping[
            str, Mapping[str, Sequence[FlextInfraProtocolsRopeRuntime.RopePyObject]]
        ]
        | None,
    ]

    type FacadeComponentClaims = Mapping[
        tuple[FlextInfraProtocolsRopeRuntime.RopeClassObject, str],
        Sequence[tuple[str, str, FlextInfraProtocolsRopeRuntime.RopeClassObject]],
    ]

    type PythonImportNode = Import | ImportFrom
    type RopeSourcePath = Path
    type RopeImplementationPaths = frozenset[RopeSourcePath]
    type RopeMutablePaths = set[RopeSourcePath]
    type RopeCallableSignature = tuple[
        Sequence[str],
        Sequence[str],
        str | None,
        Sequence[str],
        str | None,
        Sequence[str],
        Sequence[str | None],
        bool,
    ]
    type PythonClassNode = ClassDef

    type RopeProject = FlextInfraProtocolsRopeRuntime.RopeProject
    type RopeResource = FlextInfraProtocolsRopeRuntime.RopeResource
    type RopeImportLookup = MutableMapping[tuple[str, str, int], RopeResource | None]
    type CodemodImportWalkNode = (
        tuple[Path, tuple[tuple[str, RopeResource], ...]] | None
    )
    type CodemodImportWalkMemo = tuple[
        RopeImportLookup, MutableMapping[str, CodemodImportWalkNode]
    ]
    type RopeFile = FlextInfraProtocolsRopeRuntime.RopeFile
    type RopeRoot = FlextInfraProtocolsRopeRuntime.RopeRoot
    type RopeLocation = FlextInfraProtocolsRopeRuntime.RopeLocation
    type RopeSemanticModule = FlextInfraProtocolsRopeRuntime.RopeSemanticModule
    type RopeParsedModule = FlextInfraProtocolsRopeRuntime.RopeParsedModule
    type RopePyModule = FlextInfraProtocolsRopeRuntime.RopePyModule
    type RopeSourceModule = FlextInfraProtocolsRopeRuntime.RopeSourceModule
    type RopePyName = FlextInfraProtocolsRopeRuntime.RopePyName
    type RopeAssignedName = FlextInfraProtocolsRopeRuntime.RopeAssignedName
    type RopePyObject = FlextInfraProtocolsRopeRuntime.RopePyObject
    type RopeAstNode = FlextInfraProtocolsRopeRuntime.RopeAstNode
    type RopeScope = FlextInfraProtocolsRopeRuntime.RopeScope
    type RopeFromImport = FlextInfraProtocolsRopeRuntime.RopeFromImport
    type RopeNormalImport = FlextInfraProtocolsRopeRuntime.RopeNormalImport
    type RopeImportInfo = FlextInfraProtocolsRopeRuntime.RopeImportInfo
    type RopeImportStatement = FlextInfraProtocolsRopeRuntime.RopeImportStatement
    type RopeModuleImports = FlextInfraProtocolsRopeRuntime.RopeModuleImports
    type RopeChangeSet = FlextInfraProtocolsRopeRuntime.RopeChangeSet
    type RopeMoveGlobal = FlextInfraProtocolsRopeRuntime.RopeMoveGlobal
    type RopeOccurrence = FlextInfraProtocolsRopeRuntime.RopeOccurrence
    type RopeOccurrenceFinder = FlextInfraProtocolsRopeRuntime.RopeOccurrenceFinder
    type RopeOccurrenceFilter = Callable[[RopeOccurrence], bool]

    type RopeTransformFn = Callable[
        [RopeProject, RopeResource],
        tuple[str, Sequence[str]],
    ]
    type RopeMatchFilter = Callable[
        [RopePyModule, FlextInfraProtocolsRopeRuntime.RopeContractMatch],
        bool,
    ]


__all__: list[str] = ["FlextInfraTypesRope"]
