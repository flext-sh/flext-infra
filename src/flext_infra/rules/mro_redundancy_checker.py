"""Rule that removes nested MRO redeclarations."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraRefactorMRORemover, FlextInfraRefactorRule, t


class FlextInfraRefactorMRORedundancyChecker(FlextInfraRefactorRule):
    """Detect and fix nested classes inheriting from their parent namespace."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply MRO redeclaration cleanup transformer."""
        return self._apply_transformer(FlextInfraRefactorMRORemover(), tree)


__all__ = ["FlextInfraRefactorMRORedundancyChecker"]
