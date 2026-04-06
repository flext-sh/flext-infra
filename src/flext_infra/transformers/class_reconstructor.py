"""Class reconstructor transformer for method ordering — rope-based."""

from __future__ import annotations

import ast
from collections.abc import MutableSequence, Sequence
from operator import itemgetter
from typing import TypeGuard, override

from pydantic import TypeAdapter, ValidationError

from flext_infra import FlextInfraRopeTransformer, c, m, t, u


class FlextInfraRefactorClassReconstructor(FlextInfraRopeTransformer):
    """Reorder class methods based on declarative ordering configuration."""

    _description = "class reconstructor"

    def __init__(
        self,
        order_config: Sequence[t.Infra.ContainerDict],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with rule order config and optional change callback."""
        super().__init__(on_change=on_change)
        try:
            self._order_config: Sequence[m.Infra.MethodOrderRule] = TypeAdapter(
                Sequence[m.Infra.MethodOrderRule],
            ).validate_python(order_config)
        except ValidationError:
            self._order_config = list[m.Infra.MethodOrderRule]()

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply method reordering to in-memory source."""
        self.changes.clear()
        if not self._order_config:
            return source, list[str]()
        try:
            module = ast.parse(source)
        except SyntaxError:
            return source, list[str]()
        line_offsets = self._line_offsets(source)
        edits: MutableSequence[tuple[int, int, str]] = []
        for statement in module.body:
            if not isinstance(statement, ast.ClassDef):
                continue
            edits.extend(
                self._class_method_block_edits(
                    source,
                    statement,
                    line_offsets=line_offsets,
                )
            )
        if not edits:
            return source, list(self.changes)
        updated = source
        for start, end, replacement in sorted(
            edits,
            key=itemgetter(0),
            reverse=True,
        ):
            updated = updated[:start] + replacement + updated[end:]
        return updated, list(self.changes)

    def _class_method_block_edits(
        self,
        source: str,
        class_node: ast.ClassDef,
        *,
        line_offsets: Sequence[int],
    ) -> Sequence[tuple[int, int, str]]:
        edits: MutableSequence[tuple[int, int, str]] = []
        body = class_node.body
        index = 0
        while index < len(body):
            statement = body[index]
            if not self._is_method_node(statement):
                index += 1
                continue
            run_start = index
            while index < len(body) and self._is_method_node(body[index]):
                index += 1
            run = [node for node in body[run_start:index] if self._is_method_node(node)]
            if len(run) < c.Infra.MIN_METHODS_FOR_REORDER:
                continue
            edit = self._build_block_edit(
                source,
                class_name=class_node.name,
                method_nodes=run,
                next_sibling=body[index] if index < len(body) else None,
                line_offsets=line_offsets,
            )
            if edit is not None:
                edits.append(edit)
        return edits

    def _build_block_edit(
        self,
        source: str,
        *,
        class_name: str,
        method_nodes: Sequence[ast.FunctionDef | ast.AsyncFunctionDef],
        next_sibling: ast.stmt | None,
        line_offsets: Sequence[int],
    ) -> tuple[int, int, str] | None:
        start = self._node_start_offset(method_nodes[0], line_offsets)
        end = (
            self._node_start_offset(next_sibling, line_offsets)
            if next_sibling is not None
            else self._node_end_offset(method_nodes[-1], line_offsets)
        )
        method_chunks = [
            self._method_chunk(
                source,
                node=method_nodes[index],
                next_node=(
                    method_nodes[index + 1]
                    if index + 1 < len(method_nodes)
                    else next_sibling
                ),
                line_offsets=line_offsets,
            )
            for index in range(len(method_nodes))
        ]
        sorted_chunks = sorted(
            method_chunks,
            key=lambda item: u.Infra.build_method_sort_key(
                item[0],
                self._order_config,
            ),
        )
        original_names = [item[0].name for item in method_chunks]
        sorted_names = [item[0].name for item in sorted_chunks]
        if original_names == sorted_names:
            return None
        self._record_change(
            f"Reordered {len(method_chunks)} methods in class {class_name}",
        )
        return start, end, "".join(item[1] for item in sorted_chunks)

    def _method_chunk(
        self,
        source: str,
        *,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        next_node: ast.stmt | None,
        line_offsets: Sequence[int],
    ) -> tuple[m.Infra.MethodInfo, str]:
        start = self._node_start_offset(node, line_offsets)
        end = (
            self._node_start_offset(next_node, line_offsets)
            if next_node is not None
            else self._node_end_offset(node, line_offsets)
        )
        decorators = self._decorator_names(node)
        method_info = m.Infra.MethodInfo(
            name=node.name,
            category=u.Infra.categorize_method(node.name, decorators),
            node=node,
            decorators=decorators,
        )
        return method_info, source[start:end]

    @staticmethod
    def _decorator_names(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Sequence[str]:
        return [
            name
            for decorator in node.decorator_list
            if (name := FlextInfraRefactorClassReconstructor._decorator_name(decorator))
        ]

    @staticmethod
    def _decorator_name(decorator: ast.expr) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        if isinstance(decorator, ast.Call):
            return FlextInfraRefactorClassReconstructor._decorator_name(decorator.func)
        return ""

    @staticmethod
    def _line_offsets(source: str) -> Sequence[int]:
        offsets = [0]
        for line in source.splitlines(keepends=True):
            offsets.append(offsets[-1] + len(line))
        return offsets

    @staticmethod
    def _node_start_offset(node: ast.stmt, line_offsets: Sequence[int]) -> int:
        start_line = min(
            (
                decorator.lineno
                for decorator in getattr(node, "decorator_list", [])
                if hasattr(decorator, "lineno")
            ),
            default=node.lineno,
        )
        start_col = min(
            (
                decorator.col_offset
                for decorator in getattr(node, "decorator_list", [])
                if hasattr(decorator, "col_offset") and decorator.lineno == start_line
            ),
            default=node.col_offset,
        )
        return line_offsets[start_line - 1] + start_col

    @staticmethod
    def _node_end_offset(node: ast.stmt, line_offsets: Sequence[int]) -> int:
        end_line = node.end_lineno or node.lineno
        end_col = node.end_col_offset or 0
        return line_offsets[end_line - 1] + end_col

    @staticmethod
    def _is_method_node(
        node: ast.stmt,
    ) -> TypeGuard[ast.FunctionDef | ast.AsyncFunctionDef]:
        return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


__all__ = ["FlextInfraRefactorClassReconstructor"]
