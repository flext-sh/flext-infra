"""Utilities facade composing a class whose base is a third-party type.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityClient


class FlextDemoUtilities(FlextDemoCapabilityClient):
    """Facade whose MRO composes a part that cannot be deferred."""


u = FlextDemoUtilities

__all__: list[str] = ["FlextDemoUtilities", "u"]
