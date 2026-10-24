"""Rope-specific type aliases for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from ast import ClassDef, Import, ImportFrom
from collections.abc import Callable
from pathlib import Path

import libcst
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

from flext_infra._protocols import FlextInfraProtocolsRopeRuntime
from flext_infra._typings import FlextInfraTypesRopeNative


class FlextInfraTypesRope(FlextInfraTypesRopeNative):
    """Rope type aliases — accessed via t.Infra.*."""

    class Cst:
        """libcst node classes for annotation positions; runtime classes live on c."""

        type AnnAssign = libcst.AnnAssign
        type Annotation = libcst.Annotation
        type Arg = libcst.Arg
        type AsName = libcst.AsName
        type Assign = libcst.Assign
        type AssignTarget = libcst.AssignTarget
        type Attribute = libcst.Attribute
        type AugAssign = libcst.AugAssign
        type BaseAssignTargetExpression = libcst.BaseAssignTargetExpression
        type BaseCompoundStatement = libcst.BaseCompoundStatement
        type BaseExpression = libcst.BaseExpression
        type BaseSmallStatement = libcst.BaseSmallStatement
        type BaseStatement = libcst.BaseStatement
        type CSTNode = libcst.CSTNode
        type Call = libcst.Call
        type ClassDef = libcst.ClassDef
        type Comma = libcst.Comma
        type ConcatenatedString = libcst.ConcatenatedString
        type Del = libcst.Del
        type DictComp = libcst.DictComp
        type EmptyLine = libcst.EmptyLine
        type FlattenSentinel[NodeT: libcst.CSTNode] = libcst.FlattenSentinel[NodeT]
        type FunctionDef = libcst.FunctionDef
        type GeneratorExp = libcst.GeneratorExp
        type If = libcst.If
        type Import = libcst.Import
        type ImportAlias = libcst.ImportAlias
        type ImportFrom = libcst.ImportFrom
        type ImportStar = libcst.ImportStar
        type IndentedBlock = libcst.IndentedBlock
        type Index = libcst.Index
        type Lambda = libcst.Lambda
        type List = libcst.List
        type ListComp = libcst.ListComp
        type Module = libcst.Module
        type Name = libcst.Name
        type ParamSpec = libcst.ParamSpec
        type Pass = libcst.Pass
        type RemovalSentinel = libcst.RemovalSentinel
        type SetComp = libcst.SetComp
        type SimpleStatementLine = libcst.SimpleStatementLine
        type SimpleString = libcst.SimpleString
        type Subscript = libcst.Subscript
        type Tuple = libcst.Tuple
        type TypeAlias = libcst.TypeAlias
        type TypeVar = libcst.TypeVar
        type TypeVarTuple = libcst.TypeVarTuple

    type PythonImportNode = Import | ImportFrom
    type RopeSourcePath = Path
    type RopeImplementationPaths = frozenset[RopeSourcePath]
    type RopeMutablePaths = set[RopeSourcePath]
    type RopeCallableSignature = tuple[
        t.StrSequence,
        t.StrSequence,
        str | None,
        t.StrSequence,
        str | None,
        t.StrSequence,
        t.SequenceOf[str | None],
        bool,
    ]
    type PythonClassNode = ClassDef
    type CstArgument = Arg
    type CstStatement = BaseStatement
    type CstImportAlias = ImportAlias
    type CstModule = Module
    type CstClass = CstClassDef
    type CstImport = CstImportFrom
    type CstMetadata = MetadataWrapper

    type RopeProject = FlextInfraProtocolsRopeRuntime.RopeProject
    type RopeResource = FlextInfraProtocolsRopeRuntime.RopeResource
    type RopeImportLookup = t.MutableMappingKV[
        t.Triple[str, str, int], RopeResource | None
    ]
    type CodemodImportWalkNode = (
        t.Pair[Path, t.VariadicTuple[t.Pair[str, RopeResource]]] | None
    )
    type CodemodImportWalkMemo = t.Pair[
        RopeImportLookup, t.MutableMappingKV[str, CodemodImportWalkNode]
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
    type RopeChangeComputer = FlextInfraProtocolsRopeRuntime.RopeChangeComputer
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
