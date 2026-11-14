"""Examples part whose base is the letter another package publishes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import u


class ExamplesFlextDemoCapabilityExtra(u):
    """Namespace part extending the facade through its published letter."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
