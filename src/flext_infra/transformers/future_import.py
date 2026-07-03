"""Inject ``from __future__ import annotations`` when missing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorFutureImport(FlextInfraRopeTransformer):
    """Ensure the leading ``from __future__ import annotations`` line exists."""

    _description = "insert from __future__ import annotations"
    _DOCSTRING_QUOTES: ClassVar[tuple[str, str]] = ('"""', "'''")
    _TRIPLE_QUOTE_PAIR_COUNT: ClassVar[int] = 2

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Normalize the future import after the module docstring."""
        updated = self._normalized_source(source)
        if updated == source:
            return source, list(self.changes)
        self._record_change("Normalized from __future__ import annotations")
        return updated, list(self.changes)

    @classmethod
    def _normalized_source(cls, source: str) -> str:
        """Return source with exactly one canonical future import."""
        lines = source.splitlines(keepends=True)
        body = [line for line in lines if line.strip() != c.Infra.FUTURE_ANNOTATIONS]
        insertion, has_docstring = cls._insertion_index(body)
        future_line = f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        if has_docstring:
            while insertion < len(body) and not body[insertion].strip():
                del body[insertion]
            insert_lines = ["\n", future_line]
            if insertion < len(body):
                insert_lines.append("\n")
            body[insertion:insertion] = insert_lines
            return "".join(body)
        body.insert(insertion, future_line)
        return "".join(body)

    @classmethod
    def _insertion_index(cls, lines: Sequence[str]) -> tuple[int, bool]:
        """Return the canonical insertion index and whether a docstring exists."""
        statement_index = cls._first_statement_index(lines)
        if statement_index < len(lines):
            quote = cls._docstring_quote(lines[statement_index].strip())
            if quote is not None:
                return cls._index_after_docstring(lines, statement_index, quote), True
        return cls._index_after_leading_comments(lines), False

    @staticmethod
    def _first_statement_index(lines: Sequence[str]) -> int:
        """Return the first non-comment, non-blank physical line index."""
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped and not stripped.startswith("#"):
                return index
            index += 1
        return index

    @staticmethod
    def _index_after_leading_comments(lines: Sequence[str]) -> int:
        """Return index after shebang/encoding/comment header and its blank gap."""
        index = 0
        saw_comment = False
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("#"):
                saw_comment = True
                index += 1
                continue
            if not stripped and saw_comment:
                index += 1
                continue
            break
        return index

    @classmethod
    def _docstring_quote(cls, stripped_line: str) -> str | None:
        """Return the opening triple-quote used by a module docstring line."""
        for quote in cls._DOCSTRING_QUOTES:
            if stripped_line.startswith(quote):
                return quote
        return None

    @classmethod
    def _index_after_docstring(
        cls,
        lines: Sequence[str],
        start_index: int,
        quote: str,
    ) -> int:
        """Return the line index immediately after the module docstring."""
        start_line = lines[start_index].strip()
        if start_line.count(quote) >= cls._TRIPLE_QUOTE_PAIR_COUNT:
            return start_index + 1
        index = start_index + 1
        while index < len(lines):
            if quote in lines[index]:
                return index + 1
            index += 1
        return index


__all__: list[str] = ["FlextInfraRefactorFutureImport"]
