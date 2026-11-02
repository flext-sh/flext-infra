"""Strict worktree versus physical file-scope classification for writers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from flext_cli import u
from git import GitError, Repo
from git.repo.fun import is_git_dir

from flext_infra import c, config, m, p, r


class FlextInfraUtilitiesGitMutationScope:
    """Classify absent Git ownership before opening any declared Git marker."""

    @staticmethod
    def _git_mutation_scope(root: Path) -> p.Infra.GitMutationScope:
        resolved = root.resolve(strict=True)
        if not resolved.is_dir():
            msg = f"mutation scope is not a physical directory: {root}"
            raise ValueError(msg)
        for candidate in (resolved, *resolved.parents):
            marker = candidate / c.Infra.GIT_DIR
            if marker.exists() or marker.is_symlink():
                with Repo(candidate, search_parent_directories=False) as repo:
                    if (
                        repo.bare
                        or repo.working_tree_dir is None
                        or Path(repo.working_tree_dir).resolve() != candidate
                    ):
                        msg = (
                            f"declared Git marker does not own this worktree: "
                            f"{candidate}"
                        )
                        raise ValueError(msg)
                    return m.Infra.GitMutationScope(
                        root=resolved,
                        git_dir=Path(repo.git_dir).resolve(),
                    )
            if is_git_dir(candidate):
                msg = (
                    f"mutation scope belongs to Git storage rather than a "
                    f"worktree: {root}"
                )
                raise ValueError(msg)
        return m.Infra.GitMutationScope(root=resolved, git_dir=None)

    @classmethod
    def git_mutation_scope(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitMutationScope]:
        """Reject malformed declared Git roots; marker-free roots remain file scopes.

        Returns:
            The resulting ``p.Result[p.Infra.GitMutationScope]``.

        """
        try:
            scope = cls._git_mutation_scope(request.repo_root)
        except (GitError, OSError, ValueError) as exc:
            return r[p.Infra.GitMutationScope].fail(str(exc), exception=exc)
        return r[p.Infra.GitMutationScope].ok(scope)

    @classmethod
    def mutation_lock_path(cls, root: Path) -> p.Result[Path]:
        """Locate the one lock shared by every writer of ``root``'s scope.

        The lock lives in Git storage, or in the state directory outside Git,
        so it never dirties the working tree.

        Returns:
            The lock path, or the scope classification failure.

        """
        return cls.git_mutation_scope(m.Infra.GitRepoRequest(repo_root=root)).map(
            lambda scope: (
                (
                    scope.git_dir
                    if scope.git_dir is not None
                    else scope.root / c.Infra.TRANSACTION_STATE_DIRNAME
                )
                / c.Infra.MUTATION_LOCK_NAME
            )
        )

    @staticmethod
    def mutation_lock_holder_path(lock_path: Path) -> Path:
        """Locate the sibling record naming the writer that holds ``lock_path``.

        Returns:
            The holder record path beside the lock.

        """
        return lock_path.with_name(lock_path.name + c.Infra.MUTATION_LOCK_HOLDER_SUFFIX)

    @classmethod
    def mutation_lock_holder(cls, lock_path: Path) -> p.Infra.MutationLockHolder | None:
        """Read the last recorded holder of ``lock_path`` without touching the lock.

        The record is replaced atomically and never deleted, so a reader sees
        either no record (no recording writer ever held the lock) or a whole one.

        Returns:
            The last recorded holder, or ``None`` when none was ever recorded.

        """
        record = cls.mutation_lock_holder_path(lock_path)
        if not record.is_file():
            return None
        return m.Infra.MutationLockHolder.model_validate_json(record.read_bytes())

    @classmethod
    def _mutation_holder_text(cls, lock_path: Path) -> str:
        holder = cls.mutation_lock_holder(lock_path)
        if holder is None:
            return "an unrecorded holder"
        if holder.released_at is not None:
            # A plain publisher records nothing, and a holding operation
            # records itself right after acquiring: the last record is closed.
            return (
                f"an unrecorded holder (last recorded: {holder.operation} "
                f"pid={holder.pid} released "
                f"{holder.released_at:%Y-%m-%dT%H:%M:%SZ})"
            )
        return (
            f"pid={holder.pid} operation={holder.operation} "
            f"since={holder.acquired_at:%Y-%m-%dT%H:%M:%SZ}"
        )

    @classmethod
    def _record_mutation_holder(
        cls, lock_path: Path, holder: p.Infra.MutationLockHolder
    ) -> None:
        u.Cli.write_atomic_state(
            cls.mutation_lock_holder_path(lock_path),
            holder.model_dump_json().encode(c.DEFAULT_ENCODING),
        )

    @classmethod
    @contextmanager
    def hold_mutation_scope(cls, root: Path, operation: str) -> Generator[Path]:
        """Hold ``root``'s mutation lock for a whole operation, waiting visibly.

        A held lock is polled read-only until the configured deadline; every
        report interval names the recorded holder and the elapsed wait. The
        outermost holder records itself beside the lock and closes that record
        before releasing. Nested writers in the same thread re-enter the lock.

        Yields:
            The held lock path.

        Raises:
            TimeoutError: The lock is still held at the deadline; the message
                carries the last observed holder.

        """
        spec = config.Infra.mutation_lock
        lock_path = cls.mutation_lock_path(root).unwrap()
        lock = u.Cli.file_changes_lock(lock_path)
        started = time.monotonic()
        reported = started - spec.report_interval_seconds

        def report_wait() -> bool:
            nonlocal reported
            now = time.monotonic()
            if now - reported >= spec.report_interval_seconds:
                reported = now
                u.Cli.info(
                    f"{operation}: waiting {now - started:.0f}s for "
                    f"{cls._mutation_holder_text(lock_path)} (lock={lock_path})"
                )
            return False

        try:
            lock.acquire(
                timeout=spec.wait_deadline_seconds,
                poll_interval=spec.poll_interval_seconds,
                cancel_check=report_wait,
            )
        except TimeoutError as exc:
            msg = (
                f"{operation}: mutation lock {lock_path} still held after "
                f"{spec.wait_deadline_seconds:.0f}s by "
                f"{cls._mutation_holder_text(lock_path)}"
            )
            raise TimeoutError(msg) from exc
        if lock.lock_counter > 1:
            try:
                yield lock_path
            finally:
                lock.release()
            return
        holder = m.Infra.MutationLockHolder(
            pid=os.getpid(),
            operation=operation,
            root=root.resolve(),
            acquired_at=datetime.now(UTC),
            released_at=None,
        )
        try:
            cls._record_mutation_holder(lock_path, holder)
            yield lock_path
        except BaseException as original:
            # Rollback keeps the original failure as the one re-raised and
            # attaches a failed record close to its causal evidence.
            try:
                cls._record_mutation_holder(
                    lock_path,
                    holder.model_copy(update={"released_at": datetime.now(UTC)}),
                )
            except OSError as cleanup:
                original.add_note(f"mutation holder record not closed: {cleanup!r}")
            raise
        else:
            cls._record_mutation_holder(
                lock_path,
                holder.model_copy(update={"released_at": datetime.now(UTC)}),
            )
        finally:
            lock.release()


__all__: list[str] = ["FlextInfraUtilitiesGitMutationScope"]
