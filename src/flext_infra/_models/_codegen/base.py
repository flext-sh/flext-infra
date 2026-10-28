"""Codegen models facade: joins the family modules via MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._models import (
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenToolchain,
)
from flext_infra._models._codegen import (
    FlextInfraModelsModelsCodegenFix,
    FlextInfraModelsModelsCodegenLazyInit,
    FlextInfraModelsModelsCodegenPipeline,
    FlextInfraModelsModelsCodegenScaffold,
    FlextInfraModelsModelsCodegenTransaction,
)


class FlextInfraCodegen(
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodegenRender,
    FlextInfraModelsModelsCodegenTransaction,
    FlextInfraModelsModelsCodegenScaffold,
    FlextInfraModelsModelsCodegenFix,
    FlextInfraModelsModelsCodegenLazyInit,
    FlextInfraModelsModelsCodegenPipeline,
):
    """Models for codegen census, scaffold, and auto-fix pipelines."""


__all__: list[str] = ["FlextInfraCodegen"]
