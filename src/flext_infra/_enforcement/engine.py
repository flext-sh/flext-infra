"""Shared catalog-backed enforcement rule engine.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._enforcement.collection_sources import (
    FlextInfraEnforcementSourceCollectors,
)


class FlextInfraEnforcementEngine(FlextInfraEnforcementSourceCollectors):
    """Single SSOT-backed collector for validation, census, and fix flows."""


__all__: list[str] = ["FlextInfraEnforcementEngine"]
