"""Codegen models facade: joins the family modules via MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

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


class FlextInfraCodegen(
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenTransaction,
    FlextInfraModelsCodegenScaffold,
    FlextInfraModelsCodegenFix,
    FlextInfraModelsCodegenLazyInit,
    FlextInfraModelsCodegenPipeline,
):
    """Models for codegen census, scaffold, and auto-fix pipelines."""


__all__: list[str] = ["FlextInfraCodegen"]
