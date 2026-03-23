from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst

from flext_infra import m


class TopLevelClassCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self._depth = 0
        self.classes: MutableSequence[m.Infra.ClassOccurrence] = []

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        is_top_level = self._depth == 0
        self.classes.append(
            m.Infra.ClassOccurrence(
                name=node.name.value,
                line=0,
                is_top_level=is_top_level,
            ),
        )
        self._depth += 1

    @override
    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        _ = original_node
        self._depth -= 1


__all__ = ["TopLevelClassCollector"]
