"""Rule implementation for TypeAlias and inline-union unification."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraRefactorRule, FlextInfraRefactorTypingUnifier, c


class FlextInfraRefactorTypingUnificationRule(FlextInfraRefactorRule):
    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> tuple[cst.Module, Sequence[str]]:
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
            file_path=_file_path,
        )
        updated_tree = tree.visit(transformer)
        return (updated_tree, transformer.changes)


__all__ = ["FlextInfraRefactorTypingUnificationRule"]
