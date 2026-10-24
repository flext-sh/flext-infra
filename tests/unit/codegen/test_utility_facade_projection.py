"""Public evidence for declared utility-facade projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests.unit.codegen._utility_facade_projection.behavior import UtilityFacadeBehavior
from tests.unit.codegen._utility_facade_projection.planning import UtilityFacadePlanning
from tests.unit.codegen._utility_facade_projection.publication import (
    UtilityFacadePublication,
)


class TestsFlextInfraUtilityFacadeProjection(
    UtilityFacadePlanning,
    UtilityFacadeBehavior,
    UtilityFacadePublication,
):
    """Exercise declared owner projection only through ``u.Infra``."""
