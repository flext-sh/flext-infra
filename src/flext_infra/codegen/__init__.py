# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .census import FlextInfraCodegenCensus
    from .codegen_generation import FlextInfraCodegenGeneration
    from .conform import FlextInfraCodegenConform
    from .consolidator import FlextInfraCodegenConsolidator
    from .constants_quality_gate import FlextInfraCodegenQualityGate
    from .fixer import FlextInfraCodegenFixer
    from .layout import FlextInfraCodegenLayout
    from .lazy_init import FlextInfraCodegenLazyInit
    from .lazy_init_planner import FlextInfraCodegenLazyInitPlanner
    from .managed_conflicts import FlextInfraCodegenManagedConflicts
    from .pipeline import FlextInfraCodegenPipeline
    from .project_new import FlextInfraCodegenProjectNew
    from .py_typed import FlextInfraCodegenPyTyped
    from .scaffolder import FlextInfraCodegenScaffolder
    from .version_file import FlextInfraCodegenVersionFile

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

__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLayout",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenLazyInitPlanner",
    "FlextInfraCodegenManagedConflicts",
    "FlextInfraCodegenPipeline",
    "FlextInfraCodegenProjectNew",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenQualityGate",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenVersionFile",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
