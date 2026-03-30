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

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen import (
        census as census,
        cli as cli,
        constants_quality_gate as constants_quality_gate,
        fixer as fixer,
        lazy_init as lazy_init,
        py_typed as py_typed,
        scaffolder as scaffolder,
    )
    from flext_infra.codegen.census import (
        FlextInfraCodegenCensus as FlextInfraCodegenCensus,
    )
    from flext_infra.codegen.cli import FlextInfraCliCodegen as FlextInfraCliCodegen
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate as FlextInfraCodegenConstantsQualityGate,
    )
    from flext_infra.codegen.fixer import (
        FlextInfraCodegenFixer as FlextInfraCodegenFixer,
    )
    from flext_infra.codegen.lazy_init import (
        FlextInfraCodegenLazyInit as FlextInfraCodegenLazyInit,
    )
    from flext_infra.codegen.py_typed import (
        FlextInfraCodegenPyTyped as FlextInfraCodegenPyTyped,
    )
    from flext_infra.codegen.scaffolder import (
        FlextInfraCodegenScaffolder as FlextInfraCodegenScaffolder,
    )

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

_EXPORTS: Sequence[str] = [
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
