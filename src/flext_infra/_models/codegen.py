"""Codegen models composition for the infrastructure namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._models import (
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenToolchain,
)
from flext_infra._models._codegen import (
    FlextInfraModelsCodegenFix,
    FlextInfraModelsCodegenLazyInit,
    FlextInfraModelsCodegenPipeline,
    FlextInfraModelsCodegenScaffold,
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
