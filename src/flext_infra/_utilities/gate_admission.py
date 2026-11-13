"""Host-wide FIFO admission for heavy gates (FLEXT ADR-032).

Every heavy gate on one host joins one queue under the user's state home.
A ticket's owner holds an exclusive liveness lock for its whole life, so a
dead owner frees its slot the moment any waiter looks; a live owner whose
heartbeat is older than the TTL is reclaimed. Admission is strict FIFO and
capacity follows the host-pressure level the host-budget owner publishes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import _thread
import fcntl
import os
import signal
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p


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
        *,
        wait_seconds: float | None = None,
    ) -> Generator[Path]:
        """Hold one admitted slot for the duration of the block.

        A process started inside an admitted gate inherits its ancestor's
        ticket through ``FLEXT_GATE_ADMISSION_TICKET`` and never queues again.
        When the queue reclaims a stalled owner's ticket, an owner on the main
        thread is interrupted at once; any other owner fails when it leaves.

        Yields:
            The admitted ticket path, exported to every child process.

        Raises:
            RuntimeError: If the queue reclaimed the ticket.

        """
        inherited = u.Cli.process_env().get(c.Infra.GATE_ADMISSION_TICKET_ENV)
        if inherited is not None:
            yield cls._inherited_ticket(Path(inherited))
            return
        root = cls.gate_admission_root()
        root.mkdir(parents=True, exist_ok=True)
        ticket, liveness = cls._enqueue(root, gate, repository)
        reclaimed = threading.Event()
        stop = threading.Event()
        owner_is_main = threading.current_thread() is threading.main_thread()

        def refresh() -> None:
            interval = config.Infra.gate_admission.heartbeat_seconds
            while not stop.wait(interval):
                with cls._queue_lock(root):
                    if not ticket.is_file():
                        reclaimed.set()
                        break
                    cls._write(
                        ticket,
                        cls._read(ticket).model_copy(
                            update={"heartbeat_at": datetime.now(UTC)}
                        ),
                    )
            if reclaimed.is_set() and owner_is_main:
                _thread.interrupt_main(signal.SIGALRM)

        heartbeat = threading.Thread(
            target=refresh, name=f"gate-admission-{ticket.stem}", daemon=True
        )
        heartbeat.start()
        try:
            cls._await_admission(root, ticket, reclaimed, wait_seconds)
            os.environ[c.Infra.GATE_ADMISSION_TICKET_ENV] = str(ticket)
            yield ticket
        except TimeoutError as exc:
            if reclaimed.is_set():
                msg = f"gate admission ticket {ticket.name} was reclaimed"
                raise RuntimeError(msg) from exc
            raise
        finally:
            os.environ.pop(c.Infra.GATE_ADMISSION_TICKET_ENV, None)
            stop.set()
            heartbeat.join()
            with cls._queue_lock(root):
                ticket.unlink(missing_ok=True)
            cls._liveness_path(ticket).unlink(missing_ok=True)
            os.close(liveness)
        if reclaimed.is_set():
            msg = f"gate admission ticket {ticket.name} was reclaimed"
            raise RuntimeError(msg)

    @classmethod
    @contextmanager
    def gate_admitted_budget(
        cls, gate: str, repository: Path, budget: p.Infra.RouteBudgetSpec
    ) -> Generator[None]:
        """Admit one heavy route, then bound it by its budget from admission on.

        The queue wait never counts against the budget. An inherited admission
        runs inside its ancestor's budget and arms no second one.

        Yields:
            Nothing; the slot and the budget hold until the block exits.

        """
        if u.Cli.process_env().get(c.Infra.GATE_ADMISSION_TICKET_ENV) is not None:
            with cls.gate_admitted(gate, repository):
                yield
            return
        with cls.gate_admitted(gate, repository):
            deadline = m.Cli.ProcessDeadline(
                expires_at_monotonic=time.monotonic() + budget.budget_seconds,
                termination_grace_seconds=budget.grace_seconds,
            )
            with u.Cli.process_deadline_scope(deadline):
                yield

    @classmethod
    def _inherited_ticket(cls, ticket: Path) -> Path:
        """Accept an ancestor's ticket only while it is admitted and alive.

        Returns:
            The inherited ticket path.

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
        return ticket

    @classmethod
    def _enqueue(
        cls, root: Path, gate: str, repository: Path
    ) -> tuple[Path, int]:
        """Append one ticket owned by this process to the queue.

        Returns:
            The ticket path and its held liveness lock.

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
        wait_seconds: float | None,
    ) -> None:
        """Wait in FIFO order until a slot is free for this ticket.

        Raises:
            TimeoutError: If ``wait_seconds`` expires first.
            RuntimeError: If the queue reclaimed the ticket.

        """
        policy = config.Infra.gate_admission
        deadline = None if wait_seconds is None else time.monotonic() + wait_seconds
        reported = ""
        while True:
            with cls._queue_lock(root):
                if reclaimed.is_set() or not ticket.is_file():
                    msg = f"gate admission ticket {ticket.name} was reclaimed"
                    raise RuntimeError(msg)
                live = cls._sweep(root, own=ticket)
                capacity = cls.gate_admission_capacity()
                holders = [record for record in live if record.admitted_at]
                waiting = sorted(
                    (record for record in live if record.admitted_at is None),
                    key=lambda record: record.sequence,
                )
                mine = cls._read(ticket)
                if waiting[0].sequence == mine.sequence and len(holders) < capacity:
                    now = datetime.now(UTC)
                    cls._write(
                        ticket,
                        mine.model_copy(update={"admitted_at": now, "heartbeat_at": now}),
                    )
                    if reported:
                        sys.stderr.write(f"gate admission: {mine.gate} admitted\n")
                    return
                position = [record.sequence for record in waiting].index(
                    mine.sequence
                )
            state = (
                f"gate admission: {mine.gate} waiting, position {position + 1}, "
                f"capacity {capacity}, holders: "
                + ", ".join(
                    f"{record.gate} pid {record.pid} {record.repository}"
                    for record in holders
                )
            )
            if state != reported:
                sys.stderr.write(f"{state}\n")
                sys.stderr.flush()
                reported = state
            if deadline is not None and time.monotonic() >= deadline:
                msg = f"{state} (wait of {wait_seconds}s expired)"
                raise TimeoutError(msg)
            time.sleep(policy.poll_seconds)

    @classmethod
    def _sweep(cls, root: Path, *, own: Path) -> list[m.Infra.GateTicket]:
        """Drop dead and stalled tickets; return every remaining live ticket.

        Must run under the queue lock.

        Returns:
            The live tickets, including the caller's own.

        """
        ttl = config.Infra.gate_admission.ttl_seconds
        now = datetime.now(UTC)
        live: list[m.Infra.GateTicket] = []
        for ticket in sorted(root.glob(f"*{c.Infra.GATE_ADMISSION_TICKET_SUFFIX}")):
            record = cls._read(ticket)
            if ticket != own and not cls._alive(ticket):
                ticket.unlink()
                cls._liveness_path(ticket).unlink(missing_ok=True)
                continue
            stalled = (now - record.heartbeat_at).total_seconds()
            if ticket != own and stalled > ttl:
                ticket.unlink()
                sys.stderr.write(
                    f"gate admission: reclaimed ticket {record.sequence} "
                    f"({record.gate} pid {record.pid} {record.repository}): "
                    f"heartbeat {stalled:.0f}s old exceeds ttl {ttl}s\n"
                )
                continue
            live.append(record)
        return live

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
        return ticket.with_name(f"{ticket.name}{c.Infra.GATE_ADMISSION_LIVENESS_SUFFIX}")

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
