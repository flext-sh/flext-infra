# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCliCodegen": ("flext_infra.codegen.cli", "FlextInfraCliCodegen"),
    "FlextInfraCodegenCensus": (
        "flext_infra.codegen.census",
        "FlextInfraCodegenCensus",
    ),
    "FlextInfraCodegenFixer": ("flext_infra.codegen.fixer", "FlextInfraCodegenFixer"),
    "FlextInfraCodegenGeneration": (
        "flext_infra.codegen._codegen_generation",
        "FlextInfraCodegenGeneration",
    ),
    "FlextInfraCodegenLazyInit": (
        "flext_infra.codegen.lazy_init",
        "FlextInfraCodegenLazyInit",
    ),
    "FlextInfraCodegenPyTyped": (
        "flext_infra.codegen.py_typed",
        "FlextInfraCodegenPyTyped",
    ),
    "FlextInfraCodegenScaffolder": (
        "flext_infra.codegen.scaffolder",
        "FlextInfraCodegenScaffolder",
    ),
    "FlextInfraConstantsCodegenQualityGate": (
        "flext_infra.codegen.constants_quality_gate",
        "FlextInfraConstantsCodegenQualityGate",
    ),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
