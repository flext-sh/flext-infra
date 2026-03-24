from __future__ import annotations

from typing import override

import libcst as cst


class FlextInfraFunctionDependencyCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    @override
    def visit_Name(self, node: cst.Name) -> None:
        self.names.add(node.value)


__all__ = ["FlextInfraFunctionDependencyCollector"]
