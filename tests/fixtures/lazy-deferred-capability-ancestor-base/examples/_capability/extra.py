"""Examples part whose base is published by another package's initializer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import FlextDemoUtilities


class ExamplesFlextDemoCapabilityExtra(FlextDemoUtilities):
    """Namespace part extending the facade the source package publishes."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
