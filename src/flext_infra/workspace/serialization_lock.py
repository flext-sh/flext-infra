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

    @staticmethod
    def execute[TValue](
        lock_paths: t.SequenceOf[Path],
        timeout_seconds: int,
        operation: Callable[[], p.Result[TValue]],
        *,
        timeout_failure: Callable[[Path, int], p.Result[TValue]],
        acquisition_failure: Callable[[str], p.Result[TValue]],
    ) -> p.Result[TValue]:
        """Run ``operation`` while holding every unique lock in stable order."""
        ordered_paths = tuple(sorted(set(lock_paths), key=lambda path: path.as_posix()))
        with ExitStack() as lock_stack:
            try:
                for lock_path in ordered_paths:
                    lock_stack.enter_context(
                        FileLock(
                            lock_path,
                            timeout=timeout_seconds,
                            fallback_to_soft=False,
                            preserve_lock_file=True,
                        )
                    )
            except Timeout as exc:
                return timeout_failure(Path(exc.lock_file), timeout_seconds)
            except OSError as exc:
                return acquisition_failure(str(exc))
            return operation()


__all__: list[str] = ["FlextInfraSerializationLockOwner"]
