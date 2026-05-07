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
from typing import ClassVar, override

from flext_infra import FlextInfraRopeTransformer, c, t, u


class FlextInfraRefactorTypingUnifier(FlextInfraRopeTransformer):
    """Unify inline type unions and modernize TypeAlias to PEP 695."""

    _description = "canonicalize types and modernize TypeAlias"
    _CONTAINER_REWRITES: ClassVar[t.StrPairTuple] = (
        ("dict[", "t.MutableMappingKV"),
        ("Dict[", "t.MutableMappingKV"),
        ("list[", "t.MutableSequenceOf"),
        ("List[", "t.MutableSequenceOf"),
    )
    _VARIADIC_TUPLE_PARTS: ClassVar[int] = 2
    _FIXED_TUPLE_ALIASES: ClassVar[t.MappingKV[int, str]] = {
        2: "Pair",
        3: "Triple",
        4: "Quad",
    }

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

    def _rewrite_annotation_text(self, text: str) -> tuple[str, list[str]]:
        """Rewrite built-in container annotations found within ``text``."""
        result: list[str] = []
        changes: list[str] = []
        index = 0
        while index < len(text):
            container = self._match_container_prefix(text, index)
            if container is None:
                result.append(text[index])
                index += 1
                continue
            prefix, alias_name = container
            content, end_index = self._extract_square_bracket_content(
                text,
                index + len(prefix) - 1,
            )
            rewritten_content, nested_changes = self._rewrite_type_expression(content)
            if prefix.lower().startswith("tuple["):
                replacement = self._rewrite_tuple_annotation(
                    original_prefix=prefix,
                    rewritten_content=rewritten_content,
                )
            else:
                replacement = f"{alias_name}[{rewritten_content}]"
            original = text[index:end_index]
            result.append(replacement)
            changes.extend(nested_changes)
            if original != replacement:
                changes.append(
                    f"Canonicalized built-in annotation {original} -> {replacement}",
                )
            index = end_index
        return "".join(result), changes

    def _rewrite_type_expression(self, text: str) -> tuple[str, list[str]]:
        """Rewrite one nested type-expression fragment recursively."""
        result: list[str] = []
        changes: list[str] = []
        index = 0
        while index < len(text):
            container = self._match_container_prefix(text, index)
            if container is not None:
                prefix, alias_name = container
                content, end_index = self._extract_square_bracket_content(
                    text,
                    index + len(prefix) - 1,
                )
                rewritten_content, nested_changes = self._rewrite_type_expression(
                    content,
                )
                if prefix.lower().startswith("tuple["):
                    replacement = self._rewrite_tuple_annotation(
                        original_prefix=prefix,
                        rewritten_content=rewritten_content,
                    )
                else:
                    replacement = f"{alias_name}[{rewritten_content}]"
                original = text[index:end_index]
                result.append(replacement)
                changes.extend(nested_changes)
                if original != replacement:
                    changes.append(
                        f"Canonicalized built-in annotation {original} -> {replacement}",
                    )
                index = end_index
                continue
            token_rewrite = self._match_simple_type_alias(text, index)
            if token_rewrite is not None:
                original, replacement, end_index = token_rewrite
                result.append(replacement)
                if original != replacement:
                    changes.append(
                        f"Canonicalized built-in annotation {original} -> {replacement}",
                    )
                index = end_index
                continue
            result.append(text[index])
            index += 1
        return "".join(result), changes

    @staticmethod
    def _match_container_prefix(text: str, index: int) -> t.StrPair | None:
        """Return the matching built-in container prefix at ``index``, if any."""
        for prefix, alias_name in FlextInfraRefactorTypingUnifier._CONTAINER_REWRITES:
            if FlextInfraRefactorTypingUnifier._matches_type_token(text, index, prefix):
                return prefix, alias_name
        if FlextInfraRefactorTypingUnifier._matches_type_token(text, index, "tuple["):
            return "tuple[", ""
        if FlextInfraRefactorTypingUnifier._matches_type_token(text, index, "Tuple["):
            return "Tuple[", ""
        return None

    @staticmethod
    def _matches_type_token(text: str, index: int, token: str) -> bool:
        """Return whether ``token`` starts at ``index`` with identifier boundaries."""
        if not text.startswith(token, index):
            return False
        before = text[index - 1] if index > 0 else ""
        return not before or not (before.isalnum() or before == "_")

    @staticmethod
    def _match_simple_type_alias(
        text: str,
        index: int,
    ) -> tuple[str, str, int] | None:
        """Return a leaf-type rewrite for ``Any``/``typing.Any``/``object``."""
        for token in ("typing.Any", "Any", "object"):
            if not text.startswith(token, index):
                continue
            before = text[index - 1] if index > 0 else ""
            after_index = index + len(token)
            after = text[after_index] if after_index < len(text) else ""
            before_is_identifier = bool(before) and (before.isalnum() or before == "_")
            after_is_identifier = bool(after) and (
                after.isalnum() or after in {"_", "."}
            )
            if before_is_identifier or after_is_identifier:
                continue
            return token, "t.JsonValue", after_index
        return None

    @staticmethod
    def _extract_square_bracket_content(text: str, open_index: int) -> tuple[str, int]:
        """Return the content and end offset for a square-bracket type expression."""
        depth = 0
        cursor = open_index
        while cursor < len(text):
            char = text[cursor]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return text[open_index + 1 : cursor], cursor + 1
            cursor += 1
        return text[open_index + 1 :], len(text)

    def _rewrite_tuple_annotation(
        self,
        *,
        original_prefix: str,
        rewritten_content: str,
    ) -> str:
        """Rewrite one ``tuple[...]`` annotation into the canonical ``t.*`` alias."""
        parts = self._split_top_level_items(rewritten_content)
        if (
            len(parts) == FlextInfraRefactorTypingUnifier._VARIADIC_TUPLE_PARTS
            and parts[1] == "..."
        ):
            return f"t.VariadicTuple[{parts[0]}]"
        alias_name = FlextInfraRefactorTypingUnifier._FIXED_TUPLE_ALIASES.get(
            len(parts)
        )
        if alias_name is not None:
            return f"t.{alias_name}[{', '.join(parts)}]"
        prefix = "Tuple" if original_prefix.startswith("Tuple[") else "tuple"
        return f"{prefix}[{', '.join(parts)}]"

    @staticmethod
    def _split_top_level_items(text: str) -> list[str]:
        """Split a generic type-parameter list on top-level commas only."""
        items: list[str] = []
        start = 0
        depth = 0
        for index, char in enumerate(text):
            if char in "([{":
                depth += 1
            elif char in ")]}":
                if depth > 0:
                    depth -= 1
            elif char == "," and depth == 0:
                items.append(text[start:index].strip())
                start = index + 1
        items.append(text[start:].strip())
        return [item for item in items if item]

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
