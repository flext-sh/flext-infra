from __future__ import annotations

from collections.abc import Callable
from typing import override

import libcst as cst


class UnusedModelRemover(cst.CSTTransformer):
    def __init__(
        self,
        *,
        unused_classes: frozenset[str],
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._unused_classes = unused_classes
        self._on_change = on_change
        self.modified: bool = False
        self.changes: list[str] = []
        self._removed_count: int = 0

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef | cst.RemovalSentinel:
        if original_node.name.value in self._unused_classes:
            self._removed_count += 1
            self.modified = True
            self._record_change(
                f"Removed unused model class: {original_node.name.value}",
            )
            return cst.RemovalSentinel.REMOVE
        return updated_node

    def _record_change(self, msg: str) -> None:
        self.changes.append(msg)
        if self._on_change is not None:
            self._on_change(msg)


__all__ = ["UnusedModelRemover"]
