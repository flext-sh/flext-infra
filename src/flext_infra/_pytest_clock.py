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
from contextvars import ContextVar
from pathlib import Path
from threading import get_ident
from types import BuiltinMethodType, FrameType, MethodType
from typing import ClassVar
from uuid import uuid4


class FlextInfraPytestClock:
    """Own the process-local clock and immutable native profiling evidence."""

    started_at_monotonic: ClassVar[float] = time.monotonic()
    _publishing: ClassVar[set[cProfile.Profile]] = set()
    _threads: ClassVar[dict[cProfile.Profile, int]] = {}
    _operation_profile: ClassVar[ContextVar[cProfile.Profile | None]] = ContextVar(
        "flext_infra_operation_profile", default=None
    )
    profiler: ClassVar[cProfile.Profile | None] = None

    @staticmethod
    def _gate[**P, R](callback: Callable[P, R], owner: int) -> Callable[P, R | None]:
        def dispatch(*args: P.args, **kwargs: P.kwargs) -> R | None:
            return callback(*args, **kwargs) if get_ident() == owner else None

        return dispatch

    @classmethod
    def create_profiler(cls) -> cProfile.Profile:
        """Return a native profiler gated before any productive stack events."""
        profile = cProfile.Profile()
        owner = cls._threads[profile] = get_ident()
        tool = sys.monitoring.PROFILER_ID
        try:
            profile.enable()
            mask = sys.monitoring.get_events(tool)
            sys.monitoring.set_events(tool, 0)
            if not mask:
                msg = "native profiler enabled no monitoring events"
                raise RuntimeError(msg)
            remaining = mask
            if mask & sys.monitoring.events.CALL:
                remaining |= (
                    sys.monitoring.events.C_RETURN | sys.monitoring.events.C_RAISE
                )
            while remaining:
                event = remaining & -remaining
                remaining ^= event
                callback = sys.monitoring.register_callback(tool, event, None)
                if not isinstance(callback, (BuiltinMethodType, MethodType)) or (
                    callback.__self__ is not profile
                ):
                    sys.monitoring.register_callback(tool, event, callback)
                    msg = "monitoring callback belongs to another engine"
                    raise RuntimeError(msg)
                sys.monitoring.register_callback(
                    tool, event, cls._gate(callback, owner)
                )
            profile.clear()
            sys.monitoring.set_events(tool, mask)
        except BaseException as failure:
            failure.add_note(
                "native profiler acquisition failed; registration state is unrecovered; "
                "retained engine, no foreign-owner cleanup attempted"
            )
            raise
        return profile

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
            self.previous: int | Callable[[int, FrameType | None], None] = previous
            self.immutable_output = immutable_output
            self.previous_output = previous_output
            self._attempt: Iterator[bool] = iter((True,))
            self._failure: BaseException | None = None

        def __call__(self, signum: int, frame: FrameType | None) -> None:
            """Capture once, then preserve the original native signal action."""
            if next(self._attempt, False) and (
                self.profile not in FlextInfraPytestClock._publishing
            ):
                try:
                    if frame is not None:
                        traceback.print_stack(frame)
                    FlextInfraPytestClock.publish_profile(
                        self.profile,
                        self.output,
                        partial=True,
                        immutable_output=self.immutable_output,
                        previous_output=self.previous_output,
                    )
                except BaseException as failure:
                    self._failure = failure
            handler: Callable[[int, FrameType | None], None] = self
            if signal.getsignal(signum) is handler:
                signal.signal(signum, self.previous)
            try:
                if callable(self.previous):
                    self.previous(signum, frame)
                else:
                    try:
                        failure = self._failure
                        if self.previous == signal.SIG_DFL and failure is not None:
                            traceback.print_exception(failure, chain=False)
                    finally:
                        signal.raise_signal(signum)
            except BaseException as primary:
                self._surface_failure(primary)
                raise
            self._surface_failure(None)

        def retire(self) -> None:
            """Release only owned registration and surface failure after cleanup."""
            handler: Callable[[int, FrameType | None], None] = self
            if signal.getsignal(signal.SIGTERM) is handler:
                signal.signal(signal.SIGTERM, self.previous)
            primary = sys.exception()
            if isinstance(primary, SystemExit) and (
                primary.code is None or primary.code == 0
            ):
                primary = None
            self._surface_failure(primary)

        def _surface_failure(self, primary: BaseException | None) -> None:
            failure = self._failure
            if failure is None:
                return
            if primary is None:
                raise failure
            primary.add_note(
                "profile checkpoint publication failed:\n"
                + "".join(traceback.format_exception(failure, chain=False))
            )
            if isinstance(primary, SystemExit):
                try:
                    traceback.print_exception(failure, chain=False)
                except (OSError, ValueError) as diagnostic_failure:
                    primary.add_note(
                        f"profile failure diagnostic failed: {diagnostic_failure}"
                    )

    @staticmethod
    def profile_command(command: Callable[[], int], output: Path) -> int:
        """Return the native command status without replacing its first failure."""
        return FlextInfraPytestClock.profile_operation(command, output, is_failure=bool)

    @staticmethod
    def profile_operation[T](
        operation: Callable[[], T],
        output: Path,
        *,
        is_failure: Callable[[T], bool],
    ) -> T:
        """Return the original operation value with immutable native evidence."""
        current = FlextInfraPytestClock._operation_profile.get()
        if (
            current is not None
            and FlextInfraPytestClock._threads[current] == get_ident()
        ):
            return operation()
        immutable_output = output.with_stem(f"{output.stem}-{uuid4().hex}")
        previous_output = output.with_stem(f"{output.stem}.previous-{uuid4().hex}")
        profiler = FlextInfraPytestClock.create_profiler()
        failed = False
        completed = False

        try:
            retire = FlextInfraPytestClock.register_signal_checkpoint(
                profiler,
                output,
                immutable_output=immutable_output.with_suffix(".checkpoint.pstats"),
                previous_output=previous_output.with_suffix(".checkpoint.pstats"),
            )
        except BaseException as primary:
            try:
                profiler.disable()
            except BaseException as cleanup_failure:
                primary.add_note(
                    "profile setup cleanup failed:\n"
                    + "".join(traceback.format_exception(cleanup_failure, chain=False))
                )
            raise
        profile_token = FlextInfraPytestClock._operation_profile.set(profiler)
        try:
            value = operation()
            failed = is_failure(value)
            completed = True
            return value
        finally:
            FlextInfraPytestClock._operation_profile.reset(profile_token)
            primary = None if completed else sys.exception()
            if isinstance(primary, SystemExit) and (
                primary.code is None or primary.code == 0
            ):
                primary = None
            for finalize in (
                retire,
                lambda: FlextInfraPytestClock.publish_profile(
                    profiler,
                    output,
                    immutable_output=immutable_output,
                    previous_output=previous_output,
                ),
            ):
                try:
                    finalize()
                except BaseException as failure:
                    if primary is not None:
                        primary.add_note(
                            "profile finalization failed:\n"
                            + "".join(traceback.format_exception(failure, chain=False))
                        )
                    elif failed:
                        try:
                            traceback.print_exception(failure)
                        except (OSError, ValueError) as diagnostic_failure:
                            failure.add_note(
                                f"profile failure diagnostic failed: {diagnostic_failure}"
                            )
                    else:
                        primary = failure
            if primary is not None and primary is not sys.exception():
                raise primary

    @classmethod
    def start_profiler(cls) -> cProfile.Profile:
        """Share the owning thread's native profiler across startup and entrypoint."""
        current = cls._operation_profile.get()
        if current is not None and cls._threads[current] == get_ident():
            return current
        if cls.profiler is None or cls._threads[cls.profiler] != get_ident():
            cls.profiler = cls.create_profiler()
        cls._operation_profile.set(cls.profiler)
        return cls.profiler

    @staticmethod
    def _guard_staging_identity(staging: Path, identity: os.stat_result) -> None:
        """Reject a staging path that no longer names the captured device/inode."""
        current = staging.stat(follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino):
            msg = "profile staging identity changed"
            raise OSError(errno.ESTALE, msg)

    @staticmethod
    def _discard_staging(staging: Path, identity: os.stat_result) -> None:
        """Remove only owned staging; retain the original failure on cleanup error."""
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
        partial: bool = False,
    ) -> None:
        """Atomically publish native stats; partial checkpoints keep frames active."""
        if FlextInfraPytestClock._threads[profile] != get_ident():
            msg = "profile publication belongs to another thread"
            raise RuntimeError(msg)
        if profile in FlextInfraPytestClock._publishing:
            msg = "profile publication is already active"
            raise RuntimeError(msg)
        FlextInfraPytestClock._publishing.add(profile)
        try:
            if not partial:
                profile.disable()
                if FlextInfraPytestClock._operation_profile.get() is profile:
                    FlextInfraPytestClock._operation_profile.set(None)
                if FlextInfraPytestClock.profiler is profile:
                    FlextInfraPytestClock.profiler = None
            profile.snapshot_stats()
            descriptor, name = tempfile.mkstemp(
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
            )
            staging = Path(name)
            identity = os.fstat(descriptor)
            try:
                with os.fdopen(descriptor, "wb") as stream:
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
                                f"Raw capture: {immutable_output.name}\n"
                                f"Process ID: {os.getpid()}\n"
                                f"Owner thread: {FlextInfraPytestClock._threads[profile]}\n"
                                f"Partial completed-entry checkpoint: {partial}\n"
                                "Owner-thread wall timing, not worker CPU "
                                "or elapsed-time proof.\n"
                                f"Capture monotonic ns: {time.monotonic_ns()}\n\n"
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
        """Return retirement for one partial checkpoint and its previous signal action."""
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


if sys.argv[1:2] == ["profile"]:
    FlextInfraPytestClock.start_profiler()

__all__: list[str] = ["FlextInfraPytestClock"]
