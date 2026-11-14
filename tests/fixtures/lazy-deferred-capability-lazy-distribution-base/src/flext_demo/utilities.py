"""Utilities facade composing a part based on another lazy distribution's facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityCoreBased


class FlextDemoUtilities(FlextDemoCapabilityCoreBased):
    """Facade whose MRO composes a part with a lazy-distribution base."""


u = FlextDemoUtilities

__all__: list[str] = ["FlextDemoUtilities", "u"]
