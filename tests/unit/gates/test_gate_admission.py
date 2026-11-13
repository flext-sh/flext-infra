"""Host-wide heavy-gate admission through its public ``u.Infra`` owner (ADR-032).

Every case starts real holder processes (``tests.fixtures.gate_admission_holder``)
that admit themselves against a queue inside ``tmp_path``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from flext_infra import FlextInfraConfig
from tests import TestsFlextInfraGateAdmissionHolder, c, m, p, tm, u

_WAIT_SECONDS = 180.0


class TestsFlextInfraGateAdmission:
    """Prove FIFO admission, capacity, liveness, TTL and nesting."""

    @staticmethod
    def _environment(tmp_path: Path, level: str | None) -> dict[str, str]:
        environment = {"XDG_STATE_HOME": str(tmp_path / "state")}
        if level is not None:
            snapshot = tmp_path / "pressure.json"
            snapshot.write_text(
                json.dumps({
                    "level": level,
                    "observed_at": datetime.now(UTC).isoformat(),
                    "valid_seconds": 3600,
                }),
                encoding="utf-8",
            )
            environment[c.Infra.GATE_ADMISSION_PRESSURE_FILE_ENV] = str(snapshot)
        return environment

    @classmethod
    def _gate(
        cls,
        environment: dict[str, str],
        name: str,
        mode: str = TestsFlextInfraGateAdmissionHolder.Mode.HOLD,
        *,
        budget_seconds: int = 3600,
    ) -> p.Cli.ManagedProcess:
        """Start one holder that admits itself, records its run and waits for release.

        Returns:
            The running holder process.

        """
        return tm.ok(
            u.Cli.process_start(
                [
                    sys.executable,
                    "-m",
                    "tests.fixtures.gate_admission_holder",
                    name,
                    str(Path(environment["XDG_STATE_HOME"]).parent),
                    mode,
                    str(budget_seconds),
                ],
                cwd=Path.cwd(),
                options=m.Cli.ProcessOptions(env=environment),
            )
        )

    @staticmethod
    def _await(path: Path) -> None:
        deadline = time.monotonic() + _WAIT_SECONDS
        while not path.exists():
            tm.that(time.monotonic() < deadline, eq=True, msg=f"never appeared: {path}")
            time.sleep(0.2)

    @classmethod
    def _release(cls, tmp_path: Path, name: str, process: p.Cli.ManagedProcess) -> int:
        (tmp_path / f"{name}.release").write_text("", encoding="utf-8")
        return tm.ok(process.wait(timeout=_WAIT_SECONDS))

    @classmethod
    def test_high_pressure_admits_one_gate_at_a_time_in_fifo_order(
        cls, tmp_path: Path
    ) -> None:
        """Under high pressure the second and third gates queue in arrival order."""
        environment = cls._environment(tmp_path, "high")
        first = cls._gate(environment, "first")
        cls._await(tmp_path / "first.started")
        second = cls._gate(environment, "second")
        time.sleep(1)
        third = cls._gate(environment, "third")
        time.sleep(5)
        tm.that((tmp_path / "second.started").exists(), eq=False)
        tm.that((tmp_path / "third.started").exists(), eq=False)
        (tmp_path / "third.release").write_text("", encoding="utf-8")
        tm.that(cls._release(tmp_path, "first", first), eq=0)
        cls._await(tmp_path / "second.started")
        tm.that((tmp_path / "third.started").exists(), eq=False)
        tm.that(cls._release(tmp_path, "second", second), eq=0)
        tm.that(tm.ok(third.wait(timeout=_WAIT_SECONDS)), eq=0)
        ends = {
            name: float((tmp_path / f"{name}.ended").read_text(encoding="utf-8"))
            for name in ("first", "second")
        }
        starts = {
            name: float((tmp_path / f"{name}.started").read_text(encoding="utf-8"))
            for name in ("second", "third")
        }
        tm.that(starts["second"] >= ends["first"], eq=True)
        tm.that(starts["third"] >= ends["second"], eq=True)
        tm.that("position 1" in second.stderr, eq=True)
        tm.that("first pid" in second.stderr, eq=True)

    @classmethod
    def test_normal_pressure_admits_two_and_queues_the_third(
        cls, tmp_path: Path
    ) -> None:
        """Without a pressure source two gates run together and a third waits."""
        environment = cls._environment(tmp_path, None)
        first = cls._gate(environment, "first")
        second = cls._gate(environment, "second")
        cls._await(tmp_path / "first.started")
        cls._await(tmp_path / "second.started")
        third = cls._gate(environment, "third")
        time.sleep(5)
        tm.that((tmp_path / "third.started").exists(), eq=False)
        tm.that(cls._release(tmp_path, "first", first), eq=0)
        cls._await(tmp_path / "third.started")
        tm.that(cls._release(tmp_path, "second", second), eq=0)
        tm.that(cls._release(tmp_path, "third", third), eq=0)

    @classmethod
    def test_admitted_route_status_is_returned_unchanged(cls, tmp_path: Path) -> None:
        """An admitted route leaves with its own status."""
        environment = cls._environment(tmp_path, None)
        gate = cls._gate(
            tmp_path,
            environment,
            "failing",
            TestsFlextInfraGateAdmissionHolder.Mode.FAIL,
        )
        cls._await(tmp_path / "failing.started")
        tm.that(
            cls._release(tmp_path, "failing", gate),
            eq=TestsFlextInfraGateAdmissionHolder.FAILURE_STATUS,
        )

    @classmethod
    def test_budget_armed_at_admission_ends_the_route_with_the_timeout_status(
        cls, tmp_path: Path
    ) -> None:
        """A route that outlives its budget stops with the timeout status."""
        environment = cls._environment(tmp_path, None)
        gate = cls._gate(environment, "slow", budget_seconds=3)
        cls._await(tmp_path / "slow.started")
        tm.that(
            tm.ok(gate.wait(timeout=_WAIT_SECONDS)),
            eq=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
        )
        tm.that((tmp_path / "slow.ended").exists(), eq=False)

    @classmethod
    def test_queue_wait_never_counts_against_the_budget(cls, tmp_path: Path) -> None:
        """A waiter queued longer than its budget still runs once admitted."""
        environment = cls._environment(tmp_path, "high")
        holder = cls._gate(environment, "holder")
        cls._await(tmp_path / "holder.started")
        waiter = cls._gate(environment, "waiter", budget_seconds=4)
        time.sleep(6)
        tm.that((tmp_path / "waiter.started").exists(), eq=False)
        (tmp_path / "waiter.release").write_text("", encoding="utf-8")
        tm.that(cls._release(tmp_path, "holder", holder), eq=0)
        tm.that(tm.ok(waiter.wait(timeout=_WAIT_SECONDS)), eq=0)

    @classmethod
    def test_dead_holder_frees_its_slot_by_liveness(cls, tmp_path: Path) -> None:
        """A killed holder's slot goes to the next waiter without any TTL wait."""
        environment = cls._environment(tmp_path, "high")
        holder = cls._gate(environment, "holder")
        cls._await(tmp_path / "holder.started")
        waiter = cls._gate(environment, "waiter")
        time.sleep(3)
        tm.that((tmp_path / "waiter.started").exists(), eq=False)
        tm.ok(holder.kill())
        tm.ok(holder.wait(timeout=_WAIT_SECONDS))
        (tmp_path / "holder.release").write_text("", encoding="utf-8")
        cls._await(tmp_path / "waiter.started")
        tm.that(cls._release(tmp_path, "waiter", waiter), eq=0)

    @classmethod
    def test_stalled_live_holder_is_reclaimed_after_its_ttl(
        cls, tmp_path: Path
    ) -> None:
        """A held ticket whose heartbeat is older than the TTL stops blocking."""
        environment = cls._environment(tmp_path, "high")
        queue = tmp_path / "state" / Path(*c.Infra.GATE_ADMISSION_STATE_PARTS)
        queue.mkdir(parents=True)
        stale = datetime.now(UTC) - timedelta(
            seconds=FlextInfraConfig.fetch_global().Infra.gate_admission.ttl_seconds
            + 60
        )
        ticket = queue / f"{1:020d}{c.Infra.GATE_ADMISSION_TICKET_SUFFIX}"
        ticket.write_text(
            m.Infra.GateTicket(
                sequence=1,
                pid=os.getpid(),
                gate="stalled",
                repository=str(tmp_path),
                enqueued_at=stale,
                admitted_at=stale,
                heartbeat_at=stale,
            ).model_dump_json(),
            encoding="utf-8",
        )
        (queue / c.Infra.GATE_ADMISSION_SEQUENCE_FILE).write_text("1", encoding="utf-8")
        liveness = queue / f"{ticket.name}{c.Infra.GATE_ADMISSION_LIVENESS_SUFFIX}"
        holder = tm.ok(
            u.Cli.process_start(
                ["flock", "--exclusive", str(liveness), "sleep", "600"],
                cwd=tmp_path,
            )
        )
        try:
            time.sleep(1)
            waiter = cls._gate(environment, "waiter")
            cls._await(tmp_path / "waiter.started")
            tm.that(ticket.exists(), eq=False)
            tm.that(cls._release(tmp_path, "waiter", waiter), eq=0)
            tm.that("reclaimed ticket 1" in waiter.stderr, eq=True)
        finally:
            os.kill(holder.pid, signal.SIGKILL)
            tm.ok(holder.wait(timeout=_WAIT_SECONDS))

    @classmethod
    def test_nested_gate_runs_under_its_ancestor_ticket(cls, tmp_path: Path) -> None:
        """A gate started inside an admitted gate never queues behind itself."""
        environment = cls._environment(tmp_path, "high")
        gate = cls._gate(
            tmp_path,
            environment,
            "outer",
            TestsFlextInfraGateAdmissionHolder.Mode.NESTED,
        )
        cls._await(tmp_path / "outer.started")
        tm.that(cls._release(tmp_path, "outer", gate), eq=0)
        tm.that((tmp_path / "outer.nested").exists(), eq=True)

    @classmethod
    def test_stale_pressure_snapshot_stops_admission(cls, tmp_path: Path) -> None:
        """A declared pressure source older than its validity fails loud."""
        environment = cls._environment(tmp_path, "normal")
        snapshot = Path(environment[c.Infra.GATE_ADMISSION_PRESSURE_FILE_ENV])
        snapshot.write_text(
            json.dumps({
                "level": "normal",
                "observed_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                "valid_seconds": 60,
            }),
            encoding="utf-8",
        )
        gate = cls._gate(environment, "refused")
        tm.that(tm.ok(gate.wait(timeout=_WAIT_SECONDS)) != 0, eq=True)
        tm.that((tmp_path / "refused.started").exists(), eq=False)
        tm.that("host pressure snapshot" in gate.stderr, eq=True)
