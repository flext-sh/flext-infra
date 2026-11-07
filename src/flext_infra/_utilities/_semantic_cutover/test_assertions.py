"""Semantic bare-assert to ``tm`` matcher cutover planning.

Test assertions are matcher calls. This planner rewrites every ``assert`` into
the equivalent ``tm.that`` call and adds the canonical ``tm`` alias to the
generated test import, so ``make mod`` fixes the law instead of only reporting
it.

The implementation is line/offset based over the rope-owned source; it never
imports ``ast`` or ``cst``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar

from flext_infra import p, t
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesSemanticCutoverTestAssertions(
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Rewrite bare test asserts to canonical ``tm`` matcher calls."""

    ASSERT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<indent>[ \t]*)assert\s+(?P<body>.+)$",
    )
    IS_NOT_NONE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<value>.+?)\s+is\s+not\s+None$",
    )
    IS_NONE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<value>.+?)\s+is\s+None$",
    )
    NOT_IN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<item>.+?)\s+not\s+in\s+(?P<container>.+)$",
    )
    MEMBERSHIP: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<item>.+?)\s+in\s+(?P<container>.+)$",
    )
    NOT_EQUAL: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<left>.+?)\s*!=\s*(?P<right>.+)$",
    )
    EQUAL: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<left>.+?)\s*==\s*(?P<right>.+)$",
    )
    NOT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^not\s+(?P<value>.+)$")
    ISINSTANCE: ClassVar[re.Pattern[str]] = re.compile(
        r"^isinstance\(\s*(?P<value>.+?)\s*,\s*(?P<type>.+?)\s*\)$",
    )
    NOT_ISINSTANCE: ClassVar[re.Pattern[str]] = re.compile(
        r"^not\s+isinstance\(\s*(?P<value>.+?)\s*,\s*(?P<type>.+?)\s*\)$",
    )
    MATCHERS: ClassVar[tuple[tuple[re.Pattern[str], str], ...]] = (
        (NOT_ISINSTANCE, "tm.that({value}, not_={type})"),
        (ISINSTANCE, "tm.that({value}, is_={type})"),
        (IS_NOT_NONE, "tm.that({value}, none=False)"),
        (IS_NONE, "tm.that({value}, none=True)"),
        (NOT_IN, "tm.that({container}, lacks={item})"),
        (MEMBERSHIP, "tm.that({container}, has={item})"),
        (NOT_EQUAL, "tm.that({left}, ne={right})"),
        (EQUAL, "tm.that({left}, eq={right})"),
        (NOT_PATTERN, "tm.that({value}, truth=False)"),
    )

    @classmethod
    def _plan_test_assertions(
        cls,
        root: Path,
        sources: Mapping[Path, str],
        findings: Sequence[p.Infra.ModOccurrence],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan assert rewrites for every finding in the selected phase.

        Returns:
            The semantic edits that converge assertions on ``tm``.

        """
        paths = tuple(
            sorted(
                {
                    (root / finding.file).resolve()
                    for finding in findings
                    if finding.file
                },
            ),
        )
        items = tuple((path, sources[path]) for path in paths if path in sources)
        return cls._semantic_edits(
            items,
            lambda _path, source: cls.rewrite_test_assertions(source),
        )

    @classmethod
    def rewrite_test_assertions(cls, source: str) -> t.Infra.TransformResult:
        """Rewrite every assert in one module to its ``tm`` matcher.

        Returns:
            The rewritten source and the applied changes.

        """
        lines = source.splitlines(keepends=True)
        changed = False
        rewritten: list[str] = []
        for line in lines:
            replacement = cls._rewrite_line(line)
            if replacement is None:
                rewritten.append(line)
                continue
            rewritten.append(replacement)
            changed = True
        if not changed:
            return source, ()
        updated = cls._ensure_tm_import(rewritten)
        return "".join(updated), ("rewired bare asserts to tm matchers",)

    @classmethod
    def _rewrite_line(cls, line: str) -> str | None:
        """Rewrite one assert line, or return ``None`` when untouched.

        Returns:
            The rewritten line, or ``None``.

        """
        ending = "\n" if line.endswith("\n") else ""
        content = line[:-1] if ending else line
        comment = ""
        if "#" in content:
            content, comment = content.split("#", 1)
            comment = f"  #{comment}"
        match = cls.ASSERT_PATTERN.match(content.rstrip())
        if match is None:
            return None
        test, message = cls._split_message(match.group("body").strip())
        if not cls._is_complete(test):
            return None
        matcher = cls._matcher(test)
        if message is not None:
            matcher = matcher[:-1] + f", msg={message})"
        return f"{match.group('indent')}{matcher}{comment}{ending}"

    @classmethod
    def _matcher(cls, test: str) -> str:
        """Map one assert expression to its ``tm.that`` call.

        Returns:
            The matcher call.

        """
        for pattern, template in cls.MATCHERS:
            match = pattern.match(test)
            if match is not None:
                return template.format(**match.groupdict())
        return f"tm.that({test}, truth=True)"

    @staticmethod
    def _is_complete(test: str) -> bool:
        """Return whether the assert expression is complete on one line.

        Returns:
            ``True`` when the expression is non-empty and balanced.

        """
        if not test.strip():
            return False
        depth = 0
        quote = ""
        for character in test:
            if quote:
                if character == quote:
                    quote = ""
                continue
            if character in {'"', "'"}:
                quote = character
            elif character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
        return depth == 0 and not quote

    @staticmethod
    def _split_message(body: str) -> tuple[str, str | None]:
        """Split ``test, message`` at the first top-level comma.

        Returns:
            The test expression and the optional message.

        """
        depth = 0
        quote = ""
        for index, character in enumerate(body):
            if quote:
                if character == quote:
                    quote = ""
                continue
            if character in {'"', "'"}:
                quote = character
            elif character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
            elif character == "," and depth == 0:
                return body[:index].strip(), body[index + 1 :].strip() or None
        return body.strip(), None

    @classmethod
    def _ensure_tm_import(cls, lines: list[str]) -> list[str]:
        """Add the canonical ``tm`` alias to the generated test import.

        Returns:
            The lines with ``tm`` imported.

        """
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith(
                ("from tests import ", "from flext_tests import ")
            ):
                continue
            module = (
                "tests"
                if stripped.startswith("from tests import ")
                else "flext_tests"
            )
            names = stripped.removeprefix(f"from {module} import ").strip()
            if re.search(r"\btm\b", names):
                return lines
            lines[index] = f"from {module} import {names}, tm\n"
            return lines
        position = cls._import_position(lines)
        lines.insert(position, "from flext_tests import tm\n")
        return lines

    @staticmethod
    def _import_position(lines: Sequence[str]) -> int:
        """Return the first safe import position after docstring/future.

        Returns:
            The insertion index.

        """
        position = 0
        if lines:
            first = lines[0].strip()
            if first.startswith(('"""', "'''")):
                quote = first[:3]
                position = 1
                while position < len(lines) and quote not in lines[position]:
                    position += 1
                position += 1
        depth = 0
        while position < len(lines):
            stripped = lines[position].strip()
            if depth > 0:
                depth += stripped.count("(") - stripped.count(")")
                position += 1
                continue
            if stripped.startswith(("from ", "import ")):
                depth = stripped.count("(") - stripped.count(")")
                position += 1
                continue
            if not stripped:
                position += 1
                continue
            break
        return position


__all__: list[str] = [
    "FlextInfraUtilitiesSemanticCutoverTestAssertions",
]
