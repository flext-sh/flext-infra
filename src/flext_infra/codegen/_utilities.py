"""Codegen utilities composition for the infrastructure namespace."""

from __future__ import annotations

from flext_infra import (
    FlextInfraUtilitiesCodegenConstantAnalysis,
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesCodegenConstantTransformation,
    FlextInfraUtilitiesCodegenExecution,
    FlextInfraUtilitiesCodegenImportCycles,
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
