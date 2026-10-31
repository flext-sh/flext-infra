"""Compose source-owned facade capabilities without a second Python engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesFacadeComponents,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeClassMove,
)


class FlextInfraUtilitiesCodegenFacades(
    FlextInfraUtilitiesFacadeComponents,
    FlextInfraUtilitiesRopeClassMove,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesWorkspaceSnapshot,
):
    """Expose native publication and projection owners through the same MRO."""


__all__: list[str] = ["FlextInfraUtilitiesCodegenFacades"]
