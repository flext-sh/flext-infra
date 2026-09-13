# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from ._codegen_generation_file import FlextInfraCodegenGenerationFileMixin
    from ._codegen_generation_imports import FlextInfraCodegenGenerationImportsMixin
    from ._codegen_generation_lazy_entries import (
        FlextInfraCodegenGenerationLazyEntriesMixin,
    )
    from ._codegen_generation_paths import FlextInfraCodegenGenerationPathsMixin
    from ._codegen_generation_renderers import FlextInfraCodegenGenerationRenderersMixin
    from ._codegen_generation_standard import FlextInfraCodegenGenerationStandardMixin
    from ._codegen_generation_type_checking import (
        FlextInfraCodegenGenerationTypeCheckingMixin,
    )
    from ._codegen_staging import stage_file_plans
    from ._consolidator_steps import FlextInfraCodegenConsolidatorStepsMixin
    from ._fixer_passes import FlextInfraCodegenFixerPassesMixin
    from ._fixer_results import FlextInfraCodegenFixerResultsMixin
    from ._fixer_workspace import FlextInfraCodegenFixerWorkspaceMixin
    from ._layout_apply import FlextInfraCodegenLayoutApplyMixin
    from ._layout_files import FlextInfraCodegenLayoutFilesMixin
    from ._layout_gitignore import FlextInfraCodegenLayoutGitignoreMixin
    from ._layout_plan import FlextInfraCodegenLayoutPlanMixin
    from ._lazy_init_generation import FlextInfraCodegenLazyInitGenerationMixin
    from ._lazy_init_generation_files import (
        FlextInfraCodegenLazyInitGenerationFilePlanMixin,
    )
    from ._lazy_init_generation_registry import (
        FlextInfraCodegenLazyInitGenerationRegistryMixin,
    )
    from ._lazy_init_planner_public_root import (
        FlextInfraCodegenLazyInitPlannerPublicRootMixin,
    )
    from ._mise_artifacts_candidates import publication_plan
    from ._mise_artifacts_files import FlextInfraMiseArtifactsFiles
    from ._mise_artifacts_journal import FlextInfraMiseArtifactsJournal
    from ._mise_artifacts_process import FlextInfraMiseArtifactsProcess
    from ._mise_artifacts_publication import publish, publish_file_plan
    from ._mise_artifacts_recovery import FlextInfraMiseRecovery
    from ._mise_artifacts_staging import FlextInfraMiseStaging
    from ._mise_artifacts_state import FlextInfraMiseArtifactsState
    from ._mise_artifacts_verification import FlextInfraMiseArtifactsVerification
    from ._pipeline_stages import FlextInfraCodegenPipelineStagesMixin
    from .census import FlextInfraCodegenCensus
    from .codegen_generation import FlextInfraCodegenGeneration
    from .codegen_transaction import FlextInfraCodegenTransaction
    from .conform import FlextInfraCodegenConform
    from .consolidator import FlextInfraCodegenConsolidator
    from .constants_quality_gate import FlextInfraCodegenQualityGate
    from .fixer import FlextInfraCodegenFixer
    from .layout import FlextInfraCodegenLayout
    from .lazy_init import FlextInfraCodegenLazyInit
    from .lazy_init_planner import FlextInfraCodegenLazyInitPlanner
    from .make_bootstrap import FlextInfraCodegenMakeBootstrap
    from .mise_artifacts import FlextInfraCodegenMiseArtifacts
    from .mise_artifacts_workspace import FlextInfraMiseWorkspacePlanner
    from .pipeline import (
        FlextInfraCodegenLazyInitGenerationMixin,
        FlextInfraCodegenPipeline,
        FlextInfraCodegenPipelineStagesMixin,
        FlextInfraMiseArtifactsFiles,
        publish_file_plan,
    )
    from .project_new import FlextInfraCodegenProjectNew
    from .py_typed import FlextInfraCodegenPyTyped
    from .scaffolder import FlextInfraCodegenScaffolder
    from .version_file import FlextInfraCodegenVersionFile
__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenConsolidatorStepsMixin",
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
    "FlextInfraCodegenLazyInitPlannerPublicRootMixin",
    "FlextInfraCodegenMakeBootstrap",
    "FlextInfraCodegenMiseArtifacts",
    "FlextInfraCodegenPipeline",
    "FlextInfraCodegenPipelineStagesMixin",
    "FlextInfraCodegenProjectNew",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenQualityGate",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenTransaction",
    "FlextInfraCodegenVersionFile",
    "FlextInfraMiseArtifactsFiles",
    "FlextInfraMiseArtifactsJournal",
    "FlextInfraMiseArtifactsProcess",
    "FlextInfraMiseArtifactsState",
    "FlextInfraMiseArtifactsVerification",
    "FlextInfraMiseRecovery",
    "FlextInfraMiseStaging",
    "FlextInfraMiseWorkspacePlanner",
    "publication_plan",
    "publish",
    "publish_file_plan",
    "stage_file_plans",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._codegen_generation_file": ("FlextInfraCodegenGenerationFileMixin",),
            "._codegen_generation_imports": (
                "FlextInfraCodegenGenerationImportsMixin",
            ),
            "._codegen_generation_lazy_entries": (
                "FlextInfraCodegenGenerationLazyEntriesMixin",
            ),
            "._codegen_generation_paths": ("FlextInfraCodegenGenerationPathsMixin",),
            "._codegen_generation_renderers": (
                "FlextInfraCodegenGenerationRenderersMixin",
            ),
            "._codegen_generation_standard": (
                "FlextInfraCodegenGenerationStandardMixin",
            ),
            "._codegen_generation_type_checking": (
                "FlextInfraCodegenGenerationTypeCheckingMixin",
            ),
            "._codegen_staging": ("stage_file_plans",),
            "._consolidator_steps": ("FlextInfraCodegenConsolidatorStepsMixin",),
            "._fixer_passes": ("FlextInfraCodegenFixerPassesMixin",),
            "._fixer_results": ("FlextInfraCodegenFixerResultsMixin",),
            "._fixer_workspace": ("FlextInfraCodegenFixerWorkspaceMixin",),
            "._layout_apply": ("FlextInfraCodegenLayoutApplyMixin",),
            "._layout_files": ("FlextInfraCodegenLayoutFilesMixin",),
            "._layout_gitignore": ("FlextInfraCodegenLayoutGitignoreMixin",),
            "._layout_plan": ("FlextInfraCodegenLayoutPlanMixin",),
            "._lazy_init_generation": ("FlextInfraCodegenLazyInitGenerationMixin",),
            "._lazy_init_generation_files": (
                "FlextInfraCodegenLazyInitGenerationFilePlanMixin",
            ),
            "._lazy_init_generation_registry": (
                "FlextInfraCodegenLazyInitGenerationRegistryMixin",
            ),
            "._lazy_init_planner_public_root": (
                "FlextInfraCodegenLazyInitPlannerPublicRootMixin",
            ),
            "._mise_artifacts_candidates": ("publication_plan",),
            "._mise_artifacts_files": ("FlextInfraMiseArtifactsFiles",),
            "._mise_artifacts_journal": ("FlextInfraMiseArtifactsJournal",),
            "._mise_artifacts_process": ("FlextInfraMiseArtifactsProcess",),
            "._mise_artifacts_publication": ("publish", "publish_file_plan"),
            "._mise_artifacts_recovery": ("FlextInfraMiseRecovery",),
            "._mise_artifacts_staging": ("FlextInfraMiseStaging",),
            "._mise_artifacts_state": ("FlextInfraMiseArtifactsState",),
            "._mise_artifacts_verification": ("FlextInfraMiseArtifactsVerification",),
            "._pipeline_stages": ("FlextInfraCodegenPipelineStagesMixin",),
            ".census": ("FlextInfraCodegenCensus",),
            ".codegen_generation": ("FlextInfraCodegenGeneration",),
            ".codegen_transaction": ("FlextInfraCodegenTransaction",),
            ".conform": ("FlextInfraCodegenConform",),
            ".consolidator": ("FlextInfraCodegenConsolidator",),
            ".constants_quality_gate": ("FlextInfraCodegenQualityGate",),
            ".fixer": ("FlextInfraCodegenFixer",),
            ".layout": ("FlextInfraCodegenLayout",),
            ".lazy_init": ("FlextInfraCodegenLazyInit",),
            ".lazy_init_planner": ("FlextInfraCodegenLazyInitPlanner",),
            ".make_bootstrap": ("FlextInfraCodegenMakeBootstrap",),
            ".mise_artifacts": ("FlextInfraCodegenMiseArtifacts",),
            ".mise_artifacts_workspace": ("FlextInfraMiseWorkspacePlanner",),
            ".pipeline": ("FlextInfraCodegenPipeline",),
            ".project_new": ("FlextInfraCodegenProjectNew",),
            ".py_typed": ("FlextInfraCodegenPyTyped",),
            ".scaffolder": ("FlextInfraCodegenScaffolder",),
            ".version_file": ("FlextInfraCodegenVersionFile",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
