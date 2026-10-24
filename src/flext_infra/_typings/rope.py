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
        """libcst node classes, aliased once for annotations and isinstance."""

        AnnAssign = libcst.AnnAssign
        Annotation = libcst.Annotation
        Arg = libcst.Arg
        AsName = libcst.AsName
        Assign = libcst.Assign
        AssignTarget = libcst.AssignTarget
        Attribute = libcst.Attribute
        AugAssign = libcst.AugAssign
        BaseAssignTargetExpression = libcst.BaseAssignTargetExpression
        BaseCompoundStatement = libcst.BaseCompoundStatement
        BaseExpression = libcst.BaseExpression
        BaseSmallStatement = libcst.BaseSmallStatement
        BaseStatement = libcst.BaseStatement
        CSTNode = libcst.CSTNode
        Call = libcst.Call
        ClassDef = libcst.ClassDef
        Comma = libcst.Comma
        ConcatenatedString = libcst.ConcatenatedString
        Del = libcst.Del
        DictComp = libcst.DictComp
        EmptyLine = libcst.EmptyLine
        FlattenSentinel = libcst.FlattenSentinel
        FunctionDef = libcst.FunctionDef
        GeneratorExp = libcst.GeneratorExp
        If = libcst.If
        Import = libcst.Import
        ImportAlias = libcst.ImportAlias
        ImportFrom = libcst.ImportFrom
        ImportStar = libcst.ImportStar
        IndentedBlock = libcst.IndentedBlock
        Index = libcst.Index
        Lambda = libcst.Lambda
        List = libcst.List
        ListComp = libcst.ListComp
        Module = libcst.Module
        Name = libcst.Name
        ParamSpec = libcst.ParamSpec
        Pass = libcst.Pass
        RemovalSentinel = libcst.RemovalSentinel
        SetComp = libcst.SetComp
        SimpleStatementLine = libcst.SimpleStatementLine
        SimpleString = libcst.SimpleString
        Subscript = libcst.Subscript
        Tuple = libcst.Tuple
        TypeAlias = libcst.TypeAlias
        TypeVar = libcst.TypeVar
        TypeVarTuple = libcst.TypeVarTuple

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
