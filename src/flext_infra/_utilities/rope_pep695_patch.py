"""Local rope patch adding PEP 695 type-parameter syntax awareness.

Rope 1.14 and its master branch do not implement handlers for the AST nodes
introduced by PEP 695 (``ast.TypeAlias``, ``ast.TypeVar``, ``ast.ParamSpec``,
``ast.TypeVarTuple``) nor the ``type_params`` attribute on ``FunctionDef`` /
``AsyncFunctionDef`` / ``ClassDef``. Modules that use this syntax trigger
``MismatchedTokenError`` during rope analysis and abort census runs.

This module monkey-patches ``rope.refactor.patchedast._PatchingASTWalker``
once at import time to add the missing handlers. The patch is idempotent:
subsequent imports are a no-op. Semantics mirror what rope would do if it
knew about these nodes:

- ``type Name[T] = Value`` → ``["type", name, "[", type_params, "]", "=", value]``
- ``def f[T](...)`` / ``class C[T](...)`` → ``type_params`` list is rendered
  inside ``[...]`` between the name and the opening parenthesis.
- ``TypeVar``, ``ParamSpec``, ``TypeVarTuple`` emit their name (with the
  ``**`` / ``*`` prefix for ParamSpec / TypeVarTuple) plus an optional
  ``bound``.
"""
# pyright: reportPrivateUsage=none

from __future__ import annotations

import ast
from collections.abc import Sequence
from typing import ClassVar, Protocol

from rope.refactor import patchedast


class _PatchingASTWalkerProtocol(Protocol):
    """Structural contract for rope's internal AST walker used in monkey-patches."""

    def _handle(self, node: ast.AST, children: list[object]) -> None: ...

    def _child_nodes(
        self, nodes: Sequence[ast.AST], separator: str
    ) -> list[object]: ...


class FlextInfraUtilitiesRopePep695Patch:
    """Idempotent monkey-patch applying PEP 695 support to rope's AST walker."""

    _applied: ClassVar[bool] = False

    @classmethod
    def apply(cls) -> None:
        """Install PEP 695 handlers on rope's ``_PatchingASTWalker`` once."""
        if cls._applied:
            return
        walker = getattr(patchedast, "_PatchingASTWalker")
        original_function_def = getattr(walker, "_handle_function_def_node")
        original_class_def = getattr(walker, "_ClassDef")

        def _type_params_children(node: ast.AST) -> list[object]:
            type_params = getattr(node, "type_params", None) or ()
            if not type_params:
                return []
            children: list[object] = ["["]
            for index, tp in enumerate(type_params):
                if index > 0:
                    children.append(",")
                children.append(tp)
            children.append("]")
            return children

        def _patched_function_def(
            self: _PatchingASTWalkerProtocol,
            node: ast.FunctionDef | ast.AsyncFunctionDef,
            *,
            is_async: bool,
        ) -> None:
            if not getattr(node, "type_params", None):
                original_function_def(self, node, is_async=is_async)
                return
            children: list[object] = []
            for decorator in node.decorator_list:
                children.extend(("@", decorator))
            children.extend(["async", "def"] if is_async else ["def"])
            children.append(node.name)
            children.extend(_type_params_children(node))
            children.extend(["(", node.args, ")"])
            children.append(":")
            children.extend(node.body)
            self._handle(node, children)

        def _patched_class_def(
            self: _PatchingASTWalkerProtocol,
            node: ast.ClassDef,
        ) -> None:
            if not getattr(node, "type_params", None):
                original_class_def(self, node)
                return
            children: list[object] = []
            for decorator in node.decorator_list:
                children.extend(("@", decorator))
            children.extend(["class", node.name])
            children.extend(_type_params_children(node))
            if node.bases:
                children.append("(")
                children.extend(self._child_nodes(node.bases, ","))
                children.append(")")
            children.append(":")
            children.extend(node.body)
            self._handle(node, children)

        def _type_alias(
            self: _PatchingASTWalkerProtocol,
            node: ast.TypeAlias,
        ) -> None:
            children: list[object] = ["type", node.name]
            children.extend(_type_params_children(node))
            children.extend(["=", node.value])
            self._handle(node, children)

        def _type_var(
            self: _PatchingASTWalkerProtocol,
            node: ast.TypeVar,
        ) -> None:
            children: list[object] = [node.name]
            if getattr(node, "bound", None) is not None:
                children.extend([":", node.bound])
            self._handle(node, children)

        def _param_spec(
            self: _PatchingASTWalkerProtocol,
            node: ast.ParamSpec,
        ) -> None:
            self._handle(node, ["**", node.name])

        def _type_var_tuple(
            self: _PatchingASTWalkerProtocol,
            node: ast.TypeVarTuple,
        ) -> None:
            self._handle(node, ["*", node.name])

        setattr(walker, "_handle_function_def_node", _patched_function_def)
        setattr(walker, "_ClassDef", _patched_class_def)
        setattr(walker, "_TypeAlias", _type_alias)
        setattr(walker, "_TypeVar", _type_var)
        setattr(walker, "_ParamSpec", _param_spec)
        setattr(walker, "_TypeVarTuple", _type_var_tuple)
        cls._applied = True


FlextInfraUtilitiesRopePep695Patch.apply()


__all__: list[str] = ["FlextInfraUtilitiesRopePep695Patch"]
