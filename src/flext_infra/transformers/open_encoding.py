"""Add explicit ``encoding="utf-8"`` to ``open()`` calls.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorOpenEncoding(FlextInfraRopeTransformer):
    """Inject ``encoding="utf-8"`` into text-mode ``open()`` calls that omit it."""

    _description = "add encoding to text-mode open() calls"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Add encoding kwarg when missing and mode is text."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, list(self.changes)
        if not isinstance(tree, ast.Module):
            return source, list(self.changes)
        targets = self._find_open_calls(tree)
        if not targets:
            return source, list(self.changes)
        lines = source.splitlines(keepends=True)
        for lineno, col_offset in sorted(targets, reverse=True):
            line_index = lineno - 1
            if line_index >= len(lines):
                continue
            line = lines[line_index]
            # Insert encoding= before the closing parenthesis on this line.
            close = line.rfind(")", col_offset)
            if close == -1:
                continue
            lines[line_index] = f'{line[:close]}, encoding="utf-8"){line[close + 1 :]}'
            self._record_change('Added encoding="utf-8" to open() call')
        return "".join(lines), list(self.changes)

    @staticmethod
    def _find_open_calls(tree: ast.Module) -> list[tuple[int, int]]:
        """Return (lineno, col_offset) for text-mode open calls missing encoding."""
        targets: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_open = False
            if isinstance(func, ast.Name) and func.id == "open":
                is_open = True
            elif (
                isinstance(func, ast.Attribute)
                and func.attr == "open"
                and isinstance(func.value, ast.Call)
            ):
                is_open = True
            if not is_open:
                continue
            if any(kw.arg == "encoding" for kw in node.keywords):
                continue
            if _is_binary_mode(node.args):
                continue
            targets.append((node.lineno, node.col_offset))
        return targets


def _is_binary_mode(args: list[ast.expr]) -> bool:
    """Return True when any positional mode argument is a binary-mode string literal."""
    for arg in args[:2]:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "b" in arg.value:
            return True
    return False


__all__: list[str] = ["FlextInfraRefactorOpenEncoding"]
