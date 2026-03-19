from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c
from flext_infra.refactor._base_rule import FlextInfraRefactorRule
from flext_infra.transformers.typing_annotation_replacer import TypingAnnotationReplacer


class FlextInfraRefactorTypingAnnotationFixRule(FlextInfraRefactorRule):
    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> tuple[cst.Module, list[str]]:
        fix_action = (
            str(self.config.get(c.Infra.ReportKeys.FIX_ACTION, "")).strip().lower()
        )
        if fix_action == "replace_object_annotations":
            replacer = TypingAnnotationReplacer()
            updated = tree.visit(replacer)
            return (updated, replacer.changes)
        return (tree, [])


__all__ = ["FlextInfraRefactorTypingAnnotationFixRule"]
