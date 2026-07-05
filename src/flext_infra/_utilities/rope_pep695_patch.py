"""Local rope patch adding Python 3.13 AST awareness to Rope.

Rope 1.14 and its master branch do not implement handlers for part of the AST
surface used by Python 3.13 in this workspace. In practice that currently
includes the PEP 695 nodes (``ast.TypeAlias``, ``ast.TypeVar``,
``ast.ParamSpec``, ``ast.TypeVarTuple``) plus several structural pattern
matching nodes (``ast.MatchSequence``, ``ast.MatchSingleton``,
``ast.MatchStar``, ``ast.MatchOr``). Modules that use this syntax trigger
``MismatchedTokenError`` or noisy ``Unknown node type`` warnings during rope
analysis and abort census/codegen runs.

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
- Pattern-matching nodes mirror the source token stream closely enough for
    Rope's patched AST region walker to keep working without upstream support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    import ast

    from flext_infra import p


class FlextInfraUtilitiesRopePep695Patch:
    """Idempotent monkey-patch applying PEP 695 support to rope's AST walker.

    The structural contract for rope's internal ``_PatchingASTWalker`` lives
    in ``p.Infra.PatchingASTWalker`` (canonical protocol namespace).
    """

    _applied: ClassVar[bool] = False

    @classmethod
    def apply(cls) -> None:
        """Install PEP 695 handlers on rope's ``_PatchingASTWalker`` once."""
        if cls._applied:
            return
        walker = FlextInfraUtilitiesRopeRuntime.patched_ast_walker()
        original_function_def: Callable[..., None] = getattr(
            walker,
            "_handle_function_def_node",
        )
        original_class_def: Callable[..., None] = getattr(walker, "_ClassDef")

        def _type_params_children(node: ast.AST) -> list[p.AttributeProbe]:
            """Type params children."""
            type_params = getattr(node, "type_params", None) or ()
            if not type_params:
                return []
            children: list[p.AttributeProbe] = ["["]
            for index, tp in enumerate(type_params):
                if index > 0:
                    children.append(",")
                children.append(tp)
            children.append("]")
            return children

        def _pattern_opening_token(
            self: p.Infra.PatchingASTWalker,
            node: ast.AST,
        ) -> str:
            """Pattern opening token."""
            lineno = getattr(node, "lineno", None)
            col_offset = getattr(node, "col_offset", None)
            if not isinstance(lineno, int) or not isinstance(col_offset, int):
                return ""
            line_start = self.lines.get_line_start(lineno)
            source_text: str = self.source.source
            start = line_start + col_offset
            source_fragment: str = source_text[start : start + 1]
            return source_fragment

        def _patched_function_def(
            self: p.Infra.PatchingASTWalker,
            node: ast.FunctionDef | ast.AsyncFunctionDef,
            *,
            is_async: bool,
        ) -> None:
            """Patched function def."""
            if not getattr(node, "type_params", None):
                original_function_def(self, node, is_async=is_async)
                return
            children: list[p.AttributeProbe] = []
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
            self: p.Infra.PatchingASTWalker,
            node: ast.ClassDef,
        ) -> None:
            """Patched class def."""
            if not getattr(node, "type_params", None):
                original_class_def(self, node)
                return
            children: list[p.AttributeProbe] = []
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
            self: p.Infra.PatchingASTWalker,
            node: ast.TypeAlias,
        ) -> None:
            """Type alias."""
            children: list[p.AttributeProbe] = ["type", node.name]
            children.extend(_type_params_children(node))
            children.extend(["=", node.value])
            self._handle(node, children)

        def _type_var(
            self: p.Infra.PatchingASTWalker,
            node: ast.TypeVar,
        ) -> None:
            """Type var."""
            children: list[p.AttributeProbe] = [node.name]
            if getattr(node, "bound", None) is not None:
                children.extend([":", node.bound])
            self._handle(node, children)

        def _param_spec(
            self: p.Infra.PatchingASTWalker,
            node: ast.ParamSpec,
        ) -> None:
            """Param spec."""
            self._handle(node, ["**", node.name])

        def _type_var_tuple(
            self: p.Infra.PatchingASTWalker,
            node: ast.TypeVarTuple,
        ) -> None:
            """Type var tuple."""
            self._handle(node, ["*", node.name])

        def _match_sequence(
            self: p.Infra.PatchingASTWalker,
            node: ast.MatchSequence,
        ) -> None:
            """Match sequence."""
            children = self._child_nodes(node.patterns, ",")
            opening = _pattern_opening_token(self, node)
            if opening == "[":
                self._handle(node, ["[", *children, "]"])
                return
            if opening == "(" and not node.patterns:
                self._handle(node, [self.empty_tuple])
                return
            self._handle(node, children, eat_parens=opening == "(")

        def _match_singleton(
            self: p.Infra.PatchingASTWalker,
            node: ast.MatchSingleton,
        ) -> None:
            """Match singleton."""
            self._handle(node, [str(node.value)])

        def _match_star(
            self: p.Infra.PatchingASTWalker,
            node: ast.MatchStar,
        ) -> None:
            """Match star."""
            self._handle(node, ["*", node.name or "_"])

        def _match_or(
            self: p.Infra.PatchingASTWalker,
            node: ast.MatchOr,
        ) -> None:
            """Match or."""
            self._handle(node, self._child_nodes(node.patterns, "|"))

        setattr(walker, "_handle_function_def_node", _patched_function_def)
        setattr(walker, "_ClassDef", _patched_class_def)
        setattr(walker, "_TypeAlias", _type_alias)
        setattr(walker, "_TypeVar", _type_var)
        setattr(walker, "_ParamSpec", _param_spec)
        setattr(walker, "_TypeVarTuple", _type_var_tuple)
        setattr(walker, "_MatchSequence", _match_sequence)
        setattr(walker, "_MatchSingleton", _match_singleton)
        setattr(walker, "_MatchStar", _match_star)
        setattr(walker, "_MatchOr", _match_or)
        cls._applied = True


FlextInfraUtilitiesRopePep695Patch.apply()


__all__: list[str] = ["FlextInfraUtilitiesRopePep695Patch"]
