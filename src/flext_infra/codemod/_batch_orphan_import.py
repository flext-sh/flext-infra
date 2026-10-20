"""Drop the TYPE_CHECKING name once its guarded block is gone.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

import libcst as cst


class FlextInfraTypeCheckingGuardScanner(cst.CSTVisitor):
    """Detect a surviving ``if TYPE_CHECKING:`` guard in the module.

    The predicate mirrors the import-law's own guard test: a bare
    ``TYPE_CHECKING`` name or the ``typing.TYPE_CHECKING`` attribute.
    """

    def __init__(self) -> None:
        """Start unguarded."""
        self.guarded = False

    @override
    def on_visit(self, node: cst.CSTNode) -> bool:
        """Flag the first surviving guard test.

        Returns:
            Always ``True`` so descendant nodes stay on the scan path.

        """
        if isinstance(node, cst.If) and self._is_type_checking_test(node.test):
            self.guarded = True
        return True

    @staticmethod
    def _is_type_checking_test(test: cst.BaseExpression) -> bool:
        """Recognize a bare or ``typing``-qualified ``TYPE_CHECKING`` test.

        Returns:
            The resulting ``bool``.

        """
        return (isinstance(test, cst.Name) and test.value == "TYPE_CHECKING") or (
            isinstance(test, cst.Attribute)
            and test.attr.value == "TYPE_CHECKING"
            and isinstance(test.value, cst.Name)
            and test.value.value == "typing"
        )


def type_checking_guarded(module: cst.Module) -> bool:
    """Return whether the module still reads ``TYPE_CHECKING`` anywhere."""
    scanner = FlextInfraTypeCheckingGuardScanner()
    module.visit(scanner)
    return scanner.guarded


class FlextInfraOrphanImport(cst.CSTTransformer):
    """Drop the ``TYPE_CHECKING`` name once its block is gone.

    The caller owns the fact: ``guarded`` is computed on the same tree this
    transformer visits (post scaffold cleanup) and must be False only when
    no ``if TYPE_CHECKING:`` block — or any other read of the name —
    survives. Stripping the import while a guard survives unbinds the name
    (F821); keeping it after the block is gone leaves a dead import.
    """

    def __init__(self, *, guarded: bool) -> None:
        """Bind whether a surviving guard still reads the name."""
        self._guarded = guarded

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom | cst.RemovalSentinel:
        if self._guarded:
            return updated_node
        module = updated_node.module
        if not (isinstance(module, cst.Name) and module.value == "typing"):
            return updated_node
        names = updated_node.names
        if isinstance(names, cst.ImportStar):
            return updated_node
        kept = tuple(
            alias
            for alias in names
            if not (
                isinstance(alias.name, cst.Name) and alias.name.value == "TYPE_CHECKING"
            )
        )
        if len(kept) == len(names):
            return updated_node
        if not kept:
            return cst.RemoveFromParent()
        return updated_node.with_changes(names=kept)


__all__: list[str] = ["FlextInfraOrphanImport"]
