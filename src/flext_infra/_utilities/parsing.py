"""Parsing utilities for infrastructure code analysis."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from pathlib import Path

import libcst as cst


class FlextInfraUtilitiesParsing:
    """Static parsing utilities for Python source analysis."""

    @staticmethod
    def parse_ast_from_source(source: str) -> ast.Module | None:
        """Parse source text into an AST module."""
        try:
            return ast.parse(source)
        except SyntaxError:
            return None

    @staticmethod
    def parse_module_ast(file_path: Path) -> ast.Module | None:
        """Parse a Python file into an AST module."""
        try:
            return ast.parse(file_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return None

    @staticmethod
    def parse_cst_from_source(source: str) -> cst.Module | None:
        """Parse source text into a CST module."""
        try:
            return cst.parse_module(source)
        except cst.ParserSyntaxError:
            return None

    @staticmethod
    def parse_module_cst(file_path: Path) -> cst.Module | None:
        """Parse a Python file into a CST module."""
        try:
            return cst.parse_module(file_path.read_text(encoding="utf-8"))
        except (OSError, cst.ParserSyntaxError):
            return None

    @staticmethod
    def cst_module_name(node: cst.CSTNode | None) -> str:
        """Extract dotted module name from a CST node."""
        if isinstance(node, cst.ImportFrom):
            return FlextInfraUtilitiesParsing.cst_module_name(node.module)
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            base = FlextInfraUtilitiesParsing.cst_module_name(node.value)
            return f"{base}.{node.attr.value}" if base else node.attr.value
        return ""

    @staticmethod
    def cst_root_name(expr: cst.BaseExpression) -> str:
        """Extract the root (leftmost) name from a CST expression.

        Handles ``Name``, ``Attribute``, and ``Call`` nodes to find the
        base identifier.

        Args:
            expr: CST expression node.

        Returns:
            Root name string, or empty string for unsupported nodes.

        """
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return FlextInfraUtilitiesParsing.cst_root_name(expr.value)
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesParsing.cst_root_name(expr.func)
        return ""

    @staticmethod
    def cst_is_type_checking_test(node: cst.BaseExpression) -> bool:
        """Check if a CST expression is 'TYPE_CHECKING'."""
        return isinstance(node, cst.Name) and node.value == "TYPE_CHECKING"

    @staticmethod
    def cst_collect_bound_names(node: cst.ImportFrom) -> set[str]:
        """Collect all bound names from a CST ImportFrom node."""
        if isinstance(node.names, cst.ImportStar):
            return set()
        names: set[str] = set()
        for item in node.names:
            bound = FlextInfraUtilitiesParsing.cst_asname_to_local(item.asname)
            if not bound and isinstance(item.name, cst.Name):
                bound = item.name.value
            if bound:
                names.add(bound)
        return names

    @staticmethod
    def cst_import_line(module_name: str, aliases: Sequence[str]) -> cst.BaseStatement:
        """Construct a CST ImportFrom statement line."""
        return cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=FlextInfraUtilitiesParsing.module_expr_from_dotted(
                        module_name
                    ),
                    names=tuple(
                        cst.ImportAlias(name=cst.Name(alias))
                        for alias in sorted(aliases)
                    ),
                ),
            ],
        )

    @staticmethod
    def module_expr_from_dotted(dotted: str) -> cst.Name | cst.Attribute:
        """Build a CST expression tree from a dotted name string."""
        parts = [part for part in dotted.split(".") if part]
        if not parts:
            return cst.Name("")
        expr: cst.Name | cst.Attribute = cst.Name(parts[0])
        for part in parts[1:]:
            expr = cst.Attribute(value=expr, attr=cst.Name(part))
        return expr

    @staticmethod
    def extract_string_literal(node: cst.BaseExpression) -> str:
        """Extract a string value from a CST SimpleString node."""
        if isinstance(node, cst.SimpleString):
            val = node.evaluated_value
            return val if isinstance(val, str) else ""
        return ""

    @staticmethod
    def cst_asname_to_local(asname: cst.AsName | None) -> str | None:
        """Extract the local alias name from a CST AsName node."""
        if asname and isinstance(asname.name, cst.Name):
            return asname.name.value
        return None

    @staticmethod
    def cst_imported_name(imported_alias: cst.ImportAlias) -> str | None:
        """Extract the imported name from a CST ImportAlias node."""
        if imported_alias.asname is None and isinstance(imported_alias.name, cst.Name):
            return imported_alias.name.value
        return None

    @staticmethod
    def cst_is_module_toplevel(file_path: Path) -> bool:
        """Determine if a file is at the package root level (Facade level)."""
        parts = file_path.resolve().parts
        try:
            src_idx = parts.index("src")
            # Package root files are (..., 'src', 'package_name', 'file.py')
            return len(parts) == src_idx + 3
        except ValueError:
            # Fallback: if 'src' not found, check if it's in a package root
            return (file_path.parent / "__init__.py").is_file() and not (
                file_path.parent.parent / "__init__.py"
            ).is_file()


__all__ = ["FlextInfraUtilitiesParsing"]
