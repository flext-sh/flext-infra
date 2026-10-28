"""Extracted facade class for dependency.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._dependency import FlextInfraUtilitiesDependencyDeptry


class FlextInfraUtilitiesDependency(
    FlextInfraUtilitiesDependencyDeptry,
):
    """Facade for dependency."""


__all__: list[str] = ["FlextInfraUtilitiesDependency"]
