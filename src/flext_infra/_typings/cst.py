"""CST type aliases — accessed via t.Infra.Cst.*."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import libcst as cst


class FlextInfraTypesCst:
    """Type aliases for libcst-based analysis — accessed via t.Infra.Cst.*."""

    class Cst:
        """CST-specific type aliases."""

        type Module = cst.Module
        """Parsed libcst module."""

        type Node = cst.CSTNode
        """Any libcst node."""

        type Expression = cst.BaseExpression
        """Any libcst expression node."""

        type Statement = cst.BaseStatement
        """Any libcst statement node."""

        type ClassDef = cst.ClassDef
        """libcst class definition node."""

        type FunctionDef = cst.FunctionDef
        """libcst function definition node."""

        type ImportFrom = cst.ImportFrom
        """libcst from-import node."""

        type Visitor = cst.CSTVisitor
        """libcst visitor base."""

        type Transformer = cst.CSTTransformer
        """libcst transformer base."""

        type BaseNames = Sequence[str]
        """Sequence of base class name strings extracted from a ClassDef."""

        type DecoratorNames = Sequence[str]
        """Sequence of decorator name strings extracted from a definition."""

        type ImportMap = Mapping[str, str]
        """Mapping of local name → fully-qualified imported name."""


__all__ = ["FlextInfraTypesCst"]
