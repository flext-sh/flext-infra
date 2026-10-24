"""Generated-file plan decisions exposed through ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import errno
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from itertools import islice
from typing import TYPE_CHECKING

from flext_cli import m as cli_m, u

from flext_infra import c, m, p, r, t

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    def codegen_file_publication_admission(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[bool]:
        """Reapply the model's publication law to unchecked copies before effects.

        Returns:
            The first invalid plan or the complete admission.

        """
        for plan in plans:
            validated = u.validate_value(m.Infra.CodegenFilePlan, plan)
            if validated.failure:
                return r[bool].from_failure(validated)
        return r[bool].ok(value=True)

    @staticmethod
    def unique_states(
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Preserve the first identity per path and refuse conflicting snapshots.

        Returns:
            The authenticated ordered union or its first identity conflict.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        by_path: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        for file_state in states:
            previous = by_path.setdefault(file_state.path, file_state)
            if previous != file_state:
                first_hash = (
                    u.Cli.sha256_bytes(previous.content)
                    if previous.content is not None
                    else None
                )
                observed_hash = (
                    u.Cli.sha256_bytes(file_state.content)
                    if file_state.content is not None
                    else None
                )
                details = (
                    f" first={previous.model_dump_json(exclude={'content'})}"
                    f" observed={file_state.model_dump_json(exclude={'content'})}"
                    f" first_sha256={first_hash}"
                    f" observed_sha256={observed_hash}"
                )
                if previous.model_dump() == file_state.model_dump():
                    details += (
                        f" first_type={type(previous).__module__}."
                        f"{type(previous).__qualname__}"
                        f" observed_type={type(file_state).__module__}."
                        f"{type(file_state).__qualname__}"
                    )
                return result_type.fail(
                    f"planner observed two states for {file_state.path};{details}"
                )
        return result_type.ok(tuple(by_path.values()))

    @staticmethod
    def codegen_target_snapshot(
        path: Path,
    ) -> p.Result[cli_m.Cli.AtomicFileState | cli_m.Cli.AtomicDirectoryChainPlan]:
        """Capture the original leaf or the exact still-missing parent chain.

        Returns:
            The observed file state when the leaf exists, the missing-parent
            chain plan when it does not, or the propagated read failure.

        """
        result_type = r[cli_m.Cli.AtomicFileState | cli_m.Cli.AtomicDirectoryChainPlan]
        observed = u.Cli.atomic_read_binary_file_state(path, required=False)
        if observed.failure:
            return result_type.from_failure(observed)
        if observed.value.parent_device is not None:
            return result_type.ok(observed.value)
        witness = u.Cli.atomic_plan_directory_chain(path.parent)
        if witness.failure:
            return result_type.from_failure(witness)
        if not witness.value.directories:
            return result_type.fail(
                f"codegen destination parent changed during snapshot: {path}",
            )
        return result_type.ok(witness.value)

    @staticmethod
    def codegen_initializer_is_authored(content: bytes | None) -> bool:
        """Elect initializer ownership from content and declared generator markers.

        Returns:
            Whether a nonempty existing initializer belongs to its author.

        """
        return (
            content is not None
            and bool(content.strip())
            and not content.startswith(
                tuple(
                    header.encode(c.DEFAULT_ENCODING)
                    for header in c.Infra.AUTOGEN_HEADERS
                ),
            )
        )

    class JournalLeaseTimeoutError(TimeoutError):
        """Another process held the journal lease past the acquisition deadline."""

        def __init__(self, lock_file: Path) -> None:
            self.lock_file = str(lock_file)
            super().__init__(f"journal lease is held elsewhere: {self.lock_file}")

    @staticmethod
    @contextmanager
    def codegen_transaction_lease(
        journal_path: Path,
        *,
        wait_seconds: float = c.Infra.JOURNAL_LEASE_WAIT_SECONDS,
    ) -> Generator[None]:
        """Hold native ownership without unlinking the journal's lock identity.

        The lease holds an OS-native exclusive lock on a persistent lock file.
        POSIX uses ``flock``; Windows locks the first byte with ``msvcrt``.
        Neither path removes the lock identity when ownership ends.

        Acquisition waits politely for a held lease up to
        ``c.Infra.JOURNAL_LEASE_WAIT_SECONDS``: a legitimate fleet
        ``make gen`` holds the lease for minutes, so an immediate non-blocking
        refusal manufactured spurious ``JournalLeaseTimeoutError`` failures
        under ordinary concurrent traffic. The wait stays bounded, so a truly
        wedged holder still fails loud rather than hanging forever. A caller
        whose own deadline already runs (the testmon database owner) passes
        ``wait_seconds=0``: one attempt, then the loud refusal.
        Only native contention (EACCES, EAGAIN or EWOULDBLOCK) enters this wait;
        every other acquisition error escapes unchanged.

        Raises:
            OSError: If ``error.errno not in {errno.EACCES, errno.EAGAIN,
                errno.EWOULDBLOCK}``.
            JournalLeaseTimeoutError: If ``time.monotonic() >= deadline``.

        """
        lock_path = journal_path.with_name(f"{journal_path.name}.lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT,
            c.Infra.JOURNAL_MODE,
        )
        acquired = False
        waiting = False
        started = time.monotonic()
        try:
            deadline = started + wait_seconds
            while True:
                try:
                    if sys.platform == "win32":
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    if error.errno not in {
                        errno.EACCES,
                        errno.EAGAIN,
                        errno.EWOULDBLOCK,
                    }:
                        raise
                    if time.monotonic() >= deadline:
                        raise (
                            FlextInfraUtilitiesCodegenFilePlan.JournalLeaseTimeoutError
                        )(lock_path) from error
                    if not waiting:
                        print(
                            f"codegen journal lease: waiting for {lock_path}",
                            file=sys.stderr,
                            flush=True,
                        )
                        waiting = True
                    time.sleep(c.Infra.JOURNAL_LEASE_POLL_SECONDS)
                    continue
                acquired = True
                break
            if waiting:
                print(
                    "codegen journal lease: acquired "
                    f"{lock_path} after {time.monotonic() - started:.3f}s",
                    file=sys.stderr,
                    flush=True,
                )
            yield
        finally:
            try:
                if sys.platform == "win32" and acquired:
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            finally:
                os.close(descriptor)

    @staticmethod
    def required_file_states(
        paths: t.IterableOf[Path],
    ) -> p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]:
        """Snapshot descriptor-authenticated states for an inventoried path set.

        Every path must exist: an absent input is a planning defect, not an empty
        snapshot.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]``.

        """
        states: list[cli_m.Cli.AtomicFileState] = []
        for path in sorted(set(paths)):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[cli_m.Cli.AtomicFileState, ...]].from_failure(state)
            states.append(state.value)
        return r[tuple[cli_m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def codegen_file_before_state(
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[cli_m.Cli.AtomicFileState]:
        """Return a publishable state only after its parent physically exists.

        Returns:
            A publishable state only after its parent physically exists.

        """
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return r[cli_m.Cli.AtomicFileState].fail(
                f"codegen destination parent is absent: {plan.path.parent}",
            )
        return r[cli_m.Cli.AtomicFileState].ok(plan.before)

    @staticmethod
    def atomic_file_state_differs(
        before: cli_m.Cli.AtomicFileState,
        *,
        desired_content: bytes | None,
        desired_mode: int | None,
    ) -> bool:
        """Compare the owner's exact bytes, absence marker, and permission bits.

        Both content fields are binary contracts. Decoding with replacement
        would hide distinct invalid UTF-8 bytes; treating None as empty bytes
        would erase the distinction between an absent and an empty file.

        Returns:
            The resulting ``bool``.

        """
        return before.content != desired_content or before.mode != desired_mode

    @staticmethod
    def codegen_file_requires_effect(plan: m.Infra.CodegenFilePlan) -> bool:
        """Whether publication must change a generated-file destination.

        Returns:
            Whether bytes, mode or declared tracking require publication.

        """
        if plan.index_before is not None:
            return True
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return plan.desired_content is not None
        return FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            plan.before,
            desired_content=plan.desired_content,
            desired_mode=plan.desired_mode,
        )

    @staticmethod
    def codegen_fixed_point(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        subject: str,
    ) -> p.Result[bool]:
        """Reject a re-plan that still has to change any generated destination.

        Returns:
            Success only when no plan requires an effect; otherwise the failure
            names every residual destination with its bounded residual diff.

        """
        residual = tuple(
            plan
            for plan in plans
            if FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(plan)
        )
        if residual:
            names = ", ".join(str(plan.path) for plan in residual)
            drift = FlextInfraUtilitiesCodegenFilePlan.codegen_file_drift_report(
                residual,
            )
            return r[bool].fail(
                f"{subject} did not reach a fixed point: {names}\n{drift}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def codegen_file_drift_report(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        limit: int = 40,
    ) -> str:
        """Report a bounded byte-exact diff, including line endings and presence.

        Escaped byte lines preserve CRLF, missing final newlines, and non-UTF-8
        content. Only equal bytes with different modes are mode-only drift.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If codegen drift report limit must be positive.

        """
        if limit <= 0:
            msg = "codegen drift report limit must be positive"
            raise ValueError(msg)
        parts: list[str] = []
        for plan in plans:
            if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
                parts.append(f"{plan.path}: absent parent chain gains content")
                continue
            raw_before = plan.before.content
            old_lines = tuple(
                repr(line) for line in (raw_before or b"").splitlines(keepends=True)
            )
            new_lines = tuple(
                repr(line)
                for line in (plan.desired_content or b"").splitlines(keepends=True)
            )
            committed_mode = (
                oct(plan.before.mode) if plan.before.mode is not None else "absent"
            )
            rendered_mode = (
                oct(plan.desired_mode) if plan.desired_mode is not None else "absent"
            )
            header = (
                f"--- {plan.path} (committed mode={committed_mode})"
                f"\n+++ {plan.path} (rendered mode={rendered_mode})"
            )
            diff = tuple(
                islice(difflib.unified_diff(old_lines, new_lines, lineterm=""), limit),
            )
            if diff:
                parts.append("\n".join((header, *diff)))
                continue
            old_bytes = (
                raw_before.encode("utf-8")
                if isinstance(raw_before, str)
                else (raw_before or b"")
            )
            new_bytes = plan.desired_content or b""
            if old_bytes == new_bytes:
                parts.append(
                    f"{header}\n(content equal: mode-only drift "
                    f"observed={committed_mode} desired={rendered_mode})",
                )
                continue
            # Lines are equal but bytes are not: name the exact tail difference
            # (line endings / trailing newline) instead of a false mode claim.
            parts.append(
                f"{header}\n(lines equal, bytes differ: committed {len(old_bytes)}B "
                f"tail={old_bytes[-24:]!r}; rendered {len(new_bytes)}B "
                f"tail={new_bytes[-24:]!r})",
            )
        return "\n----\n".join(parts)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFilePlan"]
