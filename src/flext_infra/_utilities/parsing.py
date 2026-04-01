"""Parsing utilities for infrastructure code analysis."""

from __future__ import annotations

import ast
from collections.abc import MutableSequence, Sequence
from pathlib import Path

import libcst as cst

from flext_infra import c, t


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
            return ast.parse(file_path.read_text(encoding=c.Infra.Encoding.DEFAULT))
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
            return cst.parse_module(
                file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            )
        except (OSError, cst.ParserSyntaxError):
            return None

    @staticmethod
    def cst_module_to_str(module: cst.BaseExpression | None) -> str:
        """Convert a CST module expression to its dotted string representation.

        Handles ``Name`` and ``Attribute`` nodes using iterative traversal.

        Args:
            module: A libcst expression or None to convert to string.

        Returns:
            Dotted module name (e.g., 'package.submodule'), or empty string.

        """
        if module is None:
            return ""
        if isinstance(module, cst.Name):
            return module.value
        if isinstance(module, cst.Attribute):
            parts: MutableSequence[str] = []
            current: cst.BaseExpression = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            return ".".join(reversed(parts))
        return ""

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
    def cst_is_type_checking_test(node: cst.BaseExpression) -> bool:
        """Check if a CST expression is 'TYPE_CHECKING'."""
        return isinstance(node, cst.Name) and node.value == "TYPE_CHECKING"

    @staticmethod
    def cst_collect_bound_names(node: cst.ImportFrom) -> t.Infra.StrSet:
        """Collect all bound names from a CST ImportFrom node."""
        if isinstance(node.names, cst.ImportStar):
            return set()
        names: t.Infra.StrSet = set()
        for item in node.names:
            bound = FlextInfraUtilitiesParsing.cst_asname_to_local(item.asname)
            if not bound and isinstance(item.name, cst.Name):
                bound = item.name.value
            if bound:
                names.add(bound)
        return names

    @staticmethod
    def cst_import_line(module_name: str, aliases: t.StrSequence) -> cst.BaseStatement:
        """Construct a CST ImportFrom statement line."""
        return cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=FlextInfraUtilitiesParsing.module_expr_from_dotted(
                        module_name,
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
    def index_after_docstring_and_future_imports(
        body: Sequence[cst.BaseStatement],
    ) -> int:
        """Return insertion index after module docstring and future imports."""
        insert_idx = 0
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and (len(body[0].body) == 1)
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            insert_idx = 1
        while insert_idx < len(body):
            stmt = body[insert_idx]
            if not isinstance(stmt, cst.SimpleStatementLine):
                break
            if len(stmt.body) != 1:
                break
            only_stmt = stmt.body[0]
            if (
                isinstance(only_stmt, cst.ImportFrom)
                and isinstance(only_stmt.module, cst.Name)
                and (only_stmt.module.value == "__future__")
            ):
                insert_idx += 1
                continue
            break
        return insert_idx

    @staticmethod
    def cst_is_module_toplevel(file_path: Path) -> bool:
        """Determine if a file is at the package root level (Facade level)."""
        parts = file_path.resolve().parts
        try:
            src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            # Package root files are (..., 'src', 'package_name', 'file.py')
            return len(parts) == src_idx + 3
        except ValueError:
            # Fallback: if 'src' not found, check if it's in a package root
            return (file_path.parent / c.Infra.Files.INIT_PY).is_file() and not (
                file_path.parent.parent / c.Infra.Files.INIT_PY
            ).is_file()

    @staticmethod
    def cst_extract_base_name(base_expr: cst.BaseExpression) -> str:
        """Extract the base class name from a CST base expression.

        Recursively unwraps ``Subscript`` (e.g. ``Generic[T]``), handles
        ``Name`` and ``Attribute`` nodes.
        """
        if isinstance(base_expr, cst.Subscript):
            return FlextInfraUtilitiesParsing.cst_extract_base_name(base_expr.value)
        if isinstance(base_expr, cst.Name):
            return base_expr.value
        if isinstance(base_expr, cst.Attribute):
            dotted_name = FlextInfraUtilitiesParsing.cst_module_to_str(base_expr)
            if "." in dotted_name:
                return dotted_name.rsplit(".", maxsplit=1)[1]
            return dotted_name
        return ""

    @staticmethod
    def ast_extract_base_name(base_expr: ast.expr) -> str:
        """Extract the base class name from an AST base expression.

        Recursively unwraps ``Subscript`` (e.g. ``Generic[T]``), handles
        ``Name`` and ``Attribute`` nodes.
        """
        if isinstance(base_expr, ast.Name):
            return base_expr.id
        if isinstance(base_expr, ast.Attribute):
            return base_expr.attr
        if isinstance(base_expr, ast.Subscript):
            return FlextInfraUtilitiesParsing.ast_extract_base_name(base_expr.value)
        return ""

    @staticmethod
    def cst_root_name(expr: cst.BaseExpression) -> str:
        """Extract the leftmost root name from a CST expression."""
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return FlextInfraUtilitiesParsing.cst_root_name(expr.value)
        if isinstance(expr, cst.Call):
            return FlextInfraUtilitiesParsing.cst_root_name(expr.func)
        return ""

    @staticmethod
    def _import_already_exists(
        module: cst.Module, stmt: cst.SimpleStatementLine
    ) -> bool:
        """Check if the import statement already exists in the module."""
        return any(
            isinstance(s, cst.SimpleStatementLine) and s.deep_equals(stmt)
            for s in module.body
        )

    @staticmethod
    def insert_import_statement(source: str, import_stmt: str) -> str:
        """Insert an import statement into source at the correct position."""
        normalized_import = import_stmt.strip()
        if not normalized_import:
            return source
        module = FlextInfraUtilitiesParsing.parse_cst_from_source(source)
        if module is None:
            return source
        try:
            parsed_stmt = cst.parse_statement(f"{normalized_import}\n")
        except cst.ParserSyntaxError:
            return source
        if not isinstance(parsed_stmt, cst.SimpleStatementLine):
            return source
        if FlextInfraUtilitiesParsing._import_already_exists(
            module,
            parsed_stmt,
        ):
            return source
        insert_idx = 0
        for idx, body_stmt in enumerate(module.body):
            if not isinstance(body_stmt, cst.SimpleStatementLine):
                break
            is_docstring = (
                len(body_stmt.body) == 1
                and isinstance(body_stmt.body[0], cst.Expr)
                and isinstance(
                    body_stmt.body[0].value,
                    (cst.SimpleString, cst.ConcatenatedString),
                )
            )
            is_import = any(
                isinstance(s, (cst.Import, cst.ImportFrom)) for s in body_stmt.body
            )
            if is_docstring or is_import:
                insert_idx = idx + 1
                continue
            break
        new_body = [*module.body[:insert_idx], parsed_stmt, *module.body[insert_idx:]]
        return module.with_changes(body=new_body).code


__all__ = ["FlextInfraUtilitiesParsing"]
