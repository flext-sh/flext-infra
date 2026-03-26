"""Base mixin for CST transformers with change-tracking boilerplate."""

from __future__ import annotations

from collections.abc import MutableSequence

import libcst as cst

from flext_infra import t


class FlextInfraChangeTrackingTransformer(cst.CSTTransformer):
    """Mixin providing ``changes`` list and ``_record_change`` with optional callback."""

    def __init__(self, *, on_change: t.Infra.ChangeCallback = None) -> None:
        """Initialize change-tracking state."""
        super().__init__()
        self._on_change = on_change
        self.changes: MutableSequence[str] = []

    def _record_change(self, message: str) -> None:
        self.changes.append(message)
        if self._on_change is not None:
            self._on_change(message)

    @staticmethod
    def is_pass_statement(statement: cst.BaseStatement) -> bool:
        """Check whether a statement is a lone ``pass``."""
        if not isinstance(statement, cst.SimpleStatementLine):
            return False
        return len(statement.body) == 1 and isinstance(statement.body[0], cst.Pass)


__all__ = ["FlextInfraChangeTrackingTransformer"]
