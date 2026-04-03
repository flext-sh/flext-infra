"""Unify inline typing unions and TypeAlias declarations to canonical forms via rope."""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableSequence
from pathlib import Path

from flext_infra import c, t, u


class FlextInfraRefactorTypingUnifier:
    """Unify inline type unions into canonical t.* alias references via rope regex."""

    def __init__(
        self,
        *,
        canonical_map: Mapping[frozenset[str], str],
        file_path: Path | None = None,
    ) -> None:
        """Initialize with canonical union map and optional file path for skip logic."""
        self._canonical_map = canonical_map
        self._is_definition_file = self._is_typing_definition_file(file_path)
        self.changes: MutableSequence[str] = []

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, MutableSequence[str]]:
        """Apply union canonicalization and TypeAlias modernization."""
        if self._is_definition_file:
            return resource.read(), self.changes

        source = resource.read()
        replacements = self._build_replacements(source)
        if replacements:
            source, _count = u.batch_replace_annotations(
                rope_project,
                resource,
                replacements,
                apply=True,
            )
            for old, new in replacements.items():
                self.changes.append(f"Canonicalized inline union {old} -> {new}")

        source = self._modernize_typealias(rope_project, resource)
        return source, self.changes

    def _build_replacements(self, source: str) -> t.StrMapping:
        """Scan source for union patterns matching canonical map entries."""
        result: dict[str, str] = {}
        for member_set, canonical in self._canonical_map.items():
            pattern = self._union_pattern(member_set)
            if pattern is not None and pattern.search(source):
                result[" | ".join(sorted(member_set))] = canonical
        return result

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> re.Pattern[str] | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.Thresholds.MIN_UNION_MEMBERS:
            return None
        escaped = [re.escape(m) for m in sorted(members)]
        part = rf"(?:{'|'.join(escaped)})"
        return re.compile(rf"\b{part}(?:\s*\|\s*{part}){{{len(members) - 1}}}\b")

    @staticmethod
    def _modernize_typealias(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> str:
        """Convert ``X: TypeAlias = expr`` to ``type X = expr`` (PEP 695)."""
        pattern = re.compile(r"^(\w+)\s*:\s*TypeAlias\s*=\s*(.+)$", re.MULTILINE)
        new_source, _count = u.replace_in_source(
            rope_project,
            resource,
            pattern,
            r"type \1 = \2",
            apply=True,
        )
        return new_source

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)


__all__ = ["FlextInfraRefactorTypingUnifier"]
