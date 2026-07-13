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

from rope.base import codeanalyze

from flext_infra import c, m, t


class FlextInfraUtilitiesRopeStructure:
    """Emit ``m.Infra.LogicalStatement`` facts from rope-owned source segmentation."""

    @staticmethod
    def logical_statements(source: str) -> t.SequenceOf[m.Infra.LogicalStatement]:
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
                (enclosers[-1][1], enclosers[-1][2])
                if enclosers
                else (c.Infra.RopeScopeKind.MODULE, "")
            )
            category = FlextInfraUtilitiesRopeStructure._categorize(text)
            statements.append(
                m.Infra.LogicalStatement(
                    line=start,
                    indent=indent,
                    category=category,
                    enclosing_kind=kind,
                    enclosing_name=name,
                    text=text,
                )
            )
            FlextInfraUtilitiesRopeStructure._push_encloser(
                enclosers=enclosers, category=category, indent=indent, text=text
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
        if category == c.Infra.StatementCategory.CLASS_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.CLASS,
                FlextInfraUtilitiesRopeStructure._header_name(text),
            ))
        elif category == c.Infra.StatementCategory.FUNC_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.FUNCTION,
                FlextInfraUtilitiesRopeStructure._header_name(text),
            ))

    @staticmethod
    def header_name(statement: m.Infra.LogicalStatement) -> str:
        """Return the declared name from a ``class``/``def`` statement header."""
        return FlextInfraUtilitiesRopeStructure._header_name(statement.text)

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

    @staticmethod
    def target_name(statement: m.Infra.LogicalStatement) -> str:
        """Return the assignment/annotation target name of a statement, or empty.

        Lexical: the identifier left of the first top-level ``=`` or ``:``. Empty
        for non-assignment statements or tuple/attribute targets.
        """
        head = FlextInfraUtilitiesRopeStructure._assignment_head(statement.text.strip())
        source = head if head is not None else statement.text.strip()
        name = source.split(":", maxsplit=1)[0].strip()
        return name if name.isidentifier() else ""

    @staticmethod
    def annotation_contains(statement: m.Infra.LogicalStatement, name: str) -> bool:
        """Return whether ``name`` appears in an annotated statement's annotation.

        Lexical: the slice between the top-level ``:`` and the ``=`` (or end).
        """
        annotation = FlextInfraUtilitiesRopeStructure._annotation_source(statement.text)
        return name in FlextInfraUtilitiesRopeStructure._identifiers(annotation)

    @staticmethod
    def _annotation_source(text: str) -> str:
        """Return the annotation source slice of an annotated statement."""
        stripped = text.strip()
        head = FlextInfraUtilitiesRopeStructure._assignment_head(stripped)
        left = head if head is not None else stripped
        _target, separator, annotation = left.partition(":")
        return annotation.strip() if separator else ""

    @staticmethod
    def call_callee_name(statement: m.Infra.LogicalStatement) -> str:
        """Return the trailing identifier of the value's call callable, or empty.

        Lexical: for ``x = Factory(...)`` or ``x: T = mod.Factory(...)`` returns
        ``Factory``; empty when the value is not a call.
        """
        head = FlextInfraUtilitiesRopeStructure._assignment_head(statement.text.strip())
        if head is None:
            return ""
        value = statement.text.strip()[len(head) + 1 :].strip()
        open_paren = value.find("(")
        if open_paren <= 0:
            return ""
        callee = value[:open_paren].strip()
        return callee.rsplit(".", maxsplit=1)[-1]

    @staticmethod
    def class_base_names(statement: m.Infra.LogicalStatement) -> t.Infra.StrSet:
        """Return terminal base-class names from a ``class X(...):`` header."""
        stripped = statement.text.strip()
        open_paren = stripped.find("(")
        close_paren = stripped.rfind(")")
        if open_paren < 0 or close_paren <= open_paren:
            return set()
        inner = stripped[open_paren + 1 : close_paren]
        return {
            terminal
            for part in inner.split(",")
            if (stripped_part := part.strip())
            if (
                terminal := stripped_part
                .split("[", maxsplit=1)[0]
                .strip()
                .rsplit(".", maxsplit=1)[-1]
            )
        }

    @staticmethod
    def _identifiers(source: str) -> t.Infra.StrSet:
        """Return the set of identifier tokens in a source slice."""
        identifiers: t.Infra.StrSet = set()
        token = ""
        for char in source:
            if char.isalnum() or char == "_":
                token += char
            else:
                if token:
                    identifiers.add(token)
                token = ""
        if token:
            identifiers.add(token)
        return identifiers


__all__: list[str] = ["FlextInfraUtilitiesRopeStructure"]
