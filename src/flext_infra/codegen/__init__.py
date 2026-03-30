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
        census,
        cli,
        constants_quality_gate,
        fixer,
        lazy_init,
        py_typed,
        scaffolder,
    )
    from flext_infra.codegen.census import *
    from flext_infra.codegen.cli import *
    from flext_infra.codegen.constants_quality_gate import *
    from flext_infra.codegen.fixer import *
    from flext_infra.codegen.lazy_init import *
    from flext_infra.codegen.py_typed import *
    from flext_infra.codegen.scaffolder import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliCodegen": "flext_infra.codegen.cli",
    "FlextInfraCodegenCensus": "flext_infra.codegen.census",
    "FlextInfraCodegenConstantsQualityGate": "flext_infra.codegen.constants_quality_gate",
    "FlextInfraCodegenFixer": "flext_infra.codegen.fixer",
    "FlextInfraCodegenLazyInit": "flext_infra.codegen.lazy_init",
    "FlextInfraCodegenPyTyped": "flext_infra.codegen.py_typed",
    "FlextInfraCodegenScaffolder": "flext_infra.codegen.scaffolder",
    "census": "flext_infra.codegen.census",
    "cli": "flext_infra.codegen.cli",
    "constants_quality_gate": "flext_infra.codegen.constants_quality_gate",
    "fixer": "flext_infra.codegen.fixer",
    "lazy_init": "flext_infra.codegen.lazy_init",
    "py_typed": "flext_infra.codegen.py_typed",
    "scaffolder": "flext_infra.codegen.scaffolder",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
