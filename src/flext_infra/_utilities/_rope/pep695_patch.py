"""Local rope patch adding Python 3.13 AST awareness to Rope.

Rope 1.14 and its master branch do not implement handlers for part of the
Python 3.13 parser surface used in this workspace. In practice that currently
includes PEP 695 aliases/type parameters plus several structural pattern
matching nodes. Modules that use this syntax trigger
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
- Occurrence search (``_TextualFinder._re_search``) walks tokenizer NAME
    tokens: rope's f-string regex stops at a PEP 701 reused quote and hands
    its parser a truncated expression.

NOTE (multi-agent, flext-f8vk / kimi): this module lives in the ``_rope``
subpackage so the root ``pyproject.toml`` can scope
``reportPrivateUsage = "none"`` to this intentional monkeypatch surface —
rope 1.14 exposes no public API to register patched-AST handlers, and the
FLEXT typing law forbids the getattr-dispatch/Any workaround.
"""

from __future__ import annotations

import ast
import io
import tokenize
from collections.abc import Callable, Iterator
from operator import itemgetter
from typing import ClassVar, cast

from flext_infra import p

from ..rope_runtime import FlextInfraUtilitiesRopeRuntime


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
        # Vendor boundary: rope exposes NO public API to register a walker
        # handler, so these private slots are the library's real interface.
        # The access is written LITERALLY, never routed through getattr with a
        # name constant: hiding it from the analyzer would be a disguised
        # suppression. pep695_ast_walker narrows the walker to the handler
        # contract and raises when rope changes its internals, so the typing is
        # resolved and only the ruff rule remains exempted for this directory
        # (operator authorization 2026-08-08).
        walker = FlextInfraUtilitiesRopeRuntime.pep695_ast_walker()
        original_function_def: Callable[..., None] = walker._handle_function_def_node  # pyright: ignore[reportPrivateUsage]
        original_class_def: Callable[..., None] = walker._ClassDef  # pyright: ignore[reportPrivateUsage]

        def _source_offset(
            self: p.Infra.PatchingASTWalker, lineno: int, byte_offset: int
        ) -> int:
            """Translate the parser's UTF-8 column into Rope's character offset."""
            line_start = self.lines.get_line_start(lineno)
            line = self.source.source[line_start:].partition("\n")[0]
            column = len(line.encode("utf-8")[:byte_offset].decode("utf-8"))
            return line_start + column

        def _joined_str(self: p.Infra.PatchingASTWalker, node: ast.JoinedStr) -> None:
            """Patch PEP 701 f-strings from parser coordinates, not token guesses."""
            # Rope's consume_string tokenizes quotes: a PEP 701 expression that
            # reuses the outer quote (f"{d["k"]}") ends its span at the inner
            # quote. The parser's own node span is the literal's real extent.
            start = _source_offset(self, node.lineno, node.col_offset)
            end_lineno = node.end_lineno
            end_col_offset = node.end_col_offset
            if end_lineno is None or end_col_offset is None:
                msg = "PEP 701 joined string carries no parser end position"
                raise ValueError(msg)
            end = _source_offset(self, end_lineno, end_col_offset)

            def joined_expressions(parent: ast.JoinedStr) -> list[ast.AST]:
                expressions: list[ast.AST] = []
                for value in parent.values:
                    if not isinstance(value, ast.FormattedValue):
                        continue
                    expressions.append(value.value)
                    if isinstance(value.format_spec, ast.JoinedStr):
                        expressions.extend(joined_expressions(value.format_spec))
                return expressions

            def positioned_children(parent: ast.AST) -> list[ast.AST]:
                if isinstance(parent, ast.JoinedStr):
                    return joined_expressions(parent)
                children: list[ast.AST] = []
                for child in ast.iter_child_nodes(parent):
                    if isinstance(child, p.Infra.PatchingASTWalker.SourceSpanningNode):
                        children.append(child)
                    else:
                        children.extend(positioned_children(child))
                return children

            def patch_node(
                current: ast.AST, current_start: int, current_end: int
            ) -> None:
                patchable = cast("p.Infra.PatchingASTWalker.PatchableNode", current)
                patchable.region = (current_start, current_end)
                if not self.children:
                    return
                children: list[tuple[int, int, ast.AST]] = []
                for child in positioned_children(current):
                    if not isinstance(
                        child, p.Infra.PatchingASTWalker.SourceSpanningNode
                    ):
                        continue
                    descendant = cast("p.Infra.PatchingASTWalker.PatchableNode", child)
                    child_start = _source_offset(
                        self, descendant.lineno, descendant.col_offset
                    )
                    child_end = _source_offset(
                        self, descendant.end_lineno, descendant.end_col_offset
                    )
                    if not current_start <= child_start <= child_end <= current_end:
                        msg = "PEP 701 AST descendant escapes its source span"
                        raise ValueError(msg)
                    children.append((child_start, child_end, child))
                children.sort(key=itemgetter(0, 1))
                cursor = current_start
                interleaved: list[p.AttributeProbe] = []
                for child_start, child_end, descendant in children:
                    if child_start < cursor:
                        msg = "PEP 701 AST descendant spans overlap"
                        raise ValueError(msg)
                    interleaved.append(self.source.source[cursor:child_start])
                    patch_node(descendant, child_start, child_end)
                    interleaved.append(descendant)
                    cursor = child_end
                interleaved.append(self.source.source[cursor:current_end])
                patchable.sorted_children = interleaved

            def assign_regions(parent: ast.AST) -> None:
                """Give Rope every positioned scope node its parser region."""
                for descendant_node in ast.walk(parent):
                    if descendant_node is parent or not isinstance(
                        descendant_node, p.Infra.PatchingASTWalker.SourceSpanningNode
                    ):
                        continue
                    descendant = cast(
                        "p.Infra.PatchingASTWalker.PatchableNode", descendant_node
                    )
                    descendant.region = (
                        _source_offset(self, descendant.lineno, descendant.col_offset),
                        _source_offset(
                            self, descendant.end_lineno, descendant.end_col_offset
                        ),
                    )

            # ``FormattedValue`` and nested ``JoinedStr`` nodes use the outer
            # literal's parser span on Python 3.13.  They are structural
            # containers, not independently writable source slices.  Walking
            # every AST descendant as a writable child therefore invents
            # overlaps and rejects valid PEP 701 strings. Rope still requires
            # ``region`` on structural scope nodes such as ``GeneratorExp``.
            # Assign those semantic regions first, then let ``patch_node``
            # construct writable children only from the real expressions.
            assign_regions(node)
            patch_node(node, start, end)
            self.source.offset = end

        def _type_params_children(
            node: p.Infra.PatchingASTWalker.TypeParameterOwner,
        ) -> list[p.AttributeProbe]:
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
            node: p.Infra.PatchingASTWalker.PositionedNode,
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
            node: p.Infra.PatchingASTWalker.FunctionDefinitionNode,
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
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        def _patched_class_def(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.ClassDefinitionNode,
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
                children.extend(self._child_nodes(node.bases, ","))  # pyright: ignore[reportPrivateUsage]
                children.append(")")
            children.append(":")
            children.extend(node.body)
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        def _type_alias(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.TypeAliasNode,
        ) -> None:
            """Type alias."""
            children: list[p.AttributeProbe] = ["type", node.name]
            children.extend(_type_params_children(node))
            children.extend(["=", node.value])
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        def _type_var(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.TypeVariableNode,
        ) -> None:
            """Type var."""
            children: list[p.AttributeProbe] = [node.name]
            if getattr(node, "bound", None) is not None:
                children.extend([":", node.bound])
            self._handle(node, children)  # pyright: ignore[reportPrivateUsage]

        def _param_spec(
            self: p.Infra.PatchingASTWalker, node: p.Infra.PatchingASTWalker.NamedNode
        ) -> None:
            """Param spec."""
            self._handle(node, ["**", node.name])  # pyright: ignore[reportPrivateUsage]

        def _type_var_tuple(
            self: p.Infra.PatchingASTWalker, node: p.Infra.PatchingASTWalker.NamedNode
        ) -> None:
            """Type var tuple."""
            self._handle(node, ["*", node.name])  # pyright: ignore[reportPrivateUsage]

        def _match_sequence(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.MatchSequenceNode,
        ) -> None:
            """Match sequence."""
            children = self._child_nodes(node.patterns, ",")  # pyright: ignore[reportPrivateUsage]
            opening = _pattern_opening_token(self, node)
            if opening == "[":
                self._handle(node, ["[", *children, "]"])  # pyright: ignore[reportPrivateUsage]
                return
            if opening == "(" and not node.patterns:
                self._handle(node, [self.empty_tuple])  # pyright: ignore[reportPrivateUsage]
                return
            self._handle(node, children, eat_parens=opening == "(")  # pyright: ignore[reportPrivateUsage]

        def _match_singleton(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.MatchSingletonNode,
        ) -> None:
            """Match singleton."""
            self._handle(node, [str(node.value)])  # pyright: ignore[reportPrivateUsage]

        def _match_star(
            self: p.Infra.PatchingASTWalker,
            node: p.Infra.PatchingASTWalker.MatchStarNode,
        ) -> None:
            """Match star."""
            self._handle(node, ["*", node.name or "_"])  # pyright: ignore[reportPrivateUsage]

        def _match_or(
            self: p.Infra.PatchingASTWalker, node: p.Infra.PatchingASTWalker.MatchOrNode
        ) -> None:
            """Match or."""
            self._handle(node, self._child_nodes(node.patterns, "|"))  # pyright: ignore[reportPrivateUsage]

        walker._handle_function_def_node = _patched_function_def  # pyright: ignore[reportPrivateUsage]
        walker._ClassDef = _patched_class_def  # pyright: ignore[reportPrivateUsage]
        walker._JoinedStr = _joined_str  # pyright: ignore[reportPrivateUsage]
        walker._TypeAlias = _type_alias
        walker._TypeVar = _type_var
        walker._ParamSpec = _param_spec
        walker._TypeVarTuple = _type_var_tuple
        walker._MatchSequence = _match_sequence
        walker._MatchSingleton = _match_singleton
        walker._MatchStar = _match_star
        walker._MatchOr = _match_or

        def _token_search(
            self: p.Infra.RopeTextualFinder, source: str
        ) -> Iterator[int]:
            """Yield identifier offsets from the tokenizer, f-strings included.

            Python 3.12+ tokenizes f-string replacement fields as ordinary
            tokens, so every NAME outside strings and comments, PEP 701 nested
            quotes included, is found without re-parsing a truncated capture.
            """
            line_starts = [0]
            for line in source.splitlines(keepends=True):
                line_starts.append(line_starts[-1] + len(line))
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type == tokenize.NAME and token.string == self.name:
                    row, column = token.start
                    yield line_starts[row - 1] + column

        FlextInfraUtilitiesRopeRuntime.textual_finder()._re_search = _token_search  # pyright: ignore[reportPrivateUsage]
        cls._applied = True


__all__: list[str] = ["FlextInfraUtilitiesRopePep695Patch"]
