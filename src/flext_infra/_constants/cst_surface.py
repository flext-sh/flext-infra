"""libcst runtime classes, declared once for the whole package.

``c.Infra.Cst`` is the single owner of the libcst classes used as
``isinstance``/``issubclass`` operands. It is the only constants module that
imports libcst, so the generated initializer defers it: reading ``c`` loads
no libcst, and the first access to one of these members loads this module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import libcst

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCst:
    """libcst runtime classes published under ``c.Infra``."""

    class Cst:
        """libcst runtime classes for isinstance operands; annotations read t."""

        AnnAssign = libcst.AnnAssign
        Annotation = libcst.Annotation
        Arg = libcst.Arg
        AsName = libcst.AsName
        Assign = libcst.Assign
        AssignTarget = libcst.AssignTarget
        Attribute = libcst.Attribute
        AugAssign = libcst.AugAssign
        BaseCompoundStatement = libcst.BaseCompoundStatement
        BaseExpression = libcst.BaseExpression
        BaseStatement = libcst.BaseStatement
        Call = libcst.Call
        ClassDef = libcst.ClassDef
        Comma = libcst.Comma
        ConcatenatedString = libcst.ConcatenatedString
        Del = libcst.Del
        DictComp = libcst.DictComp
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
        SetComp = libcst.SetComp
        SimpleStatementLine = libcst.SimpleStatementLine
        SimpleString = libcst.SimpleString
        Tuple = libcst.Tuple
        TypeAlias = libcst.TypeAlias
        TypeVar = libcst.TypeVar
        TypeVarTuple = libcst.TypeVarTuple

    CST_IMPORT_TYPES: ClassVar[
        tuple[type[t.Infra.Cst.Import], type[t.Infra.Cst.ImportFrom]]
    ] = (
        libcst.Import,
        libcst.ImportFrom,
    )
    "libcst import statements, absolute and from-import."
    CST_DEFINITION_TYPES: ClassVar[
        tuple[type[t.Infra.Cst.ClassDef], type[t.Infra.Cst.FunctionDef]]
    ] = (libcst.ClassDef, libcst.FunctionDef)
    "libcst class and function definition nodes."


__all__: list[str] = ["FlextInfraConstantsCst"]
