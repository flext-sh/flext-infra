"""Collect import statements and symbols from Python source code.

This module provides tools for analyzing and extracting import information
from Python AST using libcst visitors.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst


class FlextInfraImportCollector(cst.CSTVisitor):
    """Visit and collect imported modules and symbols from code.

    Tracks top-level module roots and imported symbol names by visiting
    Import and ImportFrom statements in the concrete syntax tree.
    """

    def __init__(self) -> None:
        """Initialize the import collector visitor.

        Sets up empty sets to track imported modules and symbols as they
        are encountered during AST traversal.
        """
        super().__init__()
        self.imported_modules: set[str] = set()
        self.imported_symbols: set[str] = set()

    @override
    def visit_Import(self, node: cst.Import) -> None:
        """Visit Import statement and collect module roots.

        Args:
            node: The Import statement node from the concrete syntax tree.

        """
        for alias in node.names:
            root = self._module_root(alias.name)
            if root:
                self.imported_modules.add(root)

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Visit ImportFrom statement and collect modules and symbols.

        Extracts the imported module root and individual symbols, skipping
        relative imports and import-all statements.

        Args:
            node: The ImportFrom statement node from the concrete syntax tree.

        """
        if node.module is None or node.relative:
            return
        root = self._module_root(node.module)
        if root:
            self.imported_modules.add(root)
        if isinstance(node.names, cst.ImportStar):
            return
        for alias in node.names:
            sym = self._imported_symbol(alias.name)
            if sym:
                self.imported_symbols.add(sym)

    def _module_root(self, node: cst.BaseExpression) -> str | None:
        """Extract the top-level module name from an import expression.

        Handles both simple names (e.g., 'os') and attribute chains
        (e.g., 'package.submodule') by returning the root component.

        Args:
            node: The import expression node to analyze.

        Returns:
            The root module name, or None if extraction fails.

        """
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            parts: MutableSequence[str] = []
            cur: cst.BaseExpression | None = node
            while isinstance(cur, cst.Attribute):
                parts.append(cur.attr.value)
                cur = cur.value
            if isinstance(cur, cst.Name):
                parts.append(cur.value)
                return parts[-1]
        return None

    def _imported_symbol(self, node: cst.BaseExpression) -> str | None:
        """Extract the symbol name from an import alias expression.

        Handles both simple names and attribute access, returning the final
        symbol name being imported.

        Args:
            node: The import alias expression node.

        Returns:
            The symbol name, or None if extraction fails.

        """
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            return node.attr.value
        return None
