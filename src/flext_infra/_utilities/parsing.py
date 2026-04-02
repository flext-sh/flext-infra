"""Parsing utilities for infrastructure code analysis.

All AST access is deferred to function bodies via ``import ast`` to keep the
module-level namespace free of ast/cst imports.
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from pathlib import Path

from flext_infra import c


class FlextInfraUtilitiesParsing:
    """Static parsing utilities for Python source analysis."""

    _DOCSTRING_QUOTES = ('"""', "'''")
    _SINGLE_LINE_DOCSTRING_QUOTE_COUNT = 2

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
            return ast.parse(
                file_path.read_text(encoding=c.Infra.Encoding.DEFAULT),
            )
        except (OSError, SyntaxError):
            return None

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
            return FlextInfraUtilitiesParsing.ast_extract_base_name(
                base_expr.value,
            )
        return ""

    @staticmethod
    def is_module_toplevel(file_path: Path) -> bool:
        """Determine if a file is at the package root level (Facade level)."""
        parts = file_path.resolve().parts
        try:
            src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            return len(parts) == src_idx + 3
        except ValueError:
            return (file_path.parent / c.Infra.Files.INIT_PY).is_file() and not (
                file_path.parent.parent / c.Infra.Files.INIT_PY
            ).is_file()

    @staticmethod
    def insert_import_statement(source: str, import_stmt: str) -> str:
        """Insert an import statement into source at the correct position.

        Uses regex-based line scanning instead of CST parsing.
        """
        normalized_import = import_stmt.strip()
        if not normalized_import:
            return source
        for line in source.splitlines():
            if line.strip() == normalized_import:
                return source
        lines = source.splitlines(keepends=True)
        insert_idx = FlextInfraUtilitiesParsing._find_import_insert_position(lines)
        lines.insert(insert_idx, normalized_import + "\n")
        return "".join(lines)

    @staticmethod
    def find_import_insert_position(
        lines: Sequence[str],
        *,
        past_existing: bool = True,
    ) -> int:
        """Find line index suitable for inserting new imports.

        Delegates to module-level ``_find_import_insert_position``.
        """
        return FlextInfraUtilitiesParsing._find_import_insert_position(
            lines,
            past_existing=past_existing,
        )

    @staticmethod
    def index_after_docstring_and_future_imports(
        lines: Sequence[str],
    ) -> int:
        """Return insertion index after module docstring and future imports.

        Operates on source lines instead of CST body nodes.
        """
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if in_docstring:
                insert_idx = i + 1
                if stripped.endswith(FlextInfraUtilitiesParsing._DOCSTRING_QUOTES):
                    in_docstring = False
                continue
            if i == 0 and c.Infra.SourceCode.DOCSTRING_RE.match(stripped):
                insert_idx = i + 1
                if not (
                    stripped.count('"""')
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                    or stripped.count("'''")
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                ):
                    in_docstring = True
                continue
            if c.Infra.SourceCode.FUTURE_IMPORT_RE.match(stripped):
                insert_idx = i + 1
                continue
            if stripped and not stripped.startswith("#"):
                break
            insert_idx = i + 1
        return insert_idx

    @staticmethod
    def _find_import_insert_position(
        lines: Sequence[str],
        *,
        past_existing: bool = True,
    ) -> int:
        """Find line index suitable for inserting new imports."""
        idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                idx = i + 1
                continue
            if stripped.startswith(('"""', "'''")):
                idx = i + 1
                continue
            if stripped.startswith("from __future__"):
                idx = i + 1
                continue
            if past_existing and c.Infra.SourceCode.IMPORT_LINE_RE.match(line):
                idx = i + 1
                continue
            break
        return idx

    # ── Generic AST helpers (shared across validate/refactor/codegen) ──

    @staticmethod
    def ast_expr_name(node: ast.expr) -> str:
        """Extract the simple name from any AST expression node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Subscript):
            return FlextInfraUtilitiesParsing.ast_expr_name(node.value)
        return ""

    @staticmethod
    def ast_expr_contains(node: ast.expr | None, name: str) -> bool:
        """Check if an AST expression tree references a given name."""
        if node is None:
            return False
        return FlextInfraUtilitiesParsing.ast_expr_name(node) == name or (
            hasattr(node, "value")
            and FlextInfraUtilitiesParsing.ast_expr_contains(
                getattr(node, "value", None),
                name,
            )
        )

    @staticmethod
    def ast_assign_target_name(node: ast.stmt) -> str:
        """Extract the target name from Assign or AnnAssign."""
        if isinstance(node, ast.Assign) and node.targets:
            first = node.targets[0]
            return first.id if isinstance(first, ast.Name) else ""
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return node.target.id
        return ""

    @staticmethod
    def derive_class_prefix(project_root: Path) -> str:
        """Derive PascalCase class prefix from first package under src/."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                return "".join(part.title() for part in child.name.split("_"))
        return ""

    @staticmethod
    def is_ast_docstring(node: ast.stmt) -> bool:
        """Check if a statement is a module-level docstring."""
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )

    @staticmethod
    def looks_like_facade_file(*, file_path: Path, source: str) -> bool:
        """Check if a file looks like a namespace facade (e.g. models.py with ``m = FlextXxxModels``)."""
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return False
        return any(
            line.strip().startswith(f"{family} = ") for line in source.splitlines()
        )

    @staticmethod
    def find_import_line(*, lines: Sequence[str], module_name: str) -> int:
        """Find the 1-based line number of ``from <module_name> import ...``."""
        prefix = f"from {module_name} import "
        for index, line in enumerate(lines, start=1):
            if line.strip().startswith(prefix):
                return index
        return 1


__all__ = ["FlextInfraUtilitiesParsing"]
