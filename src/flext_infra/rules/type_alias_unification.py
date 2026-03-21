"""Rule implementation for TypeAlias and inline-union unification."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra.constants import c
from flext_infra.refactor.rule import FlextInfraRefactorRule
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier


class FlextInfraRefactorTypingUnificationRule(FlextInfraRefactorRule):
    @override
    def apply(
        self,
        tree: cst.Module,
        file_path: Path | None = None,
    ) -> tuple[cst.Module, list[str]]:
        transformer = FlextInfraRefactorTypingUnifier(
            canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
            file_path=file_path,
        )
        updated_tree = tree.visit(transformer)
        return (updated_tree, transformer.changes)


__all__ = ["FlextInfraRefactorTypingUnificationRule"]
