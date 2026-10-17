"""Rope-specific type aliases for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from ast import ClassDef, Import, ImportFrom
from collections.abc import Callable

from flext_core import t
from libcst import (
    Arg,
    BaseStatement,
    ClassDef as CstClassDef,
    ImportAlias,
    ImportFrom as CstImportFrom,
    Module,
)
from libcst.metadata import MetadataWrapper
from rope.base.builtins import BuiltinModule
from rope.base.pycore import PyCore
from rope.base.pyobjectsdef import PyModule, PyPackage
from rope.base.resources import Resource
from rope.refactor.restructure import _ChangeComputer as ChangeComputer
from rope.refactor.similarfinder import ExpressionMatch, StatementMatch

from flext_infra._protocols import FlextInfraProtocolsRopeRuntime


class FlextInfraTypesRope:
    """Rope type aliases — accessed via t.Infra.*."""

    type PythonImportNode = Import | ImportFrom
    type PythonClassNode = ClassDef
    type CstArgument = Arg
    type CstStatement = BaseStatement
    type CstImportAlias = ImportAlias
    type CstModule = Module
    type CstClass = CstClassDef
    type CstImport = CstImportFrom
    type CstMetadata = MetadataWrapper

    type RopeProject = FlextInfraProtocolsRopeRuntime.RopeProject
    type RopeNativeCore = PyCore
    type RopeNativeSourceModule = PyModule
    type RopeNativeParsedModule = PyModule | PyPackage
    type RopeNativeSemanticModule = BuiltinModule | RopeNativeParsedModule
    type RopeNativeResource = Resource
    type RopeNativeMatch = ExpressionMatch | StatementMatch
    type RopeResource = FlextInfraProtocolsRopeRuntime.RopeResource
    type RopeImportLookup = t.MutableMappingKV[
        t.Triple[str, str, int], RopeResource | None
    ]
    type RopeFile = FlextInfraProtocolsRopeRuntime.RopeFile
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
    type RopeChangeComputer = ChangeComputer
    type RopeMoveGlobal = FlextInfraProtocolsRopeRuntime.RopeMoveGlobal
    type RopeOccurrence = FlextInfraProtocolsRopeRuntime.RopeOccurrence
    type RopeOccurrenceFinder = FlextInfraProtocolsRopeRuntime.RopeOccurrenceFinder

    type RopeTransformFn = Callable[
        [RopeProject, RopeResource],
        t.Pair[str, t.StrSequence],
    ]
    type RopeMatchFilter = Callable[
        [RopePyModule, FlextInfraProtocolsRopeRuntime.RopeContractMatch],
        bool,
    ]


__all__: list[str] = ["FlextInfraTypesRope"]
