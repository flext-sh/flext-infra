"""Canonical native process-lock owner for serialized workspace operations."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path

from filelock import FileLock, Timeout

from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraSerializationLockOwner:
    """Acquire deterministic workspace locks around one typed operation."""

    @classmethod
    def execute[TValue](
        cls,
        lock_paths: t.SequenceOf[Path],
        timeout_seconds: int,
        operation: Callable[[], p.Result[TValue]],
        *,
        timeout_failure: Callable[[Path, int], p.Result[TValue]],
        acquisition_failure: Callable[[str], p.Result[TValue]],
        ephemeral: bool = False,
        wait_heartbeat_seconds: int | None = None,
        wait_progress: Callable[[Path, float], None] | None = None,
    ) -> p.Result[TValue]:
        """Run ``operation`` while holding every unique lock in stable order.

        ``ephemeral`` declares the caller's lock lifecycle. A serialized Make
        verb reuses its per-checkout lock, so the artifact is durable state and
        is preserved. An isolated worktree transaction owns its sandbox for one
        operation, so its lock -- and any directory the lock alone created --
        is removed on exit; retaining it would leak state into the source
        checkout the transaction promised not to mutate.

        When ``wait_progress`` is set, emit a heartbeat every
        ``wait_heartbeat_seconds`` while FileLock polls so operators see a
        blocked verb instead of silence for up to ``timeout_seconds``.
        """
        ordered_paths = tuple(sorted(set(lock_paths), key=lambda path: path.as_posix()))
        heartbeat = wait_heartbeat_seconds if wait_heartbeat_seconds is not None else 0
        with ExitStack() as lock_stack:
            try:
                for lock_path in ordered_paths:
                    lock = FileLock(
                        lock_path,
                        timeout=timeout_seconds,
                        fallback_to_soft=False,
                        preserve_lock_file=not ephemeral,
                    )
                    cls._acquire_with_heartbeat(
                        lock,
                        lock_path=lock_path,
                        timeout_seconds=timeout_seconds,
                        heartbeat_seconds=heartbeat,
                        wait_progress=wait_progress,
                    )
                    lock_stack.callback(lock.release)
            except Timeout as exc:
                return timeout_failure(Path(exc.lock_file), timeout_seconds)
            except OSError as exc:
                return acquisition_failure(str(exc))
            result = operation()
        if ephemeral:
            cls._discard_ephemeral_lock_state(ordered_paths)
        return result

    @staticmethod
    def _acquire_with_heartbeat(
        lock: FileLock,
        *,
        lock_path: Path,
        timeout_seconds: int,
        heartbeat_seconds: int,
        wait_progress: Callable[[Path, float], None] | None,
    ) -> None:
        """Acquire one lock, emitting optional wait heartbeats during polling."""
        if wait_progress is None or heartbeat_seconds <= 0:
            lock.acquire(timeout=timeout_seconds)
            return
        started = time.monotonic()
        last_emit = started

        def cancel_check() -> bool:
            nonlocal last_emit
            now = time.monotonic()
            if now - last_emit >= heartbeat_seconds:
                wait_progress(lock_path, now - started)
                last_emit = now
            return False

        lock.acquire(timeout=timeout_seconds, cancel_check=cancel_check)

    @staticmethod
    def _discard_ephemeral_lock_state(lock_paths: t.SequenceOf[Path]) -> None:
        """Remove the released ephemeral lock files and the dirs they created.

        ``preserve_lock_file=False`` is advisory: the Unix ``flock`` backend
        never unlinks the file, so an ephemeral caller must delete it itself.
        Only empty parents are then pruned, so a state root shared with another
        owner keeps its own content; ``rmdir`` fails closed on a non-empty or
        absent directory, which is exactly the stop condition.
        """
        for lock_path in lock_paths:
            lock_path.unlink(missing_ok=True)
            for parent in lock_path.parents:
                try:
                    parent.rmdir()
                except OSError:
                    break


__all__: list[str] = ["FlextInfraSerializationLockOwner"]
