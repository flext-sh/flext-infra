# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen import (
        FlextInfraCodegenCensus,
        FlextInfraCodegenConform,
        FlextInfraCodegenConsolidator,
        FlextInfraCodegenConsolidatorSteps,
        FlextInfraCodegenExecution,
        FlextInfraCodegenFixer,
        FlextInfraCodegenLayout,
        FlextInfraCodegenLazyInit,
        FlextInfraCodegenMakeBootstrap,
        FlextInfraCodegenMiseToolchainProof,
        FlextInfraCodegenMiseToolchainRepair,
        FlextInfraCodegenPreconditions,
        FlextInfraCodegenPyTyped,
        FlextInfraCodegenQualityGate,
        FlextInfraCodegenScaffolder,
        FlextInfraCodegenVersionFile,
        FlextInfraStagedPackage,
    )
    from flext_infra.codegen._fixer import (
        FlextInfraCodegenFixerPasses,
        FlextInfraCodegenFixerResults,
        FlextInfraCodegenFixerWorkspace,
    )
    from flext_infra.codegen._layout import (
        FlextInfraCodegenLayoutApply,
        FlextInfraCodegenLayoutFiles,
        FlextInfraCodegenLayoutGitignore,
        FlextInfraCodegenLayoutPlan,
    )


__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenConsolidatorSteps",
    "FlextInfraCodegenExecution",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenFixerPasses",
    "FlextInfraCodegenFixerResults",
    "FlextInfraCodegenFixerWorkspace",
    "FlextInfraCodegenLayout",
    "FlextInfraCodegenLayoutApply",
    "FlextInfraCodegenLayoutFiles",
    "FlextInfraCodegenLayoutGitignore",
    "FlextInfraCodegenLayoutPlan",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenMakeBootstrap",
    "FlextInfraCodegenMiseToolchainProof",
    "FlextInfraCodegenMiseToolchainRepair",
    "FlextInfraCodegenPreconditions",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenQualityGate",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenVersionFile",
    "FlextInfraStagedPackage",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraCodegenCensus": ".census",
        "FlextInfraCodegenConform": ".conform",
        "FlextInfraCodegenConsolidator": ".consolidator",
        "FlextInfraCodegenConsolidatorSteps": "._consolidator_steps",
        "FlextInfraCodegenExecution": "._execution",
        "FlextInfraCodegenFixer": ".fixer",
        "FlextInfraCodegenFixerPasses": "._fixer_passes",
        "FlextInfraCodegenFixerResults": "._fixer_results",
        "FlextInfraCodegenFixerWorkspace": "._fixer_workspace",
        "FlextInfraCodegenLayout": ".layout",
        "FlextInfraCodegenLayoutApply": "._layout_apply",
        "FlextInfraCodegenLayoutFiles": "._layout_files",
        "FlextInfraCodegenLayoutGitignore": "._layout_gitignore",
        "FlextInfraCodegenLayoutPlan": "._layout_plan",
        "FlextInfraCodegenLazyInit": ".lazy_init",
        "FlextInfraCodegenMakeBootstrap": ".make_bootstrap",
        "FlextInfraCodegenMiseToolchainProof": ".mise_toolchain_proof",
        "FlextInfraCodegenMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraCodegenPreconditions": ".codegen_preconditions",
        "FlextInfraCodegenPyTyped": ".py_typed",
        "FlextInfraCodegenQualityGate": ".constants_quality_gate",
        "FlextInfraCodegenScaffolder": ".scaffolder",
        "FlextInfraCodegenVersionFile": ".version_file",
        "FlextInfraStagedPackage": ".staged_package",
    }),
    public_exports=__all__,
)
