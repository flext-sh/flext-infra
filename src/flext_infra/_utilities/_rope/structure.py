"""Rope-native structural and static-analysis fact boundary (no stdlib AST).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence

from flext_infra import c, m, p, t
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeStructure:
    """Expose one Rope-owned fact pass to every structural detector."""

    @staticmethod
    def logical_statements(source: str) -> Sequence[m.Infra.LogicalStatement]:
        """Return Rope logical regions with scope and TYPE_CHECKING context.

        Returns:
            Rope logical regions with scope and TYPE_CHECKING context.

        Raises:
            TypeError: If Rope's source analyzer does not satisfy its contracts.

        """
        if not source:
            return ()
        lines = FlextInfraUtilitiesRopeRuntime.runtime_callable(
            "rope.base.codeanalyze",
            "SourceLinesAdapter",
        )(source)
        if not isinstance(lines, p.Infra.RopeSourceLines):
            msg = "Rope source lines do not satisfy their source contract"
            raise TypeError(msg)
        finder = FlextInfraUtilitiesRopeRuntime.runtime_callable(
            "rope.base.codeanalyze",
            "LogicalLineFinder",
        )(lines)
        if not isinstance(finder, p.Infra.RopeLogicalLineFinder):
            msg = "Rope logical line finder does not satisfy its region contract"
            raise TypeError(msg)
        statements: MutableSequence[m.Infra.LogicalStatement] = []
        enclosers: MutableSequence[tuple[int, c.Infra.RopeScopeKind, str]] = []
        type_checking_guards: MutableSequence[int] = []
        for start, end in finder.generate_regions():
            # Rope hands lines back without their newline; a multi-line logical
            # statement must keep its line breaks so a trailing comment on one
            # line cannot swallow the rest and offsets stay real source offsets.
            text = "\n".join(lines.get_line(n) for n in range(start, end + 1))
            indent = len(text) - len(text.lstrip())
            FlextInfraUtilitiesRopeStructure._pop_exited_enclosers(enclosers, indent)
            while type_checking_guards and indent <= type_checking_guards[-1]:
                type_checking_guards.pop()
            kind, name = (
                (enclosers[-1][1], enclosers[-1][2])
                if enclosers
                else (c.Infra.RopeScopeKind.MODULE, "")
            )
            category = FlextInfraUtilitiesRopeStructure._categorize(text)
            statements.append(
                m.Infra.LogicalStatement(
                    line=start,
                    end_line=end,
                    start_offset=lines.get_line_start(start),
                    end_offset=lines.get_line_end(end),
                    indent=indent,
                    category=category,
                    enclosing_kind=kind,
                    enclosing_name=name,
                    type_checking_guarded=bool(type_checking_guards),
                    text=text,
                ),
            )
            FlextInfraUtilitiesRopeStructure._push_encloser(
                enclosers=enclosers,
                category=category,
                indent=indent,
                text=text,
            )
            # All detectors consume this single guard fact.
            if (
                category == c.Infra.StatementCategory.IF_GUARD
                and FlextInfraUtilitiesRopeStructure._is_type_checking_guard(text)
            ):
                type_checking_guards.append(indent)
        return tuple(statements)

    @staticmethod
    def _is_type_checking_guard(text: str) -> bool:
        """Return whether one logical-line region opens a TYPE_CHECKING branch.

        Returns:
            Whether one logical-line region opens a TYPE_CHECKING branch.

        """
        normalized = " ".join(text.partition("#")[0].split())
        return normalized in {"if TYPE_CHECKING:", "if TYPE_CHECKING is True:"}

    @staticmethod
    def _pop_exited_enclosers(
        enclosers: MutableSequence[tuple[int, c.Infra.RopeScopeKind, str]],
        indent: int,
    ) -> None:
        """Drop enclosers whose body the current indentation has left."""
        while enclosers and indent <= enclosers[-1][0]:
            enclosers.pop()

    @staticmethod
    def _push_encloser(
        *,
        enclosers: MutableSequence[tuple[int, c.Infra.RopeScopeKind, str]],
        category: c.Infra.StatementCategory,
        indent: int,
        text: str,
    ) -> None:
        """Record a ``class``/``def`` header as an enclosing scope for its body."""
        if category == c.Infra.StatementCategory.CLASS_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.CLASS,
                FlextInfraUtilitiesRopeStructure.header_name(text),
            ))
        elif category == c.Infra.StatementCategory.FUNC_DEF:
            enclosers.append((
                indent,
                c.Infra.RopeScopeKind.FUNCTION,
                FlextInfraUtilitiesRopeStructure.header_name(text),
            ))

    @staticmethod
    def header_name(text: str) -> str:
        """Return the declared name from a ``class``/``def`` header line.

        Returns:
            The declared name from a ``class``/``def`` header line.

        """
        stripped = text.strip().removeprefix("async ").strip()
        body = stripped.split(maxsplit=1)[1] if " " in stripped else ""
        for separator in ("(", ":", "["):
            body = body.split(separator, maxsplit=1)[0]
        return body.strip()

    @staticmethod
    def _categorize(text: str) -> c.Infra.StatementCategory:
        """Classify one statement by its leading token (lexical, no AST).

        Returns:
            The resulting ``c.Infra.StatementCategory``.

        """
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
        """Classify a non-keyword statement.

        Returns:
            The resulting ``c.Infra.StatementCategory``.

        Raises:
            TypeError: If Rope Worder does not expose native annotation boundaries.

        """
        head = FlextInfraUtilitiesRopeStructure._assignment_head(stripped)
        if head is not None:
            return (
                c.Infra.StatementCategory.ANN_ASSIGN
                if ":" in head
                else c.Infra.StatementCategory.ASSIGN
            )
        if FlextInfraUtilitiesRopeStructure._string_literal_headed(stripped):
            # Docstrings carry parentheses in their prose; they are inert
            # string-literal expressions, never executable calls.
            return c.Infra.StatementCategory.OTHER
        if ":" in stripped:
            words = FlextInfraUtilitiesRopeRuntime.runtime_callable(
                "rope.base.worder", "Worder"
            )(stripped, handle_ignores=True)
            if not isinstance(words, p.Infra.RopeWorder):
                message = "Rope Worder does not expose native annotation boundaries"
                raise TypeError(message)
            begin, end = words.get_word_range(0)
            if (
                begin == 0
                and stripped[begin:end].isidentifier()
                and stripped[end:].lstrip().startswith(":")
            ):
                return c.Infra.StatementCategory.ANN_ASSIGN
        return (
            c.Infra.StatementCategory.CALL
            if "(" in stripped
            else c.Infra.StatementCategory.OTHER
        )

    @staticmethod
    def _string_literal_headed(stripped: str) -> bool:
        """Return whether a statement starts with a string literal.

        Returns:
            Whether a statement starts with a string literal.

        """
        index = 0
        while index < len(stripped) and stripped[index].lower() in "rbfu":
            index += 1
        return index < len(stripped) and stripped[index] in "'\""

    @staticmethod
    def _assignment_head(stripped: str) -> str | None:
        """Return the target side of a top-level assignment.

        Returns:
            The target side of a top-level assignment.

        """
        depth = 0
        quote = ""
        for index, char in enumerate(stripped):
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
                following = stripped[index + 1] if index + 1 < len(stripped) else ""
                previous = stripped[index - 1] if index else ""
                if following != "=" and previous not in {"=", "!", "<", ">"}:
                    return stripped[:index]
        return None

    @staticmethod
    def target_name(statement: m.Infra.LogicalStatement) -> str:
        """Return a simple assignment/annotation target name, or empty.

        Returns:
            A simple assignment/annotation target name, or empty.

        """
        head = FlextInfraUtilitiesRopeStructure._assignment_head(statement.text.strip())
        source = head if head is not None else statement.text.strip()
        name = source.split(":", maxsplit=1)[0].strip()
        return name if name.isidentifier() else ""

    @staticmethod
    def class_base_names(statement: m.Infra.LogicalStatement) -> t.Infra.StrSet:
        """Return terminal base-class names from a class header.

        Returns:
            Terminal base-class names from a class header.

        """
        stripped = statement.text.strip()
        open_paren = stripped.find("(")
        close_paren = stripped.rfind(")")
        if open_paren < 0 or close_paren <= open_paren:
            return set()
        return {
            terminal
            for part in stripped[open_paren + 1 : close_paren].split(",")
            if (item := part.strip())
            if (terminal := item.split("[", maxsplit=1)[0].strip().rsplit(".", 1)[-1])
        }


__all__: list[str] = ["FlextInfraUtilitiesRopeStructure"]
