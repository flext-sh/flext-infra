"""Canonical native process-lock owner for serialized workspace operations."""

from __future__ import annotations

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
    ) -> p.Result[TValue]:
        """Run ``operation`` while holding every unique lock in stable order.

        ``ephemeral`` declares the caller's lock lifecycle. A serialized Make
        verb reuses the primary Git worktree's repository-wide lock, so the
        artifact is durable state and is preserved. An isolated worktree
        transaction owns its sandbox for one operation, so its lock -- and any
        directory the lock alone created -- is removed on exit; retaining it
        would leak state into the source checkout the transaction promised not
        to mutate.
        """
        ordered_paths = tuple(sorted(set(lock_paths), key=lambda path: path.as_posix()))
        with ExitStack() as lock_stack:
            try:
                for lock_path in ordered_paths:
                    lock_stack.enter_context(
                        FileLock(
                            lock_path,
                            timeout=timeout_seconds,
                            fallback_to_soft=False,
                            preserve_lock_file=not ephemeral,
                        )
                    )
            except Timeout as exc:
                return timeout_failure(Path(exc.lock_file), timeout_seconds)
            except OSError as exc:
                return acquisition_failure(str(exc))
            result = operation()
        if ephemeral:
            cls._discard_ephemeral_lock_state(ordered_paths)
        return result

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
