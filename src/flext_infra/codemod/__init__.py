# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codemod._extract.duplicate import FlextInfraCodemodExtractDuplicate
    from flext_infra.codemod._loop.phase_accessor_rename import (
        FlextInfraCodemodLoopPhaseAccessorRename,
    )
    from flext_infra.codemod._loop.phase_duplicate_apply import (
        FlextInfraCodemodLoopPhaseDuplicateApply,
    )
    from flext_infra.codemod._loop.phase_import_normalization import (
        FlextInfraCodemodLoopPhaseImportNormalization,
    )
    from flext_infra.codemod._loop.phase_namespace_relocation import (
        FlextInfraCodemodLoopPhaseNamespaceRelocation,
    )
    from flext_infra.codemod._rename.sources import FlextInfraCodemodRenameSources
    from flext_infra.codemod._rename.symbols import FlextInfraCodemodRenameSymbols
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
    "FlextInfraCodemodExtractDuplicate",
    "FlextInfraCodemodLoop",
    "FlextInfraCodemodLoopPhaseAccessorRename",
    "FlextInfraCodemodLoopPhaseDuplicateApply",
    "FlextInfraCodemodLoopPhaseImportNormalization",
    "FlextInfraCodemodLoopPhaseNamespaceRelocation",
    "FlextInfraCodemodRename",
    "FlextInfraCodemodRenameSources",
    "FlextInfraCodemodRenameSymbols",
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
        "FlextInfraCodemodExtractDuplicate": "._extract.duplicate",
        "FlextInfraCodemodLoop": ".loop",
        "FlextInfraCodemodLoopPhaseAccessorRename": "._loop.phase_accessor_rename",
        "FlextInfraCodemodLoopPhaseDuplicateApply": "._loop.phase_duplicate_apply",
        "FlextInfraCodemodLoopPhaseImportNormalization": "._loop.phase_import_normalization",
        "FlextInfraCodemodLoopPhaseNamespaceRelocation": "._loop.phase_namespace_relocation",
        "FlextInfraCodemodRename": ".rename",
        "FlextInfraCodemodRenameSources": "._rename.sources",
        "FlextInfraCodemodRenameSymbols": "._rename.symbols",
        "FlextInfraCodemodSemanticApply": ".semantic_apply",
        "FlextInfraCodemodSnapshotReconciler": ".snapshot_reconciler",
        "FlextInfraCodemodSnapshotRefresh": ".snapshot_refresh",
        "FlextInfraModGateEngine": ".batch_gates",
        "FlextInfraModReplacements": ".batch_replacements",
        "FlextInfraModTextGateEngine": ".text_gates",
    }),
    public_exports=__all__,
)
