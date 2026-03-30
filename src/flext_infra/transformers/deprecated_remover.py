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

    @staticmethod
    def _init_has_deprecation_warning(init_node: cst.FunctionDef) -> bool:
        """Check if an ``__init__`` method body contains a deprecation warn() call."""
        for sub_stmt in init_node.body.body:
            if not isinstance(sub_stmt, cst.SimpleStatementLine):
                continue
            for line in sub_stmt.body:
                if not isinstance(line, cst.Expr) or not isinstance(
                    line.value,
                    cst.Call,
                ):
                    continue
                func = line.value.func
                if isinstance(func, cst.Attribute) and func.attr.value == "warn":
                    return True
        return False

    @staticmethod
    def _class_has_deprecation_warning(node: cst.ClassDef) -> bool:
        """Check if a class has a deprecation warning in its ``__init__``."""
        for stmt in node.body.body:
            if (
                isinstance(stmt, cst.FunctionDef)
                and stmt.name.value == "__init__"
                and FlextInfraRefactorDeprecatedRemover._init_has_deprecation_warning(
                    stmt,
                )
            ):
                return True
        return False

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
        if self._class_has_deprecation_warning(original_node):
            self._record_change(f"Removed deprecated class: {class_name}")
            return cst.RemovalSentinel.REMOVE
        return updated_node
