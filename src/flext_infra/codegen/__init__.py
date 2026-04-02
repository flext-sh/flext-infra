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
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.codegen import (
        _codegen_coercion,
        _codegen_execution_tools,
        _codegen_generation,
        _codegen_metrics,
        _codegen_metrics_checks,
        _codegen_snapshot,
        _constants,
        _models,
        _utilities,
        _utilities_codegen_ast_parsing,
        _utilities_codegen_constant_transformer,
        _utilities_codegen_constant_visitor,
        _utilities_codegen_execution,
        _utilities_codegen_governance,
        _utilities_transforms,
        census,
        cli,
        constants_quality_gate,
        fixer,
        lazy_init,
        py_typed,
        scaffolder,
    )
    from flext_infra.codegen._codegen_coercion import FlextInfraCodegenCoercion
    from flext_infra.codegen._codegen_execution_tools import (
        FlextInfraCodegenExecutionTools,
    )
    from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration
    from flext_infra.codegen._codegen_metrics import FlextInfraCodegenMetrics
    from flext_infra.codegen._codegen_metrics_checks import (
        FlextInfraCodegenMetricsChecks,
    )
    from flext_infra.codegen._codegen_snapshot import FlextInfraCodegenSnapshot
    from flext_infra.codegen._constants import FlextInfraCodegenConstants
    from flext_infra.codegen._models import FlextInfraCodegenModels
    from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen
    from flext_infra.codegen._utilities_codegen_ast_parsing import (
        FlextInfraUtilitiesCodegenAstParsing,
    )
    from flext_infra.codegen._utilities_codegen_constant_transformer import (
        FlextInfraUtilitiesCodegenConstantTransformation,
    )
    from flext_infra.codegen._utilities_codegen_constant_visitor import (
        FlextInfraUtilitiesCodegenConstantDetection,
    )
    from flext_infra.codegen._utilities_codegen_execution import (
        FlextInfraUtilitiesCodegenExecution,
    )
    from flext_infra.codegen._utilities_codegen_governance import (
        FlextInfraUtilitiesCodegenGovernance,
    )
    from flext_infra.codegen._utilities_transforms import (
        FlextInfraUtilitiesCodegenTransforms,
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

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCliCodegen": "flext_infra.codegen.cli",
    "FlextInfraCodegenCensus": "flext_infra.codegen.census",
    "FlextInfraCodegenCoercion": "flext_infra.codegen._codegen_coercion",
    "FlextInfraCodegenConstants": "flext_infra.codegen._constants",
    "FlextInfraCodegenConstantsQualityGate": "flext_infra.codegen.constants_quality_gate",
    "FlextInfraCodegenExecutionTools": "flext_infra.codegen._codegen_execution_tools",
    "FlextInfraCodegenFixer": "flext_infra.codegen.fixer",
    "FlextInfraCodegenGeneration": "flext_infra.codegen._codegen_generation",
    "FlextInfraCodegenLazyInit": "flext_infra.codegen.lazy_init",
    "FlextInfraCodegenMetrics": "flext_infra.codegen._codegen_metrics",
    "FlextInfraCodegenMetricsChecks": "flext_infra.codegen._codegen_metrics_checks",
    "FlextInfraCodegenModels": "flext_infra.codegen._models",
    "FlextInfraCodegenPyTyped": "flext_infra.codegen.py_typed",
    "FlextInfraCodegenScaffolder": "flext_infra.codegen.scaffolder",
    "FlextInfraCodegenSnapshot": "flext_infra.codegen._codegen_snapshot",
    "FlextInfraUtilitiesCodegen": "flext_infra.codegen._utilities",
    "FlextInfraUtilitiesCodegenAstParsing": "flext_infra.codegen._utilities_codegen_ast_parsing",
    "FlextInfraUtilitiesCodegenConstantDetection": "flext_infra.codegen._utilities_codegen_constant_visitor",
    "FlextInfraUtilitiesCodegenConstantTransformation": "flext_infra.codegen._utilities_codegen_constant_transformer",
    "FlextInfraUtilitiesCodegenExecution": "flext_infra.codegen._utilities_codegen_execution",
    "FlextInfraUtilitiesCodegenGovernance": "flext_infra.codegen._utilities_codegen_governance",
    "FlextInfraUtilitiesCodegenTransforms": "flext_infra.codegen._utilities_transforms",
    "_codegen_coercion": "flext_infra.codegen._codegen_coercion",
    "_codegen_execution_tools": "flext_infra.codegen._codegen_execution_tools",
    "_codegen_generation": "flext_infra.codegen._codegen_generation",
    "_codegen_metrics": "flext_infra.codegen._codegen_metrics",
    "_codegen_metrics_checks": "flext_infra.codegen._codegen_metrics_checks",
    "_codegen_snapshot": "flext_infra.codegen._codegen_snapshot",
    "_constants": "flext_infra.codegen._constants",
    "_models": "flext_infra.codegen._models",
    "_utilities": "flext_infra.codegen._utilities",
    "_utilities_codegen_ast_parsing": "flext_infra.codegen._utilities_codegen_ast_parsing",
    "_utilities_codegen_constant_transformer": "flext_infra.codegen._utilities_codegen_constant_transformer",
    "_utilities_codegen_constant_visitor": "flext_infra.codegen._utilities_codegen_constant_visitor",
    "_utilities_codegen_execution": "flext_infra.codegen._utilities_codegen_execution",
    "_utilities_codegen_governance": "flext_infra.codegen._utilities_codegen_governance",
    "_utilities_transforms": "flext_infra.codegen._utilities_transforms",
    "census": "flext_infra.codegen.census",
    "cli": "flext_infra.codegen.cli",
    "constants_quality_gate": "flext_infra.codegen.constants_quality_gate",
    "fixer": "flext_infra.codegen.fixer",
    "lazy_init": "flext_infra.codegen.lazy_init",
    "py_typed": "flext_infra.codegen.py_typed",
    "scaffolder": "flext_infra.codegen.scaffolder",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
