# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.codegen package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".census": ("FlextInfraCodegenCensus",),
    ".codegen_generation": ("FlextInfraCodegenGeneration",),
    ".conform": ("FlextInfraCodegenConform",),
    ".consolidator": ("FlextInfraCodegenConsolidator",),
    ".constants_quality_gate": ("FlextInfraCodegenQualityGate",),
    ".fixer": ("FlextInfraCodegenFixer",),
    ".layout": ("FlextInfraCodegenLayout",),
    ".lazy_init": ("FlextInfraCodegenLazyInit",),
    ".lazy_init_planner": ("FlextInfraCodegenLazyInitPlanner",),
    ".managed_conflicts": ("FlextInfraCodegenManagedConflicts",),
    ".pipeline": ("FlextInfraCodegenPipeline",),
    ".project_new": ("FlextInfraCodegenProjectNew",),
    ".py_typed": ("FlextInfraCodegenPyTyped",),
    ".scaffolder": ("FlextInfraCodegenScaffolder",),
    ".version_file": ("FlextInfraCodegenVersionFile",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
