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
    from flext_infra.codegen._codegen_generation_file import (
        FlextInfraCodegenGenerationFileMixin,
    )
    from flext_infra.codegen._codegen_generation_imports import (
        FlextInfraCodegenGenerationImportsMixin,
    )
    from flext_infra.codegen._codegen_generation_lazy_entries import (
        FlextInfraCodegenGenerationLazyEntriesMixin,
    )
    from flext_infra.codegen._codegen_generation_paths import (
        FlextInfraCodegenGenerationPathsMixin,
    )
    from flext_infra.codegen._codegen_generation_renderers import (
        FlextInfraCodegenGenerationRenderersMixin,
    )
    from flext_infra.codegen._codegen_generation_standard import (
        FlextInfraCodegenGenerationStandardMixin,
    )
    from flext_infra.codegen._codegen_generation_type_checking import (
        FlextInfraCodegenGenerationTypeCheckingMixin,
    )
    from flext_infra.codegen._conform import (
        FlextInfraCodegenConformArtifactRender,
        FlextInfraCodegenConformBeadsRoutes,
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
    from flext_infra.codegen._lazy_init_generation import (
        FlextInfraCodegenLazyInitGenerationMixin,
    )
    from flext_infra.codegen._lazy_init_generation_files import (
        FlextInfraCodegenLazyInitGenerationFilePlanMixin,
    )
    from flext_infra.codegen._lazy_init_generation_registry import (
        FlextInfraCodegenLazyInitGenerationRegistryMixin,
    )
    from flext_infra.codegen._lazy_init_planner_aliases import (
        FlextInfraCodegenLazyInitPlannerAliasesMixin,
    )
    from flext_infra.codegen._lazy_init_planner_cache import (
        FlextInfraCodegenLazyInitPlannerCacheMixin,
    )
    from flext_infra.codegen._lazy_init_planner_children import (
        FlextInfraCodegenLazyInitPlannerChildrenMixin,
    )
    from flext_infra.codegen._lazy_init_planner_collision import (
        FlextInfraCodegenLazyInitPlannerCollisionMixin,
    )
    from flext_infra.codegen._lazy_init_planner_exports import (
        FlextInfraCodegenLazyInitPlannerExportsMixin,
    )
    from flext_infra.codegen._lazy_init_planner_parents import (
        FlextInfraCodegenLazyInitPlannerParentsMixin,
    )
    from flext_infra.codegen._lazy_init_planner_public_root import (
        FlextInfraCodegenLazyInitPlannerPublicRootMixin,
    )
    from flext_infra.codegen._lazy_init_projection_manifest import (
        FlextInfraCodegenLazyInitProjectionManifest,
    )
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
    from flext_infra.codegen.conform import FlextInfraCodegenConform
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.layout import FlextInfraCodegenLayout
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
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
    "FlextInfraCodegenConformBeadsRoutes",
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
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenGenerationFileMixin",
    "FlextInfraCodegenGenerationImportsMixin",
    "FlextInfraCodegenGenerationLazyEntriesMixin",
    "FlextInfraCodegenGenerationPathsMixin",
    "FlextInfraCodegenGenerationRenderersMixin",
    "FlextInfraCodegenGenerationStandardMixin",
    "FlextInfraCodegenGenerationTypeCheckingMixin",
    "FlextInfraCodegenLayout",
    "FlextInfraCodegenLayoutApplyMixin",
    "FlextInfraCodegenLayoutFilesMixin",
    "FlextInfraCodegenLayoutGitignoreMixin",
    "FlextInfraCodegenLayoutPlanMixin",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenLazyInitGenerationFilePlanMixin",
    "FlextInfraCodegenLazyInitGenerationMixin",
    "FlextInfraCodegenLazyInitGenerationRegistryMixin",
    "FlextInfraCodegenLazyInitPlanner",
    "FlextInfraCodegenLazyInitPlannerAliasesMixin",
    "FlextInfraCodegenLazyInitPlannerCacheMixin",
    "FlextInfraCodegenLazyInitPlannerChildrenMixin",
    "FlextInfraCodegenLazyInitPlannerCollisionMixin",
    "FlextInfraCodegenLazyInitPlannerExportsMixin",
    "FlextInfraCodegenLazyInitPlannerParentsMixin",
    "FlextInfraCodegenLazyInitPlannerPublicRootMixin",
    "FlextInfraCodegenLazyInitProjectionManifest",
    "FlextInfraCodegenMakeBootstrap",
    "FlextInfraCodegenMiseToolchainProof",
    "FlextInfraCodegenMiseToolchainRepair",
    "FlextInfraCodegenPreconditions",
    "FlextInfraCodegenPyTyped",
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
        "FlextInfraCodegenConformBeadsRoutes": "._conform.beads_routes",
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
        "FlextInfraCodegenGeneration": ".codegen_generation",
        "FlextInfraCodegenGenerationFileMixin": "._codegen_generation_file",
        "FlextInfraCodegenGenerationImportsMixin": "._codegen_generation_imports",
        "FlextInfraCodegenGenerationLazyEntriesMixin": (
            "._codegen_generation_lazy_entries"
        ),
        "FlextInfraCodegenGenerationPathsMixin": "._codegen_generation_paths",
        "FlextInfraCodegenGenerationRenderersMixin": "._codegen_generation_renderers",
        "FlextInfraCodegenGenerationStandardMixin": "._codegen_generation_standard",
        "FlextInfraCodegenGenerationTypeCheckingMixin": (
            "._codegen_generation_type_checking"
        ),
        "FlextInfraCodegenLayout": ".layout",
        "FlextInfraCodegenLayoutApplyMixin": "._layout_apply",
        "FlextInfraCodegenLayoutFilesMixin": "._layout_files",
        "FlextInfraCodegenLayoutGitignoreMixin": "._layout_gitignore",
        "FlextInfraCodegenLayoutPlanMixin": "._layout_plan",
        "FlextInfraCodegenLazyInit": ".lazy_init",
        "FlextInfraCodegenLazyInitGenerationFilePlanMixin": (
            "._lazy_init_generation_files"
        ),
        "FlextInfraCodegenLazyInitGenerationMixin": "._lazy_init_generation",
        "FlextInfraCodegenLazyInitGenerationRegistryMixin": (
            "._lazy_init_generation_registry"
        ),
        "FlextInfraCodegenLazyInitPlanner": ".lazy_init_planner",
        "FlextInfraCodegenLazyInitPlannerAliasesMixin": "._lazy_init_planner_aliases",
        "FlextInfraCodegenLazyInitPlannerCacheMixin": "._lazy_init_planner_cache",
        "FlextInfraCodegenLazyInitPlannerChildrenMixin": "._lazy_init_planner_children",
        "FlextInfraCodegenLazyInitPlannerCollisionMixin": (
            "._lazy_init_planner_collision"
        ),
        "FlextInfraCodegenLazyInitPlannerExportsMixin": "._lazy_init_planner_exports",
        "FlextInfraCodegenLazyInitPlannerParentsMixin": "._lazy_init_planner_parents",
        "FlextInfraCodegenLazyInitPlannerPublicRootMixin": (
            "._lazy_init_planner_public_root"
        ),
        "FlextInfraCodegenLazyInitProjectionManifest": (
            "._lazy_init_projection_manifest"
        ),
        "FlextInfraCodegenMakeBootstrap": ".make_bootstrap",
        "FlextInfraCodegenMiseToolchainProof": ".mise_toolchain_proof",
        "FlextInfraCodegenMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraCodegenPreconditions": ".codegen_preconditions",
        "FlextInfraCodegenPyTyped": ".py_typed",
        "FlextInfraCodegenQualityGate": ".constants_quality_gate",
        "FlextInfraCodegenScaffolder": ".scaffolder",
        "FlextInfraCodegenVersionFile": ".version_file",
        "FlextInfraStagedPackage": ".staged_package",
        "_conform": "._conform",
    }),
    public_exports=__all__,
)
