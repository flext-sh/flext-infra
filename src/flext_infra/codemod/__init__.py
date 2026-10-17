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
    from flext_infra.codemod._batch_dead_scaffold import FlextInfraDeadScaffold
    from flext_infra.codemod._batch_orphan_import import FlextInfraOrphanImport
    from flext_infra.codemod._extract_duplicate import FlextInfraExtractDuplicatePhase
    from flext_infra.codemod._loop_phase_accessor_rename import (
        FlextInfraAccessorRenamePhase,
    )
    from flext_infra.codemod._loop_phase_duplicate_apply import (
        FlextInfraDuplicateApplyPhase,
    )
    from flext_infra.codemod._loop_phase_import_normalization import (
        FlextInfraImportNormalizationPhase,
    )
    from flext_infra.codemod._loop_phase_namespace_relocation import (
        FlextInfraNamespaceRelocationPhase,
    )
    from flext_infra.codemod._rename_sources import FlextInfraRenameSources
    from flext_infra.codemod._rename_symbols import FlextInfraRenameSymbols
    from flext_infra.codemod.apply_renames import FlextInfraApplyRenames
    from flext_infra.codemod.ast_scan import FlextInfraCodemodAstScan
    from flext_infra.codemod.batch_apply import FlextInfraCodemodBatchApply
    from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
    from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
    from flext_infra.codemod.duplicate_apply import FlextInfraCodemodDuplicateApply
    from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply
    from flext_infra.codemod.snapshot_reconciler import (
        FlextInfraCodemodSnapshotReconciler,
    )
    from flext_infra.codemod.snapshot_refresh import FlextInfraCodemodSnapshotRefresh
    from flext_infra.codemod.text_gates import FlextInfraModTextGateEngine


__all__: tuple[str, ...] = (
    "FlextInfraAccessorRenamePhase",
    "FlextInfraApplyRenames",
    "FlextInfraCodemodAstScan",
    "FlextInfraCodemodBatchApply",
    "FlextInfraCodemodDuplicateApply",
    "FlextInfraCodemodSemanticApply",
    "FlextInfraCodemodSnapshotReconciler",
    "FlextInfraCodemodSnapshotRefresh",
    "FlextInfraDeadScaffold",
    "FlextInfraDuplicateApplyPhase",
    "FlextInfraExtractDuplicatePhase",
    "FlextInfraImportNormalizationPhase",
    "FlextInfraModGateEngine",
    "FlextInfraModReplacements",
    "FlextInfraModTextGateEngine",
    "FlextInfraNamespaceRelocationPhase",
    "FlextInfraOrphanImport",
    "FlextInfraRenameSources",
    "FlextInfraRenameSymbols",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraAccessorRenamePhase": "._loop_phase_accessor_rename",
        "FlextInfraApplyRenames": ".apply_renames",
        "FlextInfraCodemodAstScan": ".ast_scan",
        "FlextInfraCodemodBatchApply": ".batch_apply",
        "FlextInfraCodemodDuplicateApply": ".duplicate_apply",
        "FlextInfraCodemodSemanticApply": ".semantic_apply",
        "FlextInfraCodemodSnapshotReconciler": ".snapshot_reconciler",
        "FlextInfraCodemodSnapshotRefresh": ".snapshot_refresh",
        "FlextInfraDeadScaffold": "._batch_dead_scaffold",
        "FlextInfraDuplicateApplyPhase": "._loop_phase_duplicate_apply",
        "FlextInfraExtractDuplicatePhase": "._extract_duplicate",
        "FlextInfraImportNormalizationPhase": "._loop_phase_import_normalization",
        "FlextInfraModGateEngine": ".batch_gates",
        "FlextInfraModReplacements": ".batch_replacements",
        "FlextInfraModTextGateEngine": ".text_gates",
        "FlextInfraNamespaceRelocationPhase": "._loop_phase_namespace_relocation",
        "FlextInfraOrphanImport": "._batch_orphan_import",
        "FlextInfraRenameSources": "._rename_sources",
        "FlextInfraRenameSymbols": "._rename_symbols",
    }),
    public_exports=__all__,
)
