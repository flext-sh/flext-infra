"""Import insertion helpers for LibCST module rewrites."""

from __future__ import annotations

from collections.abc import Sequence

import libcst as cst


class FlextInfraTransformerImportInsertion:
    """Helper methods for safe import insertion positions."""

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


__all__ = ["FlextInfraTransformerImportInsertion"]
