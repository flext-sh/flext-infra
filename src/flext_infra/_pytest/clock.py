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
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from pathlib import Path
from threading import get_ident
from types import BuiltinMethodType, FrameType, MethodType, TracebackType
from typing import IO, ClassVar, Self
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

    class FailureCapture:
        """Retain the first failure of a guarded step for later surfacing."""

        def __init__(self) -> None:
            self.failure: BaseException | None = None

        def __enter__(self) -> Self:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            exc_traceback: TracebackType | None,
        ) -> bool:
            if exc is None:
                return False
            self.failure = exc
            return True

    @classmethod
    def create_profiler(cls) -> cProfile.Profile:
        """Gate native callbacks before productive events.

        Returns:
            The actual owning-thread cProfile engine.

        """
        profile = cProfile.Profile()
        owner = cls._threads[profile] = get_ident()
        try:
            profile.enable()
            cls._gate_monitoring_events(profile, owner)
        except BaseException as failure:
            failure.add_note(
                "native profiler acquisition failed; registration state is "
                "unrecovered; retained engine, no foreign-owner cleanup attempted"
            )
            raise
        return profile

    @staticmethod
    def _gate_monitoring_events(profile: cProfile.Profile, owner: int) -> None:
        """Restrict every native monitoring callback to the owning thread.

        Raises:
            RuntimeError: If the engine enabled no events or a callback belongs to
                another engine.

        """
        tool = sys.monitoring.PROFILER_ID
        mask = sys.monitoring.get_events(tool)
        sys.monitoring.set_events(tool, 0)
        if not mask:
            msg = "native profiler enabled no monitoring events"
            raise RuntimeError(msg)
        remaining = mask
        if mask & sys.monitoring.events.CALL:
            remaining |= sys.monitoring.events.C_RETURN | sys.monitoring.events.C_RAISE
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
                tool, event, FlextInfraPytestClock._gate(callback, owner)
            )
        profile.clear()
        sys.monitoring.set_events(tool, mask)

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
            self._capture(frame, partial=self.previous != signal.SIG_DFL)
            handler: Callable[[int, FrameType | None], None] = self
            if signal.getsignal(signum) is handler:
                signal.signal(signum, self.previous)
            try:
                self._invoke_previous(signum, frame)
            except BaseException as primary:
                self._surface_failure(primary)
                raise
            self._surface_failure(None)

        def on_operator_signal(self, signum: int, frame: FrameType | None) -> None:
            """Checkpoint while the process owner retains cancellation and reaping."""
            del signum
            self._capture(frame, partial=True)

        def _capture(self, frame: FrameType | None, *, partial: bool) -> None:
            """Retain the first checkpoint failure for surfacing after cleanup."""
            if next(self._attempt, False) and (
                self.profile not in FlextInfraPytestClock._publishing
            ):
                capture = FlextInfraPytestClock.FailureCapture()
                with capture:
                    if frame is not None:
                        traceback.print_stack(frame)
                    FlextInfraPytestClock.publish_profile(
                        self.profile,
                        self.output,
                        partial=partial,
                        immutable_output=self.immutable_output,
                        previous_output=self.previous_output,
                    )
                self._failure = capture.failure

        def _invoke_previous(self, signum: int, frame: FrameType | None) -> None:
            """Run the previous native action, or re-raise the default signal."""
            if callable(self.previous):
                self.previous(signum, frame)
                return
            try:
                failure = self._failure
                if self.previous == signal.SIG_DFL and failure is not None:
                    traceback.print_exception(failure, chain=False)
            finally:
                signal.raise_signal(signum)

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
                FlextInfraPytestClock._print_diagnostic(failure, primary, chain=False)

    @staticmethod
    def profile_command(
        command: Callable[[], int],
        output: Path,
        *,
        after_profile: Callable[[Path], None] | None = None,
    ) -> int:
        """Return the native command status without replacing its first failure."""
        return FlextInfraPytestClock.profile_operation(
            command, output, is_failure=bool, after_profile=after_profile
        )

    @staticmethod
    def profile_operation[T](
        operation: Callable[[], T],
        output: Path,
        *,
        is_failure: Callable[[T], bool],
        after_profile: Callable[[Path], None] | None = None,
    ) -> T:
        """Return the original operation value with immutable native evidence."""
        current = FlextInfraPytestClock._operation_profile.get()
        if (
            current is not None
            and FlextInfraPytestClock._threads[current] == get_ident()
        ):
            return operation()
        output.parent.mkdir(parents=True, exist_ok=True)
        immutable_output = output.with_stem(f"{output.stem}-{uuid4().hex}")
        previous_output = output.with_stem(f"{output.stem}.previous-{uuid4().hex}")
        profiler = FlextInfraPytestClock.create_profiler()
        failed = False
        completed = False

        retire: Callable[[], None] | None = None
        profile_token = FlextInfraPytestClock._operation_profile.set(profiler)
        try:
            retire = FlextInfraPytestClock.register_signal_checkpoint(
                profiler,
                output,
                immutable_output=immutable_output.with_suffix(".checkpoint.pstats"),
                previous_output=previous_output.with_suffix(".checkpoint.pstats"),
            )
            value = operation()
            failed = is_failure(value)
            completed = True
            return value
        finally:
            FlextInfraPytestClock._operation_profile.reset(profile_token)
            FlextInfraPytestClock._finalize_steps(
                (
                    *((retire,) if retire is not None else ()),
                    lambda: FlextInfraPytestClock.publish_profile(
                        profiler,
                        output,
                        immutable_output=immutable_output,
                        previous_output=previous_output,
                    ),
                    *(
                        (partial(after_profile, immutable_output),)
                        if after_profile is not None
                        else ()
                    ),
                ),
                completed=completed,
                failed=failed,
            )

    @staticmethod
    def _print_diagnostic(
        failure: BaseException,
        note_target: BaseException,
        *,
        chain: bool,
    ) -> None:
        """Print a failure, noting on the target when the diagnostic itself fails."""
        try:
            traceback.print_exception(failure, chain=chain)
        except (OSError, ValueError) as diagnostic_failure:
            note_target.add_note(
                f"profile failure diagnostic failed: {diagnostic_failure}"
            )

    @staticmethod
    def _finalize_steps(
        steps: tuple[Callable[[], None], ...],
        *,
        completed: bool,
        failed: bool,
    ) -> None:
        """Run every finalization step, keeping the first failure primary."""
        primary = None if completed else sys.exception()
        if isinstance(primary, SystemExit) and (
            primary.code is None or primary.code == 0
        ):
            primary = None
        for finalize in steps:
            capture = FlextInfraPytestClock.FailureCapture()
            with capture:
                finalize()
            failure = capture.failure
            if failure is None:
                continue
            if primary is not None:
                primary.add_note(
                    "profile finalization failed:\n"
                    + "".join(traceback.format_exception(failure, chain=False))
                )
                if isinstance(primary, SystemExit):
                    FlextInfraPytestClock._print_diagnostic(
                        failure, primary, chain=False
                    )
            elif failed:
                FlextInfraPytestClock._print_diagnostic(failure, failure, chain=True)
            else:
                primary = failure
        if primary is not None and primary is not sys.exception():
            raise primary

    @classmethod
    def start_profiler(cls) -> cProfile.Profile:
        """Share the owning thread's native profiler across startup and entrypoint.

        Returns:
            The profiler owned by the current thread.

        """
        current = cls._operation_profile.get()
        if current is not None and cls._threads[current] == get_ident():
            return current
        if cls.profiler is None or cls._threads[cls.profiler] != get_ident():
            cls.profiler = cls.create_profiler()
        cls._operation_profile.set(cls.profiler)
        return cls.profiler

    @staticmethod
    def _guard_staging_identity(staging: Path, identity: os.stat_result) -> None:
        """Reject a staging path that no longer names the captured device/inode.

        Raises:
            OSError: If the staging identity changed.

        """
        current = staging.stat(follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino):
            msg = "profile staging identity changed"
            raise OSError(errno.ESTALE, msg)

    @staticmethod
    def _discard_staging(staging: Path, identity: os.stat_result) -> None:
        """Remove only owned staging; retain the original failure on cleanup error.

        Raises:
            OSError: If cleanup fails and no other failure is in flight.

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
    @contextmanager
    def _staging(output: Path) -> Generator[tuple[IO[bytes], Path, os.stat_result]]:
        """Own a native temporary descriptor and remove only its recorded inode.

        Yields:
            The open binary stream, its staging path and its captured identity.

        """
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
        ) as resource:
            staging = Path(resource.name)
            identity = os.fstat(resource.fileno())
            try:
                yield resource.file, staging, identity
            finally:
                FlextInfraPytestClock._discard_staging(staging, identity)

    @staticmethod
    def publish_profile(
        profile: cProfile.Profile,
        output: Path,
        *,
        immutable_output: Path | None = None,
        previous_output: Path | None = None,
        partial: bool = False,
    ) -> None:
        """Atomically publish native stats; partial checkpoints keep frames active.

        Raises:
            RuntimeError: If publication belongs to another thread or is already
                active.

        """
        if FlextInfraPytestClock._threads[profile] != get_ident():
            msg = "profile publication belongs to another thread"
            raise RuntimeError(msg)
        if profile in FlextInfraPytestClock._publishing:
            msg = "profile publication is already active"
            raise RuntimeError(msg)
        FlextInfraPytestClock._publishing.add(profile)
        try:
            if not partial:
                FlextInfraPytestClock._retire_profile(profile)
            # Staging precedes the native snapshot: a signal whose native
            # action aborts publication during staging leaves no snapshot taken.
            with FlextInfraPytestClock._staging(output) as (stream, staging, identity):
                profile.snapshot_stats()
                marshal.dump(profile.stats, stream)
                stream.flush()
                os.fsync(stream.fileno())
                FlextInfraPytestClock._guard_staging_identity(staging, identity)
                if immutable_output is not None:
                    immutable_output.hardlink_to(staging)
                    FlextInfraPytestClock._publish_report(
                        profile, immutable_output, identity, partial=partial
                    )
                if previous_output is not None:
                    FlextInfraPytestClock._preserve_previous(output, previous_output)
                staging.replace(output)
        finally:
            FlextInfraPytestClock._publishing.remove(profile)

    @classmethod
    def _retire_profile(cls, profile: cProfile.Profile) -> None:
        """Disable a completed profiler and release its process-local ownership."""
        profile.disable()
        if cls._operation_profile.get() is profile:
            cls._operation_profile.set(None)
        if cls.profiler is profile:
            cls.profiler = None

    @staticmethod
    def _publish_report(
        profile: cProfile.Profile,
        immutable_output: Path,
        identity: os.stat_result,
        *,
        partial: bool,
    ) -> None:
        """Publish the text report beside the immutable raw capture."""
        report = immutable_output.with_name(f"{immutable_output.name}.txt")
        owner_thread = FlextInfraPytestClock._threads[profile]
        with FlextInfraPytestClock._staging(report) as (
            stream,
            staging,
            report_identity,
        ):
            with open(
                stream.fileno(), "w", encoding="utf-8", closefd=False
            ) as report_stream:
                report_stream.write(
                    "Native profile snapshot, not operation acceptance.\n"
                    f"Raw capture: {immutable_output.name}\n"
                    f"Process ID: {os.getpid()}\n"
                    f"Owner thread: {owner_thread}\n"
                    f"Partial completed-entry checkpoint: {partial}\n"
                    "Owner-thread wall timing, not worker CPU "
                    "or elapsed-time proof.\n"
                    f"Capture monotonic ns: {time.monotonic_ns()}\n\n"
                )
                FlextInfraPytestClock._guard_staging_identity(
                    immutable_output, identity
                )
                pstats.Stats(str(immutable_output), stream=report_stream).sort_stats(
                    pstats.SortKey.CUMULATIVE
                ).print_stats()
                FlextInfraPytestClock._guard_staging_identity(
                    immutable_output, identity
                )
                report_stream.flush()
                os.fsync(report_stream.fileno())
            FlextInfraPytestClock._guard_staging_identity(staging, report_identity)
            report.hardlink_to(staging)
        sys.stderr.write(
            f"cProfile capture: pid={os.getpid()} owner_thread={owner_thread} "
            f"partial={partial} immutable={immutable_output}\n"
        )

    @staticmethod
    def _preserve_previous(output: Path, previous_output: Path) -> None:
        """Link the previous regular profile artifact before it is replaced.

        Raises:
            OSError: If the previous artifact is not a regular file.

        """
        try:
            previous = output.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISREG(previous.st_mode):
            msg = "previous profile artifact is not a regular file"
            raise OSError(errno.EINVAL, msg)
        os.link(output, previous_output, follow_symlinks=False)
        FlextInfraPytestClock._guard_staging_identity(previous_output, previous)

    @classmethod
    def register_signal_checkpoint(
        cls,
        profile: cProfile.Profile,
        output: Path,
        *,
        immutable_output: Path | None = None,
        previous_output: Path | None = None,
    ) -> Callable[[], None]:
        """Return retirement for one partial checkpoint and its previous action.

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


if sys.argv[1:2] == ["profile"]:
    FlextInfraPytestClock.start_profiler()

__all__: list[str] = ["FlextInfraPytestClock"]
