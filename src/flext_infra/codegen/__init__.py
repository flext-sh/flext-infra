# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
    from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.pyproject_keys import FlextInfraCodegenPyprojectKeys
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".census": ("FlextInfraCodegenCensus",),
        ".codegen_generation": ("FlextInfraCodegenGeneration",),
        ".consolidator": ("FlextInfraCodegenConsolidator",),
        ".constants_quality_gate": ("FlextInfraCodegenQualityGate",),
        ".fixer": ("FlextInfraCodegenFixer",),
        ".lazy_init": ("FlextInfraCodegenLazyInit",),
        ".lazy_init_planner": ("FlextInfraCodegenLazyInitPlanner",),
        ".pipeline": ("FlextInfraCodegenPipeline",),
        ".py_typed": ("FlextInfraCodegenPyTyped",),
        ".pyproject_keys": ("FlextInfraCodegenPyprojectKeys",),
        ".scaffolder": ("FlextInfraCodegenScaffolder",),
        ".version_file": ("FlextInfraCodegenVersionFile",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
