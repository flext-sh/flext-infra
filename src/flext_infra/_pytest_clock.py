"""Capture native operation timing and profiling before importing its runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import errno
import marshal
import os
import pstats
import signal
import stat
import sys
import tempfile
import time
import traceback
from collections.abc import Callable, Iterator
from pathlib import Path
from types import FrameType, TracebackType
from typing import ClassVar
from uuid import uuid4


class FlextInfraPytestClock:
    """Own the process-local clock and immutable native profiling evidence."""

    started_at_monotonic: ClassVar[float] = time.monotonic()
    _publishing: ClassVar[set[cProfile.Profile]] = set()
    profiler: ClassVar[cProfile.Profile | None] = (
        cProfile.Profile() if sys.argv[1:2] == ["profile"] else None
    )
    if profiler is not None:
        profiler.enable()

    class SignalCheckpoint:
        """Observe once, preserving native actions and deferred publication failure."""

        def __init__(
            self,
            profile: cProfile.Profile,
            output: Path,
            previous: int | Callable[[int, FrameType | None], None],
            *,
            immutable_output: Path | None,
            previous_output: Path | None,
        ) -> None:
            self.profile = profile
            self.output = output
            self.previous = previous
            self.immutable_output = immutable_output
            self.previous_output = previous_output
            self._attempt: Iterator[bool] = iter((True,))
            self._failure: BaseException | None = None
            self._failure_traceback: TracebackType | None = None

        def on_operator_signal(self, signum: int, frame: FrameType | None) -> None:
            """Capture without restoring handlers, terminating or raising failure."""
            # Consume the attempt in one native step, including reentrant delivery.
            if not next(self._attempt, False):
                return
            if self.profile in FlextInfraPytestClock._publishing:
                return
            try:
                if frame is not None:
                    traceback.print_stack(frame)
                FlextInfraPytestClock.publish_profile(
                    self.profile,
                    self.output,
                    immutable_output=self.immutable_output,
                    previous_output=self.previous_output,
                )
            except BaseException as failure:
                self._failure = failure
                self._failure_traceback = failure.__traceback__
            finally:
                # create_stats() disables profiling even when publication fails.
                try:
                    self.profile.enable()
                except BaseException as failure:
                    if self._failure is None:
                        self._failure = failure
                        self._failure_traceback = failure.__traceback__
                    else:
                        self._failure.add_note(
                            "profile resumption failed:\n"
                            + "".join(traceback.format_exception(failure, chain=False))
                        )

        def __call__(self, signum: int, frame: FrameType | None) -> None:
            """Capture once, then preserve the original native signal action."""
            self.on_operator_signal(signum, frame)
            if signal.getsignal(signum) is self:
                signal.signal(signum, self.previous)
            try:
                if callable(self.previous):
                    self.previous(signum, frame)
                else:
                    try:
                        if (
                            self.previous == signal.SIG_DFL
                            and self._failure is not None
                        ):
                            traceback.print_exception(
                                type(self._failure),
                                self._failure,
                                self._failure_traceback,
                                chain=False,
                            )
                    finally:
                        signal.raise_signal(signum)
            except BaseException as primary:
                self._surface_failure(primary)
                raise
            self._surface_failure(None)

        def retire(self) -> None:
            """Release only owned registration and surface failure after cleanup."""
            if signal.getsignal(signal.SIGTERM) is self:
                signal.signal(signal.SIGTERM, self.previous)
            primary = sys.exception()
            if isinstance(primary, SystemExit) and (
                primary.code is None or primary.code == 0
            ):
                primary = None
            self._surface_failure(primary)

        def _surface_failure(self, primary: BaseException | None) -> None:
            if self._failure is None:
                return
            if primary is None:
                raise self._failure.with_traceback(self._failure_traceback)
            primary.add_note(
                "profile checkpoint publication failed:\n"
                + "".join(
                    traceback.format_exception(
                        type(self._failure),
                        self._failure,
                        self._failure_traceback,
                        chain=False,
                    )
                )
            )
            if isinstance(primary, SystemExit):
                try:
                    traceback.print_exception(
                        type(self._failure),
                        self._failure,
                        self._failure_traceback,
                        chain=False,
                    )
                except (OSError, ValueError) as diagnostic_failure:
                    primary.add_note(
                        f"profile failure diagnostic failed: {diagnostic_failure}"
                    )

    @staticmethod
    def profile_command(command: Callable[[], int], output: Path) -> int:
        """Profile a command while retaining its native status and first exception.

        Returns:
            The command exit status.

        """
        immutable_output = output.with_stem(f"{output.stem}-{uuid4().hex}")
        previous_output = output.with_stem(f"{output.stem}.previous-{uuid4().hex}")
        profiler = cProfile.Profile()
        status: int | None = None

        retire = FlextInfraPytestClock.register_signal_checkpoint(
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
            primary = sys.exception() if status is None else None
            if isinstance(primary, SystemExit) and (
                primary.code is None or primary.code == 0
            ):
                primary = None
            try:
                retire()
            except BaseException as checkpoint_failure:
                if primary is not None:
                    primary.add_note(
                        "profile checkpoint retirement failed:\n"
                        + "".join(
                            traceback.format_exception(checkpoint_failure, chain=False)
                        )
                    )
                elif status:
                    traceback.print_exception(checkpoint_failure)
                else:
                    primary = checkpoint_failure
                    raise
            finally:
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
                                traceback.format_exception(
                                    publication_failure, chain=False
                                )
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
        """Publish native profiling evidence without exposing partial artifacts.

        Args:
            profile: The real profiler whose current stats are recorded.
            output: The destination elected by the profiling invocation.
            immutable_output: Optional invocation-owned raw link and text statistics.
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
                    report = immutable_output.with_name(f"{immutable_output.name}.txt")
                    report_descriptor, report_name = tempfile.mkstemp(
                        dir=report.parent,
                        prefix=f".{report.name}.",
                        suffix=".tmp",
                    )
                    report_staging = Path(report_name)
                    report_identity = os.fstat(report_descriptor)
                    try:
                        with os.fdopen(
                            report_descriptor, "w", encoding="utf-8"
                        ) as report_stream:
                            report_stream.write(
                                "Native profile snapshot, not operation acceptance.\n"
                                f"Raw capture: {immutable_output.name}\n\n"
                            )
                            FlextInfraPytestClock._guard_staging_identity(
                                immutable_output, identity
                            )
                            pstats.Stats(
                                str(immutable_output), stream=report_stream
                            ).sort_stats(pstats.SortKey.CUMULATIVE).print_stats()
                            FlextInfraPytestClock._guard_staging_identity(
                                immutable_output, identity
                            )
                            report_stream.flush()
                            os.fsync(report_stream.fileno())
                        FlextInfraPytestClock._guard_staging_identity(
                            report_staging, report_identity
                        )
                        report.hardlink_to(report_staging)
                    finally:
                        FlextInfraPytestClock._discard_staging(
                            report_staging, report_identity
                        )
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

        checkpoint = cls.SignalCheckpoint(
            profile,
            output,
            previous,
            immutable_output=immutable_output,
            previous_output=previous_output,
        )
        signal.signal(signal.SIGTERM, checkpoint)
        return checkpoint.retire


__all__: list[str] = ["FlextInfraPytestClock"]
