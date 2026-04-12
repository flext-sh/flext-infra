# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".census": ("FlextInfraCodegenCensus",),
        ".cli": ("FlextInfraCliCodegen",),
        ".codegen_generation": ("FlextInfraCodegenGeneration",),
        ".constants_quality_gate": ("FlextInfraConstantsCodegenQualityGate",),
        ".fixer": ("FlextInfraCodegenFixer",),
        ".lazy_init": ("FlextInfraCodegenLazyInit",),
        ".lazy_init_planner": ("FlextInfraCodegenLazyInitPlanner",),
        ".py_typed": ("FlextInfraCodegenPyTyped",),
        ".scaffolder": ("FlextInfraCodegenScaffolder",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
