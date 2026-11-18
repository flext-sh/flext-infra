"""libcst type aliases, declared once for the whole package.

``t.Infra.Cst`` names the libcst node classes in annotation positions; the
runtime classes live on ``c.Infra.Cst``. This is the only typings module that
imports libcst, so the generated initializer defers it: reading ``t`` loads
no libcst, and the first access to one of these aliases loads this module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import libcst
import libcst.matchers
from libcst import (
    Arg,
    BaseStatement,
    ClassDef as CstClassDef,
    ImportAlias,
    ImportFrom as CstImportFrom,
    Module,
)
from libcst.metadata import MetadataWrapper


class FlextInfraTypesCst:
    """libcst type aliases published under ``t.Infra``."""

    class Cst:
        """libcst node classes for annotation positions; runtime classes live on c."""

        type AnnAssign = libcst.AnnAssign
        type Annotation = libcst.Annotation
        type Arg = libcst.Arg
        type AsName = libcst.AsName
        type Assign = libcst.Assign
        type AssignTarget = libcst.AssignTarget
        type Attribute = libcst.Attribute
        type AttributeMatcher = libcst.matchers.Attribute
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

    type CstArgument = Arg
    type CstStatement = BaseStatement
    type CstImportAlias = ImportAlias
    type CstModule = Module
    type CstClass = CstClassDef
    type CstImport = CstImportFrom
    type CstMetadata = MetadataWrapper


__all__: list[str] = ["FlextInfraTypesCst"]
