"""Descriptor-bound generation lock over an existing worktree Git HEAD."""

from __future__ import annotations

import errno
import os
import stat
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Never

from filelock import lock_descriptor, unlock_descriptor

from flext_infra import m, u

_LEASE_FAILURES: tuple[type[BaseException], ...] = (
    Exception,
    BaseExceptionGroup,
    GeneratorExit,
    KeyboardInterrupt,
    SystemExit,
)


class FlextInfraMiseLock:
    """Own one authenticated native lock on a worktree-specific Git anchor."""

    _UNSAFE_MODE_BITS = 0o7133

    @staticmethod
    @contextmanager
    def lease(
        identity: m.Infra.GitIdentityReport,
    ) -> Generator[m.Infra.MiseToolchainLockLease]:
        """Lock existing per-worktree ``git_dir/HEAD`` exactly once."""
        if not identity.is_inside_work_tree:
            raise OSError(
                errno.EINVAL,
                f"generation lock requires a Git worktree: {identity.repo_root}",
            )
        path = identity.git_dir / "HEAD"
        before = FlextInfraMiseLock._snapshot(path)
        descriptor = os.open(path, FlextInfraMiseLock._open_flags())
        acquired = False
        authenticated = False
        try:
            FlextInfraMiseLock._assert_descriptor(before, descriptor)
            acquired = FlextInfraMiseLock._acquire(descriptor, path)
            FlextInfraMiseLock._assert_held(before, descriptor)
            authenticated = True
            yield m.Infra.MiseToolchainLockLease(descriptor=descriptor, state=before)
        except _LEASE_FAILURES as operation_error:
            try:
                FlextInfraMiseLock._release(
                    before, descriptor, acquired=acquired, authenticated=authenticated
                )
            except _LEASE_FAILURES as release_error:
                FlextInfraMiseLock._raise_failures(
                    [operation_error, release_error],
                    "generation operation and Git HEAD lock release failed",
                )
            raise
        else:
            FlextInfraMiseLock._release(
                before, descriptor, acquired=acquired, authenticated=authenticated
            )

    @staticmethod
    def _release(
        expected: m.Cli.AtomicFileState,
        descriptor: int,
        *,
        acquired: bool,
        authenticated: bool,
    ) -> None:
        """Reauthenticate, unlock, and close without hiding cleanup failures."""
        failures: list[BaseException] = []
        if authenticated:
            try:
                FlextInfraMiseLock._assert_held(expected, descriptor)
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
            FlextInfraMiseLock._raise_failures(failures, "Git HEAD lock release failed")

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
        """Read complete HEAD identity through the canonical atomic owner."""
        snapshot = u.Cli.atomic_read_binary_file_state(path, required=True)
        if snapshot.failure:
            raise OSError(
                errno.EPERM,
                snapshot.error or f"cannot authenticate generation lock HEAD: {path}",
            )
        state = snapshot.value
        mode = state.mode
        if mode is None:
            raise FileNotFoundError(
                errno.ENOENT, f"generation lock HEAD is absent: {path}", path
            )
        if mode & FlextInfraMiseLock._UNSAFE_MODE_BITS or not mode & stat.S_IRUSR:
            raise PermissionError(
                errno.EPERM,
                f"generation lock HEAD has unsafe mode {mode:#o}: {path}",
                path,
            )
        return state

    @staticmethod
    def _assert_held(expected: m.Cli.AtomicFileState, descriptor: int) -> None:
        """Require pathname, parent, bytes, and descriptor to remain unchanged."""
        observed = FlextInfraMiseLock._snapshot(expected.path)
        if observed != expected:
            raise OSError(
                errno.ESTALE,
                f"generation lock HEAD changed while held: {expected.path}",
                expected.path,
            )
        FlextInfraMiseLock._assert_descriptor(expected, descriptor)

    @staticmethod
    def _assert_descriptor(expected: m.Cli.AtomicFileState, descriptor: int) -> None:
        """Bind the exact HEAD physical state to the opened descriptor."""
        before = os.fstat(descriptor)
        after = os.fstat(descriptor)
        expected_key = (
            expected.mode,
            expected.device,
            expected.inode,
            expected.link_count,
            expected.file_attributes,
            expected.reparse_tag,
        )
        if (
            FlextInfraMiseLock._state_key(before) != expected_key
            or FlextInfraMiseLock._state_key(after) != expected_key
        ):
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
        """Build a read-only, non-creating, non-inheritable open contract."""
        flags = os.O_RDONLY | os.O_NONBLOCK
        flags |= getattr(os, "O_CLOEXEC", 0)
        if os.name == "nt":
            flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
        else:
            nofollow = getattr(os, "O_NOFOLLOW", None)
            if nofollow is None:
                raise OSError(errno.ENOTSUP, "Git HEAD no-follow open is unsupported")
            flags |= nofollow
        return flags


__all__: list[str] = ["FlextInfraMiseLock"]
