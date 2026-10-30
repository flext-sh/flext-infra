"""Pure lexical binding discovery shared across analysis and migration owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast


class FlextInfraUtilitiesRopeAstBindings:
    """Enumerate language bindings without guessing their runtime values."""

    @staticmethod
    def bound_identifiers(node: ast.AST) -> tuple[str, ...]:
        """Include match, exception, import, type-parameter and scope targets.

        Returns:
            The resulting ``tuple[str, ...],``.

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
            case _:
                return FlextInfraUtilitiesRopeAstBindings._bound_scope_identifiers(
                    node,
                )

    @staticmethod
    def _bound_scope_identifiers(node: ast.AST) -> tuple[str, ...]:
        """Return the module, import, and scope target names of one node.

        Returns:
            The resulting ``tuple[str, ...],``.

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


__all__: list[str] = ["FlextInfraUtilitiesRopeAstBindings"]
