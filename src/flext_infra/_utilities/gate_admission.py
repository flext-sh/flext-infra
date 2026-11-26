"""Host-wide FIFO admission for heavy gates (FLEXT ADR-032).

Every heavy gate on one host joins one queue under the user's state home.
A ticket's owner holds an exclusive liveness lock for its whole life, so a
dead owner frees its slot the moment any waiter looks, and a live owner is
never reclaimed: its heartbeat renews for the whole declared budget but is
diagnostic, never ownership. Admission is strict FIFO and capacity follows
the host-pressure level the host-budget owner publishes. A full-weight run
that succeeded in a checkout is refused before it queues while its declared
repeat window is open.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import threading
import time
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, settings
from flext_infra._utilities import (
    FlextInfraUtilitiesMiseBinary,
    FlextInfraUtilitiesProjectDiscovery,
)


class FlextInfraUtilitiesGateAdmission:
    """Admit heavy gates through one per-host FIFO queue."""

    @staticmethod
    def gate_admission_root() -> Path:
        """Derive the per-user, per-host queue directory.

        Returns:
            ``$XDG_STATE_HOME/flext/gate-admission`` or its ``$HOME`` default.

        Raises:
            ValueError: If neither state root is an absolute path.

        """
        env = u.Cli.process_env()
        state = env.get("XDG_STATE_HOME") or (
            str(Path(env["HOME"], ".local", "state")) if env.get("HOME") else ""
        )
        root = Path(state, *c.Infra.GATE_ADMISSION_STATE_PARTS)
        if not state or not root.is_absolute():
            msg = "gate admission requires an absolute XDG_STATE_HOME or HOME"
            raise ValueError(msg)
        return root

    @staticmethod
    def gate_admission_capacity() -> int:
        """Select the admission capacity from the published host-pressure level.

        Returns:
            ``capacity_normal`` when no pressure source is declared or the
            level is normal, otherwise ``capacity_high``.

        Raises:
            ValueError: If the declared source is not an absolute path.
            RuntimeError: If the published level is older than its validity.

        """
        policy = config.Infra.gate_admission
        source = u.Cli.process_env().get(c.Infra.GATE_ADMISSION_PRESSURE_FILE_ENV)
        if source is None:
            return policy.capacity_normal
        path = Path(source)
        if not source.strip() or not path.is_absolute():
            msg = f"{c.Infra.GATE_ADMISSION_PRESSURE_FILE_ENV} must be an absolute path"
            raise ValueError(msg)
        snapshot = m.Infra.HostPressureSnapshot.model_validate_json(path.read_bytes())
        age = (datetime.now(UTC) - snapshot.observed_at).total_seconds()
        if age > snapshot.valid_seconds:
            msg = (
                f"host pressure snapshot {path} is {age:.0f}s old, "
                f"valid for {snapshot.valid_seconds}s"
            )
            raise RuntimeError(msg)
        if snapshot.level is c.Infra.HostPressureLevel.NORMAL:
            return policy.capacity_normal
        return policy.capacity_high

    @classmethod
    @contextmanager
    def gate_admitted(
        cls,
        gate: str,
        repository: Path,
        budget: p.Infra.RouteBudgetSpec | None,
        *,
        wait_seconds: float | None = None,
    ) -> Generator[p.Infra.GateTicket]:
        """Admit one heavy route, then bound it by its budget from admission on.

        The queue wait never counts against the budget: the flext-cli process
        deadline is armed only once the route is admitted, and on expiry the
        process supervisor stops the owned children and the route exits with
        the timeout status; a route without a budget keeps the deadline of its
        native runner. A process started inside an admitted gate inherits
        its ancestor's ticket through ``FLEXT_GATE_ADMISSION_TICKET``, runs
        inside its ancestor's deadline and never queues again. A ticket that
        vanishes fails the admission; an admitted route whose lease renewal
        fails expires that same deadline with the first cause.

        Yields:
            The admitted ticket; its path is exported to every child process.

        """
        inherited = u.Cli.process_env().get(c.Infra.GATE_ADMISSION_TICKET_ENV)
        if inherited is not None:
            yield cls._inherited_ticket(Path(inherited))
            return
        cls._preflight_toolchain()
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        ticket, liveness = cls._enqueue(root, gate, repository)
        reclaimed = threading.Event()
        armed = threading.Event()
        stop = threading.Event()
        renewals: list[BaseException] = []

        def refresh() -> None:
            interval = cls._heartbeat_interval(budget)
            while not stop.wait(interval):
                try:
                    cls._renew(root, ticket, reclaimed)
                except BaseException as failure:
                    renewals.append(failure)
                    if armed.is_set():
                        u.Cli.process_deadline_expire()
                    else:
                        reclaimed.set()
                    raise
                if reclaimed.is_set():
                    break
            if reclaimed.is_set() and armed.is_set():
                u.Cli.error(f"gate admission ticket {ticket.name} was reclaimed")
                u.Cli.process_deadline_expire()

        heartbeat = threading.Thread(
            target=refresh, name=f"gate-admission-{ticket.stem}", daemon=True
        )
        heartbeat.start()
        try:
            admitted = cls._await_admission(
                root, ticket, reclaimed, renewals, wait_seconds
            )
            os.environ[c.Infra.GATE_ADMISSION_TICKET_ENV] = str(ticket)
            with u.Cli.process_deadline_scope(
                None
                if budget is None
                else m.Cli.ProcessDeadline(
                    expires_at_monotonic=time.monotonic() + budget.budget_seconds,
                    termination_grace_seconds=budget.grace_seconds,
                )
            ):
                armed.set()
                yield admitted
        finally:
            os.environ.pop(c.Infra.GATE_ADMISSION_TICKET_ENV, None)
            stop.set()
            heartbeat.join()
            with cls._queue_lock(root):
                ticket.unlink(missing_ok=True)
            cls._liveness_path(ticket).unlink(missing_ok=True)
            os.close(liveness)

    @staticmethod
    def _preflight_toolchain() -> None:
        """Fail before queueing when a declared tool cannot be resolved.

        ADR-032 "Fail early": a heavy route validates what it can decide
        without running a tool before it takes a slot. Every executable a
        route runs is declared by the toolchain owner and resolved from the
        invocation's tool-owning runtime, the same root the native runners
        use, so each declared tool must resolve to its pinned install first.

        Raises:
            FileNotFoundError: At the first declared tool that does not resolve.

        """
        owner_root = FlextInfraUtilitiesProjectDiscovery.runtime_environment_dir(
            Path.cwd(),
            runtime_root=settings.fetch_global().Infra.runtime_root,
        ).parent
        resolved = FlextInfraUtilitiesMiseBinary.resolve_declared_tools(owner_root)
        if resolved.failure:
            msg = (
                "preflight: declared toolchain does not resolve before queueing: "
                f"{resolved.error}"
            )
            raise FileNotFoundError(msg)

    @classmethod
    def gate_repeat_refuse(
        cls,
        gate: str,
        repository: Path,
        window: p.Infra.GateRepeatWindow,
        selection: Sequence[str] = (),
    ) -> None:
        """Refuse a full-weight run that already succeeded inside its window.

        Runs before the gate queues. CI runners and the pre-push hook are not
        limited, and only successes are recorded, so a failed run never opens
        a window.

        Raises:
            SystemExit: With the refusal status while the window is open; a
                refusal is a failure, never a pass.

        """
        if cls._repeat_exempt():
            return
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        with cls._queue_lock(root):
            earlier = [
                record
                for record in cls._ledger(root, repository)
                if record.gate == gate and record.selection == tuple(selection)
            ]
        if not earlier:
            return
        elapsed = (datetime.now(UTC) - earlier[-1].finished_at).total_seconds()
        if elapsed >= window.window_seconds:
            return
        scope = "".join(f" {item}" for item in selection)
        u.Cli.emit_raw(
            f"gate admission: refused {gate}{scope} in {repository}: the same "
            f"full-weight run succeeded at "
            f"{earlier[-1].finished_at.isoformat(timespec='seconds')} "
            f"({elapsed:.0f}s ago); its repeat window is "
            f"{window.window_seconds}s, {window.window_seconds - elapsed:.0f}s "
            f"left.\nRun the lighter form instead: {window.lighter}\n"
            "This refusal is a failure, never a pass (FLEXT ADR-032).\n",
            error=True,
        )
        raise SystemExit(c.Infra.GATE_ADMISSION_REFUSED_EXIT_CODE)

    @classmethod
    def gate_repeat_record(
        cls,
        ticket: p.Infra.GateTicket,
        selection: Sequence[str] = (),
    ) -> None:
        """Record a successful full-weight run for repeat limiting.

        Only successes are recorded. The record is written to the repeat ledger
        for the ticket's gate and selection, so a subsequent run inside the
        window will be refused.

        """
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC)
        record = m.Infra.GateRunRecord(
            gate=ticket.gate,
            status="success",
            selection=tuple(selection),
            repository=ticket.repository,
            admitted_at=ticket.admitted_at or now,
            finished_at=now,
        )
        ledger = cls._ledger_path(root, Path(ticket.repository))
        with cls._queue_lock(root):
            kept = [
                earlier
                for earlier in cls._ledger(root, Path(ticket.repository))
                if earlier.gate != ticket.gate or earlier.selection != tuple(selection)
            ]
            ledger.parent.mkdir(exist_ok=True)
            u.Cli.atomic_write_text_file(
                ledger,
                "".join(f"{entry.model_dump_json()}\n" for entry in (*kept, record)),
                durability=c.Cli.WriteDurability.SCRATCH,
            ).unwrap()

    @classmethod
    def gate_health_record(
        cls,
        repository: Path,
        gate: str,
        *,
        success: bool,
    ) -> None:
        """Record the outcome of a check/tests run for heavy-op gating.

        Writes (or replaces) the latest entry for ``gate`` with its ``status``.
        CI runners and the pre-push hook are not exempt here: health is recorded
        in every context so heavy ops can see the real state.

        """
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        health_gate = f"health-{gate}"
        now = datetime.now(UTC)
        record = m.Infra.GateRunRecord(
            gate=health_gate,
            status="success" if success else "failure",
            selection=(),
            repository=str(repository),
            admitted_at=now,
            finished_at=now,
        )
        ledger = cls._ledger_path(root, repository)
        with cls._queue_lock(root):
            kept = [
                earlier
                for earlier in cls._ledger(root, repository)
                if earlier.gate != health_gate
            ]
            ledger.parent.mkdir(exist_ok=True)
            u.Cli.atomic_write_text_file(
                ledger,
                "".join(f"{entry.model_dump_json()}\n" for entry in (*kept, record)),
                durability=c.Cli.WriteDurability.SCRATCH,
            ).unwrap()

    @classmethod
    def gate_health_refuse(cls, repository: Path) -> None:
        """Refuse a heavy op when the check or tests health is failed or stale.

        Missing records are allowed (first-run grace). Exempt contexts (CI,
        remote, pre-push) bypass. Generation is not gated here: it runs inside
        ``make check`` (ADR-037), so a check-health gate on it is circular
        (operator 2026-11-26).

        Raises:
            SystemExit: When the last recorded health is a failure or stale.

        """
        if cls._repeat_exempt():
            return
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        repeat = config.Infra.gate_admission.repeat
        windows = {
            "health-check": repeat.check.window_seconds,
            "health-tests": repeat.tests_full.window_seconds,
        }
        remediation = {
            "health-check": "make check",
            "health-tests": "make tests",
        }
        with cls._queue_lock(root):
            records = cls._ledger(root, repository)
        now = datetime.now(UTC)
        for health_gate, window in windows.items():
            matches = [r for r in records if r.gate == health_gate]
            if not matches:
                continue
            last = matches[-1]
            elapsed = (now - last.finished_at).total_seconds()
            if last.status != "success":
                u.Cli.emit_raw(
                    f"gate admission: refused heavy operation in {repository}: "
                    f"last {remediation[health_gate]} failed at "
                    f"{last.finished_at.isoformat(timespec='seconds')}; "
                    f"repair and rerun it before heavy work.\n",
                    error=True,
                )
                raise SystemExit(c.Infra.GATE_ADMISSION_REFUSED_EXIT_CODE)
            if elapsed >= window:
                u.Cli.emit_raw(
                    f"gate admission: refused heavy operation in {repository}: "
                    f"last green {remediation[health_gate]} is "
                    f"{elapsed:.0f}s old (window {window}s); rerun it.\n",
                    error=True,
                )
                raise SystemExit(c.Infra.GATE_ADMISSION_REFUSED_EXIT_CODE)

    @staticmethod
    def _repeat_exempt() -> bool:
        """Report whether a CI runner or the pre-push hook runs this gate.

        Returns:
            ``True`` for the declared CI token, a remote runner, or prek's
            pre-push stage.

        """
        env = u.Cli.process_env()
        ci = config.Infra.codegen.make.ci
        return (
            env.get(ci.variable) == ci.value
            or env.get(ci.remote_variable) == ci.remote_value
            or env.get(c.Infra.GATE_REPEAT_HOOK_STAGE_ENV)
            == c.Infra.GATE_REPEAT_EXEMPT_HOOK_STAGE
        )

    @staticmethod
    def _ledger_path(root: Path, repository: Path) -> Path:
        digest = hashlib.sha256(str(repository.resolve()).encode()).hexdigest()
        return (
            root
            / c.Infra.GATE_ADMISSION_HISTORY_DIR
            / f"{digest[:16]}{c.Infra.GATE_ADMISSION_HISTORY_SUFFIX}"
        )

    @classmethod
    def _ledger(cls, root: Path, repository: Path) -> list[m.Infra.GateRunRecord]:
        """Read a checkout's repeat ledger; must run under the queue lock.

        Returns:
            The recorded successes, oldest first.

        """
        ledger = cls._ledger_path(root, repository)
        if not ledger.is_file():
            return []
        return [
            m.Infra.GateRunRecord.model_validate_json(line)
            for line in ledger.read_text(encoding=c.DEFAULT_ENCODING).splitlines()
            if line.strip()
        ]

    @classmethod
    def _inherited_ticket(cls, ticket: Path) -> m.Infra.GateTicket:
        """Accept an ancestor's ticket only while it is admitted and alive.

        Returns:
            The inherited ticket.

        Raises:
            RuntimeError: If the ticket is missing, waiting or dead.

        """
        with cls._queue_lock(ticket.parent):
            if not ticket.is_file():
                msg = f"inherited gate admission ticket is gone: {ticket}"
                raise RuntimeError(msg)
            record = cls._read(ticket)
            if record.admitted_at is None or not cls._alive(ticket):
                msg = f"inherited gate admission ticket is not admitted: {ticket}"
                raise RuntimeError(msg)
        return record

    @classmethod
    def _enqueue(cls, root: Path, gate: str, repository: Path) -> tuple[Path, int]:
        """Append one ticket owned by this process to the queue.

        Returns:
            The ticket path and its held liveness lock.

        Raises:
            RuntimeError: If gate admission liveness lock is already held.

        """
        with cls._queue_lock(root):
            counter = root / c.Infra.GATE_ADMISSION_SEQUENCE_FILE
            sequence = (
                int(counter.read_text(encoding=c.DEFAULT_ENCODING))
                if counter.is_file()
                else 0
            ) + 1
            u.Cli.atomic_write_text_file(counter, str(sequence)).unwrap()
            ticket = root / f"{sequence:020d}{c.Infra.GATE_ADMISSION_TICKET_SUFFIX}"
            liveness = cls._try_lock(cls._liveness_path(ticket))
            if liveness is None:
                msg = f"gate admission liveness lock is already held: {ticket}"
                raise RuntimeError(msg)
            now = datetime.now(UTC)
            cls._write(
                ticket,
                m.Infra.GateTicket(
                    sequence=sequence,
                    pid=os.getpid(),
                    gate=gate,
                    repository=str(repository),
                    enqueued_at=now,
                    heartbeat_at=now,
                ),
            )
        return ticket, liveness

    @classmethod
    def _await_admission(
        cls,
        root: Path,
        ticket: Path,
        reclaimed: threading.Event,
        renewals: list[BaseException],
        wait_seconds: float | None,
    ) -> m.Infra.GateTicket:
        """Wait in FIFO order until a slot is free for this ticket.

        Returns:
            The admitted ticket.

        Raises:
            TimeoutError: If ``wait_seconds`` expires first.
            RuntimeError: If the lease renewal failed or the ticket vanished.

        """
        policy = config.Infra.gate_admission
        deadline = None if wait_seconds is None else time.monotonic() + wait_seconds
        reported = ""
        while True:
            with cls._queue_lock(root):
                if renewals or reclaimed.is_set() or not ticket.is_file():
                    msg = (
                        f"gate admission lease renewal failed: {renewals[0]}"
                        if renewals
                        else f"gate admission ticket {ticket.name} was reclaimed"
                    )
                    raise RuntimeError(msg) from (renewals[0] if renewals else None)
                live = cls._sweep(root, own=ticket)
                capacity = cls.gate_admission_capacity()
                holders = [record for record in live if record.admitted_at]
                waiting = sorted(
                    (record for record in live if record.admitted_at is None),
                    key=lambda record: record.sequence,
                )
                mine = cls._read(ticket)
                blocked = next(
                    (
                        record
                        for record in holders
                        if FlextInfraUtilitiesGateAdmission._workspace_conflict(
                            mine, record
                        )
                    ),
                    None,
                )
                if (
                    waiting[0].sequence == mine.sequence
                    and len(holders) < capacity
                    and blocked is None
                ):
                    now = datetime.now(UTC)
                    admitted = mine.model_copy(
                        update={"admitted_at": now, "heartbeat_at": now}
                    )
                    cls._write(ticket, admitted)
                    if reported:
                        u.Cli.emit_raw(
                            f"gate admission: {mine.gate} admitted\n", error=True
                        )
                    return admitted
                position = [record.sequence for record in waiting].index(mine.sequence)
            conflict = (
                f"; workspace conflict with {blocked.gate} pid {blocked.pid} "
                f"{blocked.repository}"
                if blocked is not None
                else ""
            )
            state = (
                f"gate admission: {mine.gate} waiting, position {position + 1}, "
                f"capacity {capacity}, holders: "
                + ", ".join(
                    f"{record.gate} pid {record.pid} {record.repository}"
                    for record in holders
                )
                + conflict
            )
            if state != reported:
                u.Cli.emit_raw(f"{state}\n", error=True)
                reported = state
            if deadline is not None and time.monotonic() >= deadline:
                msg = f"{state} (wait of {wait_seconds}s expired)"
                raise TimeoutError(msg)
            time.sleep(policy.poll_seconds)

    @staticmethod
    def _workspace_overlap(left: str, right: str) -> bool:
        """Whether two ticket repositories are the same checkout or nested.

        Returns:
            True for the same path or a parent/child relationship.

        """
        first = Path(left).resolve()
        second = Path(right).resolve()
        return (
            first == second
            or first.is_relative_to(second)
            or second.is_relative_to(first)
        )

    @classmethod
    def _workspace_conflict(
        cls,
        mine: m.Infra.GateTicket,
        holder: m.Infra.GateTicket,
    ) -> bool:
        """Whether admitting ``mine`` beside ``holder`` would race mutations.

        A generation or modification route writes the workspace; another heavy
        route on the same checkout or a member of it cannot run beside it.
        Two read-only routes, or routes on unrelated workspaces, stay
        concurrent under the declared capacity.

        Returns:
            True when either gate mutates and their repositories overlap.

        """
        mutating = c.Infra.GATE_ADMISSION_MUTATING_GATES
        if mine.gate not in mutating and holder.gate not in mutating:
            return False
        return cls._workspace_overlap(mine.repository, holder.repository)

    @classmethod
    def _sweep(cls, root: Path, *, own: Path) -> list[m.Infra.GateTicket]:
        """Drop dead owners' tickets; return every remaining live ticket.

        The liveness lock is the only ownership proof: a ticket whose lock no
        process holds is released, and a live owner keeps its slot whatever
        its heartbeat age. Must run under the queue lock.

        Returns:
            The live tickets, including the caller's own.

        """
        live: list[m.Infra.GateTicket] = []
        for ticket in sorted(root.glob(f"*{c.Infra.GATE_ADMISSION_TICKET_SUFFIX}")):
            record = cls._read(ticket)
            if ticket == own or cls._alive(ticket):
                live.append(record)
                continue
            ticket.unlink()
            cls._liveness_path(ticket).unlink(missing_ok=True)
            u.Cli.emit_raw(
                f"gate admission: released ticket {record.sequence} "
                f"({record.gate} pid {record.pid} {record.repository}): "
                "its owner no longer holds the liveness lock\n",
                error=True,
            )
        return live

    @classmethod
    def _renew(cls, root: Path, ticket: Path, reclaimed: threading.Event) -> None:
        """Refresh one live ticket's heartbeat under the queue lock.

        A vanished ticket marks ``reclaimed``; the owner then expires its
        deadline instead of running without an admitted slot.

        """
        with cls._queue_lock(root):
            if not ticket.is_file():
                reclaimed.set()
                return
            cls._write(
                ticket,
                cls._read(ticket).model_copy(
                    update={"heartbeat_at": datetime.now(UTC)}
                ),
            )

    @staticmethod
    def _heartbeat_interval(budget: p.Infra.RouteBudgetSpec | None) -> float:
        """Derive the lease renewal interval from the declared route budget.

        A live owner renews its lease for its whole declared budget: the
        configured ``heartbeat_seconds`` is the ceiling and a declared
        fraction of the budget guarantees several renewals before the
        deadline. A route without a budget renews at the ceiling.

        Returns:
            The renewal interval in seconds.

        """
        ceiling = config.Infra.gate_admission.heartbeat_seconds
        if budget is None:
            return float(ceiling)
        return float(
            max(
                1,
                min(
                    ceiling,
                    budget.budget_seconds // c.Infra.GATE_ADMISSION_HEARTBEAT_DIVISOR,
                ),
            )
        )

    @staticmethod
    def _alive(ticket: Path) -> bool:
        """Probe whether a ticket's owner still holds its liveness lock.

        Returns:
            ``True`` while another process (or thread) holds the lock.

        """
        probe = FlextInfraUtilitiesGateAdmission._try_lock(
            FlextInfraUtilitiesGateAdmission._liveness_path(ticket)
        )
        if probe is None:
            return True
        os.close(probe)
        return False

    @staticmethod
    def _try_lock(path: Path) -> int | None:
        """Take an exclusive non-blocking ``flock`` on a close-on-exec descriptor.

        Returns:
            The locked descriptor, or ``None`` while another descriptor holds it.

        """
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(descriptor)
            return None
        return descriptor

    @staticmethod
    def _liveness_path(ticket: Path) -> Path:
        return ticket.with_name(
            f"{ticket.name}{c.Infra.GATE_ADMISSION_LIVENESS_SUFFIX}"
        )

    @staticmethod
    @contextmanager
    def _queue_lock(root: Path) -> Generator[None]:
        descriptor = os.open(
            root / c.Infra.GATE_ADMISSION_QUEUE_LOCK,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC,
            0o600,
        )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)

    @staticmethod
    def _read(ticket: Path) -> m.Infra.GateTicket:
        return m.Infra.GateTicket.model_validate_json(ticket.read_bytes())

    @staticmethod
    def _write(ticket: Path, record: m.Infra.GateTicket) -> None:
        u.Cli.atomic_write_text_file(
            ticket,
            record.model_dump_json(),
            durability=c.Cli.WriteDurability.SCRATCH,
        ).unwrap()


__all__: list[str] = ["FlextInfraUtilitiesGateAdmission"]
