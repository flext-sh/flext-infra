"""Examples part whose base an installed distribution's initializer publishes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import FlextUtilities


class ExamplesFlextDemoCapabilityExtra(FlextUtilities):
    """Namespace part extending the facade an installed provider publishes."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
