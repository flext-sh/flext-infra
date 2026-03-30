# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Code generation services.

Provides code generation tools for workspace standardization,
including lazy-import init file generation (PEP 562).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.codegen import (
        census,
        cli,
        constants_quality_gate,
        fixer,
        lazy_init,
        py_typed,
        scaffolder,
    )
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.cli import FlextInfraCliCodegen
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate,
    )
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliCodegen": ["flext_infra.codegen.cli", "FlextInfraCliCodegen"],
    "FlextInfraCodegenCensus": [
        "flext_infra.codegen.census",
        "FlextInfraCodegenCensus",
    ],
    "FlextInfraCodegenConstantsQualityGate": [
        "flext_infra.codegen.constants_quality_gate",
        "FlextInfraCodegenConstantsQualityGate",
    ],
    "FlextInfraCodegenFixer": ["flext_infra.codegen.fixer", "FlextInfraCodegenFixer"],
    "FlextInfraCodegenLazyInit": [
        "flext_infra.codegen.lazy_init",
        "FlextInfraCodegenLazyInit",
    ],
    "FlextInfraCodegenPyTyped": [
        "flext_infra.codegen.py_typed",
        "FlextInfraCodegenPyTyped",
    ],
    "FlextInfraCodegenScaffolder": [
        "flext_infra.codegen.scaffolder",
        "FlextInfraCodegenScaffolder",
    ],
    "census": ["flext_infra.codegen.census", ""],
    "cli": ["flext_infra.codegen.cli", ""],
    "constants_quality_gate": ["flext_infra.codegen.constants_quality_gate", ""],
    "fixer": ["flext_infra.codegen.fixer", ""],
    "lazy_init": ["flext_infra.codegen.lazy_init", ""],
    "py_typed": ["flext_infra.codegen.py_typed", ""],
    "scaffolder": ["flext_infra.codegen.scaffolder", ""],
}

__all__ = [
    "FlextInfraCliCodegen",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "census",
    "cli",
    "constants_quality_gate",
    "fixer",
    "lazy_init",
    "py_typed",
    "scaffolder",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
