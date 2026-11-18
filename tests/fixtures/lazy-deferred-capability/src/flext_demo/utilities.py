"""Utilities facade composing the capability mixin by MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityHeavy


class FlextDemoUtilities(FlextDemoCapabilityHeavy):
    """Facade whose MRO composes the heavy capability mixin."""


u = FlextDemoUtilities

__all__: list[str] = ["FlextDemoUtilities", "u"]
