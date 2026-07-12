"""Rope-native syntactic structure boundary (no stdlib ``ast``).

The single sanctioned source of *syntactic* facts for detectors: statement
lines, indentation, lexical category, and the enclosing def/class scope. It is
built on rope's own ``codeanalyze.LogicalLineFinder`` + ``SourceLinesAdapter``
(rope owns the tokenizer) — never ``PyModule.get_ast()`` (which returns a stdlib
``ast.Module``) and never ``import ast``. Detectors consume ``m.Infra`` data
models, never rope internals.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rope.base import codeanalyze

from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesRopeStructure:
    """Emit ``m.Infra.LogicalStatement`` facts from rope-owned source segmentation."""

    @staticmethod
    def logical_statements(
        source: str,
    ) -> t.SequenceOf[m.Infra.LogicalStatement]:
        """Return one ``LogicalStatement`` per rope logical-line region.

        A single forward pass over ``LogicalLineFinder.generate_regions`` with an
        indent stack that tracks the nearest enclosing ``class``/``def`` header,
        so every statement carries its enclosing scope without an ``ast`` walk.
        """
        if not source:
            return ()
        lines = codeanalyze.SourceLinesAdapter(source)
        finder = codeanalyze.LogicalLineFinder(lines)
        statements: t.MutableSequenceOf[m.Infra.LogicalStatement] = []
        enclosers: t.MutableSequenceOf[tuple[int, c.Infra.RopeScopeKind, str]] = []
        for start, end in finder.generate_regions():
            text = "".join(lines.get_line(n) for n in range(start, end + 1))
            indent = len(text) - len(text.lstrip())
            FlextInfraUtilitiesRopeStructure._pop_exited_enclosers(enclosers, indent)
            kind, name = (
                enclosers[-1][1],
                enclosers[-1][2],
            ) if enclosers else (c.Infra.RopeScopeKind.MODULE, "")
            category = FlextInfraUtilitiesRopeStructure._categorize(text)
            statements.append(
                m.Infra.LogicalStatement(
                    line=start,
                    indent=indent,
                    category=category,
                    enclosing_kind=kind,
                    enclosing_name=name,
                    text=text,
                ),
            )
            FlextInfraUtilitiesRopeStructure._push_encloser(
                enclosers=enclosers,
                category=category,
                indent=indent,
                text=text,
            )
        return tuple(statements)

    @staticmethod
    def _pop_exited_enclosers(
        enclosers: t.MutableSequenceOf[tuple[int, c.Infra.RopeScopeKind, str]],
        indent: int,
    ) -> None:
        """Drop enclosers whose body the current indentation has left."""
        while enclosers and indent <= enclosers[-1][0]:
            enclosers.pop()

    @staticmethod
    def _push_encloser(
        *,
        enclosers: t.MutableSequenceOf[tuple[int, c.Infra.RopeScopeKind, str]],
        category: c.Infra.StatementCategory,
        indent: int,
        text: str,
    ) -> None:
        """Record a ``class``/``def`` header as an enclosing scope for its body."""
        if category is c.Infra.StatementCategory.CLASS_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.CLASS,
                FlextInfraUtilitiesRopeStructure._header_name(text),
            ))
        elif category is c.Infra.StatementCategory.FUNC_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.FUNCTION,
                FlextInfraUtilitiesRopeStructure._header_name(text),
            ))

    @staticmethod
    def _header_name(text: str) -> str:
        """Return the declared name from a ``class``/``def`` header line."""
        stripped = text.strip().removeprefix("async ").strip()
        body = stripped.split(maxsplit=1)[1] if " " in stripped else ""
        for separator in ("(", ":", "["):
            body = body.split(separator, maxsplit=1)[0]
        return body.strip()

    @staticmethod
    def _categorize(text: str) -> c.Infra.StatementCategory:
        """Classify one statement by its leading token (lexical, no ``ast``)."""
        stripped = text.strip()
        first = stripped.split(maxsplit=1)[0] if stripped else ""
        keyword_map = {
            "import": c.Infra.StatementCategory.IMPORT,
            "from": c.Infra.StatementCategory.FROM_IMPORT,
            "type": c.Infra.StatementCategory.TYPE_ALIAS,
            "class": c.Infra.StatementCategory.CLASS_DEF,
            "def": c.Infra.StatementCategory.FUNC_DEF,
            "async": c.Infra.StatementCategory.FUNC_DEF,
            "if": c.Infra.StatementCategory.IF_GUARD,
        }
        if first in keyword_map:
            return keyword_map[first]
        return FlextInfraUtilitiesRopeStructure._categorize_expression(stripped)

    @staticmethod
    def _categorize_expression(stripped: str) -> c.Infra.StatementCategory:
        """Classify a non-keyword statement (assignment / call / other)."""
        head = FlextInfraUtilitiesRopeStructure._assignment_head(stripped)
        if head is not None:
            if ":" in head:
                return c.Infra.StatementCategory.ANN_ASSIGN
            return c.Infra.StatementCategory.ASSIGN
        if "(" in stripped:
            return c.Infra.StatementCategory.CALL
        return c.Infra.StatementCategory.OTHER

    @staticmethod
    def _assignment_head(stripped: str) -> str | None:
        """Return the target side of a top-level ``=`` assignment, or None.

        Scans outside brackets/quotes so ``==``, keyword args, and dict literals
        do not read as assignments.
        """
        depth = 0
        quote = ""
        index = 0
        length = len(stripped)
        while index < length:
            char = stripped[index]
            if quote:
                if char == quote:
                    quote = ""
            elif char in {"'", '"'}:
                quote = char
            elif char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "=" and depth == 0:
                following = stripped[index + 1] if index + 1 < length else ""
                previous = stripped[index - 1] if index else ""
                if following != "=" and previous not in {"=", "!", "<", ">"}:
                    return stripped[:index]
            index += 1
        return None


__all__: list[str] = ["FlextInfraUtilitiesRopeStructure"]
