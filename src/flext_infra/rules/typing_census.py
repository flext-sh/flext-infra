"""Rule implementation for replacing forbidden ``t.NormalizedValue`` annotations."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraRefactorRule, FlextInfraTypingAnnotationReplacer, c, t


class FlextInfraRefactorTypingAnnotationFixRule(FlextInfraRefactorRule):
    """Replace legacy typing annotations with canonical t.* contracts."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        fix_action = (
            str(self.config.get(c.Infra.ReportKeys.FIX_ACTION, "")).strip().lower()
        )
        if fix_action == "replace_object_annotations":
            return self._apply_transformer(
                FlextInfraTypingAnnotationReplacer(),
                tree,
            )
        return (tree, [])


__all__ = ["FlextInfraRefactorTypingAnnotationFixRule"]
