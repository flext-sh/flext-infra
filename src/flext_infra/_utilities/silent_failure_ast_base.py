"""Shared AST state for silent-failure enforcement."""

from __future__ import annotations

import ast
from typing import ClassVar, NamedTuple

from flext_infra import t


class FlextInfraUtilitiesSilentFailureAstBase(ast.NodeVisitor):
    """Own AST traversal state and structural predicates."""

    class Finding(NamedTuple):
        """One silent-failure occurrence and its optional structural fix."""

        line: int
        column: int
        kind: str
        detail: str
        fix_action: str
        replacement: t.Triple[int, int, str] | None = None

    _SENTINEL_CONSTANTS: ClassVar[frozenset[object]] = frozenset({False, None})
    _BROAD_EXCEPTION_NAMES: ClassVar[frozenset[str]] = frozenset({
        "Exception",
        "BaseException",
    })

    def __init__(self, source: str) -> None:
        self._lines = source.splitlines(keepends=True)
        self._findings: list[FlextInfraUtilitiesSilentFailureAstBase.Finding] = []
        self._import_aliases: dict[str, str] = {}
        self._parents: dict[ast.AST, ast.AST] = {}

    def analyze(self, tree: ast.Module) -> t.VariadicTuple[Finding]:
        """Build the parent map and collect findings from one module."""
        self._parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        self.visit(tree)
        return tuple(self._findings)

    def _enclosing_function(
        self, node: ast.AST
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        current: ast.AST | None = node
        while current is not None:
            if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
                return current
            current = self._parents.get(current)
        return None

    @staticmethod
    def _result_inner_type(
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> str | None:
        returns = function.returns
        if not isinstance(returns, ast.Subscript):
            return None
        value = returns.value
        is_result = (isinstance(value, ast.Name) and value.id in {"r", "Result"}) or (
            isinstance(value, ast.Attribute) and value.attr == "Result"
        )
        return ast.unparse(returns.slice) if is_result else None

    def _line_offsets(self, line_number: int) -> t.Pair[int, int]:
        start = sum(len(self._lines[index]) for index in range(line_number - 1))
        return start, start + len(self._lines[line_number - 1])

    def _indent_of(self, node: ast.Return) -> str:
        line = self._lines[node.lineno - 1]
        return line[: len(line) - len(line.lstrip())]

    def _add(
        self,
        *,
        line: int,
        column: int,
        kind: str,
        detail: str,
        fix_action: str = "manual",
        replacement: t.Triple[int, int, str] | None = None,
    ) -> None:
        self._findings.append(
            self.Finding(
                line=line,
                column=column,
                kind=kind,
                detail=detail,
                fix_action=fix_action,
                replacement=replacement,
            )
        )

    @classmethod
    def _is_sentinel_value(cls, node: ast.expr | None) -> bool:
        if node is None:
            return True
        if isinstance(node, ast.Constant) and node.value in cls._SENTINEL_CONSTANTS:
            return True
        if isinstance(node, ast.List) and not node.elts:
            return True
        return isinstance(node, ast.Dict) and not node.keys

    def _first_sentinel_return(self, body: t.SequenceOf[ast.stmt]) -> ast.Return | None:
        return next(
            (
                child
                for statement in body
                for child in ast.walk(statement)
                if isinstance(child, ast.Return)
                and self._is_sentinel_value(child.value)
            ),
            None,
        )

    @staticmethod
    def _body_has_raise_or_fail(body: t.SequenceOf[ast.stmt]) -> bool:
        return any(
            isinstance(child, ast.Raise)
            or (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "fail"
            )
            for statement in body
            for child in ast.walk(statement)
        )

    def _resolve_call_name(self, node: ast.Call) -> str:
        function = node.func
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            base = self._import_aliases.get(function.value.id, function.value.id)
            return f"{base}.{function.attr}"
        if isinstance(function, ast.Name):
            return self._import_aliases.get(function.id, function.id)
        return ""

    def _expression_name(self, node: ast.expr | None) -> str:
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return self._import_aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = self._import_aliases.get(node.value.id, node.value.id)
            return f"{base}.{node.attr}"
        return ""

    @classmethod
    def _is_unwrap_or_call(cls, node: ast.Call) -> bool:
        function = node.func
        return (
            isinstance(function, ast.Attribute)
            and function.attr == "unwrap_or"
            and bool(node.args)
            and cls._is_sentinel_value(node.args[0])
        )


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesSilentFailureAstBase",)
