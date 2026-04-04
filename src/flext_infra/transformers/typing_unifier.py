"""Unify inline typing unions and TypeAlias declarations to canonical forms via rope."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import override

from flext_infra import FlextInfraRopeTransformer, c, t


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

                def replacer(match: re.Match[str], canonical: str = canonical) -> str:
                    # Capture exact matched text for accurate reporting.
                    matched_text = match.group(0)
                    self._record_change(
                        f"Canonicalized inline union {matched_text} -> {canonical}"
                    )
                    return canonical

                source, _count = pattern.subn(replacer, source)

        source = self._modernize_typealias(source)
        return source, list(self.changes)

    @staticmethod
    def _union_pattern(members: frozenset[str]) -> re.Pattern[str] | None:
        """Build regex matching any permutation of a ``A | B | C`` union."""
        if len(members) < c.Infra.Thresholds.MIN_UNION_MEMBERS:
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


__all__ = ["FlextInfraRefactorTypingUnifier"]
