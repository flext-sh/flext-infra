# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.codegen._codegen_generation as _flext_infra_codegen__codegen_generation

    _codegen_generation = _flext_infra_codegen__codegen_generation
    import flext_infra.codegen._utilities as _flext_infra_codegen__utilities
    from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration

    _utilities = _flext_infra_codegen__utilities
    import flext_infra.codegen.census as _flext_infra_codegen_census
    from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen

    census = _flext_infra_codegen_census
    import flext_infra.codegen.cli as _flext_infra_codegen_cli
    from flext_infra.codegen.census import FlextInfraCodegenCensus

    cli = _flext_infra_codegen_cli
    import flext_infra.codegen.constants_quality_gate as _flext_infra_codegen_constants_quality_gate
    from flext_infra.codegen.cli import FlextInfraCliCodegen

    constants_quality_gate = _flext_infra_codegen_constants_quality_gate
    import flext_infra.codegen.fixer as _flext_infra_codegen_fixer
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate,
    )

    fixer = _flext_infra_codegen_fixer
    import flext_infra.codegen.lazy_init as _flext_infra_codegen_lazy_init
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer

    lazy_init = _flext_infra_codegen_lazy_init
    import flext_infra.codegen.py_typed as _flext_infra_codegen_py_typed
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit

    py_typed = _flext_infra_codegen_py_typed
    import flext_infra.codegen.scaffolder as _flext_infra_codegen_scaffolder
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped

    scaffolder = _flext_infra_codegen_scaffolder
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
_LAZY_IMPORTS = {
    "FlextInfraCliCodegen": ("flext_infra.codegen.cli", "FlextInfraCliCodegen"),
    "FlextInfraCodegenCensus": (
        "flext_infra.codegen.census",
        "FlextInfraCodegenCensus",
    ),
    "FlextInfraCodegenConstantsQualityGate": (
        "flext_infra.codegen.constants_quality_gate",
        "FlextInfraCodegenConstantsQualityGate",
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
    "FlextInfraUtilitiesCodegen": (
        "flext_infra.codegen._utilities",
        "FlextInfraUtilitiesCodegen",
    ),
    "_codegen_generation": "flext_infra.codegen._codegen_generation",
    "_utilities": "flext_infra.codegen._utilities",
    "census": "flext_infra.codegen.census",
    "cli": "flext_infra.codegen.cli",
    "constants_quality_gate": "flext_infra.codegen.constants_quality_gate",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer": "flext_infra.codegen.fixer",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "lazy_init": "flext_infra.codegen.lazy_init",
    "py_typed": "flext_infra.codegen.py_typed",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scaffolder": "flext_infra.codegen.scaffolder",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliCodegen",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraUtilitiesCodegen",
    "_codegen_generation",
    "_utilities",
    "census",
    "cli",
    "constants_quality_gate",
    "d",
    "e",
    "fixer",
    "h",
    "lazy_init",
    "py_typed",
    "r",
    "s",
    "scaffolder",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
