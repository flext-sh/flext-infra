"""Typed runtime boundary facade for Rope, which lacks typing metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._rope.runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)


class FlextInfraUtilitiesRopeRuntime(
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesTypesRopeRuntime,
):
    """Compose typed Rope runtime boundary helpers."""


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntime"]
