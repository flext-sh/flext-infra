"""Rule that removes nested MRO redeclarations."""

from __future__ import annotations

import libcst as cst

from flext_infra import FlextInfraGenericTransformerRule, FlextInfraRefactorMRORemover


class FlextInfraRefactorMRORedundancyChecker(FlextInfraGenericTransformerRule):
    """Detect and fix nested classes inheriting from their parent namespace."""

    TRANSFORMER_CLASS: type[cst.CSTTransformer] = FlextInfraRefactorMRORemover


__all__ = ["FlextInfraRefactorMRORedundancyChecker"]
