"""Descriptor-bound generation lock in the exact worktree Git directory."""

from __future__ import annotations

import errno
import os
import stat
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Never

from filelock import lock_descriptor, unlock_descriptor

from flext_infra import c, m, u

_LEASE_FAILURES: tuple[type[BaseException], ...] = (
    Exception,
    BaseExceptionGroup,
    GeneratorExit,
    KeyboardInterrupt,
    SystemExit,
)


class FlextInfraMiseLock:
    """Own one authenticated native lock without locking mutable Git refs."""

    _UNSAFE_MODE_BITS = 0o7133

    @staticmethod
    @contextmanager
    def lease(
        identity: m.Infra.GitIdentityReport,
    ) -> Generator[m.Infra.MiseToolchainLockLease]:
        """Lock one dedicated per-worktree administrative file exactly once."""
        if not identity.is_inside_work_tree:
            raise OSError(
                errno.EINVAL,
                f"generation lock requires a Git worktree: {identity.repo_root}",
            )
        head_path = identity.git_dir / "HEAD"
        lock_path = identity.git_dir / c.Infra.CODEGEN_TRANSACTION_LOCK_FILENAME
        head_state = FlextInfraMiseLock._snapshot(head_path)
        descriptor = os.open(
            lock_path,
            FlextInfraMiseLock._open_flags(),
            c.Infra.CODEGEN_TRANSACTION_LOCK_MODE,
        )
        try:
            lock_state = FlextInfraMiseLock._snapshot_lock(lock_path)
        except _LEASE_FAILURES:
            os.close(descriptor)
            raise
        acquired = False
        authenticated = False
        try:
            FlextInfraMiseLock._assert_descriptor(lock_state, descriptor)
            acquired = FlextInfraMiseLock._acquire(descriptor, lock_path)
            FlextInfraMiseLock._assert_held(lock_state, head_state, descriptor)
            authenticated = True
            yield m.Infra.MiseToolchainLockLease(
                descriptor=descriptor, lock_state=lock_state, head_state=head_state
            )
        except _LEASE_FAILURES as operation_error:
            try:
                FlextInfraMiseLock._release(
                    lock_state,
                    head_state,
                    descriptor,
                    acquired=acquired,
                    authenticated=authenticated,
                )
            except _LEASE_FAILURES as release_error:
                FlextInfraMiseLock._raise_failures(
                    [operation_error, release_error],
                    "generation operation and lock release failed",
                )
            raise
        else:
            FlextInfraMiseLock._release(
                lock_state,
                head_state,
                descriptor,
                acquired=acquired,
                authenticated=authenticated,
            )

    @staticmethod
    def _release(
        expected_lock: m.Cli.AtomicFileState,
        expected_head: m.Cli.AtomicFileState,
        descriptor: int,
        *,
        acquired: bool,
        authenticated: bool,
    ) -> None:
        """Reauthenticate, unlock, and close without hiding cleanup failures."""
        failures: list[BaseException] = []
        if authenticated:
            try:
                FlextInfraMiseLock._assert_held(
                    expected_lock, expected_head, descriptor
                )
            except _LEASE_FAILURES as exc:
                failures.append(exc)
        if acquired:
            try:
                unlock_descriptor(descriptor)
            except _LEASE_FAILURES as exc:
                failures.append(exc)
        try:
            os.close(descriptor)
        except _LEASE_FAILURES as exc:
            failures.append(exc)
        if failures:
            FlextInfraMiseLock._raise_failures(
                failures, "generation lock release failed"
            )

    @staticmethod
    def _acquire(descriptor: int, path: Path) -> bool:
        """Acquire the descriptor once and raise the canonical contention error."""
        if lock_descriptor(descriptor, blocking=False):
            return True
        raise BlockingIOError(
            errno.EWOULDBLOCK, f"another codegen transaction owns the workspace: {path}"
        )

    @staticmethod
    def _raise_failures(failures: list[BaseException], message: str) -> Never:
        """Raise one failure directly or preserve every independent cause."""
        if len(failures) == 1:
            raise failures[0]
        raise BaseExceptionGroup(message, failures)

    @staticmethod
    def _snapshot(path: Path) -> m.Cli.AtomicFileState:
        """Read complete file identity through the canonical atomic owner."""
        snapshot = u.Cli.atomic_read_binary_file_state(path, required=True)
        if snapshot.failure:
            raise OSError(
                errno.EPERM,
                snapshot.error or f"cannot authenticate generation state: {path}",
            )
        state = snapshot.value
        mode = state.mode
        if mode is None:
            raise FileNotFoundError(
                errno.ENOENT, f"generation state is absent: {path}", path
            )
        if mode & FlextInfraMiseLock._UNSAFE_MODE_BITS or not mode & stat.S_IRUSR:
            raise PermissionError(
                errno.EPERM, f"generation state has unsafe mode {mode:#o}: {path}", path
            )
        return state

    @staticmethod
    def _snapshot_lock(path: Path) -> m.Cli.AtomicFileState:
        """Require the dedicated administrative lock to remain owner-private."""
        state = FlextInfraMiseLock._snapshot(path)
        if state.mode != c.Infra.CODEGEN_TRANSACTION_LOCK_MODE:
            raise PermissionError(
                errno.EPERM,
                "generation lock requires mode "
                f"{c.Infra.CODEGEN_TRANSACTION_LOCK_MODE:#o}, "
                f"observed {state.mode:#o}: {path}",
                path,
            )
        return state

    @staticmethod
    def _assert_held(
        expected_lock: m.Cli.AtomicFileState,
        expected_head: m.Cli.AtomicFileState,
        descriptor: int,
    ) -> None:
        """Require the lock descriptor and observed HEAD to remain unchanged."""
        observed_lock = FlextInfraMiseLock._snapshot_lock(expected_lock.path)
        if observed_lock != expected_lock:
            raise OSError(
                errno.ESTALE,
                f"generation lock pathname changed while held: {expected_lock.path}",
                expected_lock.path,
            )
        observed_head = FlextInfraMiseLock._snapshot(expected_head.path)
        if observed_head != expected_head:
            raise OSError(
                errno.ESTALE,
                f"generation observed HEAD changed while held: {expected_head.path}",
                expected_head.path,
            )
        FlextInfraMiseLock._assert_descriptor(expected_lock, descriptor)

    @staticmethod
    def _assert_descriptor(expected: m.Cli.AtomicFileState, descriptor: int) -> None:
        """Bind the exact physical lock state to the opened descriptor."""
        observed = os.fstat(descriptor)
        expected_key = (
            expected.mode,
            expected.device,
            expected.inode,
            expected.link_count,
            expected.file_attributes,
            expected.reparse_tag,
        )
        if FlextInfraMiseLock._state_key(observed) != expected_key:
            raise OSError(
                errno.ESTALE,
                f"generation lock descriptor changed while held: {expected.path}",
                expected.path,
            )

    @staticmethod
    def _state_key(
        state: os.stat_result,
    ) -> tuple[int, int, int, int, int | None, int | None]:
        """Return the physical fields represented by ``AtomicFileState``."""
        if not stat.S_ISREG(state.st_mode) or state.st_nlink != 1:
            raise OSError(errno.EPERM, "generation lock descriptor is not unique")
        return (
            stat.S_IMODE(state.st_mode),
            state.st_dev,
            state.st_ino,
            state.st_nlink,
            getattr(state, "st_file_attributes", None),
            getattr(state, "st_reparse_tag", None),
        )

    @staticmethod
    def _open_flags() -> int:
        """Build a dedicated, non-following, non-inheritable lock contract."""
        flags = os.O_RDWR | os.O_CREAT | os.O_NONBLOCK
        flags |= getattr(os, "O_CLOEXEC", 0)
        if os.name == "nt":
            flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
        else:
            nofollow = getattr(os, "O_NOFOLLOW", None)
            if nofollow is None:
                raise OSError(errno.ENOTSUP, "no-follow lock open is unsupported")
            flags |= nofollow
        return flags


__all__: list[str] = ["FlextInfraMiseLock"]
