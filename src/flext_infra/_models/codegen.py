"""Codegen models composition for the infrastructure namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._models import (
    FlextInfraModelsCodegenFix,
    FlextInfraModelsCodegenLazyInit,
    FlextInfraModelsCodegenPipeline,
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenScaffold,
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodegenTransaction,
)


class FlextInfraModelsCodegen(
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenTransaction,
    FlextInfraModelsCodegenScaffold,
    FlextInfraModelsCodegenFix,
    FlextInfraModelsCodegenLazyInit,
    FlextInfraModelsCodegenPipeline,
):
    """Codegen models composition for the infrastructure namespace."""


__all__: list[str] = ["FlextInfraModelsCodegen"]
