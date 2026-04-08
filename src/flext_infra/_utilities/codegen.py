"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

from flext_infra._utilities.codegen_constants import (
    FlextInfraUtilitiesCodegenConstantAnalysis,
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesCodegenConstantTransformation,
)
from flext_infra._utilities.codegen_execution import FlextInfraUtilitiesCodegenExecution
from flext_infra._utilities.codegen_import_cycles import (
    FlextInfraUtilitiesCodegenImportCycles,
)
from flext_infra._utilities.codegen_lazy import (
    FlextInfraUtilitiesCodegenLazyAliases,
    FlextInfraUtilitiesCodegenLazyScanning,
)
from flext_infra._utilities.codegen_namespace import (
    FlextInfraUtilitiesCodegenNamespace,
)


class FlextInfraUtilitiesCodegen(
    FlextInfraUtilitiesCodegenConstantAnalysis,
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesCodegenConstantTransformation,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodegenImportCycles,
    FlextInfraUtilitiesCodegenLazyAliases,
    FlextInfraUtilitiesCodegenLazyScanning,
    FlextInfraUtilitiesCodegenExecution,
):
    """Compose all codegen utility concerns for ``u.Infra``."""


__all__ = ["FlextInfraUtilitiesCodegen"]
