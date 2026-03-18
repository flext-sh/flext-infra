"""Lazy import fixer transformer for legacy compatibility cleanup."""

from __future__ import annotations

from collections.abc import Callable
from typing import override

import libcst as cst

from flext_infra.transformers.import_insertion import (
    FlextInfraTransformerImportInsertion,
)


class FlextInfraRefactorLazyImportFixer(cst.CSTTransformer):
    """Hoist function-local imports to module top while preserving ordering."""

    def __init__(self, on_change: Callable[[str], None] | None = None) -> None:
        """Initialize lazy import collector and emitted change sink."""
        self._on_change = on_change
        self.changes: list[str] = []
        self.hoisted_imports: list[cst.SimpleStatementLine] = []

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        """Extract imports from function body and keep other statements."""
        if not isinstance(updated_node.body, cst.IndentedBlock):
            return updated_node
        new_function_body: list[cst.BaseStatement] = []
        for stmt in updated_node.body.body:
            if (
                isinstance(stmt, cst.SimpleStatementLine)
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], (cst.Import, cst.ImportFrom))
            ):
                self.hoisted_imports.append(stmt)
                message = f"Hoisted lazy import in function {original_node.name.value}"
                self.changes.append(message)
                if self._on_change is not None:
                    self._on_change(message)
                continue
            new_function_body.append(stmt)
        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=new_function_body),
        )

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        """Insert hoisted imports after docstring and __future__ imports."""
        del original_node
        if not self.hoisted_imports:
            return updated_node
        existing_import_codes: set[str] = set()
        for stmt in updated_node.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            if len(stmt.body) != 1:
                continue
            if isinstance(stmt.body[0], (cst.Import, cst.ImportFrom)):
                existing_import_codes.add(cst.Module(body=[stmt]).code)
        unique_hoisted: list[cst.SimpleStatementLine] = []
        for stmt in self.hoisted_imports:
            stmt_code = cst.Module(body=[stmt]).code
            if stmt_code in existing_import_codes:
                continue
            existing_import_codes.add(stmt_code)
            unique_hoisted.append(stmt)
        if not unique_hoisted:
            return updated_node
        body = list(updated_node.body)
        insert_idx = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
            body,
        )
        new_body = body[:insert_idx] + unique_hoisted + body[insert_idx:]
        return updated_node.with_changes(body=new_body)
