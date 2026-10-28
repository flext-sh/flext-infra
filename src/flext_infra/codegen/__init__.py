# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package.

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
    from flext_infra.codegen._conform.artifact_render import (
        FlextInfraCodegenConformArtifactRender,
    )
    from flext_infra.codegen._conform.bootstrap import FlextInfraCodegenConformBootstrap
    from flext_infra.codegen._conform.context_render import (
        FlextInfraCodegenConformContextRender,
    )
    from flext_infra.codegen._conform.editor import FlextInfraCodegenConformEditor
    from flext_infra.codegen._conform.execute import FlextInfraCodegenConformExecute
    from flext_infra.codegen._conform.existing_plan import (
        FlextInfraCodegenConformExistingPlan,
    )
    from flext_infra.codegen._conform.file_plans import (
        FlextInfraCodegenConformFilePlans,
    )
    from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan
    from flext_infra.codegen._conform.pyproject_policy import (
        FlextInfraCodegenConformPyprojectPolicy,
    )
    from flext_infra.codegen._conform.scaffold_plan import (
        FlextInfraCodegenConformScaffoldPlan,
    )
    from flext_infra.codegen._consolidator.steps import (
        FlextInfraCodegenConsolidatorSteps,
    )
    from flext_infra.codegen._fixer.passes import FlextInfraCodegenFixerPasses
    from flext_infra.codegen._fixer.results import FlextInfraCodegenFixerResults
    from flext_infra.codegen._fixer.workspace import FlextInfraCodegenFixerWorkspace
    from flext_infra.codegen._layout.apply import FlextInfraCodegenLayoutApply
    from flext_infra.codegen._layout.files import FlextInfraCodegenLayoutFiles
    from flext_infra.codegen._layout.gitignore import FlextInfraCodegenLayoutGitignore
    from flext_infra.codegen._layout.plan import FlextInfraCodegenLayoutPlan
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
    from flext_infra.codegen.conform import FlextInfraCodegenConform
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
    from flext_infra.codegen.execution import FlextInfraCodegenExecution
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.layout import FlextInfraCodegenLayout
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.make_bootstrap import FlextInfraCodegenMakeBootstrap
    from flext_infra.codegen.mise_toolchain_proof import (
        FlextInfraCodegenMiseToolchainProof,
    )
    from flext_infra.codegen.mise_toolchain_repair import (
        FlextInfraCodegenMiseToolchainRepair,
    )
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.codegen.staged_package import FlextInfraStagedPackage
    from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile


__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConformArtifactRender",
    "FlextInfraCodegenConformBootstrap",
    "FlextInfraCodegenConformContextRender",
    "FlextInfraCodegenConformEditor",
    "FlextInfraCodegenConformExecute",
    "FlextInfraCodegenConformExistingPlan",
    "FlextInfraCodegenConformFilePlans",
    "FlextInfraCodegenConformPlan",
    "FlextInfraCodegenConformPyprojectPolicy",
    "FlextInfraCodegenConformScaffoldPlan",
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
        "FlextInfraCodegenConformArtifactRender": "._conform.artifact_render",
        "FlextInfraCodegenConformBootstrap": "._conform.bootstrap",
        "FlextInfraCodegenConformContextRender": "._conform.context_render",
        "FlextInfraCodegenConformEditor": "._conform.editor",
        "FlextInfraCodegenConformExecute": "._conform.execute",
        "FlextInfraCodegenConformExistingPlan": "._conform.existing_plan",
        "FlextInfraCodegenConformFilePlans": "._conform.file_plans",
        "FlextInfraCodegenConformPlan": "._conform.plan",
        "FlextInfraCodegenConformPyprojectPolicy": "._conform.pyproject_policy",
        "FlextInfraCodegenConformScaffoldPlan": "._conform.scaffold_plan",
        "FlextInfraCodegenConsolidator": ".consolidator",
        "FlextInfraCodegenConsolidatorSteps": "._consolidator.steps",
        "FlextInfraCodegenExecution": ".execution",
        "FlextInfraCodegenFixer": ".fixer",
        "FlextInfraCodegenFixerPasses": "._fixer.passes",
        "FlextInfraCodegenFixerResults": "._fixer.results",
        "FlextInfraCodegenFixerWorkspace": "._fixer.workspace",
        "FlextInfraCodegenLayout": ".layout",
        "FlextInfraCodegenLayoutApply": "._layout.apply",
        "FlextInfraCodegenLayoutFiles": "._layout.files",
        "FlextInfraCodegenLayoutGitignore": "._layout.gitignore",
        "FlextInfraCodegenLayoutPlan": "._layout.plan",
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
