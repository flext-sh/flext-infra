"""Package version the root initializer binds eagerly from an internal part.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo._capability import FlextDemoCapabilityBase

__version__ = f"{FlextDemoCapabilityBase.base_value()}.0.0"

__all__: list[str] = ["__version__"]
