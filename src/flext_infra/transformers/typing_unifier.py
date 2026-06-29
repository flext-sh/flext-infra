"""Unify inline typing unions and TypeAlias declarations to canonical forms.

All transformations are syntactic and driven by ``c.Infra.*_RE`` regex
constants — no ``ast`` parsing or tree walking is required:

- **Inline-union canonicalization**: replaces permutations like
  ``int | str`` with the canonical ``t.<Alias>`` (configured via
  ``canonical_map``).
- **Built-in annotation canonicalization**: rewrites ``dict[K, V]`` →
  ``t.MappingKV[K, V]``, ``list[X]`` → ``t.SequenceOf[X]``, and bare
  ``Any``/``object`` / ``typing.Any`` → ``t.JsonValue``. The bracket
  forms guard against false positives by requiring an immediate ``[``.
- **PEP 695 TypeAlias modernization**: rewrites ``X: TypeAlias = expr``
  into ``type X = expr``.
- **Canonical ``t`` import injection**: adds ``from <pkg> import t``
  after the last import line when ``t.`` is used but the import is
  missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import c, t, u
from flext_infra.transformers._typing_rewrite import (
    FlextInfraRefactorTypingUnifierRewriteMixin,
)
from flext_infra.transformers.base import FlextInfraRopeTransformer


class FlextInfraRefactorTypingUnifier(
    FlextInfraRopeTransformer,
    FlextInfraRefactorTypingUnifierRewriteMixin,
):
    """Unify inline type unions and modernize TypeAlias to PEP 695."""

    _description = "canonicalize types and modernize TypeAlias"

    def __init__(
        self,
        *,
        canonical_map: t.MappingKV[frozenset[str], str],
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
        for member_set, canonical in sorted(
            self._canonical_map.items(),
            key=lambda i: len(i[0]),
            reverse=True,
        ):
            pattern = self._union_pattern(member_set)
            if pattern is None:
                continue

            def replacer(
                match: t.Infra.RegexMatch,
                canonical: str = canonical,
            ) -> str:
                """Replace one matched union with the canonical alias."""
                self._record_change(
                    f"Canonicalized inline union {match.group(0)} -> {canonical}",
                )
                return canonical

            source, _count = pattern.subn(replacer, source)
        source = self._canonicalize_annotation_builtins(source)
        source = self._modernize_typealias(source)
        source = self._ensure_t_import(source)
        return source, list(self.changes)

    def _canonicalize_annotation_builtins(self, source: str) -> str:
        """Rewrite built-in generic annotations to canonical ``t.*`` aliases."""
        rewritten, changes = self._rewrite_annotation_text(source)
        for change in changes:
            self._record_change(change)
        return rewritten

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> t.Infra.RegexPattern | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.MIN_UNION_MEMBERS:
            return None
        escaped = [c.Infra.escape(m) for m in sorted(members)]
        part = rf"(?:{'|'.join(escaped)})"
        return c.Infra.compile(
            rf"\b{part}(?:\s*\|\s*{part}){{{len(members) - 1}}}\b",
        )

    def _modernize_typealias(self, source: str) -> str:
        """Convert ``X: TypeAlias = expr`` to ``type X = expr`` (PEP 695)."""
        for match in c.Infra.LEGACY_TYPEALIAS_RE.finditer(source):
            self._record_change(
                f"Converted legacy TypeAlias assignment: {match.group(1)}",
            )
        new_source: str = c.Infra.LEGACY_TYPEALIAS_RE.sub(
            r"type \1 = \2",
            source,
        )
        return new_source

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        """Return whether ``file_path`` is one of the typing definition files."""
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)

    def _ensure_t_import(self, source: str) -> str:
        """Inject ``from <pkg> import t`` when ``t.`` is used without import."""
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

    def _canonical_import_module(self) -> str:
        """Return the root package name for the file under transformation."""
        if self._file_path is None:
            return ""
        package_name: str = u.Infra.package_name(self._file_path)
        return package_name.split(".", maxsplit=1)[0]

    @staticmethod
    def _has_t_import(source: str) -> bool:
        """Return whether the source already imports ``t`` on one or multiple lines."""
        if c.Infra.T_IMPORT_RE.search(source) is not None:
            return True
        lines = source.splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("from ") and stripped.endswith("import ("):
                index += 1
                while index < len(lines):
                    current = lines[index].strip().rstrip(",")
                    if current == ")":
                        break
                    if current == "t":
                        return True
                    index += 1
            index += 1
        return False

    @staticmethod
    def _import_insertion_offset(source: str) -> int:
        """Return the byte offset where a new import line should be inserted."""
        last_match: t.Infra.RegexMatch | None = None
        for match in c.Infra.IMPORT_LINE_ANCHORED_RE.finditer(source):
            last_match = match
        if last_match is None:
            return 0
        matched_line = source[last_match.start() : last_match.end()]
        if matched_line.rstrip().endswith("("):
            tail = source[last_match.end() :]
            close_match = c.Infra.IMPORT_PAREN_CLOSE_RE.search(tail)
            if close_match is not None:
                close_offset: int = last_match.end() + close_match.end()
                if close_offset < len(source) and source[close_offset] == "\n":
                    close_offset += 1
                return close_offset
        line_end = source.find("\n", last_match.end())
        return len(source) if line_end == -1 else line_end + 1


__all__: list[str] = ["FlextInfraRefactorTypingUnifier"]
