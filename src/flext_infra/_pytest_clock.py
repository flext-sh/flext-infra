"""Capture pytest timing and optional profiling before importing its runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import sys
import time
from typing import ClassVar


class FlextInfraPytestClock:
    """Own the process-local clock for the canonical pytest entrypoint."""

    started_at_monotonic: ClassVar[float] = time.monotonic()
    profiler: ClassVar[cProfile.Profile | None] = (
        cProfile.Profile() if sys.argv[1:2] == ["profile"] else None
    )
    if profiler is not None:
        profiler.enable()
