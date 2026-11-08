"""Promoted-command header rendering: one command into its PEP 723 block.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesPromotedHeader:
    """Render the canonical ``[tool.flext.command]`` script block.

    Ruff exempts a PEP 723 ``script`` block from commented-out-code but still
    measures its lines, so every rendered line fits the width the caller reads
    from the tooling configuration. TOML text comes from the TOML owner; this
    class only lays the items out.
    """

    @classmethod
    def promoted_render_header(cls, command: t.JsonMapping, *, width: int) -> str:
        """Render ``command`` as one ``script`` block whose lines fit ``width``.

        Keys keep their declared order inside each table. Sub-tables and arrays
        of tables follow the plain keys, as TOML 1.0 requires, so ``params``
        become ``[[tool.flext.command.params]]`` tables: an inline table cannot
        span lines. A string that does not fit its line becomes a multi-line
        basic string continued by line-ending backslashes; an array that does
        not fit holds one element per line.

        Returns:
            The block text, without a trailing newline.

        """
        table = c.Infra.PROMOTED_HEADER_TABLE
        return "\n".join((
            f"{c.Infra.SCRIPT_METADATA_START}{c.Infra.SCRIPT_METADATA_TYPE}",
            cls._promoted_header_name(table, "[", "]"),
            *cls._promoted_header_body(table, command, width),
            c.Infra.SCRIPT_METADATA_END,
        ))

    @classmethod
    def _promoted_header_body(
        cls,
        path: Sequence[str],
        table: t.JsonMapping,
        width: int,
    ) -> list[str]:
        """Render one table's plain keys, then its sub-tables and table arrays.

        Returns:
            The table's block lines after its header line.

        """
        lines: list[str] = []
        nested: list[str] = []
        for key, value in table.items():
            child = (*path, key)
            items = value if isinstance(value, list) else []
            tables = [item for item in items if isinstance(item, Mapping)]
            if isinstance(value, Mapping):
                nested.append(cls._promoted_header_name(child, "[", "]"))
                nested.extend(cls._promoted_header_body(child, value, width))
            elif tables and len(tables) == len(items):
                for item in tables:
                    nested.append(cls._promoted_header_name(child, "[[", "]]"))
                    nested.extend(cls._promoted_header_body(child, item, width))
            else:
                head = (
                    f"{c.Infra.SCRIPT_METADATA_LINE_PREFIX}"
                    f"{cls._promoted_header_key(key)} = "
                )
                lines.extend(cls._promoted_header_value(head, value, "", width))
        return [*lines, *nested]

    @classmethod
    def _promoted_header_name(
        cls,
        path: Sequence[str],
        opening: str,
        closing: str,
    ) -> str:
        """Render one table or array-of-tables header line.

        Returns:
            The header line.

        """
        name = ".".join(cls._promoted_header_key(part) for part in path)
        return f"{c.Infra.SCRIPT_METADATA_LINE_PREFIX}{opening}{name}{closing}"

    @classmethod
    def _promoted_header_value(
        cls,
        head: str,
        value: t.JsonValue,
        tail: str,
        width: int,
    ) -> list[str]:
        """Render one value after ``head``, closing its last line with ``tail``.

        Nested lines indent one level past the margin ``head`` starts with.

        Returns:
            The value's block lines.

        Raises:
            ValueError: If a table sits inside an array of values, where only a
                single-line inline table could hold it.

        """
        if isinstance(value, str):
            return cls._promoted_header_string(head, value, tail, width)
        if isinstance(value, Mapping) or (
            isinstance(value, list) and any(isinstance(item, Mapping) for item in value)
        ):
            msg = f"promoted header cannot render a table inside an array: {head}"
            raise ValueError(msg)
        inline = f"{head}{u.Cli.toml_item_from_json_value(value).as_string()}{tail}"
        if not isinstance(value, list) or not value or len(inline) <= width:
            return [inline]
        margin = cls._promoted_header_margin(head)
        return [
            f"{head}[",
            *(
                line
                for item in value
                for line in cls._promoted_header_value(
                    f"{margin}{c.Infra.PROMOTED_HEADER_INDENT}", item, ",", width
                )
            ),
            f"{margin}]{tail}",
        ]

    @classmethod
    def _promoted_header_string(
        cls,
        head: str,
        value: str,
        tail: str,
        width: int,
    ) -> list[str]:
        """Render one string inline or as a continued multi-line basic string.

        A line-ending backslash trims the newline and the indentation after
        it, so each continuation line starts with the first non-space
        character of its piece and the value is preserved exactly.

        Returns:
            The string's block lines.

        """
        inline = f"{head}{cls._promoted_header_escaped(value, quoted=True)}{tail}"
        if len(inline) <= width:
            return [inline]
        quote = '"' * c.Infra.TOML_MULTILINE_QUOTE_LENGTH
        continuation = (
            f"{cls._promoted_header_margin(head)}{c.Infra.PROMOTED_HEADER_INDENT}"
        )
        # The last line closes with the quotes and the tail; every other line
        # ends with one backslash, so reserving the longer end fits both.
        reserve = len(quote) + len(tail)
        pieces = cls._promoted_header_pieces(
            value,
            first=width - len(head) - len(quote) - reserve,
            rest=width - len(continuation) - reserve,
        )
        last = len(pieces) - 1
        return [
            (head + quote if index == 0 else continuation)
            + cls._promoted_header_escaped(piece, quoted=False)
            + (quote + tail if index == last else "\\")
            for index, piece in enumerate(pieces)
        ]

    @staticmethod
    def _promoted_header_margin(head: str) -> str:
        """Return the comment marker and indentation ``head`` starts with.

        Returns:
            The line margin nested lines extend.

        """
        prefix = c.Infra.SCRIPT_METADATA_LINE_PREFIX
        content = head.removeprefix(prefix)
        return f"{prefix}{content[: len(content) - len(content.lstrip(' '))]}"

    @classmethod
    def _promoted_header_pieces(cls, value: str, *, first: int, rest: int) -> list[str]:
        """Split ``value`` into pieces whose escaped text fits each line.

        Pieces break after spaces; a word longer than its line breaks inside
        the word. No piece after the first starts with a space, because the
        line-ending backslash before it would trim that space.

        Returns:
            The pieces in order; their concatenation is ``value``.

        """
        pieces: list[str] = []
        current = ""
        for token in c.Infra.PROMOTED_HEADER_WORD_RE.findall(value):
            pending = str(token)
            while pending:
                capacity = rest if pieces else first
                if cls._promoted_header_fits(current + pending, capacity):
                    current += pending
                    break
                if current:
                    pieces.append(current)
                    current = ""
                    continue
                word = len(pending.rstrip(" "))
                cut = next(
                    (
                        index
                        for index in range(word - 1, 0, -1)
                        if cls._promoted_header_fits(pending[:index], capacity)
                    ),
                    len(pending),
                )
                pieces.append(pending[:cut])
                pending = pending[cut:]
        return [*pieces, current] if current or not pieces else pieces

    @classmethod
    def _promoted_header_fits(cls, text: str, capacity: int) -> bool:
        """Return whether ``text`` escaped fits ``capacity`` characters.

        Returns:
            Whether the escaped text fits.

        """
        return len(cls._promoted_header_escaped(text, quoted=False)) <= capacity

    @staticmethod
    def _promoted_header_escaped(text: str, *, quoted: bool) -> str:
        """Return ``text`` as a TOML basic string, with or without its quotes.

        Escaping is per character, so the pieces of one value escape
        independently and their concatenation escapes the whole value.

        Returns:
            The escaped text.

        """
        rendered = u.Cli.toml_item_from_json_value(text).as_string()
        return rendered if quoted else rendered[1:-1]

    @staticmethod
    def _promoted_header_key(key: str) -> str:
        """Return ``key`` bare when TOML admits it, otherwise quoted.

        Returns:
            The TOML key text.

        """
        if c.Infra.TOML_BARE_KEY_RE.fullmatch(key):
            return key
        return u.Cli.toml_item_from_json_value(key).as_string()


__all__: list[str] = ["FlextInfraUtilitiesPromotedHeader"]
