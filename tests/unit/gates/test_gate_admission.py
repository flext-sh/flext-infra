"""Host-wide heavy-gate admission through its public ``u.Infra`` owner (ADR-032).

Every case starts real holder processes (``tests.fixtures.gate_admission_holder``)
that admit themselves against a queue inside ``tmp_path``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig
from tests import c, m, p, tm, u
from tests.fixtures import TestsFlextInfraGateAdmissionHolder

_WAIT_SECONDS = 180.0


class TestsFlextInfraGateAdmission:
    """Prove FIFO admission, capacity, liveness, nesting and repeat limit."""

    @staticmethod
    def _environment(tmp_path: Path, level: str | None) -> dict[str, str]:
        state_home = Path(
            os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")
        )
        environment = {
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "MISE_STATE_DIR": os.environ.get(
                "MISE_STATE_DIR", str(state_home / "mise")
            ),
        }
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
        policy: tuple[int, bool] = (3600, False),
    ) -> p.Cli.ManagedProcess:
        """Start one holder that admits itself, records its run and waits for release.

        The runner's own CI and hook-stage markers never leak into a holder:
        only ``environment`` decides whether the repeat limit applies.

        Returns:
            The running holder process.

        """
        ci = FlextInfraConfig.fetch_global().Infra.codegen.make.ci
        budget_seconds, repeat = policy
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
                    *(("repeat",) if repeat else ()),
                ],
                cwd=Path.cwd(),
                options=m.Cli.ProcessOptions(
                    env=environment,
                    remove_env_keys=[
                        key
                        for key in (
                            ci.variable,
                            ci.remote_variable,
                            c.Infra.GATE_REPEAT_HOOK_STAGE_ENV,
                            c.Infra.GATE_ADMISSION_TICKET_ENV,
                        )
                        if key not in environment
                    ],
                ),
            )
        )

    @classmethod
    def _gate_in(
        cls,
        environment: dict[str, str],
        name: str,
        root: Path,
    ) -> p.Cli.ManagedProcess:
        """Start one held gate whose ticket repository is ``root``.

        Returns:
            The running holder process.

        """
        ci = FlextInfraConfig.fetch_global().Infra.codegen.make.ci
        return tm.ok(
            u.Cli.process_start(
                [
                    sys.executable,
                    "-m",
                    "tests.fixtures.gate_admission_holder",
                    name,
                    str(root),
                    TestsFlextInfraGateAdmissionHolder.Mode.HOLD,
                    "3600",
                ],
                cwd=Path.cwd(),
                options=m.Cli.ProcessOptions(
                    env=environment,
                    remove_env_keys=[
                        key
                        for key in (
                            ci.variable,
                            ci.remote_variable,
                            c.Infra.GATE_REPEAT_HOOK_STAGE_ENV,
                            c.Infra.GATE_ADMISSION_TICKET_ENV,
                        )
                        if key not in environment
                    ],
                ),
            )
        )

    @staticmethod
    def _await(path: Path) -> None:
        deadline = time.monotonic() + _WAIT_SECONDS
        while not path.exists():
            tm.that(time.monotonic() < deadline, eq=True, msg=f"never appeared: {path}")
            time.sleep(0.2)

    @staticmethod
    def _await_waiting(tmp_path: Path, process: p.Cli.ManagedProcess) -> None:
        queue = tmp_path / "state" / Path(*c.Infra.GATE_ADMISSION_STATE_PARTS)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            for path in queue.glob(f"*{c.Infra.GATE_ADMISSION_TICKET_SUFFIX}"):
                if not path.exists():
                    continue
                ticket = m.Infra.GateTicket.model_validate_json(path.read_bytes())
                if ticket.pid == process.pid:
                    tm.that(ticket.admitted_at is None, eq=True)
                    return
            time.sleep(0.05)
        pytest.fail(f"Gate process {process.pid} did not queue")

    @classmethod
    def _release(cls, tmp_path: Path, name: str, process: p.Cli.ManagedProcess) -> int:
        (tmp_path / f"{name}.release").write_text("", encoding="utf-8")
        return tm.ok(process.wait(timeout=_WAIT_SECONDS))

    @classmethod
    @pytest.mark.slow
    def test_mutating_gate_waits_for_an_overlapping_workspace(
        cls,
        tmp_path: Path,
    ) -> None:
        """A gen beside a gen on its parent or child checkout is not admitted."""
        environment = cls._environment(tmp_path, "normal")
        workspace = tmp_path / "workspace"
        member = workspace / "member"
        member.mkdir(parents=True)
        gate = c.Infra.GATE_ADMISSION_GENERATION
        holder = cls._gate_in(environment, gate, workspace)
        waiter: p.Cli.ManagedProcess | None = None
        try:
            cls._await(workspace / f"{gate}.started")
            waiter = cls._gate_in(environment, gate, member)
            cls._await_waiting(tmp_path, waiter)
            policy = FlextInfraConfig.fetch_global().Infra.gate_admission
            time.sleep(2 * policy.poll_seconds + 1)
            tm.that((member / f"{gate}.started").exists(), eq=False)
            (workspace / f"{gate}.release").write_text("", encoding="utf-8")
            cls._await(member / f"{gate}.started")
        finally:
            for process, root in ((holder, workspace), (waiter, member)):
                if process is None:
                    continue
                if process.poll() is None:
                    (root / f"{gate}.release").write_text("", encoding="utf-8")
                tm.ok(process.wait(timeout=_WAIT_SECONDS))

    @classmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("status", [0, 17])
    def test_native_gate_preserves_child_status(
        cls, tmp_path: Path, status: int
    ) -> None:
        """The public route preserves the native status and working directory."""
        output = cls._native_gate(
            tmp_path, f"import os, sys; print(os.getcwd()); sys.exit({status})", "5"
        )
        tm.that(output.outcome.raw_return_code, eq=status)
        tm.that(str(tmp_path) in output.stdout, eq=True)

    @classmethod
    @pytest.mark.slow
    def test_native_gate_bounds_child_execution(cls, tmp_path: Path) -> None:
        """The admitted child cannot outlive the declared execution budget."""
        output = cls._native_gate(tmp_path, "import time; time.sleep(60)", "2")
        tm.that(output.outcome.timed_out, eq=False)
        tm.that(output.outcome.raw_return_code, eq=124)

    @classmethod
    def _native_gate(
        cls, tmp_path: Path, program: str, budget: str
    ) -> p.Cli.CommandOutput:
        """Invoke the installed CLI against an isolated admission queue.

        Returns:
            The native route output, including its shell status.

        """
        return tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "workspace",
                    "native-gate",
                    "--repository-root",
                    str(tmp_path),
                    "--budget-seconds",
                    budget,
                    f"--argv={sys.executable}",
                    "--argv=-c",
                    f"--argv={program}",
                ],
                timeout=10,
                options=m.Cli.ProcessOptions(
                    env=cls._environment(tmp_path, "normal"),
                    remove_env_keys=[c.Infra.GATE_ADMISSION_TICKET_ENV],
                ),
            )
        )

    @classmethod
    @pytest.mark.slow
    def test_high_pressure_admits_one_gate_at_a_time_in_fifo_order(
        cls, tmp_path: Path
    ) -> None:
        """Under high pressure the second and third gates queue in arrival order."""
        environment = cls._environment(tmp_path, "high")
        first = cls._gate(environment, "first")
        cls._await(tmp_path / "first.started")
        second = cls._gate(environment, "second")
        cls._await_waiting(tmp_path, second)
        third = cls._gate(environment, "third")
        cls._await_waiting(tmp_path, third)
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
    @pytest.mark.slow
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
        cls._await_waiting(tmp_path, third)
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
    def test_unresolvable_tool_fails_before_the_route_queues(
        cls, tmp_path: Path
    ) -> None:
        """Preflight refuses a route whose declared tools cannot resolve.

        With no Mise on the PATH no declared tool resolves, so the route ends
        before it writes a ticket: the queue never holds a slot for it.
        """
        environment = {**cls._environment(tmp_path, None), "PATH": str(tmp_path)}
        gate = cls._gate(environment, "preflight")
        tm.that(tm.ok(gate.wait(timeout=_WAIT_SECONDS)), ne=0)
        tm.fail((tmp_path / "preflight.started").exists())
        queue = tmp_path / "state" / Path(*c.Infra.GATE_ADMISSION_STATE_PARTS)
        tm.that(
            [path.name for path in queue.glob("*.json")] if queue.is_dir() else [],
            empty=True,
        )

    @classmethod
    def test_budget_armed_at_admission_ends_the_route_with_the_timeout_status(
        cls, tmp_path: Path
    ) -> None:
        """A route that outlives its budget stops with the timeout status."""
        environment = cls._environment(tmp_path, None)
        gate = cls._gate(environment, "slow", policy=(3, False))
        cls._await(tmp_path / "slow.started")
        tm.that(
            tm.ok(gate.wait(timeout=_WAIT_SECONDS)),
            eq=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
        )
        tm.that((tmp_path / "slow.ended").exists(), eq=False)

    @classmethod
    @pytest.mark.slow
    def test_queue_wait_never_counts_against_the_budget(cls, tmp_path: Path) -> None:
        """A waiter queued longer than its budget still runs once admitted."""
        environment = cls._environment(tmp_path, "high")
        holder = cls._gate(environment, "holder")
        cls._await(tmp_path / "holder.started")
        waiter = cls._gate(environment, "waiter", policy=(2, False))
        cls._await_waiting(tmp_path, waiter)
        time.sleep(2.05)
        tm.that((tmp_path / "waiter.started").exists(), eq=False)
        (tmp_path / "waiter.release").write_text("", encoding="utf-8")
        tm.that(cls._release(tmp_path, "holder", holder), eq=0)
        tm.that(tm.ok(waiter.wait(timeout=_WAIT_SECONDS)), eq=0)

    @classmethod
    @pytest.mark.slow
    def test_dead_holder_frees_its_slot_by_liveness(cls, tmp_path: Path) -> None:
        """A killed holder's slot goes to the next waiter without any TTL wait."""
        environment = cls._environment(tmp_path, "high")
        holder = cls._gate(environment, "holder")
        cls._await(tmp_path / "holder.started")
        waiter = cls._gate(environment, "waiter")
        cls._await_waiting(tmp_path, waiter)
        tm.that((tmp_path / "waiter.started").exists(), eq=False)
        tm.ok(holder.kill())
        tm.ok(holder.wait(timeout=_WAIT_SECONDS))
        (tmp_path / "holder.release").write_text("", encoding="utf-8")
        cls._await(tmp_path / "waiter.started")
        tm.that(cls._release(tmp_path, "waiter", waiter), eq=0)

    @classmethod
    def test_live_holder_is_never_reclaimed(cls, tmp_path: Path) -> None:
        """A live owner keeps its slot even when its heartbeat is stale."""
        environment = cls._environment(tmp_path, "high")
        queue = tmp_path / "state" / Path(*c.Infra.GATE_ADMISSION_STATE_PARTS)
        queue.mkdir(parents=True)
        stale = datetime.now(UTC) - timedelta(days=1)
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
        lock = os.open(liveness, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        waiter = cls._gate(environment, "waiter")
        try:
            cls._await_waiting(tmp_path, waiter)
            policy = FlextInfraConfig.fetch_global().Infra.gate_admission
            time.sleep(2 * policy.poll_seconds + 1)
            tm.that(ticket.exists(), eq=True)
            tm.that((tmp_path / "waiter.started").exists(), eq=False)
        finally:
            os.close(lock)
        cls._await(tmp_path / "waiter.started")
        tm.that(cls._release(tmp_path, "waiter", waiter), eq=0)
        tm.that("released ticket 1" in waiter.stderr, eq=True)

    @classmethod
    def test_nested_gate_runs_under_its_ancestor_ticket(cls, tmp_path: Path) -> None:
        """A gate started inside an admitted gate never queues behind itself."""
        environment = cls._environment(tmp_path, "high")
        gate = cls._gate(
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

    @classmethod
    def _succeed(cls, tmp_path: Path, environment: dict[str, str]) -> None:
        """Run one full-weight gate to success, opening its repeat window."""
        (tmp_path / "check.started").unlink(missing_ok=True)
        gate = cls._gate(environment, "check", policy=(3600, True))
        cls._await(tmp_path / "check.started")
        tm.that(cls._release(tmp_path, "check", gate), eq=0)
        (tmp_path / "check.release").unlink()

    @classmethod
    def test_success_refuses_its_repeat_inside_the_window(cls, tmp_path: Path) -> None:
        """A second full-weight run inside the window fails before it queues."""
        environment = cls._environment(tmp_path, None)
        cls._succeed(tmp_path, environment)
        (tmp_path / "check.started").unlink()
        repeated = cls._gate(environment, "check", policy=(3600, True))
        tm.that(
            tm.ok(repeated.wait(timeout=_WAIT_SECONDS)),
            eq=c.Infra.GATE_ADMISSION_REFUSED_EXIT_CODE,
        )
        tm.that((tmp_path / "check.started").exists(), eq=False)
        window = FlextInfraConfig.fetch_global().Infra.gate_admission.repeat.check
        tm.that(window.lighter in repeated.stderr, eq=True)
        tm.that("never a pass" in repeated.stderr, eq=True)

    @classmethod
    def test_failed_run_never_opens_a_repeat_window(cls, tmp_path: Path) -> None:
        """Only a success is recorded; the corrected run is always admitted."""
        environment = cls._environment(tmp_path, None)
        failing = cls._gate(
            environment,
            "check",
            TestsFlextInfraGateAdmissionHolder.Mode.FAIL,
            policy=(3600, True),
        )
        cls._await(tmp_path / "check.started")
        tm.that(
            cls._release(tmp_path, "check", failing),
            eq=TestsFlextInfraGateAdmissionHolder.FAILURE_STATUS,
        )
        (tmp_path / "check.release").unlink()
        cls._succeed(tmp_path, environment)

    @classmethod
    def test_generation_health_ignores_a_red_tests_run(cls, tmp_path: Path) -> None:
        """Generation needs a green check only; other heavy routes need tests too."""
        environment = cls._environment(tmp_path, None)
        generation = cls._gate(
            environment, "gen", TestsFlextInfraGateAdmissionHolder.Mode.GEN_HEALTH
        )
        tm.that(tm.ok(generation.wait(timeout=_WAIT_SECONDS)), eq=0)
        refused = cls._gate(
            environment, "mod", TestsFlextInfraGateAdmissionHolder.Mode.FULL_HEALTH
        )
        tm.that(
            tm.ok(refused.wait(timeout=_WAIT_SECONDS)),
            eq=c.Infra.GATE_ADMISSION_REFUSED_EXIT_CODE,
        )
        tm.that("last make tests failed" in refused.stderr, eq=True)

    @classmethod
    def test_ci_runner_and_pre_push_hook_are_not_repeat_limited(
        cls, tmp_path: Path
    ) -> None:
        """The CI token and prek's pre-push stage run inside an open window."""
        environment = cls._environment(tmp_path, None)
        cls._succeed(tmp_path, environment)
        ci = FlextInfraConfig.fetch_global().Infra.codegen.make.ci
        cls._succeed(tmp_path, {**environment, ci.variable: ci.value})
        cls._succeed(
            tmp_path,
            {
                **environment,
                c.Infra.GATE_REPEAT_HOOK_STAGE_ENV: (
                    c.Infra.GATE_REPEAT_EXEMPT_HOOK_STAGE
                ),
            },
        )
