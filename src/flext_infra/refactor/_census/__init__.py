# AUTO-GENERATED FILE — Regenerate with: make gen
"""Internal package for census.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.refactor._census.collect import FlextInfraRefactorCensusCollect
    from flext_infra.refactor._census.collect_helpers import (
        FlextInfraRefactorCensusCollectHelpers,
    )
    from flext_infra.refactor._census.filters import FlextInfraRefactorCensusFilters
    from flext_infra.refactor._census.objects import FlextInfraRefactorCensusObjects
    from flext_infra.refactor._census.project import FlextInfraRefactorCensusProject
    from flext_infra.refactor._census.removal import FlextInfraRefactorCensusRemoval
    from flext_infra.refactor._census.render import FlextInfraRefactorCensusRender

__all__: tuple[str, ...] = (
    "FlextInfraRefactorCensusCollect",
    "FlextInfraRefactorCensusCollectHelpers",
    "FlextInfraRefactorCensusFilters",
    "FlextInfraRefactorCensusObjects",
    "FlextInfraRefactorCensusProject",
    "FlextInfraRefactorCensusRemoval",
    "FlextInfraRefactorCensusRender",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRefactorCensusCollect": ".collect",
        "FlextInfraRefactorCensusCollectHelpers": ".collect_helpers",
        "FlextInfraRefactorCensusFilters": ".filters",
        "FlextInfraRefactorCensusObjects": ".objects",
        "FlextInfraRefactorCensusProject": ".project",
        "FlextInfraRefactorCensusRemoval": ".removal",
        "FlextInfraRefactorCensusRender": ".render",
    }),
    public_exports=__all__,
)
