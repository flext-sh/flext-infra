"""Behavior tests for bounded Mypy process execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pstats
import signal
import sys
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraUtilitiesResourceLimits:
    """Behavior tests for the canonical Mypy resource-limit command."""

    @staticmethod
    def test_candidate_mypy_keeps_persistent_cache_outside_sources(
        tmp_path: Path,
    ) -> None:
        """Use the elected real runtime without modifying candidate membership."""
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'fixture-candidate-cache'\nversion = '1.0'\n"
            "[tool.mypy]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = tmp_path / "candidate.py"
        source.write_text("value: int = 1\n", encoding=c.DEFAULT_ENCODING)
        workspace = u.Infra.runtime_environment_dir(Path(__file__).parents[3]).parent
        cache = u.Infra.mypy_cache_directory(tmp_path)
        for value in (1, 2):
            source.write_text(f"value: int = {value}\n", encoding=c.DEFAULT_ENCODING)
            before = {
                path.relative_to(tmp_path): path.read_bytes()
                for path in tmp_path.rglob("*")
                if path.is_file()
            }
            observed = u.Infra.lint_snapshot(source, workspace, gates=(c.Infra.MYPY,))
            tm.that(u.Infra.lint_execution_errors(observed), empty=True)
            tm.that(observed[c.Infra.MYPY].errors, empty=True)
            tm.that(
                {
                    path.relative_to(tmp_path): path.read_bytes()
                    for path in tmp_path.rglob("*")
                    if path.is_file()
                },
                eq=before,
            )
            tm.fail(cache.is_relative_to(tmp_path))
            tm.ok(cache.is_dir())
            tm.ok(any(path.is_file() for path in cache.rglob("*")))

    @staticmethod
    @pytest.mark.requires_engine("mypy")
    def test_mypy_command_checks_source_with_memory_and_time_limits(
        tmp_path: Path,
    ) -> None:
        """Check a real typed source through both validated resource ceilings."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        command = u.Infra.mypy_limited_command(
            u.Tests.mypy_workload(tmp_path),
            limit,
        )
        if sys.platform != "darwin":
            tm.that(command, has="--verbose")
        result = u.Cli.run_raw(command, timeout=u.Infra.mypy_runner_timeout(limit))

        tm.ok(result)
        tm.ok(u.Cli.process_succeeded(result.value.outcome))

    @staticmethod
    @pytest.mark.requires_engine("mypy")
    @pytest.mark.slow
    def test_mypy_profile_records_the_real_checker(tmp_path: Path) -> None:
        """Profile the real checker without changing its incremental workload."""
        project = u.Tests.mypy_workload(tmp_path)
        profile = tmp_path / "checker.pstats"
        invocation = m.Infra.MypyInvocation(
            targets=project.targets,
            config_file=project.config_file,
            profile_output=profile,
            verbose=True,
        )
        tm.that(
            u.Infra.mypy_arguments(invocation),
            eq=u.Infra.mypy_arguments(
                m.Infra.MypyInvocation(
                    targets=project.targets,
                    config_file=project.config_file,
                    verbose=True,
                ),
            ),
        )
        result = u.Cli.run_raw(
            u.Infra.mypy_limited_command(invocation),
            timeout=u.Infra.mypy_runner_timeout(),
        )
        tm.ok(result)
        tm.ok(u.Cli.process_succeeded(result.value.outcome))
        tm.that(
            bool(pstats.Stats(str(profile)).get_stats_profile().func_profiles),
            eq=True,
        )
        tm.that(result.value.stderr, has=f"Parsing {project.targets[0]}")
        tm.that(
            profile.with_suffix(".timing.txt").read_text(encoding=c.DEFAULT_ENCODING),
            has="checked ",
        )
        tm.that(
            profile.with_suffix(".lines.txt").read_text(encoding=c.DEFAULT_ENCODING),
            has="checked:",
        )
        # Profiling retains the same warm-cache behavior as the production gate.
        repeated = u.Cli.run_raw(
            u.Infra.mypy_limited_command(invocation),
            timeout=u.Infra.mypy_runner_timeout(),
        )
        tm.ok(repeated)
        tm.ok(u.Cli.process_succeeded(repeated.value.outcome))
        tm.that(
            repeated.value.stderr,
            has="Metadata fresh for checked:",
            lacks=f"Parsing {project.targets[0]}",
        )
        tm.that(
            bool(pstats.Stats(str(profile)).get_stats_profile().func_profiles),
            eq=True,
        )

    @staticmethod
    @pytest.mark.requires_engine("mypy")
    @pytest.mark.slow
    @pytest.mark.parametrize("scenario", ["assignment", "SIGINT", "SIGTERM"])
    def test_mypy_profile_preserves_failure_and_interruption(
        tmp_path: Path,
        scenario: str,
    ) -> None:
        """Retain native failure status and readable profiles after termination."""
        project = u.Tests.mypy_workload(
            tmp_path,
            ""
            if scenario == "assignment"
            else (
                "import signal\nfrom pathlib import Path\n"
                f"Path(__file__).with_suffix('.signal').write_text('{scenario}', "
                f"encoding={c.DEFAULT_ENCODING!r})\n"
                f"signal.raise_signal(signal.{scenario})"
            ),
        )
        if scenario == "assignment":
            project.targets[0].write_text(
                "value: int = 'invalid'\n",
                encoding=c.DEFAULT_ENCODING,
            )
        profile = tmp_path / "checker.pstats"
        result = u.Cli.run_raw(
            u.Infra.mypy_limited_command(
                m.Infra.MypyInvocation(
                    targets=project.targets,
                    config_file=project.config_file,
                    profile_output=profile,
                ),
            ),
            timeout=u.Infra.mypy_runner_timeout(),
        )
        tm.ok(result)
        tm.fail(u.Cli.process_succeeded(result.value.outcome))
        tm.fail(result.value.outcome.timed_out)
        if scenario == "assignment":
            tm.that(result.value.stdout, has="Incompatible types in assignment")
        else:
            tm.that(
                (tmp_path / "workload.signal").read_text(encoding=c.DEFAULT_ENCODING),
                eq=scenario,
            )
        tm.that(
            bool(pstats.Stats(str(profile)).get_stats_profile().func_profiles),
            eq=True,
        )

    @staticmethod
    @pytest.mark.parametrize("ceiling", [False, True])
    def test_mypy_budget_resolves_the_project_tooling_overlay(
        tmp_path: Path,
        ceiling: bool,
    ) -> None:
        """A project tooling.yaml budget drives the runner timeout."""
        policy = config.Infra.tooling.tools.mypy
        budget = policy.max_timeout_seconds if ceiling else policy.timeout_seconds // 2
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "tooling.yaml").write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            f"        timeout_seconds: {budget}\n",
            encoding="utf-8",
        )
        expected_limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=u.Infra.mypy_resource_limit().memory_limit_mb,
            timeout_seconds=budget,
        )

        tm.that(
            u.Infra.mypy_runner_timeout_for_project(tmp_path),
            eq=u.Infra.mypy_runner_timeout(expected_limit),
        )
        effective = u.Infra.mypy_resource_limit_for_project(tmp_path)
        tm.that(effective, eq=expected_limit)
        command = u.Infra.mypy_limited_command(
            u.Tests.mypy_workload(tmp_path),
            effective,
        )
        tm.that(
            command,
            has=str(budget) if sys.platform == "darwin" else f"{budget}s",
        )
        diagnostic = u.Infra.mypy_failure_diagnostic(
            m.Cli.CommandOutput(
                stdout="",
                stderr="deadline exhausted",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=124,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            ),
            effective,
        )
        tm.that(diagnostic, has=f"timeout={budget}s")

    @staticmethod
    def test_mypy_budget_overlay_above_the_fleet_bound_fails_loud(
        tmp_path: Path,
    ) -> None:
        """A project budget above the ceiling fails without clamping."""
        above = config.Infra.tooling.tools.mypy.max_timeout_seconds + 1
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "tooling.yaml").write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            f"        timeout_seconds: {above}\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="exceeds the fleet ceiling"):
            u.Infra.mypy_runner_timeout_for_project(tmp_path)

    @staticmethod
    @pytest.mark.parametrize("budget", ["0", "-1", "true", "1.5", "'12'"])
    def test_mypy_budget_rejects_non_positive_or_non_integer_values(
        tmp_path: Path,
        budget: str,
    ) -> None:
        """Malformed project budgets cannot launch an unbounded child."""
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "tooling.yaml").write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            f"        timeout_seconds: {budget}\n",
            encoding="utf-8",
        )
        with pytest.raises((TypeError, ValueError)):
            u.Infra.mypy_resource_limit_for_project(tmp_path)

    @staticmethod
    @pytest.mark.parametrize("field", ["timeout_seconds", "max_timeout_seconds"])
    @pytest.mark.parametrize("value", [0, -1, True, 1.5, "12"])
    def test_mypy_policy_requires_positive_integer_seconds(
        field: str,
        value: float | str,
    ) -> None:
        """Both canonical budgets reject coercion and non-positive seconds."""
        policy = config.Infra.tooling.tools.mypy
        payload = policy.model_dump(by_alias=True)
        payload[field] = value
        with pytest.raises(ValueError):
            type(policy).model_validate(payload)

    @staticmethod
    def test_mypy_policy_rejects_default_above_its_ceiling() -> None:
        """The typed SSOT rejects an inconsistent default and ceiling."""
        policy = config.Infra.tooling.tools.mypy
        payload = policy.model_dump(by_alias=True)
        payload["timeout_seconds"] = policy.max_timeout_seconds + 1
        with pytest.raises(ValueError, match="default timeout exceeds"):
            type(policy).model_validate(payload)

    @staticmethod
    def test_mypy_budget_without_overlay_uses_the_fleet_default(
        tmp_path: Path,
    ) -> None:
        """No project overlay falls back to the fleet tooling SSOT."""
        tm.that(
            u.Infra.mypy_runner_timeout_for_project(tmp_path),
            eq=u.Infra.mypy_runner_timeout(),
        )

    @staticmethod
    def test_workspace_checker_requires_its_own_environment(
        tmp_path: Path,
    ) -> None:
        """An unprovisioned target never borrows the orchestrator's interpreter."""
        u.Tests.initialize_git_repo(tmp_path)
        project = u.Tests.mypy_workload(tmp_path)
        invocation = m.Infra.MypyInvocation(
            targets=project.targets,
            config_file=project.config_file,
            workspace=tmp_path,
        )
        with pytest.raises(FileNotFoundError, match="managed workspace interpreter"):
            u.Infra.mypy_command(invocation)
        tm.ok(u.Tests.create_python_environment(tmp_path))
        with pytest.raises(FileNotFoundError, match="managed workspace checker"):
            u.Infra.mypy_command(invocation)

    @staticmethod
    def test_supervisor_rejects_executable_selection_before_launch(
        tmp_path: Path,
    ) -> None:
        """A hostile request cannot turn the supervisor into an arbitrary executor."""
        project = u.Tests.mypy_workload(tmp_path)
        command = u.Infra.mypy_limited_command(project, host_system="Darwin")
        injected = project.model_dump_json()[:-1] + ',"command":["/bin/sh"]}'
        result = u.Cli.run_raw(
            (*command[:-1], injected),
            timeout=u.Infra.mypy_runner_timeout(),
        )
        tm.ok(result)
        tm.that(result.value.outcome.raw_return_code, eq=1)
        tm.that(result.value.stderr, has="Extra inputs are not permitted")

    @staticmethod
    @pytest.mark.parametrize(
        ("scenario", "expected"),
        [
            ("exit", 7),
            # Real interpreter startup and controlled group cleanup use the
            # existing integration-harness budget, not the default case budget.
            pytest.param("deadline", 124, marks=pytest.mark.slow),
            # The checker may use different nonzero exit codes while reporting
            # the same bounded allocation failure through its public output.
            ("memory", None),
        ],
    )
    def test_resource_limit_enforces_exit_deadline_and_memory(
        tmp_path: Path,
        scenario: str,
        expected: int | None,
    ) -> None:
        """Exercise a real exit, deadline and resident allocation through the owner."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=max(1, c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT // 2)
            if scenario == "memory"
            else c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=u.Tests.mypy_deadline_limit().timeout_seconds
            if scenario == "deadline"
            else config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        source = "import sys,time; print('workload-ready', flush=True); "
        if scenario == "exit":
            source += "sys.exit(7)"
        else:
            if scenario == "memory":
                source += f"allocation = bytearray({limit.memory_limit_bytes * 2}); "
            source += f"time.sleep({limit.timeout_seconds + 1})"
        command = u.Infra.mypy_limited_command(
            u.Tests.mypy_workload(tmp_path, source),
            limit,
        )
        result = u.Cli.run_raw(command, timeout=u.Infra.mypy_runner_timeout(limit))
        tm.ok(result)
        tm.that(result.value.stdout, has="workload-ready")
        if scenario == "memory":
            tm.that(
                any(str(limit.memory_limit_bytes) in part for part in command[:-1]),
                eq=True,
            )
            tm.fail(u.Cli.process_succeeded(result.value.outcome))
            tm.fail(result.value.outcome.timed_out)
            # The configured bound itself must cause the stop: only a
            # resource-exhaustion outcome (memory marker or signal) yields the
            # public diagnostic, so an unrelated checker failure after the
            # workload start can no longer satisfy this scenario.
            diagnostic = tm.not_none(
                u.Infra.mypy_failure_diagnostic(result.value, limit),
            )
            tm.that(diagnostic, has=f"memory_limit={limit.memory_limit_mb} MiB")
            if sys.platform == "darwin":
                tm.that(result.value.stderr, has="RSS limit reached")
        else:
            tm.that(result.value.outcome.raw_return_code, eq=expected)
            if scenario == "deadline":
                tm.fail(result.value.outcome.timed_out)
                tm.that(
                    u.Infra.mypy_failure_diagnostic(result.value, limit),
                    has=[f"exit={expected}", "signal=none"],
                )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("leader_exits", "expected"),
        [(True, 7), (False, c.Infra.PROCESS_TIMEOUT_EXIT_CODE)],
    )
    def test_resource_limit_stops_resistant_descendant_group(
        tmp_path: Path,
        *,
        leader_exits: bool,
        expected: int,
        request: pytest.FixtureRequest,
    ) -> None:
        """Kill a TERM-resistant descendant after leader exit or deadline."""
        limit = u.Tests.mypy_deadline_limit()
        policy = config.Infra.tooling.tools.pytest
        pid_file = tmp_path / "descendant.pid"
        error_file = tmp_path / "descendant.stderr"
        request.addfinalizer(
            lambda: u.Tests.reap_mypy_descendant(
                pid_file,
                policy.termination_grace_seconds,
            ),
        )
        bound = u.Infra.mypy_runner_timeout(limit) + policy.slow_timeout_seconds
        sleep = f"time.sleep({bound})"
        tail = f"sys.exit({expected})" if leader_exits else sleep
        descendant = (
            "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            f"print('ready', flush=True); {sleep}"
        )
        source = (
            "import subprocess,sys,time\nfrom pathlib import Path\n"
            f"errors = Path({str(error_file)!r})\n"
            "with errors.open('w', encoding='utf-8') as stderr:\n"
            f"    p = subprocess.Popen([sys.executable, '-c', {descendant!r}], "
            "stdout=subprocess.PIPE, stderr=stderr, text=True)\n"
            f"    Path({str(pid_file)!r}).write_text(str(p.pid), encoding='utf-8')\n"
            "    if p.stdout is None or p.stdout.readline() != 'ready\\n':\n"
            "        stderr.flush()\n"
            "        sys.stderr.write(errors.read_text(encoding='utf-8'))\n"
            "        raise RuntimeError('descendant readiness failed')\n"
            f"    print(p.pid, flush=True)\n    {tail}"
        )
        result = u.Cli.run_raw(
            u.Infra.mypy_limited_command(
                u.Tests.mypy_workload(tmp_path, source),
                limit,
            ),
            timeout=u.Infra.mypy_runner_timeout(limit),
        )
        tm.ok(result)
        tm.that(result.value.outcome.raw_return_code, eq=expected)
        tm.ok(bool(result.value.stdout.splitlines()))
        pid = int(result.value.stdout.splitlines()[0])
        tm.that(int(pid_file.read_text(encoding=c.DEFAULT_ENCODING)), eq=pid)
        tm.that(error_file.read_text(encoding=c.DEFAULT_ENCODING), empty=True)
        remaining = u.Cli.run_raw(
            ("/bin/ps", "-p", str(pid), "-o", "stat="),
            timeout=policy.termination_grace_seconds,
        )
        tm.ok(remaining)
        state = remaining.value.stdout.strip()
        if sys.platform == "darwin":
            tm.ok(not state or state.startswith("Z"))
        # GNU timeout reaps the resistant group when it stops the leader at
        # the deadline; on a clean leader exit the group outlives the
        # wrapper, so pytest teardown reaps its own descendant instead.
        elif not leader_exits:
            tm.ok(not state)

    @staticmethod
    def test_resource_limit_stops_workload_on_termination(tmp_path: Path) -> None:
        """Preserve external termination and reap the running workload."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        started = u.Cli.process_start(
            u.Infra.mypy_limited_command(
                u.Tests.mypy_workload(
                    tmp_path,
                    "import time; print('ready', flush=True); "
                    f"time.sleep({limit.timeout_seconds + 1})",
                ),
                limit,
            ),
        )
        tm.ok(started)
        child = started.value
        try:
            tm.ok(child.stdout_read_until(b"ready", timeout=limit.timeout_seconds))
            tm.ok(child.terminate())
            exited = child.wait(timeout=10)
            tm.ok(exited)
            expected_exit = 143 if sys.platform == "darwin" else -15
            tm.that(exited.value, eq=expected_exit)
        finally:
            if child.poll() is None:
                tm.ok(child.kill())
                tm.ok(child.wait(timeout=5))

    @staticmethod
    def test_mypy_resource_contract_rejects_non_positive_limits() -> None:
        """Reject invalid external configuration before spawning a process."""
        invalid: int = 0
        with pytest.raises(ValueError, match="greater than 0"):
            m.Infra.MypyResourceLimit(memory_limit_mb=invalid, timeout_seconds=invalid)

    @staticmethod
    def test_mypy_resource_limit_parses_environment_at_boundary() -> None:
        """Convert valid process text once; the time bound stays the SSOT value."""
        memory_limit = c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT // 2
        with tm.scope(env={c.Infra.MYPY_MEMORY_LIMIT_MB_ENV: str(memory_limit)}):
            limit = u.Infra.mypy_resource_limit()

        tm.that(limit.memory_limit_mb, eq=memory_limit)
        tm.that(
            limit.timeout_seconds,
            eq=config.Infra.tooling.tools.mypy.timeout_seconds,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "invalid_value",
        [
            # Each case spawns a real interpreter that imports the full
            # package tree before the boundary rejects the text, so they run
            # on the integration-harness budget like the deadline scenario
            # above, never on the default case budget.
            pytest.param("", marks=pytest.mark.slow),
            pytest.param("1024.0", marks=pytest.mark.slow),
            pytest.param("-1", marks=pytest.mark.slow),
            pytest.param(" 1024", marks=pytest.mark.slow),
        ],
    )
    def test_mypy_resource_limit_rejects_non_integer_environment(
        invalid_value: str,
    ) -> None:
        """Reject non-integer process text before constructing the strict model.

        A real child process receives the value verbatim, so nothing test-side
        can repair `` 1024`` into a valid limit (``tm.scope`` routes env values
        through a whitespace-stripping model) and the test process's own
        environment is never mutated. The contract under test is exactly that
        the parse boundary performs no such repair.
        """
        result = u.Cli.run_raw(
            [
                sys.executable,
                "-c",
                "from flext_infra import u; u.Infra.mypy_resource_limit()",
            ],
            options=m.Cli.ProcessOptions(
                env={c.Infra.MYPY_MEMORY_LIMIT_MB_ENV: invalid_value},
            ),
        )
        tm.ok(result)
        tm.fail(u.Cli.process_succeeded(result.value.outcome))
        tm.that(result.value.stderr, has=f"{c.Infra.MYPY_MEMORY_LIMIT_MB_ENV} must be")

    @staticmethod
    def test_mypy_resource_contract_rejects_memory_above_ceiling() -> None:
        """Reject a configured limit above the canonical hard ceiling."""
        with pytest.raises(
            ValueError,
            match=f"less than or equal to {c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT}",
        ):
            m.Infra.MypyResourceLimit(
                memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT + 1,
                timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("exit_code", "timed_out"),
        [
            (0, True),
            (7, True),
            (c.Infra.PROCESS_TIMEOUT_EXIT_CODE, True),
            (c.Infra.PROCESS_TIMEOUT_EXIT_CODE, False),
        ],
    )
    def test_mypy_timeout_has_controlled_exit_and_signal_diagnostic(
        exit_code: int,
        *,
        timed_out: bool,
    ) -> None:
        """Expose the configured ceilings and process status on timeout."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        diagnostic = u.Infra.mypy_failure_diagnostic(
            m.Cli.CommandOutput(
                stdout="LOG:  Parsing oci.models\nTRACE: dependency graph",
                stderr="timeout: sending signal TERM to command 'prlimit'",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=exit_code,
                    timed_out=timed_out,
                    forwarded_signal=None,
                ),
            ),
            limit,
        )

        tm.that(
            diagnostic,
            has=[
                f"memory_limit={limit.memory_limit_mb} MiB",
                f"timeout={limit.timeout_seconds}s",
                f"exit={exit_code}",
                "signal=none",
                "timeout: sending signal TERM",
            ],
        )
        tm.that(diagnostic, lacks=["LOG:", "TRACE:"])

    @staticmethod
    @pytest.mark.parametrize(
        "exit_code",
        [1, 2, c.Infra.PROCESS_SIGNAL_EXIT_OFFSET + 1],
    )
    def test_ordinary_exit_codes_do_not_invent_resource_failures(
        exit_code: int,
    ) -> None:
        """Numeric exit conventions cannot replace causal resource evidence."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        diagnostic = u.Infra.mypy_failure_diagnostic(
            m.Cli.CommandOutput(
                stdout="",
                stderr="",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=exit_code,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            ),
            limit,
        )
        tm.that(diagnostic, is_=None)

    @staticmethod
    @pytest.mark.parametrize(
        ("exit_code", "forwarded_signal", "signal_number"),
        [
            (-signal.SIGSEGV, None, signal.SIGSEGV),
            (0, signal.SIGINT, signal.SIGINT),
            (
                c.Infra.PROCESS_SIGNAL_EXIT_OFFSET + signal.SIGKILL,
                None,
                signal.SIGKILL,
            ),
        ],
    )
    def test_mypy_signal_diagnostic_preserves_both_output_streams(
        exit_code: int,
        forwarded_signal: int | None,
        signal_number: int,
    ) -> None:
        """Expose traceback output when Mypy also writes an error banner."""
        limit = m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=config.Infra.tooling.tools.mypy.timeout_seconds,
        )
        diagnostic = u.Infra.mypy_failure_diagnostic(
            m.Cli.CommandOutput(
                stdout="Traceback: checker frame",
                stderr="INTERNAL ERROR",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=exit_code,
                    timed_out=False,
                    forwarded_signal=forwarded_signal,
                ),
            ),
            limit,
        )

        tm.that(
            diagnostic,
            has=[
                "Traceback: checker frame",
                "INTERNAL ERROR",
                f"exit={exit_code}",
                f"signal={signal_number}",
            ],
        )

    @staticmethod
    def test_mypy_cache_directory_is_project_keyed_and_survives_relocks(
        tmp_path: Path,
    ) -> None:
        """One shared Mypy cache per project, reused by every checkout and relock."""
        spec = config.Infra.codegen.make.mypy_cache

        def checkout(name: str, project: str) -> Path:
            root = tmp_path / name
            root.mkdir()
            (root / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname = '{project}'\nversion = '0.0.0'\n",
                encoding="utf-8",
            )
            return root

        lane = checkout("lane", "fixture-alpha")
        primary = checkout("primary", "fixture-alpha")
        other = checkout("other", "fixture-beta")
        shared = u.Infra.mypy_cache_directory(lane)
        # Every checkout of one project reuses one analysis.
        tm.that(u.Infra.mypy_cache_directory(primary), eq=shared)
        tm.that(
            shared.is_relative_to(u.Infra.external_cache_directory(spec)),
            eq=True,
        )
        # A relock keeps the directory: Mypy revalidates changed modules itself.
        (lane / c.Infra.UV_LOCK_FILENAME).write_text("rotated\n", encoding="utf-8")
        tm.that(u.Infra.mypy_cache_directory(lane), eq=shared)
        # Distinct projects never share one tests package namespace.
        tm.ok(u.Infra.mypy_cache_directory(other) != shared)
