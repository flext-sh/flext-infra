"""Capability part whose base is the facade of another generated lazy distribution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import FlextConstants


class FlextDemoCapabilityCoreBased(FlextConstants):
    """Part a facade composes; its base loads lazily from flext_core."""

    DEMO_LIMIT: int = 3


__all__: list[str] = ["FlextDemoCapabilityCoreBased"]
