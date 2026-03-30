"""Deprecated class remover transformer for legacy cleanup."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst

from flext_infra import FlextInfraChangeTrackingTransformer, t


class FlextInfraRefactorDeprecatedRemover(FlextInfraChangeTrackingTransformer):
    """Remove classes marked as deprecated by name or warning usage."""

    def __init__(
        self,
        changes: MutableSequence[str] | None = None,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize change sinks used by the transformer."""
        super().__init__(on_change=on_change)
        if changes is not None:
            self.changes = changes

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef | cst.RemovalSentinel:
        """Remove deprecated classes based on naming and __init__ warnings."""
        class_name = original_node.name.value
        if "deprecated" in class_name.lower():
            self._record_change(f"Removed deprecated class: {class_name}")
            return cst.RemovalSentinel.REMOVE
        for stmt in original_node.body.body:
            if isinstance(stmt, cst.FunctionDef) and stmt.name.value == "__init__":
                for sub_stmt in stmt.body.body:
                    if isinstance(sub_stmt, cst.SimpleStatementLine):
                        for line in sub_stmt.body:
                            if isinstance(line, cst.Expr) and isinstance(
                                line.value,
                                cst.Call,
                            ):
                                func = line.value.func
                                if (
                                    isinstance(func, cst.Attribute)
                                    and func.attr.value == "warn"
                                ):
                                    self._record_change(
                                        f"Removed deprecated class: {class_name}",
                                    )
                                    return cst.RemovalSentinel.REMOVE
        return updated_node
