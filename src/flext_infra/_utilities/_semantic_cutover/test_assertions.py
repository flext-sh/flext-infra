"""Semantic bare-assert to ``tm`` matcher cutover planning.

Test assertions are matcher calls. This planner rewrites every ``assert`` into
the equivalent ``tm.that`` call and adds the canonical ``tm`` alias to the
generated test import, so ``make mod`` fixes the law instead of only reporting
it.

Statements come from the rope logical-line boundary, so a multi-line assert is
one unit. Operators are matched on a masked copy of the expression in which
string contents and bracketed groups are blanked at the same offsets: only the
assert's own top-level operator selects the matcher, never an ``in`` or ``==``
inside a comprehension, call or string. The implementation never imports
``ast`` or ``cst``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesProtectedEditLinting
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeStructure
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
        r"^(?P<indent>[ \t]*)assert\b(?P<body>.*)$",
        re.DOTALL,
    )
    WHOLE_PREDICATE: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:and|or|if|else|lambda|for)\b",
    )
    NEGATION: ClassVar[re.Pattern[str]] = re.compile(r"^not\b\s*")
    COMPARISON: ClassVar[re.Pattern[str]] = re.compile(
        r"==|!=|<=|>=|<|>|\bnot\s+in\b|\bin\b|\bis\s+not\b|\bis\b",
    )
    ISINSTANCE: ClassVar[re.Pattern[str]] = re.compile(r"^isinstance\(_*\)$")
    COMPARISON_MATCHERS: ClassVar[Mapping[str, str]] = MappingProxyType({
        "==": "tm.that({left}, eq={right})",
        "!=": "tm.that({left}, ne={right})",
        "in": "tm.that({right}, has={left})",
        "not in": "tm.that({right}, lacks={left})",
        "is None": "tm.that({left}, none=True)",
        "is not None": "tm.that({left}, none=False)",
    })
    STRING_MESSAGE: ClassVar[re.Pattern[str]] = re.compile(
        r"(?:\s*[rRfFuU]{0,2}(?P<quote>\"\"\"|'''|\"|')_*(?P=quote)\s*)+",
    )
    ISINSTANCE_PREFIX: ClassVar[str] = "isinstance("
    MASK: ClassVar[str] = "_"
    STRING_LITERAL: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<![\w\"'])(?P<prefix>[rRbBfFuU]{0,2})(?P<quote>\"\"\"|'''|\"|')",
    )
    SCOPE_OPENER: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:async\s+def|def|class)\b"
    )
    DEFINITION: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:async\s+)?def\s+\w+\s*(?:\[[^\]]*\])?\((?P<params>.*)\)\s*(?:->[^:]*)?:",
        re.DOTALL,
    )
    ASSIGNMENT: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<targets>[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*(?::[^=]+)?=(?!=)",
    )
    LOOP_TARGET: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:async\s+)?for\s+(?P<targets>.+?)\s+in\b",
    )
    ALIAS_TARGET: ClassVar[re.Pattern[str]] = re.compile(
        r"\bas\s+(?P<name>[A-Za-z_]\w*)"
    )
    WALRUS_TARGET: ClassVar[re.Pattern[str]] = re.compile(r"([A-Za-z_]\w*)\s*:=")
    SCOPE_DECLARATION: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:global|nonlocal)\s+(?P<names>.+)$",
    )
    NAME: ClassVar[re.Pattern[str]] = re.compile(r"[A-Za-z_]\w*")
    LITERAL_CHUNK: ClassVar[int] = 48
    LITERAL_PART_INDENT: ClassVar[str] = " " * 8
    LITERAL_PART_CLOSE: ClassVar[str] = " " * 4

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
        return cls._semantic_checked_edits(
            items,
            lambda path, source: cls._formattable_assert_rewrite(root, path, source),
        )

    @classmethod
    def rewrite_test_assertions(cls, source: str) -> t.Infra.TransformResult:
        """Rewrite every assert statement in one module to its ``tm`` matcher.

        Returns:
            The rewritten source and the applied changes.

        """
        return cls._assert_rewrites_applied(source, cls._assert_replacements(source))

    @classmethod
    def _formattable_assert_rewrite(
        cls,
        root: Path,
        path: Path,
        source: str,
    ) -> p.Result[t.Infra.TransformResult]:
        """Rewrite every assert in a form the destination's formatter can fit.

        Publication rejects an edit that introduces a line the formatter cannot
        fit (``c.Infra.FORMATTER_UNSATISFIED_CODE``) and a phase that leaves
        any assert behind. When the whole module is rejected for width, each
        assert is admitted on its own; one whose matcher keyword pushes a long
        string literal past the width is emitted with that literal split at
        whitespace into implicitly concatenated parts (the same value, which
        the formatter lays out one part per line). A matcher that still cannot
        fit fails loud with its location.

        Returns:
            The admitted rewrite, or the failure naming the unfittable assert.

        """
        replacements = cls._assert_replacements(source)
        if not replacements:
            return r[t.Infra.TransformResult].ok((source, ()))
        whole = cls._assert_rewrite_admitted(root, path, source, replacements)
        if whole.failure or whole.value:
            return whole.map(
                lambda _: cls._assert_rewrites_applied(source, replacements)
            )
        accepted: list[tuple[int, int, str]] = []
        for first, last, matcher in replacements:
            for candidate in dict.fromkeys((
                matcher,
                cls._assert_split_literals(matcher),
            )):
                trial = cls._assert_rewrite_admitted(
                    root, path, source, (*accepted, (first, last, candidate))
                )
                if trial.failure:
                    return r[t.Infra.TransformResult].from_failure(trial)
                if trial.value:
                    accepted.append((first, last, candidate))
                    break
            else:
                return r[t.Infra.TransformResult].fail(
                    f"{path}:{first}: the tm matcher of this assert cannot fit the"
                    f" formatting width; shorten or split its operand at the owner",
                )
        return r[t.Infra.TransformResult].ok(
            cls._assert_rewrites_applied(source, accepted)
        )

    @classmethod
    def _assert_split_literals(cls, text: str) -> str:
        """Split each long string literal in ``text`` at whitespace.

        A split never lands inside an f-string replacement field or after a
        backslash, so every part keeps the literal's prefix and quoting and the
        concatenation equals the original value. Parts are emitted one per
        line: a single-line implicit concatenation is joined back by the
        normalizer's own repair (ISC001) before the formatter sees it.

        Returns:
            ``text`` with long literals as parenthesized implicit concatenations.

        """
        indent = text[: len(text) - len(text.lstrip())]
        separator = f"\n{indent}{cls.LITERAL_PART_INDENT}"
        pieces: list[str] = []
        position = 0
        for literal in cls.STRING_LITERAL.finditer(text):
            if literal.start() < position:
                continue
            prefix, quote = literal.group("prefix"), literal.group("quote")
            end = cls._assert_literal_end(text, literal.end(), quote)
            if end is None:
                break
            content = text[literal.end() : end]
            chunks = cls._assert_literal_chunks(
                content, formatted="f" in prefix.lower()
            )
            pieces.append(text[position : literal.start()])
            if len(chunks) > 1:
                parts = separator.join(
                    f"{prefix}{quote}{chunk}{quote}" for chunk in chunks
                )
                pieces.append(f"({separator}{parts}\n{indent}{cls.LITERAL_PART_CLOSE})")
            else:
                pieces.append(text[literal.start() : end + len(quote)])
            position = end + len(quote)
        pieces.append(text[position:])
        return "".join(pieces)

    @staticmethod
    def _assert_literal_end(text: str, start: int, quote: str) -> int | None:
        """Return the offset of the closing quote of a literal body.

        Returns:
            The closing quote offset, or ``None`` for an unterminated literal.

        """
        index = start
        while index < len(text):
            if text[index] == "\\":
                index += 2
                continue
            if text.startswith(quote, index):
                return index
            index += 1
        return None

    @classmethod
    def _assert_literal_chunks(cls, content: str, *, formatted: bool) -> list[str]:
        """Cut a literal body into parts of at most the chunk size at spaces.

        Returns:
            The parts, or the whole body when it is short or has no safe cut.

        """
        if len(content) <= cls.LITERAL_CHUNK:
            return [content]
        cuts: list[int] = []
        braces = 0
        for index, character in enumerate(content):
            if formatted and character == "{":
                braces += 1
            elif formatted and character == "}":
                braces -= 1
            elif (
                character == " " and braces == 0 and content[index - 1 : index] != "\\"
            ):
                cuts.append(index + 1)
        chunks: list[str] = []
        start = 0
        last = 0
        for cut in (*cuts, len(content)):
            if cut - start > cls.LITERAL_CHUNK and last > start:
                chunks.append(content[start:last])
                start = last
            last = cut
        chunks.append(content[start:])
        return [chunk for chunk in chunks if chunk]

    @classmethod
    def _assert_rewrite_admitted(
        cls,
        root: Path,
        path: Path,
        source: str,
        replacements: Sequence[tuple[int, int, str]],
    ) -> p.Result[bool]:
        """Return whether publication admits ``replacements`` for ``path``.

        Returns:
            ``True`` when admitted, ``False`` when only the width is
            unsatisfiable, or the normalizer's own failure.

        """
        candidate, _changes = cls._assert_rewrites_applied(source, replacements)
        normalized = FlextInfraUtilitiesProtectedEditLinting.normalize_source(
            root,
            path,
            candidate,
            before_source=source,
        )
        width_only = (normalized.error or "").endswith(
            f": {c.Infra.FORMATTER_UNSATISFIED_CODE}",
        )
        if normalized.failure and not width_only:
            return r[bool].from_failure(normalized)
        return r[bool].ok(not normalized.failure)

    @classmethod
    def _assert_replacements(cls, source: str) -> list[tuple[int, int, str]]:
        """Return ``(first line, last line, matcher)`` for each rewritable assert.

        Returns:
            One replacement per rewritable logical assert statement.

        """
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        return [
            (statement.line, statement.end_line, replacement)
            for statement, local_names in zip(
                statements, cls._assert_local_names(statements), strict=True
            )
            if (
                replacement := cls._rewrite_assert_statement(
                    statement.text, local_names
                )
            )
            is not None
        ]

    @classmethod
    def _assert_local_names(
        cls,
        statements: Sequence[p.Infra.LogicalStatement],
    ) -> list[frozenset[str]]:
        """Return, per statement, the names local to its enclosing function.

        A name is local when the function binds it (parameter, assignment,
        loop, ``with``/``except`` alias or walrus) and does not declare it
        ``global``/``nonlocal``; rebinding any other name would make it local
        and break its earlier reads.

        Returns:
            One frozenset of local names per statement, empty outside functions.

        """
        scopes: list[tuple[int, int | None]] = []
        bound: dict[int, set[str]] = {}
        outer: dict[int, set[str]] = {}
        owners: list[int | None] = []
        for index, statement in enumerate(statements):
            text = statement.text.strip()
            while scopes and statement.indent <= scopes[-1][0]:
                scopes.pop()
            function = scopes[-1][1] if scopes else None
            owners.append(function)
            if function is not None:
                cls._assert_bind(
                    text,
                    bound.setdefault(function, set()),
                    outer.setdefault(function, set()),
                )
            if cls.SCOPE_OPENER.match(text) is not None:
                definition = cls.DEFINITION.match(text)
                if definition is None:
                    scopes.append((statement.indent, None))
                    continue
                bound[index] = cls._assert_parameters(definition.group("params"))
                scopes.append((statement.indent, index))
        return [
            frozenset()
            if function is None
            else frozenset(bound.get(function, set()) - outer.get(function, set()))
            for function in owners
        ]

    @classmethod
    def _assert_bind(cls, text: str, names: set[str], outer: set[str]) -> None:
        """Record the names one statement binds in, or declares out of, a scope."""
        declaration = cls.SCOPE_DECLARATION.match(text)
        if declaration is not None:
            outer.update(name.strip() for name in declaration.group("names").split(","))
        assignment = cls.ASSIGNMENT.match(text)
        if assignment is not None:
            names.update(
                name.strip() for name in assignment.group("targets").split(",")
            )
        loop = cls.LOOP_TARGET.match(text)
        if loop is not None:
            names.update(cls.NAME.findall(loop.group("targets")))
        if text.startswith(("with ", "async with ", "except")):
            names.update(
                alias.group("name") for alias in cls.ALIAS_TARGET.finditer(text)
            )
        names.update(cls.WALRUS_TARGET.findall(text))

    @classmethod
    def _assert_parameters(cls, parameters: str) -> set[str]:
        """Return the parameter names of one ``def`` signature body.

        Returns:
            The bound parameter names.

        """
        masked = cls._assert_mask(parameters)
        names: set[str] = set()
        start = 0
        for end in (*(i for i, ch in enumerate(masked) if ch == ","), len(masked)):
            name = cls.NAME.match(parameters[start:end].strip().lstrip("*"))
            if name is not None:
                names.add(name.group())
            start = end + 1
        return names

    @classmethod
    def _assert_typed_rebind(
        cls,
        test: str,
        local_names: frozenset[str],
    ) -> tuple[str, str] | None:
        """Return ``(name, typed helper call)`` for a local type or None check.

        ``tm.instance``/``tm.not_none`` return the checked value typed, so the
        rebound local keeps ``T`` for its later uses without a narrowing guard
        (ENFORCE-125).

        Returns:
            The rebound name and its helper call, or ``None``.

        """
        arguments = cls._assert_isinstance_arguments(test)
        if arguments is not None:
            name, kind = arguments
            if name in local_names and not kind.startswith("("):
                return name, f"tm.instance({name}, {kind})"
            return None
        masked = cls._assert_mask(test)
        if cls.WHOLE_PREDICATE.search(masked) or cls.NEGATION.match(masked):
            return None
        operators = tuple(cls.COMPARISON.finditer(masked))
        if len(operators) != 1 or " ".join(operators[0].group().split()) != "is not":
            return None
        name = test[: operators[0].start()].strip()
        if test[operators[0].end() :].strip() == "None" and name in local_names:
            return name, f"tm.not_none({name})"
        return None

    @classmethod
    def _assert_rewrites_applied(
        cls,
        source: str,
        replacements: Sequence[tuple[int, int, str]],
    ) -> t.Infra.TransformResult:
        """Apply line-range replacements and import ``tm`` when any applied.

        Returns:
            The rewritten source and the applied changes.

        """
        if not replacements:
            return source, ()
        lines = source.splitlines(keepends=True)
        for first, last, replacement in sorted(replacements, reverse=True):
            ending = "\n" if lines[last - 1].endswith("\n") else ""
            lines[first - 1 : last] = [f"{replacement}{ending}"]
        updated = cls._ensure_tm_import(lines)
        return "".join(updated), ("rewired bare asserts to tm matchers",)

    @classmethod
    def _rewrite_assert_statement(
        cls,
        text: str,
        local_names: frozenset[str],
    ) -> str | None:
        """Rewrite one logical assert statement, or return ``None``.

        A comment inside a multi-line assert has no place in the matcher call,
        so that statement is left for review instead of losing the comment.

        Returns:
            The rewritten statement, or ``None`` when it is not rewritable.

        """
        match = cls.ASSERT_PATTERN.match(text)
        if match is None:
            return None
        body = match.group("body")
        comment = ""
        comment_index = cls._assert_comment_index(body)
        if comment_index is not None:
            if "\n" in body[comment_index:]:
                return None
            comment = f"  {body[comment_index:].strip()}"
            body = body[:comment_index]
        test, message = cls._split_message(body)
        if not test:
            return None
        indent = match.group("indent")
        unwrapped = cls._assert_unwrap(test)
        if (
            message is not None
            and cls.STRING_MESSAGE.fullmatch(cls._assert_mask(message)) is None
        ):
            # ``assert`` evaluates any message lazily and raises it as given;
            # ``tm.reject`` keeps both, where ``msg=`` would coerce eagerly.
            return (
                f"{indent}if not ({unwrapped}):{comment}\n"
                f"{indent}    tm.reject({message})"
            )
        rebind = cls._assert_typed_rebind(unwrapped, local_names)
        prefix = f"{rebind[0]} = " if rebind is not None else ""
        call = rebind[1] if rebind is not None else cls._matcher(unwrapped)
        if message is not None:
            call = f"{call[:-1]}, msg={message})"
        return f"{indent}{prefix}{call}{comment}"

    @classmethod
    def _matcher(cls, test: str) -> str:
        """Map one assert expression to its ``tm.that`` call.

        Python precedence decides the matcher: a top-level boolean or
        conditional keeps the whole predicate, ``not`` negates everything after
        it, and only a single top-level comparison maps to a typed matcher.

        Returns:
            The matcher call.

        """
        masked = cls._assert_mask(test)
        if cls.WHOLE_PREDICATE.search(masked):
            return f"tm.that({test}, truth=True)"
        negation = cls.NEGATION.match(masked)
        if negation is not None:
            return cls._assert_negated_matcher(test[negation.end() :])
        arguments = cls._assert_isinstance_arguments(test)
        if arguments is not None:
            return f"tm.that({arguments[0]}, is_={arguments[1]})"
        return cls._assert_comparison_matcher(test, masked)

    @classmethod
    def _assert_negated_matcher(cls, operand: str) -> str:
        """Map the operand of a top-level ``not`` to its matcher.

        Returns:
            The ``not_`` type matcher, or the negated truth matcher.

        """
        expression = cls._assert_unwrap(operand)
        arguments = cls._assert_isinstance_arguments(expression)
        if arguments is not None:
            return f"tm.that({arguments[0]}, not_={arguments[1]})"
        return f"tm.that({expression}, truth=False)"

    @classmethod
    def _assert_comparison_matcher(cls, test: str, masked: str) -> str:
        """Map a single top-level comparison to its typed matcher.

        Returns:
            The typed matcher, or the truth matcher for any other expression.

        """
        operators = tuple(cls.COMPARISON.finditer(masked))
        if len(operators) == 1:
            operator = operators[0]
            left = test[: operator.start()].strip()
            right = test[operator.end() :].strip()
            symbol = " ".join(operator.group().split())
            if symbol in {"is", "is not"} and right == "None":
                symbol = f"{symbol} None"
            template = cls.COMPARISON_MATCHERS.get(symbol)
            if template is not None:
                return template.format(left=left, right=right)
        return f"tm.that({test}, truth=True)"

    @classmethod
    def _assert_isinstance_arguments(cls, test: str) -> tuple[str, str] | None:
        """Return ``(value, type)`` when ``test`` is one ``isinstance`` call.

        Returns:
            The value and type operands, or ``None``.

        """
        if cls.ISINSTANCE.match(cls._assert_mask(test)) is None:
            return None
        inner = test[len(cls.ISINSTANCE_PREFIX) : -1]
        commas = [
            index
            for index, character in enumerate(cls._assert_mask(inner))
            if character == ","
        ]
        if len(commas) != 1:
            return None
        return inner[: commas[0]].strip(), inner[commas[0] + 1 :].strip()

    @classmethod
    def _split_message(cls, body: str) -> tuple[str, str | None]:
        """Split ``test, message`` at the first top-level comma.

        Returns:
            The test expression and the optional message.

        """
        comma = cls._assert_mask(body).find(",")
        if comma < 0:
            return body.strip(), None
        return body[:comma].strip(), body[comma + 1 :].strip() or None

    @classmethod
    def _assert_unwrap(cls, test: str) -> str:
        """Drop parentheses that enclose the whole expression.

        A tuple or generator stays wrapped: its comma or ``for`` would change
        meaning without the parentheses.

        Returns:
            The expression without redundant outer parentheses.

        """
        expression = test.strip()
        while expression.startswith("(") and expression.endswith(")"):
            masked = cls._assert_mask(expression)
            if set(masked[1:-1]) - {cls.MASK}:
                return expression
            inner = expression[1:-1].strip()
            inner_masked = cls._assert_mask(inner)
            if "," in inner_masked or re.search(r"\bfor\b", inner_masked):
                return expression
            expression = inner
        return expression

    @classmethod
    def _assert_mask(cls, text: str) -> str:
        """Blank string contents and bracketed groups, keeping every offset.

        Returns:
            A copy of ``text`` of equal length where only top-level code shows.

        """
        masked: list[str] = []
        depth = 0
        quote = ""
        index = 0
        while index < len(text):
            character = text[index]
            if quote:
                if character == "\\":
                    step = min(2, len(text) - index)
                    masked.append(cls.MASK * step)
                    index += step
                    continue
                if text.startswith(quote, index):
                    masked.append(quote if depth == 0 else cls.MASK * len(quote))
                    index += len(quote)
                    quote = ""
                    continue
                masked.append(cls.MASK)
                index += 1
                continue
            if character in {'"', "'"}:
                quote = (
                    character * 3
                    if text.startswith(character * 3, index)
                    else character
                )
                masked.append(quote if depth == 0 else cls.MASK * len(quote))
                index += len(quote)
                continue
            if character in "([{":
                masked.append(character if depth == 0 else cls.MASK)
                depth += 1
            elif character in ")]}":
                depth -= 1
                masked.append(character if depth == 0 else cls.MASK)
            else:
                masked.append(character if depth == 0 else cls.MASK)
            index += 1
        return "".join(masked)

    @staticmethod
    def _assert_comment_index(body: str) -> int | None:
        """Return the offset of the first ``#`` outside string literals.

        Returns:
            The comment offset, or ``None`` when the body has no comment.

        """
        quote = ""
        index = 0
        while index < len(body):
            character = body[index]
            if quote:
                if character == "\\":
                    index += 2
                    continue
                if body.startswith(quote, index):
                    index += len(quote)
                    quote = ""
                    continue
            elif character in {'"', "'"}:
                quote = (
                    character * 3
                    if body.startswith(character * 3, index)
                    else character
                )
                index += len(quote)
                continue
            elif character == "#":
                return index
            index += 1
        return None

    @classmethod
    def _ensure_tm_import(cls, lines: list[str]) -> list[str]:
        """Add the canonical ``tm`` alias to the generated test import.

        Statements come from the rope logical-line boundary, so a parenthesized
        multi-line import is one unit: ``tm`` joins the existing ``tests``
        import, or a new import follows the module's leading docstring and
        import block, never the middle of a statement.

        Returns:
            The lines with ``tm`` imported.

        """
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(
            "".join(lines),
        )
        position = 0
        for index, statement in enumerate(statements):
            text = statement.text
            if statement.indent == 0 and text.startswith("from tests import "):
                names = text.removeprefix("from tests import ")
                if re.search(r"\btm\b", names):
                    return lines
                bound = [
                    name.strip()
                    for name in names.strip().strip("()").split(",")
                    if name.strip()
                ]
                ending = "\n" if lines[statement.end_line - 1].endswith("\n") else ""
                lines[statement.line - 1 : statement.end_line] = [
                    f"from tests import {', '.join([*bound, 'tm'])}{ending}",
                ]
                return lines
            leading_docstring = index == 0 and text.startswith(("'", '"'))
            if statement.indent == 0 and (
                leading_docstring or text.startswith(("from ", "import "))
            ):
                position = statement.end_line
                continue
            break
        if position and not lines[position - 1].endswith("\n"):
            lines[position - 1] = f"{lines[position - 1]}\n"
        lines.insert(position, "from tests import tm\n")
        return lines


__all__: list[str] = [
    "FlextInfraUtilitiesSemanticCutoverTestAssertions",
]
