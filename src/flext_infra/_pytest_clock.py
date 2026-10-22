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
import stat
import sys
import tempfile
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import ClassVar
from uuid import uuid4


class FlextInfraPytestClock:
    """Own the process-local clock for the canonical pytest entrypoint."""

    started_at_monotonic: ClassVar[float] = time.monotonic()
    _publishing: ClassVar[set[cProfile.Profile]] = set()
    profiler: ClassVar[cProfile.Profile | None] = (
        cProfile.Profile() if sys.argv[1:2] == ["profile"] else None
    )
    if profiler is not None:
        profiler.enable()

    @staticmethod
    def profile_command(command: Callable[[], int], output: Path) -> int:
        """Profile a command while retaining its native status and first exception.

        Returns:
            The command exit status.

        """
        immutable_output = output.with_stem(f"{output.stem}-{uuid4().hex}")
        previous_output = output.with_stem(f"{output.stem}.previous-{uuid4().hex}")
        profiler = cProfile.Profile()
        previous = signal.getsignal(signal.SIGTERM)
        status: int | None = None

        FlextInfraPytestClock.register_signal_checkpoint(
            profiler,
            output,
            immutable_output=immutable_output.with_suffix(".checkpoint.pstats"),
            previous_output=previous_output.with_suffix(".checkpoint.pstats"),
        )
        profiler.enable()
        try:
            status = command()
            return status
        finally:
            profiler.disable()
            signal.signal(signal.SIGTERM, previous)
            primary = sys.exception() if status is None else None
            try:
                FlextInfraPytestClock.publish_profile(
                    profiler,
                    output,
                    immutable_output=immutable_output,
                    previous_output=previous_output,
                )
            except BaseException as publication_failure:
                if primary is not None:
                    primary.add_note(
                        "profile publication failed:\n"
                        + "".join(
                            traceback.format_exception(publication_failure, chain=False)
                        )
                    )
                elif status:
                    traceback.print_exception(publication_failure)
                else:
                    raise

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
    def _guard_staging_identity(staging: Path, identity: os.stat_result) -> None:
        """Fail when the staging file no longer matches its recorded identity.

        Args:
            staging: The staging path whose live identity is compared.
            identity: The device and inode captured when the file was opened.

        Raises:
            OSError: If the live device and inode differ from ``identity``.

        """
        current = staging.stat(follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino):
            msg = "profile staging identity changed"
            raise OSError(errno.ESTALE, msg)

    @staticmethod
    def _discard_staging(staging: Path, identity: os.stat_result) -> None:
        """Remove the staging file or attach its cleanup failure to the active error.

        Args:
            staging: The staging path replaced by a successful publication.
            identity: The device and inode that authorize the removal.

        Raises:
            OSError: If cleanup fails while no earlier exception is active.

        """
        failure = sys.exception()
        try:
            if staging.exists() or staging.is_symlink():
                FlextInfraPytestClock._guard_staging_identity(staging, identity)
                staging.unlink()
        except OSError as cleanup_failure:
            if failure is None:
                raise
            failure.add_note(f"profile staging cleanup failed: {cleanup_failure}")

    @staticmethod
    def publish_profile(
        profile: cProfile.Profile,
        output: Path,
        *,
        immutable_output: Path | None = None,
        previous_output: Path | None = None,
    ) -> None:
        """Publish native pstats atomically without exposing an incomplete artifact.

        Args:
            profile: The real profiler whose current stats are recorded.
            output: The destination elected by the profiling invocation.
            immutable_output: Optional invocation-owned link to the staged inode.
            previous_output: Optional retained link to the previous completed artifact.

        Raises:
            OSError: If staging identity or atomic publication fails.
            RuntimeError: If the same profiler is already being published.

        """
        if profile in FlextInfraPytestClock._publishing:
            msg = "profile publication is already active"
            raise RuntimeError(msg)
        FlextInfraPytestClock._publishing.add(profile)
        try:
            descriptor, name = tempfile.mkstemp(
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
            )
            staging = Path(name)
            identity = os.fstat(descriptor)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    profile.create_stats()
                    marshal.dump(profile.stats, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                FlextInfraPytestClock._guard_staging_identity(staging, identity)
                if immutable_output is not None:
                    immutable_output.hardlink_to(staging)
                if previous_output is not None:
                    try:
                        previous = output.lstat()
                    except FileNotFoundError:
                        previous = None
                    if previous is not None:
                        if not stat.S_ISREG(previous.st_mode):
                            msg = "previous profile artifact is not a regular file"
                            raise OSError(errno.EINVAL, msg)
                        os.link(output, previous_output, follow_symlinks=False)
                        FlextInfraPytestClock._guard_staging_identity(
                            previous_output, previous
                        )
                Path(staging).replace(output)
            finally:
                FlextInfraPytestClock._discard_staging(staging, identity)
        finally:
            FlextInfraPytestClock._publishing.remove(profile)

    @classmethod
    def register_signal_checkpoint(
        cls,
        profile: cProfile.Profile,
        output: Path,
        *,
        immutable_output: Path | None = None,
        previous_output: Path | None = None,
    ) -> Callable[[], None]:
        """Persist measured progress before preserving native termination handling.

        Args:
            profile: The real profiler elected by the invocation.
            output: The profile artifact elected by the canonical launcher.
            immutable_output: Invocation-owned link to the interrupted profile.
            previous_output: Retained link to the previously published profile.

        Returns:
            A callback retiring only this checkpoint's signal ownership.

        Raises:
            RuntimeError: If the native termination handler cannot be observed.

        """
        previous = signal.getsignal(signal.SIGTERM)
        if previous is None:
            msg = "cannot observe native profiler termination handler"
            raise RuntimeError(msg)

        def checkpoint(signum: int, frame: FrameType | None) -> None:
            """Persist the profiler, then delegate the original signal unchanged."""
            signal.signal(signum, previous)
            publishing = profile in cls._publishing
            try:
                if frame is not None:
                    traceback.print_stack(frame)
                if not publishing:
                    cls.publish_profile(
                        profile,
                        output,
                        immutable_output=immutable_output,
                        previous_output=previous_output,
                    )
            finally:
                signal.signal(signum, previous)
                if callable(previous):
                    previous(signum, frame)
                else:
                    signal.raise_signal(signum)
                # create_stats() disables profiling; returning handlers keep
                # the command alive and must keep measuring its remaining work.
                if not publishing:
                    profile.enable()

        signal.signal(signal.SIGTERM, checkpoint)

        def retire() -> None:
            """Release only this checkpoint's signal ownership."""
            if signal.getsignal(signal.SIGTERM) is checkpoint:
                signal.signal(signal.SIGTERM, previous)

        return retire


__all__: list[str] = ["FlextInfraPytestClock"]
