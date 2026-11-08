"""MkDocs list indentation: the repair rumdl reports but withholds.

Python-Markdown, the MkDocs renderer, reads the blocks of a list item four
columns per nesting level, whatever the marker width; CommonMark reads them at
the marker's content column, three columns after ``1.``. Under the MkDocs
flavor rumdl reports both gaps: MD007 for a bullet nested at an ordered item's
content column, MD077 for loose item content below the MkDocs column. It
withholds either fix whenever moving the reported line alone would leave the
rest of its block behind.

Each residual finding selects one line and its block moves as a whole to the
column of the item that owns it: a nested item with every line it owns, a
fence with its body, a paragraph or quote line by itself. A line rumdl does
not report never moves, so a repaired document is a fixed point.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from flext_infra import c, u


class FlextInfraMarkdownListIndent:
    """Move the list blocks of MkDocs findings to their owner's column."""

    @staticmethod
    def _indent(line: str) -> int:
        """Count the spaces that open ``line``.

        Returns:
            The leading space count.

        """
        return len(line) - len(line.lstrip(" "))

    @staticmethod
    def _item(line: str) -> tuple[int, int, bool] | None:
        """Read the list item a line opens, with CommonMark's content column.

        Returns:
            The marker column, the content column and whether the item is
            ordered, or ``None`` when the line opens no item.

        """
        match = c.Infra.MARKDOWN_LIST_MARKER_RE.fullmatch(line.rstrip("\r"))
        if match is None:
            return None
        end = match.end("marker")
        gap = len(match.group("gap"))
        if match.group("text") and not gap:
            return None
        content = (
            end + gap
            if match.group("text") and gap <= c.Infra.MARKDOWN_LIST_MAX_MARKER_GAP
            else end + 1
        )
        return match.end("indent"), content, match.group("marker")[-1] in ".)"

    @classmethod
    def _owner(
        cls,
        lines: Sequence[str],
        code: Collection[int],
        index: int,
    ) -> tuple[int, int, bool] | None:
        """Find the nearest item above whose content column ``index`` reaches.

        Returns:
            The owner's marker column, content column and ordered flag.

        """
        column = cls._indent(lines[index])
        for above in range(index - 1, -1, -1):
            item = None if above in code else cls._item(lines[above])
            if item is not None and item[1] <= column:
                return item
        return None

    @classmethod
    def _item_lines(
        cls,
        lines: Sequence[str],
        code: Collection[int],
        index: int,
        content: int,
    ) -> range:
        """Collect the item opened at ``index`` with every line it owns.

        A line belongs to the item when it sits at the item's content column
        or past it, when it is code of a fence the item opened, or when it
        continues the item's paragraph lazily.

        Returns:
            The item's line range.

        """
        last = index
        paragraph = True
        for below in range(index + 1, len(lines)):
            line = lines[below]
            if below in code:
                last, paragraph = below, False
            elif not line.strip():
                paragraph = False
            elif cls._indent(line) >= content or (
                paragraph
                and cls._item(line) is None
                and c.Infra.MARKDOWN_PARAGRAPH_INTERRUPTION_RE.match(line) is None
            ):
                last, paragraph = below, True
            else:
                break
        return range(index, last + 1)

    @classmethod
    def _move(
        cls,
        lines: Sequence[str],
        code: Collection[int],
        fences: Mapping[int, int],
        *,
        rule: str,
        index: int,
    ) -> tuple[int, range] | None:
        """Plan the move of the block a reported line opens.

        A nested-item line is a bullet under an ordered item: it moves with
        every line it owns to the ordered marker plus four. An item-content
        line moves to four columns per level of its owner, a fence with its
        body.

        Returns:
            The columns to add and the block's lines, or ``None`` when the
            line has no ordered owner to move under or already sits there.

        """
        owner = cls._owner(lines, code, index)
        if owner is None:
            return None
        marker, content, ordered = owner
        width = c.Infra.MARKDOWN_MKDOCS_LIST_INDENT
        if rule == c.Infra.MARKDOWN_MKDOCS_NESTED_ITEM_RULE:
            item = cls._item(lines[index])
            if item is None or not ordered:
                return None
            target = marker + width
            block = cls._item_lines(lines, code, index, item[1])
        else:
            target = max(content, width * (marker // width + 1))
            block = range(index, fences.get(index, index + 1))
        delta = target - cls._indent(lines[index])
        return (delta, block) if delta > 0 else None

    @classmethod
    def reindent(cls, text: str, rule: str, reported: Collection[int]) -> str:
        """Move the block of each line ``rule`` reports to the MkDocs column.

        A line inside a block already moved keeps that move; fence code keeps
        its whitespace-only lines aligned with the fence.

        Returns:
            ``text`` with every reported block re-indented.

        """
        lines = text.split("\n")
        fences = {
            fence.opening_line - 1: fence.closing_line
            for fence in u.Cli.markdown_fences(text)
        }
        code = frozenset(
            index
            for opening, closing in fences.items()
            for index in range(opening + 1, closing)
        )
        shifts: dict[int, int] = {}
        for index in sorted(line - 1 for line in reported):
            move = (
                None
                if index in shifts or index in code
                else cls._move(lines, code, fences, rule=rule, index=index)
            )
            if move is None:
                continue
            delta, block = move
            base = cls._indent(lines[index])
            shifts.update(
                (moved, delta)
                for moved in block
                if moved not in shifts
                and (
                    lines[moved].strip()
                    or (moved in code and len(lines[moved].rstrip("\r")) > base)
                )
            )
        return "\n".join(
            " " * shifts.get(index, 0) + line for index, line in enumerate(lines)
        )


__all__: list[str] = ["FlextInfraMarkdownListIndent"]
