# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
