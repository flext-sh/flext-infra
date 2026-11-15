"""Utilities facade composing a part whose base is a builtin type.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityMeta


class FlextDemoUtilities(FlextDemoCapabilityMeta):
    """Facade whose MRO composes a part that cannot be deferred."""


u = FlextDemoUtilities

__all__: list[str] = ["FlextDemoUtilities", "u"]
