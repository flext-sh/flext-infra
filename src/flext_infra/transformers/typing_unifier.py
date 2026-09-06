"""Unify inline typing unions and TypeAlias declarations to canonical forms.

All transformations are syntactic and driven by ``c.Infra.*_RE`` regex
constants — no ``ast`` parsing or tree walking is required:

- **Inline-union canonicalization**: replaces permutations like
  ``int | str`` with the canonical ``t.<Alias>`` (configured via
  ``canonical_map``).
- **Built-in annotation canonicalization**: rewrites ``t.MutableMappingKV[K, V]`` →
  ``t.MutableMappingKV[K, V]``, ``t.MutableSequenceOf[X]`` → ``t.SequenceOf[X]``, and bare
  ``Any``/``object`` / ``typing.Any`` → ``t.JsonValue``. The bracket
  forms guard against false positives by requiring an immediate ``[``.
- **PEP 695 TypeAlias modernization**: rewrites ``X: TypeAlias = expr``
  into ``type X = expr``.
- **Canonical ``t`` import injection**: adds ``from <pkg> import t``
  after the last import line when ``t.`` is used but the import is
  missing.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, override

from flext_infra import c

from .._utilities.transformer_base import FlextInfraRopeTransformer
from ._canonical_t_import import FlextInfraEnsureCanonicalTImportMixin
from ._typing_rewrite import FlextInfraRefactorTypingUnifierRewriteMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraRefactorTypingUnifier(
    FlextInfraEnsureCanonicalTImportMixin,
    FlextInfraRopeTransformer,
    FlextInfraRefactorTypingUnifierRewriteMixin,
):
    """Unify inline type unions and modernize TypeAlias to PEP 695."""

    _description = "canonicalize types and modernize TypeAlias"

    def __init__(
        self,
        *,
        canonical_map: t.MutableMappingKV[frozenset[str], str],
        file_path: Path | None = None,
    ) -> None:
        """Initialize with canonical union map and optional file path for skip logic."""
        super().__init__()
        self._canonical_map = canonical_map
        self._file_path = file_path
        self._is_definition_file = self._is_typing_definition_file(file_path)

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply unions, built-in canonicalization, TypeAlias and t import."""
        if self._is_definition_file:
            return source, list(self.changes)

        def union_size(item: t.Pair[frozenset[str], str]) -> int:
            return len(item[0])

        for member_set, canonical in sorted(
            self._canonical_map.items(), key=union_size, reverse=True
        ):
            pattern = self._union_pattern(member_set)
            if pattern is None:
                continue

            def replacer(match: t.Infra.RegexMatch, canonical: str = canonical) -> str:
                """Replace one matched union with the canonical alias."""
                self._record_change(
                    f"Canonicalized inline union {match.group(0)} -> {canonical}"
                )
                return canonical

            source, _count = pattern.subn(replacer, source)
        source = self._canonicalize_annotation_builtins(source)
        source = self._modernize_typealias(source)
        added, did_add = self._ensure_t_import(
            source,
            FlextInfraEnsureCanonicalTImportMixin.canonical_import_module(
                self._file_path
            ),
        )
        if did_add:
            self._record_change(
                "Added canonical t import from "
                f"{FlextInfraEnsureCanonicalTImportMixin.canonical_import_module(self._file_path)}"
            )
        source = added
        return source, list(self.changes)

    def _canonicalize_annotation_builtins(self, source: str) -> str:
        """Rewrite built-in generic annotations to canonical ``t.*`` aliases.

        Only annotation spans are rewritten. Passing the whole file to the
        annotation rewriter made it edit any text that merely looked like one:
        it rewrote the literal ``"dict["`` inside this package's own rewrite
        tables, destroying them, and left unbalanced brackets in three
        transformer modules. An annotation is an AST position, so the AST is
        what decides which text is eligible.
        """
        try:
            module = ast.parse(source)
        except SyntaxError:
            return source
        # A function-local annotation is not a contract. Rewriting one to an
        # abstract container broke every call that hands the value to a
        # concretely typed parameter, including APIs owned by other packages
        # that this repository cannot widen. The policy governs the interface:
        # parameters, return types, and class or module level declarations.
        local_declarations = {
            declaration
            for node in ast.walk(module)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            for statement in node.body
            for declaration in ast.walk(statement)
            if isinstance(declaration, ast.AnnAssign)
        }
        mutated = self._mutated_names(module)
        spans: t.MutableSequenceOf[t.Pair[int, int]] = []
        for node in ast.walk(module):
            annotations: list[ast.expr | None] = []
            if isinstance(node, ast.AnnAssign):
                target = node.target
                if node in local_declarations or (
                    isinstance(target, ast.Name) and target.id in mutated
                ):
                    continue
                annotations.append(node.annotation)
            elif isinstance(node, ast.arg):
                if node.arg in mutated:
                    continue
                annotations.append(node.annotation)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                annotations.append(node.returns)
            for annotation in annotations:
                if annotation is None:
                    continue
                start = self._offset(source, annotation.lineno, annotation.col_offset)
                end_lineno = annotation.end_lineno
                end_col = annotation.end_col_offset
                if end_lineno is None or end_col is None:
                    continue
                spans.append((start, self._offset(source, end_lineno, end_col)))
        rewritten = source
        for start, end in sorted(spans, reverse=True):
            text = rewritten[start:end]
            replacement, changes = self._rewrite_annotation_text(text)
            if replacement == text:
                continue
            for change in changes:
                self._record_change(change)
            rewritten = f"{rewritten[:start]}{replacement}{rewritten[end:]}"
        return rewritten

    @staticmethod
    def _mutated_names(module: ast.Module) -> frozenset[str]:
        """Return every name the module mutates in place.

        The read-only abstractions are what generalize an annotation, but a
        value the code mutates cannot be one: Mapping has no item assignment
        and Sequence has no append. Rewriting those declarations produced
        exactly those errors, so a mutated name keeps its concrete type.
        """
        mutating_methods = frozenset({
            "append",
            "extend",
            "insert",
            "pop",
            "popitem",
            "remove",
            "setdefault",
            "sort",
            "update",
            "clear",
        })
        names: set[str] = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and isinstance(
                        target.value, ast.Name
                    ):
                        names.add(target.value.id)
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and isinstance(
                        target.value, ast.Name
                    ):
                        names.add(target.value.id)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in mutating_methods
                and isinstance(node.func.value, ast.Name)
            ):
                names.add(node.func.value.id)
        return frozenset(names)

    @staticmethod
    def _offset(source: str, lineno: int, col: int) -> int:
        """Return the character offset of one 1-based line and 0-based column."""
        lines = source.splitlines(keepends=True)
        return sum(len(line) for line in lines[: lineno - 1]) + col

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> t.Infra.RegexPattern | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.MIN_UNION_MEMBERS:
            return None
        escaped = [c.Infra.escape(m) for m in sorted(members)]
        part = rf"(?:{'|'.join(escaped)})"
        pattern: t.Infra.RegexPattern = c.Infra.compile(
            rf"\b{part}(?:\s*\|\s*{part}){{{len(members) - 1}}}\b"
        )
        return pattern

    def _modernize_typealias(self, source: str) -> str:
        """Convert ``X: TypeAlias = expr`` to ``type X = expr`` (PEP 695)."""
        for match in c.Infra.LEGACY_TYPEALIAS_RE.finditer(source):
            self._record_change(
                f"Converted legacy TypeAlias assignment: {match.group(1)}"
            )
        new_source: str = c.Infra.LEGACY_TYPEALIAS_RE.sub(r"type \1 = \2", source)
        return new_source

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        """Return whether ``file_path`` is one of the typing definition files."""
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)


__all__: t.MutableSequenceOf[str] = ["FlextInfraRefactorTypingUnifier"]
