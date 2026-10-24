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
    from flext_infra.codegen import _conform as _conform
    from flext_infra.codegen._conform import (
        FlextInfraCodegenConformArtifactRender,
        FlextInfraCodegenConformBootstrap,
        FlextInfraCodegenConformContextRender,
        FlextInfraCodegenConformEditor,
        FlextInfraCodegenConformExecute,
        FlextInfraCodegenConformExistingPlan,
        FlextInfraCodegenConformFilePlans,
        FlextInfraCodegenConformPlan,
        FlextInfraCodegenConformPyprojectPolicy,
        FlextInfraCodegenConformScaffoldPlan,
    )
    from flext_infra.codegen._consolidator_steps import (
        FlextInfraCodegenConsolidatorStepsMixin,
    )
    from flext_infra.codegen._execution import FlextInfraCodegenExecutionBase
    from flext_infra.codegen._fixer_passes import FlextInfraCodegenFixerPassesMixin
    from flext_infra.codegen._fixer_results import FlextInfraCodegenFixerResultsMixin
    from flext_infra.codegen._fixer_workspace import (
        FlextInfraCodegenFixerWorkspaceMixin,
    )
    from flext_infra.codegen._layout_apply import FlextInfraCodegenLayoutApplyMixin
    from flext_infra.codegen._layout_files import FlextInfraCodegenLayoutFilesMixin
    from flext_infra.codegen._layout_gitignore import (
        FlextInfraCodegenLayoutGitignoreMixin,
    )
    from flext_infra.codegen._layout_plan import FlextInfraCodegenLayoutPlanMixin
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
    from flext_infra.codegen.conform import FlextInfraCodegenConform
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.layout import FlextInfraCodegenLayout
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.lazy_init_render import FlextInfraCodegenLazyInitRender
    from flext_infra.codegen.make_bootstrap import FlextInfraCodegenMakeBootstrap
    from flext_infra.codegen.mise_toolchain_proof import (
        FlextInfraCodegenMiseToolchainProof,
    )
    from flext_infra.codegen.mise_toolchain_repair import (
        FlextInfraCodegenMiseToolchainRepair,
    )
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.python_model import FlextInfraCodegenPythonModel
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
    "FlextInfraCodegenConsolidatorStepsMixin",
    "FlextInfraCodegenExecutionBase",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenFixerPassesMixin",
    "FlextInfraCodegenFixerResultsMixin",
    "FlextInfraCodegenFixerWorkspaceMixin",
    "FlextInfraCodegenLayout",
    "FlextInfraCodegenLayoutApplyMixin",
    "FlextInfraCodegenLayoutFilesMixin",
    "FlextInfraCodegenLayoutGitignoreMixin",
    "FlextInfraCodegenLayoutPlanMixin",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenLazyInitRender",
    "FlextInfraCodegenMakeBootstrap",
    "FlextInfraCodegenMiseToolchainProof",
    "FlextInfraCodegenMiseToolchainRepair",
    "FlextInfraCodegenPreconditions",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenPythonModel",
    "FlextInfraCodegenQualityGate",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenVersionFile",
    "FlextInfraStagedPackage",
    "_conform",
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
        "FlextInfraCodegenConsolidatorStepsMixin": "._consolidator_steps",
        "FlextInfraCodegenExecutionBase": "._execution",
        "FlextInfraCodegenFixer": ".fixer",
        "FlextInfraCodegenFixerPassesMixin": "._fixer_passes",
        "FlextInfraCodegenFixerResultsMixin": "._fixer_results",
        "FlextInfraCodegenFixerWorkspaceMixin": "._fixer_workspace",
        "FlextInfraCodegenLayout": ".layout",
        "FlextInfraCodegenLayoutApplyMixin": "._layout_apply",
        "FlextInfraCodegenLayoutFilesMixin": "._layout_files",
        "FlextInfraCodegenLayoutGitignoreMixin": "._layout_gitignore",
        "FlextInfraCodegenLayoutPlanMixin": "._layout_plan",
        "FlextInfraCodegenLazyInit": ".lazy_init",
        "FlextInfraCodegenLazyInitRender": ".lazy_init_render",
        "FlextInfraCodegenMakeBootstrap": ".make_bootstrap",
        "FlextInfraCodegenMiseToolchainProof": ".mise_toolchain_proof",
        "FlextInfraCodegenMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraCodegenPreconditions": ".codegen_preconditions",
        "FlextInfraCodegenPyTyped": ".py_typed",
        "FlextInfraCodegenPythonModel": ".python_model",
        "FlextInfraCodegenQualityGate": ".constants_quality_gate",
        "FlextInfraCodegenScaffolder": ".scaffolder",
        "FlextInfraCodegenVersionFile": ".version_file",
        "FlextInfraStagedPackage": ".staged_package",
        "_conform": "._conform",
    }),
    public_exports=__all__,
)
