"""Utilities facade with a namespace class another package extends.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityHeavy


class FlextDemoUtilities(FlextDemoCapabilityHeavy):
    """Facade whose MRO composes the heavy capability mixin."""

    class Demo:
        """Namespace an ancestor-package part extends by attribute."""

        DEMO_VALUE = 4


u = FlextDemoUtilities

__all__: list[str] = ["FlextDemoUtilities", "u"]
