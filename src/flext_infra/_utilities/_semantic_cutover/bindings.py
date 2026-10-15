"""Shared lexical binding discovery for conservative semantic migrations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast

from flext_infra import t


class FlextInfraUtilitiesSemanticCutoverBindings:
    """Enumerate language bindings without guessing their runtime values."""

    @staticmethod
    def bound_value(
        node: ast.AST,
        parents: t.MappingKV[ast.AST, ast.AST],
    ) -> t.Pair[ast.expr | None, bool]:
        """Elect a binding's value; only ordinary aliases propagate member paths."""
        current: ast.AST | None = node
        while current is not None:
            match current:
                case ast.Assign(value=value) | ast.AnnAssign(value=value) | ast.NamedExpr(value=value):
                    return value, isinstance(value, ast.Name | ast.Attribute)
                case ast.AugAssign(value=value):
                    return value, False
                case ast.ExceptHandler(type=value):
                    return value, False
                case ast.For(iter=value) | ast.AsyncFor(iter=value) | ast.comprehension(iter=value):
                    return value, False
                case ast.withitem(context_expr=value):
                    return value, False
                case ast.Match(subject=value):
                    return value, False
                case ast.arg(annotation=value):
                    return value, False
                case ast.TypeAlias(value=value):
                    return value, isinstance(value, ast.Name | ast.Attribute)
                case ast.ClassDef() | ast.FunctionDef() | ast.AsyncFunctionDef() | ast.Module():
                    return None, False
            current = parents.get(current)
        return None, False

    @staticmethod
    def bound_identifiers(node: ast.AST) -> t.VariadicTuple[str]:
        """Include match, exception, import, type-parameter and scope targets.

        Returns:
            The resulting ``t.VariadicTuple[str]``.

        """
        match node:
            case ast.Name(id=name, ctx=ast.Store() | ast.Del()):
                return (name,)
            case (
                ast.arg(arg=name)
                | ast.FunctionDef(name=name)
                | ast.AsyncFunctionDef(name=name)
                | ast.ClassDef(name=name)
            ):
                return (name,)
            case (
                ast.ExceptHandler(name=str() as name)
                | ast.MatchAs(name=str() as name)
                | ast.MatchStar(name=str() as name)
                | ast.MatchMapping(rest=str() as name)
            ):
                return (name,)
            case (
                ast.TypeVar(name=name)
                | ast.ParamSpec(name=name)
                | ast.TypeVarTuple(name=name)
            ):
                return (name,)
        return FlextInfraUtilitiesSemanticCutoverBindings._bound_scope_identifiers(node)

    @staticmethod
    def _bound_scope_identifiers(node: ast.AST) -> t.VariadicTuple[str]:
        """Return the module, import, and scope target names of one node.

        Returns:
            The resulting ``t.VariadicTuple[str]``.

        """
        match node:
            case ast.Global(names=names) | ast.Nonlocal(names=names):
                return tuple(names)
            case ast.Import(names=aliases):
                return tuple(
                    alias.asname or alias.name.split(".")[0] for alias in aliases
                )
            case ast.ImportFrom(names=aliases):
                return tuple(alias.asname or alias.name for alias in aliases)
            case _:
                return ()


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverBindings"]
