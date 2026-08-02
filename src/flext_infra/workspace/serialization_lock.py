"""Canonical native process-lock owner for serialized workspace operations."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path

from filelock import FileLock, Timeout

from flext_core import r
from flext_infra import c, m
from flext_infra._utilities.workspace_fingerprint import (
    FlextInfraUtilitiesWorkspaceFingerprint,
)
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraSerializationLockOwner:
    """Acquire deterministic workspace locks around one typed operation."""

    @staticmethod
    def _capture_make_fingerprints(
        context: m.Infra.MakeExecutionContext,
    ) -> p.Result[tuple[tuple[Path, m.Infra.WorkspaceFingerprint], ...]]:
        snapshots: list[tuple[Path, m.Infra.WorkspaceFingerprint]] = []
        for checkout in dict.fromkeys(item.root for item in context.targets):
            captured = FlextInfraUtilitiesWorkspaceFingerprint.workspace_fingerprint(
                checkout,
                excluded_paths=context.make.serialization.snapshot_excludes,
            )
            if captured.failure:
                return r.fail(r.require_error(captured))
            snapshots.append((checkout, captured.value))
        return r.ok(tuple(snapshots))

    @staticmethod
    def _make_fingerprint_changes(
        before: tuple[tuple[Path, m.Infra.WorkspaceFingerprint], ...],
        after: tuple[tuple[Path, m.Infra.WorkspaceFingerprint], ...],
    ) -> p.Result[tuple[str, ...]]:
        changed: list[str] = []
        for (root_before, snapshot_before), (root_after, snapshot_after) in zip(
            before, after, strict=True
        ):
            if root_before != root_after:
                return r.fail(
                    "workspace fingerprint target order changed during operation"
                )
            if snapshot_before.digest == snapshot_after.digest:
                continue
            paths = (
                FlextInfraUtilitiesWorkspaceFingerprint.workspace_fingerprint_changes(
                    snapshot_before, snapshot_after
                )
            )
            changed.extend(
                (f"{root_before}:{path}" for path in paths)
                if paths
                else (f"{root_before}:HEAD/index",)
            )
        return r.ok(tuple(changed))

    @classmethod
    def _verify_make_fingerprints(
        cls,
        context: m.Infra.MakeExecutionContext,
        before: tuple[tuple[Path, m.Infra.WorkspaceFingerprint], ...],
    ) -> p.Result[bool]:
        after = cls._capture_make_fingerprints(context)
        if after.failure:
            return r.fail(r.require_error(after))
        changed = cls._make_fingerprint_changes(before, after.value)
        if changed.failure:
            return r.fail(r.require_error(changed))
        if changed.value:
            return r.fail(
                "workspace changed during read-only Make operation: "
                + ", ".join(changed.value)
            )
        return r.ok(True)

    @classmethod
    def execute_guarded_make(
        cls,
        context: m.Infra.MakeExecutionContext,
        operation: Callable[[], p.Result[m.Infra.ProcessExit]],
        failure: Callable[[int, str], p.Result[m.Infra.ProcessExit]],
    ) -> p.Result[m.Infra.ProcessExit]:
        """Execute one Make operation and prove every read-only target unchanged."""
        invocation = context.invocation
        read_only = invocation.operation.mutation == "never" or (
            invocation.operation.mutation == "apply" and not invocation.applying
        )
        if not read_only:
            return operation()
        before = cls._capture_make_fingerprints(context)
        if before.failure:
            return failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(before)
            )
        result = operation()
        verified = cls._verify_make_fingerprints(context, before.value)
        if verified.failure:
            return failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(verified)
            )
        return result

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
        verb reuses its per-checkout lock, so the artifact is durable state and
        is preserved. An isolated worktree transaction owns its sandbox for one
        operation, so its lock -- and any directory the lock alone created --
        is removed on exit; retaining it would leak state into the source
        checkout the transaction promised not to mutate.
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
