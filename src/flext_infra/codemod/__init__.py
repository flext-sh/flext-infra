# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codemod.apply_renames import FlextInfraApplyRenames
    from flext_infra.codemod.ast_scan import FlextInfraCodemodAstScan
    from flext_infra.codemod.batch_apply import FlextInfraCodemodBatchApply
    from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
    from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
    from flext_infra.codemod.duplicate_apply import FlextInfraCodemodDuplicateApply
    from flext_infra.codemod.extract import FlextInfraCodemodExtract
    from flext_infra.codemod.loop import FlextInfraCodemodLoop
    from flext_infra.codemod.rename import FlextInfraCodemodRename
    from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply
    from flext_infra.codemod.snapshot_reconciler import (
        FlextInfraCodemodSnapshotReconciler,
    )
    from flext_infra.codemod.snapshot_refresh import FlextInfraCodemodSnapshotRefresh
    from flext_infra.codemod.text_gates import FlextInfraModTextGateEngine


__all__: tuple[str, ...] = (
    "FlextInfraApplyRenames",
    "FlextInfraCodemodAstScan",
    "FlextInfraCodemodBatchApply",
    "FlextInfraCodemodDuplicateApply",
    "FlextInfraCodemodExtract",
    "FlextInfraCodemodLoop",
    "FlextInfraCodemodRename",
    "FlextInfraCodemodSemanticApply",
    "FlextInfraCodemodSnapshotReconciler",
    "FlextInfraCodemodSnapshotRefresh",
    "FlextInfraModGateEngine",
    "FlextInfraModReplacements",
    "FlextInfraModTextGateEngine",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraApplyRenames": ".apply_renames",
        "FlextInfraCodemodAstScan": ".ast_scan",
        "FlextInfraCodemodBatchApply": ".batch_apply",
        "FlextInfraCodemodDuplicateApply": ".duplicate_apply",
        "FlextInfraCodemodExtract": ".extract",
        "FlextInfraCodemodLoop": ".loop",
        "FlextInfraCodemodRename": ".rename",
        "FlextInfraCodemodSemanticApply": ".semantic_apply",
        "FlextInfraCodemodSnapshotReconciler": ".snapshot_reconciler",
        "FlextInfraCodemodSnapshotRefresh": ".snapshot_refresh",
        "FlextInfraModGateEngine": ".batch_gates",
        "FlextInfraModReplacements": ".batch_replacements",
        "FlextInfraModTextGateEngine": ".text_gates",
    }),
    public_exports=__all__,
)
