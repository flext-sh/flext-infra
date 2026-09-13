# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from ._lazy_init_generation import FlextInfraCodegenLazyInitGenerationMixin
    from ._mise_artifacts_files import FlextInfraMiseArtifactsFiles
    from ._mise_artifacts_publication import publish_file_plan
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
    from .pipeline import FlextInfraCodegenPipeline
    from .project_new import FlextInfraCodegenProjectNew
    from .py_typed import FlextInfraCodegenPyTyped
    from .scaffolder import FlextInfraCodegenScaffolder
    from .version_file import FlextInfraCodegenVersionFile
__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenLazyInitGenerationMixin",
    "FlextInfraCodegenLazyInitPlanner",
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
    "FlextInfraMiseWorkspacePlanner",
    "publish_file_plan",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
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
            "._lazy_init_generation": ("FlextInfraCodegenLazyInitGenerationMixin",),
            "._pipeline_stages": ("FlextInfraCodegenPipelineStagesMixin",),
            ".make_bootstrap": ("FlextInfraCodegenMakeBootstrap",),
            ".mise_artifacts": ("FlextInfraCodegenMiseArtifacts",),
            ".mise_artifacts_workspace": ("FlextInfraMiseWorkspacePlanner",),
            "._mise_artifacts_files": ("FlextInfraMiseArtifactsFiles",),
            "._mise_artifacts_publication": ("publish_file_plan",),
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
