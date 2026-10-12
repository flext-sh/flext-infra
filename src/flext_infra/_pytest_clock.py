"""Capture pytest timing and optional profiling before importing its runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import errno
import marshal
import os
import signal
import sys
import tempfile
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

    @staticmethod
    def publish_profile(profile: cProfile.Profile, output: Path) -> None:
        """Publish native pstats atomically without exposing an incomplete artifact.

        Args:
            profile: The real profiler whose current stats are recorded.
            output: The destination elected by the profiling invocation.
        """
        stream = tempfile.NamedTemporaryFile(
            mode="wb",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        )
        staging = Path(stream.name)
        identity = os.fstat(stream.fileno())
        try:
            with stream:
                profile.create_stats()
                marshal.dump(profile.stats, stream)
                stream.flush()
                os.fsync(stream.fileno())
            current = staging.stat(follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (
                identity.st_dev,
                identity.st_ino,
            ):
                raise OSError(errno.ESTALE, "profile staging identity changed")
            Path(staging).replace(output)
        finally:
            failure = sys.exception()
            try:
                if staging.exists() or staging.is_symlink():
                    current = staging.stat(follow_symlinks=False)
                    if (current.st_dev, current.st_ino) != (
                        identity.st_dev,
                        identity.st_ino,
                    ):
                        raise OSError(
                            errno.ESTALE,
                            "profile staging identity changed before cleanup",
                        )
                    staging.unlink()
            except OSError as cleanup_failure:
                if failure is None:
                    raise
                failure.add_note(f"profile staging cleanup failed: {cleanup_failure}")

    @classmethod
    def register_signal_checkpoint(
        cls,
        profile: cProfile.Profile,
        output: Path,
    ) -> None:
        """Persist measured progress before preserving native termination handling.

        Args:
            profile: The real profiler elected by the invocation.
            output: The profile artifact elected by the canonical launcher.

        Raises:
            RuntimeError: If the native termination handler cannot be observed.
        """
        previous = signal.getsignal(signal.SIGTERM)
        if previous is None:
            msg = "cannot observe native profiler termination handler"
            raise RuntimeError(msg)

        def checkpoint(signum: int, frame: FrameType | None) -> None:
            """Persist the profiler, then delegate the original signal unchanged."""
            try:
                cls.publish_profile(profile, output)
            finally:
                signal.signal(signum, previous)
                if callable(previous):
                    previous(signum, frame)
                else:
                    signal.raise_signal(signum)

        signal.signal(signal.SIGTERM, checkpoint)
