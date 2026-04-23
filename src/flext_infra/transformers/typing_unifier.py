"""Unify inline typing unions and TypeAlias declarations to canonical forms via rope."""

from __future__ import annotations

import ast
import copy
import re
from collections.abc import (
    Mapping,
)
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraRopeTransformer, c, t, u


class FlextInfraRefactorTypingUnifier(FlextInfraRopeTransformer):
    """Unify inline type unions into canonical t.* alias references via regex."""

    _description = "canonicalize types and modernize TypeAlias"

    def __init__(
        self,
        *,
        canonical_map: Mapping[frozenset[str], str],
        file_path: Path | None = None,
    ) -> None:
        """Initialize with canonical union map and optional file path for skip logic."""
        super().__init__()
        self._canonical_map = canonical_map
        self._file_path = file_path
        self._is_definition_file = self._is_typing_definition_file(file_path)

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply union canonicalization and TypeAlias modernization."""
        if self._is_definition_file:
            return source, list(self.changes)

        for member_set, canonical in sorted(
            self._canonical_map.items(), key=lambda i: len(i[0]), reverse=True
        ):
            pattern = self._union_pattern(member_set)
            if pattern is not None:

                def replacer(
                    match: t.Infra.RegexMatch, canonical: str = canonical
                ) -> str:
                    # Capture exact matched text for accurate reporting.
                    matched_text = match.group(0)
                    self._record_change(
                        f"Canonicalized inline union {matched_text} -> {canonical}"
                    )
                    return canonical

                source, _count = pattern.subn(replacer, source)

        source = self._canonicalize_annotation_builtins(source)
        source = self._modernize_typealias(source)
        source = self._ensure_t_import(source)
        return source, list(self.changes)

    def _canonicalize_annotation_builtins(self, source: str) -> str:
        try:
            module = ast.parse(source)
        except SyntaxError:
            return source
        line_offsets = self._line_offsets(source)
        edits: list[tuple[int, int, str]] = []
        for annotation in self._annotation_nodes(module):
            rewritten = self._rewrite_annotation(annotation)
            if rewritten is None:
                continue
            replacement = ast.unparse(rewritten)
            start = self._offset(line_offsets, annotation.lineno, annotation.col_offset)
            end_lineno = annotation.end_lineno or annotation.lineno
            end_col_offset = annotation.end_col_offset or annotation.col_offset
            end = self._offset(
                line_offsets,
                end_lineno,
                end_col_offset,
            )
            if source[start:end] == replacement:
                continue
            edits.append((start, end, replacement))
        if not edits:
            return source
        updated = source
        for start, end, replacement in sorted(edits, reverse=True):
            updated = f"{updated[:start]}{replacement}{updated[end:]}"
        return updated

    @staticmethod
    def _line_offsets(source: str) -> list[int]:
        offsets = [0]
        total = 0
        for line in source.splitlines(keepends=True):
            total += len(line)
            offsets.append(total)
        return offsets

    @staticmethod
    def _offset(line_offsets: list[int], lineno: int, col: int) -> int:
        return line_offsets[lineno - 1] + col

    @classmethod
    def _annotation_nodes(cls, module: ast.Module) -> list[ast.expr]:
        annotations: list[ast.expr] = []
        for node in ast.walk(module):
            if isinstance(node, ast.AnnAssign):
                annotations.append(node.annotation)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annotations.extend(
                    arg.annotation
                    for arg in (
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                    )
                    if arg.annotation is not None
                )
                if node.args.vararg and node.args.vararg.annotation is not None:
                    annotations.append(node.args.vararg.annotation)
                if node.args.kwarg and node.args.kwarg.annotation is not None:
                    annotations.append(node.args.kwarg.annotation)
                if node.returns is not None:
                    annotations.append(node.returns)
            if isinstance(node, ast.TypeAlias):
                annotations.append(node.value)
        return annotations

    def _rewrite_annotation(self, annotation: ast.expr) -> ast.expr | None:
        rewritten = self._AnnotationRewriter().visit(copy.deepcopy(annotation))
        if ast.dump(rewritten) == ast.dump(annotation):
            return None
        self._record_change(
            f"Canonicalized built-in annotation {ast.unparse(annotation)} -> {ast.unparse(rewritten)}"
        )
        return rewritten

    class _AnnotationRewriter(ast.NodeTransformer):
        PAIR_ARITY: ClassVar[int] = 2
        _TUPLE_NAMES: ClassVar[Mapping[int, str]] = {
            2: "Pair",
            3: "Triple",
            4: "Quad",
            5: "Quint",
        }

        @override
        def visit_Name(self, node: ast.Name) -> ast.expr:
            if node.id in {"Any", "object"}:
                return ast.copy_location(
                    ast.Attribute(
                        value=ast.Name(id="t", ctx=ast.Load()),
                        attr="JsonValue",
                        ctx=ast.Load(),
                    ),
                    node,
                )
            return node

        @override
        def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
            self.generic_visit(node)
            if (
                node.attr == "Any"
                and isinstance(node.value, ast.Name)
                and node.value.id == "typing"
            ):
                return ast.copy_location(
                    ast.Attribute(
                        value=ast.Name(id="t", ctx=ast.Load()),
                        attr="JsonValue",
                        ctx=ast.Load(),
                    ),
                    node,
                )
            return node

        @override
        def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
            self.generic_visit(node)
            name = self._name(node.value)
            if name == "dict":
                key_node, value_node = self._mapping_args(node.slice)
                if key_node is None or value_node is None:
                    return node
                return ast.copy_location(
                    ast.Subscript(
                        value=self._t_attr("MutableMappingKV"),
                        slice=ast.Tuple(elts=[key_node, value_node], ctx=ast.Load()),
                        ctx=ast.Load(),
                    ),
                    node,
                )
            if name == "list":
                return ast.copy_location(
                    ast.Subscript(
                        value=self._t_attr("MutableSequenceOf"),
                        slice=self._sequence_arg(node.slice),
                        ctx=ast.Load(),
                    ),
                    node,
                )
            if name == "tuple":
                return self._rewrite_tuple(node)
            return node

        def _rewrite_tuple(self, node: ast.Subscript) -> ast.expr:
            items = self._tuple_items(node.slice)
            if (
                len(items) == self.PAIR_ARITY
                and isinstance(items[1], ast.Constant)
                and items[1].value is Ellipsis
            ):
                return ast.copy_location(
                    ast.Subscript(
                        value=self._t_attr("VariadicTuple"),
                        slice=items[0],
                        ctx=ast.Load(),
                    ),
                    node,
                )
            tuple_name = self._TUPLE_NAMES.get(len(items))
            if tuple_name is None:
                return node
            return ast.copy_location(
                ast.Subscript(
                    value=self._t_attr(tuple_name),
                    slice=ast.Tuple(elts=items, ctx=ast.Load()),
                    ctx=ast.Load(),
                ),
                node,
            )

        @staticmethod
        def _name(node: ast.expr) -> str:
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Attribute):
                return node.attr
            return ""

        @staticmethod
        def _mapping_args(
            slice_node: ast.expr,
        ) -> tuple[ast.expr | None, ast.expr | None]:
            if (
                isinstance(slice_node, ast.Tuple)
                and len(slice_node.elts)
                == FlextInfraRefactorTypingUnifier._AnnotationRewriter.PAIR_ARITY
            ):
                return slice_node.elts[0], slice_node.elts[1]
            return None, None

        @staticmethod
        def _sequence_arg(slice_node: ast.expr) -> ast.expr:
            if isinstance(slice_node, ast.Tuple) and len(slice_node.elts) == 1:
                return slice_node.elts[0]
            return slice_node

        @staticmethod
        def _tuple_items(slice_node: ast.expr) -> list[ast.expr]:
            if isinstance(slice_node, ast.Tuple):
                return list(slice_node.elts)
            return [slice_node]

        @staticmethod
        def _t_attr(name: str) -> ast.Attribute:
            return ast.Attribute(
                value=ast.Name(id="t", ctx=ast.Load()),
                attr=name,
                ctx=ast.Load(),
            )

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> t.Infra.RegexPattern | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.MIN_UNION_MEMBERS:
            return None
        escaped = [re.escape(m) for m in sorted(members)]
        part = rf"(?:{'|'.join(escaped)})"
        return re.compile(rf"\b{part}(?:\s*\|\s*{part}){{{len(members) - 1}}}\b")

    def _modernize_typealias(self, source: str) -> str:
        """Convert ``X: TypeAlias = expr`` to ``type X = expr`` (PEP 695)."""
        pattern = re.compile(r"^(\w+)\s*:\s*TypeAlias\s*=\s*(.+)$", re.MULTILINE)
        for match in pattern.finditer(source):
            self._record_change(
                f"Converted legacy TypeAlias assignment: {match.group(1)}"
            )
        new_source, _count = pattern.subn(r"type \1 = \2", source)
        return new_source

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)

    def _ensure_t_import(self, source: str) -> str:
        if "t." not in source or self._has_t_import(source):
            return source
        module_name = self._canonical_import_module()
        if not module_name:
            return source
        insertion = self._import_insertion_offset(source)
        updated = (
            f"{source[:insertion]}from {module_name} import t\n{source[insertion:]}"
        )
        self._record_change(f"Added canonical t import from {module_name}")
        return updated

    @staticmethod
    def _has_t_import(source: str) -> bool:
        try:
            module = ast.parse(source)
        except SyntaxError:
            return bool(
                re.search(
                    r"^from\s+\S+\s+import\s+.*\bt\b",
                    source,
                    re.MULTILINE,
                )
            )
        for node in module.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if any(alias.name == "t" for alias in node.names):
                return True
        return False

    def _canonical_import_module(self) -> str:
        if self._file_path is None:
            return ""
        parts = self._file_path.resolve().parts
        for package_name in ("tests", "examples", "scripts"):
            if package_name in parts:
                return package_name
        return u.Infra.package_name(self._file_path).split(
            ".",
            maxsplit=1,
        )[0]

    @staticmethod
    def _import_insertion_offset(source: str) -> int:
        pattern = re.compile(
            r"^(?:from\s+\S+\s+import\s+.+|import\s+.+)$",
            re.MULTILINE,
        )
        last_match = None
        for match in pattern.finditer(source):
            last_match = match
        if last_match is None:
            return 0
        matched_line = source[last_match.start() : last_match.end()]
        if matched_line.rstrip().endswith("("):
            tail = source[last_match.end() :]
            close_match = re.search(r"^\)\s*$", tail, re.MULTILINE)
            if close_match is not None:
                close_offset = last_match.end() + close_match.end()
                if close_offset < len(source) and source[close_offset] == "\n":
                    close_offset += 1
                return close_offset
        line_end = source.find("\n", last_match.end())
        return len(source) if line_end == -1 else line_end + 1


__all__: list[str] = ["FlextInfraRefactorTypingUnifier"]
