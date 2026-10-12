"""Capture pytest timing and optional profiling before importing its runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import signal
import sys
import time
from pathlib import Path
from types import FrameType
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

    @classmethod
    def register_signal_checkpoint(cls, output: Path) -> None:
        """Persist measured progress before preserving native termination handling.

        Args:
            output: The profile artifact elected by the canonical launcher.

        Raises:
            RuntimeError: If the native termination handler cannot be observed.
        """
        profile = cls.start_profiler()
        previous = signal.getsignal(signal.SIGTERM)
        if previous is None:
            msg = "cannot observe native profiler termination handler"
            raise RuntimeError(msg)

        def checkpoint(signum: int, frame: FrameType | None) -> None:
            """Persist the profiler, then delegate the original signal unchanged."""
            try:
                profile.dump_stats(str(output))
            finally:
                signal.signal(signum, previous)
                if callable(previous):
                    previous(signum, frame)
                else:
                    signal.raise_signal(signum)

        signal.signal(signal.SIGTERM, checkpoint)
