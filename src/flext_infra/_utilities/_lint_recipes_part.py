"""Positioning primitives for the lint repair recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c


class FlextInfraUtilitiesLintRecipesPart:
    """Source-position primitives composed into the lint repair recipes."""

    @staticmethod
    def _utf8_chars(line: str, col_offset: int) -> int:
        """Return the character index of a UTF-8 AST column on ``line``.

        Returns:
            The character index of a UTF-8 AST column on ``line``.

        """
        return len(
            line.encode(c.DEFAULT_ENCODING)[:col_offset].decode(
                c.DEFAULT_ENCODING,
            ),
        )

    @staticmethod
    def _defined_at(
        tree: ast.Module,
        line: int,
        path: Path,
    ) -> ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef:
        """Return the class or function defined at ``line``.

        An inline body is a legal definition. The summary edit expands it.

        Returns:
            The class or function defined at ``line``.

        Raises:
            ValueError: If no class or function is defined at ``line``.

        """
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
                and node.lineno == line
            ):
                return node
        msg = f"{path}: no class or function is defined at line {line}"
        raise ValueError(msg)

    @staticmethod
    def _enclosing_function(
        tree: ast.Module,
        line: int,
        path: Path,
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        """Return the innermost function whose body spans ``line``.

        Returns:
            The innermost function whose body spans ``line``.

        Raises:
            ValueError: If ``not enclosing``.

        """
        enclosing = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.lineno <= line <= (node.end_lineno or node.lineno)
        ]
        if not enclosing:
            msg = f"{path}: no function encloses line {line}"
            raise ValueError(msg)
        return max(enclosing, key=lambda node: node.lineno)

    @classmethod
    def _documented_at(
        cls,
        tree: ast.Module,
        line: int,
        path: Path,
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        """Return the function whose docstring starts at ``line``.

        Returns:
            The function whose docstring starts at ``line``.

        Raises:
            ValueError: Always.

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                docstring = cls._docstring_expr(node)
                if docstring is not None and docstring.lineno == line:
                    return node
        msg = f"{path}: no function docstring starts at line {line}"
        raise ValueError(msg)
