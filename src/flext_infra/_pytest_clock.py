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

    @classmethod
    def start_profiler(cls) -> cProfile.Profile:
        """Share the process profiler across startup, launcher and entrypoint.

        Returns:
            The active profiler owned by this process.
        """
        if cls.profiler is None:
            cls.profiler = cProfile.Profile()
            cls.profiler.enable()
        return cls.profiler


__all__: list[str] = ["FlextInfraPytestClock"]
