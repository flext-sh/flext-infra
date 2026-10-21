"""Observable public profiling contract for the cached-pytest runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import pstats
import signal
import sys
from pathlib import Path

import pytest

from flext_infra import config, validate
from tests import c, m, t, tm, u


class TestsFlextInfraPytestProfile:
    """Exercise the real profiling child transport and its receipt binding."""

    @staticmethod
    @pytest.mark.parametrize("handler", ["default", "raise", "return"])
    @pytest.mark.parametrize("event", ["tempfile.mkstemp", "marshal.dumps"])
    def test_sigterm_during_publication_never_reenters_snapshot(
        tmp_path: Path, handler: str, event: str
    ) -> None:
        """A real synchronous signal delegates without another staging or snapshot."""
        output = tmp_path / "current.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import os, pstats, signal\n"
            "output = Path(sys.argv[1])\n"
            "sum(range(10))\n"
            "clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "before = output.read_bytes()\n"
            "profile.enable()\n"
            "stages = []\n"
            "snapshots = []\n"
            "def observe(frame, name, argument):\n"
            "    if (name == 'c_call'\n"
            "            and getattr(argument, '__name__', '') == 'getstats'):\n"
            "        snapshots.append(name)\n"
            "def native(signum, frame):\n"
            "    print('native-handler', flush=True)\n"
            + (
                "    raise RuntimeError('first native signal failure')\n"
                if handler == "raise"
                else "    return\n"
            )
            + (
                "signal.signal(signal.SIGTERM, native)\n"
                if handler != "default"
                else ""
            )
            + "clock.FlextInfraPytestClock.register_signal_checkpoint(\n"
            "    profile, output)\n"
            "def interrupt(name, arguments):\n"
            "    if name == 'tempfile.mkstemp':\n"
            "        stages.append(name)\n"
            f"    if name == {event!r}:\n"
            "        os.kill(os.getpid(), signal.SIGTERM)\n"
            "sys.addaudithook(interrupt)\n"
            "sys.setprofile(observe)\n"
            "try:\n"
            "    clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "except RuntimeError as failure:\n"
            "    assert str(failure) == 'first native signal failure'\n"
            "    assert output.read_bytes() == before\n"
            "else:\n"
            "    assert pstats.Stats(str(output)).get_stats_profile().func_profiles\n"
            "finally:\n"
            "    sys.setprofile(None)\n"
            "assert len(stages) == 1, stages\n"
            "assert len(snapshots) == "
            f"{int(event == 'marshal.dumps' or handler == 'return')}, snapshots\n"
            "assert not tuple(output.parent.glob('.current.pstats.*.tmp'))\n"
        )
        result = tm.ok(
            u.Cli.run_raw((sys.executable, "-c", script, str(output)), cwd=tmp_path)
        )
        tm.that(
            result.outcome.raw_return_code,
            eq=-signal.SIGTERM if handler == "default" else 0,
            msg=result.stdout + result.stderr,
        )
        tm.fail(result.outcome.timed_out)
        if handler != "default":
            tm.that(result.stdout.count("native-handler"), eq=1)

    @staticmethod
    def test_interrupted_publication_preserves_the_previous_readable_profile(
        tmp_path: Path,
    ) -> None:
        """A real SIGINT during serialization cannot truncate an earlier profile."""
        output = tmp_path / "checkpoint.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import os, signal, sys, pstats\n"
            "output = Path(sys.argv[1])\n"
            "sum(range(10))\n"
            "clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "before = output.read_bytes()\n"
            "before_modified = output.stat().st_mtime_ns\n"
            "def interrupt(event, arguments):\n"
            "    if event == 'marshal.dumps':\n"
            "        assert output.read_bytes() == before\n"
            "        os.kill(os.getpid(), signal.SIGINT)\n"
            "sys.addaudithook(interrupt)\n"
            "try:\n"
            "    clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "except KeyboardInterrupt:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('native SIGINT did not escape publication')\n"
            "assert output.read_bytes() == before\n"
            "assert output.stat().st_mtime_ns == before_modified\n"
            "assert pstats.Stats(str(output)).get_stats_profile().func_profiles\n"
        )
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script, str(output)),
                cwd=tmp_path,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )

    @staticmethod
    def test_startup_transfers_finalization_to_launcher(tmp_path: Path) -> None:
        """Startup and launcher share one profiler and publish the elected output."""
        output = tmp_path / "suite.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import atexit, os, pstats\n"
            "stages = []\n"
            "def observe(name, arguments):\n"
            "    if name == 'tempfile.mkstemp':\n"
            "        stages.append(arguments[0])\n"
            "sys.addaudithook(observe)\n"
            "def finished():\n"
            "    assert len(stages) == 1, stages\n"
            "    assert pstats.Stats(sys.argv[0]).get_stats_profile().func_profiles\n"
            "    print('single-finalization', flush=True)\n"
            "atexit.register(finished)\n"
            "os.environ[child.FlextInfraPytestProfileChild.CHILD_ROOT_ENV] = (\n"
            "    sys.argv[2])\n"
            "child.FlextInfraPytestProfileChild.startup(\n"
            "    sys.argv[2] + '/sitecustomize.py')\n"
            "assert child.FlextInfraPytestProfileChild.bootstrap()[1] is profile\n"
            "sys.argv = [sys.argv[1], sys.argv[1], '--version']\n"
            + c.Infra.PYTEST_PROFILE_LAUNCHER
        )
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script, str(output), str(tmp_path)),
                cwd=tmp_path,
            )
        )
        tm.ok(u.Cli.process_succeeded(result.outcome), msg=result.stderr)
        tm.that(result.stdout, has="single-finalization")
        tm.that(tuple(tmp_path.glob("*.pstats")), eq=(output,))

    @staticmethod
    @pytest.mark.parametrize("cause", ["exception", "exit", "success"])
    def test_launcher_publication_failure_preserves_first_cause(
        tmp_path: Path, cause: str
    ) -> None:
        """A failed final artifact cannot hide a native failure or accept success."""
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "def fail_pytest(name, arguments):\n"
            "    if (name == 'exec'\n"
            "            and arguments[0].co_filename.endswith('/pytest/__main__.py')):\n"
            + (
                "        raise RuntimeError('original pytest failure')\n"
                if cause == "exception"
                else f"        raise SystemExit({7 if cause == 'exit' else 0})\n"
            )
            + "sys.addaudithook(fail_pytest)\n"
            + c.Infra.PYTEST_PROFILE_LAUNCHER
        )
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    script,
                    str(tmp_path / "missing" / "suite.pstats"),
                ),
                cwd=tmp_path,
            )
        )
        tm.that(result.outcome.raw_return_code, eq=7 if cause == "exit" else 1)
        tm.fail(result.outcome.timed_out)
        tm.that(result.stderr, has="FileNotFoundError")
        if cause == "exception":
            tm.that(result.stderr, has="RuntimeError: original pytest failure")
            tm.that(result.stderr, has="profile publication failed")

    @staticmethod
    def test_immutable_profile_is_linked_before_public_replacement(
        tmp_path: Path,
    ) -> None:
        """The invocation-owned inode exists before the shared name is replaced."""
        output = tmp_path / "shared.pstats"
        immutable = tmp_path / "owned.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import os, pstats\n"
            "output, immutable = map(Path, sys.argv[1:])\n"
            "def interleave(event, arguments):\n"
            "    if event == 'os.rename' and str(arguments[1]) == str(output):\n"
            "        assert immutable.samefile(Path(arguments[0]))\n"
            "        output.write_bytes(b'another publisher')\n"
            "sys.addaudithook(interleave)\n"
            "clock.FlextInfraPytestClock.publish_profile(\n"
            "    profile, output, immutable_output=immutable)\n"
            "assert immutable.samefile(output)\n"
            "assert pstats.Stats(str(immutable)).get_stats_profile().func_profiles\n"
        )
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script, str(output), str(immutable)),
                cwd=tmp_path,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )

    @staticmethod
    @pytest.mark.parametrize("interruption", ["signal", "timeout"])
    def test_native_termination_keeps_a_readable_profile_checkpoint(
        tmp_path: Path,
        interruption: str,
    ) -> None:
        """Preserve native SIGTERM and timeout outcomes alongside measured progress."""
        deadline = config.Infra.tooling.tools.pytest.termination_grace_seconds
        probe = tmp_path / "termination_probe.py"
        action = (
            "os.kill(os.getpid(), signal.SIGTERM)"
            if interruption == "signal"
            else f"time.sleep({deadline * 2!r})"
        )
        probe.write_text(
            "import os\nimport signal\nimport time\n"
            "def interrupt_import():\n"
            f"    {action}\n"
            "interrupt_import()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        output = tmp_path / "terminated.pstats"
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    c.Infra.PYTEST_PROFILE_LAUNCHER,
                    str(output),
                    "-p",
                    probe.stem,
                    "--collect-only",
                ),
                cwd=tmp_path,
                timeout=deadline,
            ),
        )
        tm.that(result.outcome.raw_return_code, eq=-signal.SIGTERM)
        tm.that(result.outcome.timed_out, eq=interruption == "timeout")
        tm.that(result.outcome.forwarded_signal, eq=None)
        measured = pstats.Stats(str(output)).get_stats_profile().func_profiles
        tm.that(
            any(Path(function.file_name) == probe for function in measured.values()),
            eq=True,
        )

    @staticmethod
    @pytest.mark.slow
    def test_native_profiler_owns_workload_after_startup_handoff(
        cached_runner_project: Path,
    ) -> None:
        """Native cProfile and automatic startup publish distinct real segments."""
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        workload = cached_runner_project / "native_profile_workload.py"
        workload.write_text(
            "import os\n"
            "def workload():\n    return sum(range(4))\n"
            "if __name__ == '__main__':\n"
            "    print(os.getpid())\n    print(workload())\n",
            encoding=c.DEFAULT_ENCODING,
        )
        native = cached_runner_project / "native-workload.pstats"
        target = Path(cache.target_directory) / "test_runtime.py"
        (cached_runner_project / target).write_text(
            "import os, pstats, subprocess, sys\n"
            "from pathlib import Path\n"
            "import pytest\n"
            f"@pytest.mark.{policy.slow_marker}\n"
            "def test_runtime():\n"
            f"    root = Path({str(cached_runner_project)!r})\n"
            "    completed = subprocess.run((sys.executable, '-m', 'cProfile', "
            f"'-o', {str(native)!r}, {str(workload)!r}), "
            "cwd=root, capture_output=True, text=True)\n"
            "    assert completed.returncode == 0, completed.stderr\n"
            "    native_pid, value = completed.stdout.splitlines()\n"
            "    assert value == '6'\n"
            f"    assert 'workload' in pstats.Stats({str(native)!r})"
            ".get_stats_profile().func_profiles\n"
            "    malformed = subprocess.run((sys.executable, '-m', 'cProfile', "
            "'--flext-invalid-profile-option'), cwd=root, capture_output=True)\n"
            "    assert malformed.returncode == 2\n"
            "    ordinary = subprocess.run((sys.executable, '-m', "
            "'native_profile_workload', '-m', 'cProfile'), cwd=root, "
            "capture_output=True, text=True)\n"
            "    assert ordinary.returncode == 0, ordinary.stderr\n"
            "    ordinary_pid, value = ordinary.stdout.splitlines()\n"
            "    assert value == '6'\n"
            "    children = Path(os.environ["
            f"{c.Infra.PYTEST_PROFILE_CHILD_ROOT_ENV!r}])\n"
            "    startup = children / f'{native_pid}.pstats'\n"
            "    assert pstats.Stats(str(startup)).get_stats_profile().func_profiles\n"
            "    automatic = children / f'{ordinary_pid}.pstats'\n"
            "    assert 'workload' in pstats.Stats(str(automatic))"
            ".get_stats_profile().func_profiles\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project,
            target_file=target,
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / policy.profile_suite_filename
        )
        tm.that(
            u.Tests.PytestRunner.profile_parent(runner, output), eq=pytest.ExitCode.OK
        )
        tm.that(
            "workload" in pstats.Stats(str(native)).get_stats_profile().func_profiles,
            eq=True,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("termination_signal", [signal.SIGKILL, signal.SIGTERM])
    def test_interrupted_profile_preserves_the_child_process_failure(
        cached_runner_project: Path,
        termination_signal: int,
    ) -> None:
        """A killed real child keeps its signal instead of a missing-profile error."""
        cache = config.Infra.codegen.make.testmon_cache
        target = Path(cache.target_directory) / "test_runtime.py"
        (cached_runner_project / target).write_text(
            "import os\n"
            "import signal\n"
            "def test_runtime():\n"
            f"    os.kill(os.getpid(), {termination_signal:d})\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        ).model_copy(update={"profile_enabled": True})
        tm.that(tm.ok(runner.execute()), eq=-termination_signal)
        reports = cached_runner_project / runner.reports
        contexts = tuple(reports.glob("*/run-context.json"))
        tm.that(len(contexts), eq=1)
        directory = contexts[0].parent
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / "suite-outcome.json").read_text(encoding=c.DEFAULT_ENCODING)
        )
        tm.that(outcome.raw_return_code, eq=-termination_signal)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, eq=None)
        profile = directory / config.Infra.tooling.tools.pytest.profile_suite_filename
        tm.that(profile.exists(), eq=termination_signal == signal.SIGTERM)
        tm.fail((directory / "run-accounting.json").exists())
        if termination_signal == signal.SIGTERM:
            policy = config.Infra.tooling.tools.pytest
            receipt = profile.with_suffix(".pstats.json")
            recorded = m.Infra.PytestRunContext.model_validate_json(
                receipt.read_text(encoding=c.DEFAULT_ENCODING)
            )
            tm.that(
                recorded.profile_sha256, eq=u.Cli.sha256_bytes(profile.read_bytes())
            )
            output = directory / "interrupted-profile.txt"
            tm.that(
                tm.ok(
                    validate.FlextInfraCProfileReport(
                        repository_root=cached_runner_project,
                        profile=profile,
                        run_receipt=receipt,
                        output=output,
                        sort=policy.profile_sort,
                        limit=policy.profile_limit,
                    ).execute()
                ),
                eq=True,
            )
            tm.that(output.read_text(encoding=c.DEFAULT_ENCODING), has="test_runtime")

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("phase", ["between_children", "suite"])
    def test_parent_sigterm_publishes_bound_receipts_and_reaps_child(
        cached_runner_project: Path,
        phase: str,
    ) -> None:
        """Parent termination retains reportable evidence and native child cleanup."""
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        target = Path(cache.target_directory) / "test_runtime.py"
        child_pid = cached_runner_project / "interrupted-child.pid"
        (cached_runner_project / target).write_text(
            "import os, signal\nfrom pathlib import Path\n"
            "def test_runtime():\n"
            f"    Path({str(child_pid)!r}).write_text(str(os.getpid()))\n"
            "    os.kill(int(os.environ['PROFILE_PARENT_PID']), signal.SIGTERM)\n"
            "    signal.pause()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / policy.profile_suite_filename
        )
        script = (
            "import os, runpy, signal, sys\n"
            # This probe measures interruption, not cold framework import;
            # the startup handoff has its own public profiling regression.
            "from flext_infra import FlextInfraPytestProfile\n"
            + c.Infra.PYTEST_PROFILE_BOOTSTRAP
            + "os.environ['PROFILE_PARENT_PID'] = str(os.getpid())\n"
            "sys.argv = ['flext_infra._pytest_entry', 'profile', sys.argv[1]]\n"
            "def interrupt(event, arguments):\n"
            "    if event == 'os.rename' and "
            "str(arguments[1]).endswith('/command.txt'):\n"
            "        os.kill(os.getpid(), signal.SIGTERM)\n"
            + ("sys.addaudithook(interrupt)\n" if phase == "between_children" else "")
            + "runpy.run_module('flext_infra._pytest_entry', run_name='__main__')\n"
        )
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script, str(output)),
                cwd=cached_runner_project,
                timeout=policy.slow_timeout_seconds,
                options=m.Cli.ProcessOptions(
                    env=u.Cli.process_env(
                        overrides={
                            c.Infra.PYTEST_ENV_REPOSITORY_ROOT: str(
                                runner.repository_root
                            ),
                            c.Infra.PYTEST_ENV_TARGET: str(runner.target),
                            c.Infra.PYTEST_ENV_TARGET_FILE: str(target),
                            c.Infra.PYTEST_ENV_REPORTS: str(runner.reports),
                            cache.database_environment_variable: str(runner.testmon_db),
                        },
                    ),
                ),
            ),
        )
        tm.that(
            result.outcome.timed_out,
            eq=False,
            msg=result.stdout + result.stderr,
        )
        tm.that(
            result.outcome.raw_return_code,
            eq=128 + signal.SIGTERM
            if phase == "between_children"
            else (-signal.SIGTERM) % 256,
        )
        receipt = output.with_suffix(".pstats.json")
        context = m.Infra.PytestRunContext.model_validate_json(receipt.read_bytes())
        tm.that(context.profile_sha256, eq=u.Cli.sha256_bytes(output.read_bytes()))
        tm.that(pstats.Stats(str(output)).get_stats_profile().func_profiles, truth=True)
        contexts = tuple(
            (cached_runner_project / runner.reports).glob("*/run-context.json")
        )
        tm.that(len(contexts), eq=1)
        tm.that(context.report_directory, eq=contexts[0].parent)
        processes = output.parent / policy.profile_process_directory
        immutable = tuple(processes.glob("*.pstats"))
        tm.that(len(immutable), eq=1)
        tm.that(
            immutable[0].with_suffix(".pstats.json").read_bytes(),
            eq=receipt.read_bytes(),
        )
        if phase == "suite":
            with pytest.raises(ProcessLookupError):
                os.kill(int(child_pid.read_text(encoding=c.DEFAULT_ENCODING)), 0)
            tm.ok(
                validate.FlextInfraCProfileReport(
                    repository_root=cached_runner_project,
                    profile=output,
                    run_receipt=receipt,
                    output=output.with_suffix(".txt"),
                    sort=policy.profile_sort,
                    limit=policy.profile_limit,
                ).execute()
            )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("publication_error", ["receipt", "context", "stderr"])
    def test_parent_publication_error_preserves_the_child_failure(
        cached_runner_project: Path,
        publication_error: str,
    ) -> None:
        """A real receipt write error cannot replace a killed suite's exit code."""
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        target = Path(cache.target_directory) / "test_runtime.py"
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / policy.profile_suite_filename
        )
        damage = (
            "    (Path(os.environ["
            f"{c.Infra.PYTEST_PROFILE_CHILD_ROOT_ENV!r}]).parent / 'run-context.json')"
            ".write_text('{')\n"
            if publication_error == "context"
            else f"    Path({str(output.with_suffix('.pstats.json'))!r}).mkdir()\n"
        )
        (cached_runner_project / target).write_text(
            "import os, signal\nfrom pathlib import Path\n"
            "def test_runtime():\n"
            + damage
            + "    os.kill(os.getpid(), signal.SIGKILL)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        script = (
            "import os, runpy, sys\n"
            "from flext_infra import FlextInfraPytestProfile\n"
            + c.Infra.PYTEST_PROFILE_BOOTSTRAP
            + "sys.argv = ['flext_infra._pytest_entry', 'profile', sys.argv[1]]\n"
            "def close_diagnostic(event, arguments):\n"
            "    if event == 'os.rename' and str(arguments[1]) == "
            f"{str(output.with_suffix('.pstats.json'))!r}:\n"
            "        sys.stderr.close()\n"
            + (
                "sys.addaudithook(close_diagnostic)\n"
                if publication_error == "stderr"
                else ""
            )
            + "runpy.run_module('flext_infra._pytest_entry', run_name='__main__')\n"
        )
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    script,
                    str(output),
                ),
                cwd=cached_runner_project,
                timeout=policy.slow_timeout_seconds,
                options=m.Cli.ProcessOptions(
                    env=u.Cli.process_env(
                        overrides={
                            c.Infra.PYTEST_ENV_REPOSITORY_ROOT: str(
                                runner.repository_root
                            ),
                            c.Infra.PYTEST_ENV_TARGET: str(runner.target),
                            c.Infra.PYTEST_ENV_TARGET_FILE: str(target),
                            c.Infra.PYTEST_ENV_REPORTS: str(runner.reports),
                            cache.database_environment_variable: str(runner.testmon_db),
                        },
                    ),
                ),
            ),
        )
        tm.that(
            result.outcome.timed_out,
            eq=False,
            msg=result.stdout + result.stderr,
        )
        tm.that(result.outcome.raw_return_code, eq=(-signal.SIGKILL) % 256)
        tm.ok(output.is_file())
        tm.that(
            bool(pstats.Stats(str(output)).get_stats_profile().func_profiles),
            eq=True,
        )
        if publication_error != "stderr":
            tm.that(
                result.stderr, has=[f"raw_return_code={-signal.SIGKILL}", "Traceback"]
            )
        if publication_error == "context":
            tm.fail(output.with_suffix(".pstats.json").exists())
        processes = output.parent / policy.profile_process_directory
        tm.that(
            len(tuple(processes.glob("*.pstats.json"))),
            eq=0 if publication_error == "context" else 1,
        )

    @staticmethod
    @pytest.mark.slow
    def test_focused_profile_keeps_one_run_and_excludes_other_files(
        cached_runner_project: Path,
    ) -> None:
        """The fresh entry profiles one declared file on the persistent database."""
        cache = config.Infra.codegen.make.testmon_cache
        target = Path(cache.target_directory) / "test_runtime.py"
        unselected = (
            cached_runner_project / cache.target_directory / "test_unselected.py"
        )
        unselected.write_text(
            "def test_unselected():\n    raise RuntimeError('unselected file ran')\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / config.Infra.tooling.tools.pytest.profile_suite_filename
        )
        tm.that(
            u.Tests.PytestRunner.profile_parent(runner, output), eq=pytest.ExitCode.OK
        )
        contexts = list(
            (cached_runner_project / runner.reports).glob("*/run-context.json"),
        )
        tm.that(len(contexts), eq=1)
        context = m.Infra.PytestRunContext.model_validate_json(
            contexts[0].read_text(encoding="utf-8"),
        )
        tm.that(context.testmon_db, eq=runner.testmon_db)
        tm.ok(context.deadline_monotonic is not None)
        command = (contexts[0].parent / "command.txt").read_text(encoding="utf-8")
        tm.that(command, has=str(target))
        tm.that(command, lacks="test_unselected.py")
        tm.ok(runner.testmon_db.is_file())
        stats = pstats.Stats(str(output)).get_stats_profile().func_profiles
        tm.ok(validate.FlextInfraPytestRunner.__name__ in stats)
        tm.ok("FlextInfraPytestProfile" in stats)
        processes = (
            output.parent / config.Infra.tooling.tools.pytest.profile_process_directory
        )
        immutable_profiles = tuple(processes.glob("*.pstats"))
        tm.that(len(immutable_profiles), eq=1)
        immutable = immutable_profiles[0]
        receipt = immutable.with_suffix(".pstats.json").read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            receipt,
            eq=output.with_suffix(".pstats.json").read_text(
                encoding=c.DEFAULT_ENCODING
            ),
        )
        # Replacing the public destination must leave the per-process evidence intact.
        replacement = output.with_suffix(".replacement")
        replacement.write_bytes(b"a later invocation")
        replacement.replace(output)
        bound = m.Infra.PytestRunContext.model_validate_json(receipt)
        tm.that(bound.report_directory, eq=context.report_directory)
        tm.that(bound.profile_sha256, eq=u.Cli.sha256_bytes(immutable.read_bytes()))

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("target_file", [Path("../outside.py"), Path("missing.py")])
    def test_profile_entry_rejects_invalid_focused_targets(
        cached_runner_project: Path,
        target_file: Path,
    ) -> None:
        """Invalid input fails through the real entry before publishing a run."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / config.Infra.tooling.tools.pytest.profile_suite_filename
        )
        with pytest.raises(RuntimeError, match=r"target_file|test target file"):
            u.Tests.PytestRunner.profile_parent(runner, output, target_file=target_file)
        tm.that(
            list((cached_runner_project / runner.reports).glob("*/run-context.json")),
            eq=[],
        )

    @staticmethod
    @pytest.mark.slow
    def test_pytester_children_profile_startup_and_preserve_native_exits(
        cached_runner_project: Path,
    ) -> None:
        """Real pytester children retain imports, site customization and exits."""
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        customization = (
            cached_runner_project / c.Infra.DEFAULT_SRC_DIR / "sitecustomize.py"
        )
        customization.write_text(
            "class ProfiledSiteCustomization:\n    pass\n",
            encoding="utf-8",
        )
        target = Path(cache.target_directory) / "test_runtime.py"
        (cached_runner_project / target).write_text(
            "import pytest\n"
            "pytest_plugins = ['pytester']\n"
            f"@pytest.mark.{policy.slow_marker}\n"
            "def test_runtime(pytester):\n"
            "    result = pytester.runpytest_subprocess('--version')\n"
            "    assert result.ret == pytest.ExitCode.OK\n"
            "    result = pytester.runpytest_subprocess('--invalid-profile-probe')\n"
            "    assert result.ret == pytest.ExitCode.USAGE_ERROR\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / policy.profile_suite_filename
        )
        tm.that(
            u.Tests.PytestRunner.profile_parent(runner, output), eq=pytest.ExitCode.OK
        )
        receipt = m.Infra.PytestRunContext.model_validate_json(
            output.with_suffix(".pstats.json").read_text(encoding="utf-8"),
        )
        directory = receipt.report_directory
        if directory is None:
            pytest.fail("profile did not bind its run directory")
        processes = directory / policy.profile_process_directory
        profiles = list(processes.glob("*.pstats"))
        tm.ok(len(profiles) >= 2)
        for child in profiles:
            functions = pstats.Stats(str(child)).get_stats_profile().func_profiles
            startup_functions = tuple(
                (name, function.file_name)
                for name, function in functions.items()
                if function.file_name.endswith("sitecustomize.py")
            )
            tm.that(
                "ProfiledSiteCustomization" in functions,
                eq=True,
                msg=f"site customization absent from {child}: {startup_functions}",
            )
            tm.that(
                any("_pytest" in function.file_name for function in functions.values()),
                eq=True,
            )
        report = validate.FlextInfraCProfileReport(
            repository_root=cached_runner_project,
            profile=output,
            output=output.with_suffix(".txt"),
            run_receipt=output.with_suffix(".pstats.json"),
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )
        tm.ok(report.execute())
        text = report.output.read_text(encoding="utf-8")
        for child in profiles:
            tm.that(text, has=str(child))
        child = profiles[0]
        child.write_bytes(child.read_bytes() + b"changed")
        tm.ok(report.execute().failure)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("arguments", "expected_exit"),
        [
            (("--version",), pytest.ExitCode.OK),
            (("--flext-invalid-profile-option",), pytest.ExitCode.USAGE_ERROR),
        ],
    )
    def test_profile_child_preserves_exit_status_and_arguments(
        tmp_path: Path,
        arguments: t.StrTuple,
        expected_exit: int,
    ) -> None:
        """The real pytest module exits natively and leaves its raw profile."""
        profile = tmp_path / "collection.pstats"
        result = u.Tests.PytestRunner.profile_collection(profile, arguments)
        tm.that(result.outcome.raw_return_code == expected_exit, truth=True)
        tm.that(result.outcome.timed_out, truth=False)
        tm.that(result.outcome.forwarded_signal, none=True)
        if expected_exit == pytest.ExitCode.USAGE_ERROR:
            tm.that(arguments[0] in result.stderr, truth=True)
        tm.that(
            pstats.Stats(str(profile)).get_stats_profile().func_profiles, truth=True
        )

    @staticmethod
    @pytest.mark.slow
    def test_profile_failure_exposes_the_write_error(tmp_path: Path) -> None:
        """A real profile I/O failure remains visible rather than becoming success."""
        output = tmp_path / "collection.pstats"
        output.mkdir()
        result = u.Tests.PytestRunner.profile_collection(output, ("--version",))
        tm.that(result.outcome.raw_return_code != 0, truth=True)
        tm.that(result.outcome.timed_out, truth=False)
        tm.that(result.outcome.forwarded_signal, none=True)
        tm.that("IsADirectoryError" in result.stderr, truth=True)

    @staticmethod
    @pytest.mark.parametrize("complete", [False, True])
    def test_collection_profile_preserves_pytest_arguments(
        cached_runner_project: Path,
        *,
        complete: bool,
    ) -> None:
        """Only the interpreter prefix changes; suite execution is not profiled."""
        plain = u.Tests.PytestRunner.runner_for(cached_runner_project)
        profiled = u.Tests.PytestRunner.runner_for(
            cached_runner_project, profile_collection=True
        )
        report = cached_runner_project / plain.reports
        manifest = report / "collection.json"
        plain_command = plain.build_selection_command(
            report_log=report / "collection.jsonl",
            manifest_path=manifest,
            complete=complete,
        )
        profiled_command = profiled.build_selection_command(
            report_log=report / "collection.jsonl",
            manifest_path=manifest,
            complete=complete,
        )
        tm.that(
            profiled_command
            == (
                *profiled.collection_command_prefix,
                str(manifest.with_suffix(".pstats")),
                *plain_command[3:],
            ),
            truth=True,
        )
        tm.that(
            c.Infra.PYTEST_PROFILE_LAUNCHER not in profiled.build_command(report),
            truth=True,
        )

    @staticmethod
    def _assert_parent_profile_evidence(
        project: Path,
        reports_root: Path,
        latest_name: str,
    ) -> None:
        """Prove the parent profiler captured the public runner import.

        The profiled run's parent profile names pytest internals and the
        runner class, its report pairs only this run, and every tampered
        receipt input fails the report loudly.

        """
        parent_profile = project / ".reports" / "profiles" / "pytest.pstats"
        profile = reports_root / latest_name / "testmon-selection.pstats"
        stats = pstats.Stats(str(profile))
        directory = reports_root / latest_name
        policy = config.Infra.tooling.tools.pytest
        suite = pstats.Stats(
            *(
                str(path)
                for path in (
                    directory / policy.profile_suite_filename,
                    *sorted(
                        (directory / policy.profile_process_directory).glob("*.pstats")
                    ),
                )
            )
        ).get_stats_profile()
        tm.that(
            any(
                name == "test_runtime"
                and Path(function.file_name)
                == project
                / config.Infra.codegen.make.testmon_cache.target_directory
                / "test_runtime.py"
                for name, function in suite.func_profiles.items()
            ),
            eq=True,
        )
        tm.that(
            any(
                "_pytest" in function.file_name
                for function in stats.get_stats_profile().func_profiles.values()
            ),
            truth=True,
        )
        parent_stats = pstats.Stats(str(parent_profile)).get_stats_profile()
        # The class body runs on import, unlike its methods: this proves the
        # public runner was first imported while the parent profiler was active.
        tm.that(
            validate.FlextInfraPytestRunner.__name__ in parent_stats.func_profiles,
            truth=True,
        )
        report = validate.FlextInfraCProfileReport(
            repository_root=project,
            profile=parent_profile,
            output=parent_profile.with_suffix(".txt"),
            run_receipt=parent_profile.with_suffix(".pstats.json"),
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )
        # An unrelated latest pointer must never pair this parent with another run.
        latest = reports_root / "latest.txt"
        latest.write_text("unrelated-run\n", encoding="utf-8")
        tm.ok(report.execute())
        latest.write_text(latest_name + "\n", encoding="utf-8")
        text = report.output.read_text(encoding="utf-8")
        tm.that(str(parent_profile) in text, truth=True)
        tm.that(str(profile) in text, truth=True)
        receipt_path = profile.with_suffix(".pstats.json")
        original = receipt_path.read_text(encoding="utf-8")
        receipt = m.Infra.PytestRunContext.model_validate_json(original)
        # The profiled incremental operation is bounded, so its receipt names
        # a deadline.
        deadline = receipt.deadline_monotonic
        if deadline is None:
            pytest.fail("bounded selection receipt did not record its deadline")
        receipt_path.write_text(
            receipt.model_copy(
                update={"deadline_monotonic": deadline + 1},
            ).model_dump_json(),
            encoding="utf-8",
        )
        tm.that(report.execute().failure, truth=True)
        receipt_path.write_text("{", encoding="utf-8")
        tm.that(report.execute().failure, truth=True)
        receipt_path.unlink()
        tm.that(report.execute().failure, truth=True)
        receipt_path.write_text(original, encoding="utf-8")
        parent_profile.write_bytes(parent_profile.read_bytes() + b"stale")
        tm.that(report.execute().failure, truth=True)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("profile_collection", [False, True])
    def test_complete_suite_persists_cache_and_zero_diagnostic_evidence(
        cached_runner_project: Path,
        *,
        profile_collection: bool,
    ) -> None:
        """One public execution collects every test and publishes real evidence.

        The profiled run loads ``flext_infra`` as a plugin package, as consumer
        projects do: a child that imported it before pytest makes pytest warn
        that it cannot rewrite it, and the collection gate rejects warnings.
        """
        cache = config.Infra.codegen.make.testmon_cache
        if profile_collection:
            pyproject = cached_runner_project / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding="utf-8") + 'addopts = "-p flext_infra"\n',
                encoding="utf-8",
            )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project,
            profile_collection=profile_collection,
        )
        testmon_db = runner.testmon_db

        parent_profile = (
            cached_runner_project / ".reports" / "profiles" / "pytest.pstats"
        )
        exit_code = (
            u.Tests.PytestRunner.profile_parent(runner, parent_profile)
            if profile_collection
            else tm.ok(runner.execute())
        )

        tm.that(exit_code, eq=0)
        tm.ok(testmon_db.is_file())
        tm.fail(testmon_db.is_relative_to(cached_runner_project))
        tm.fail((cached_runner_project / cache.database_filename).exists())
        reports_root = cached_runner_project / cache.reports_directory
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        profile = reports_root / latest_name / "testmon-selection.pstats"
        tm.that(profile.is_file() == profile_collection, truth=True)
        if profile_collection:
            TestsFlextInfraPytestProfile._assert_parent_profile_evidence(
                cached_runner_project,
                reports_root,
                latest_name,
            )
        tm.that(
            (reports_root / latest_name / "testmon-inventory.pstats").exists(),
            truth=False,
        )
        summary = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "summary.txt"),
        )
        tm.that(
            summary,
            has=[
                "executed=1",
                "failed=0",
                "errors=0",
                "warnings=0",
                "skipped=0",
                "exit=0",
            ],
        )
        tm.ok((reports_root / latest_name / "junit.xml").is_file())
        # The testmon verb owns no coverage plugin (testmon 2.x refuses branch
        # coverage through the cov plugin), so its command carries --no-cov and
        # the coverage artifact belongs to the coverage verb alone.
        selection = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "testmon-selection.txt"),
        )
        command = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "command.txt"),
        )
        # Selection runs once before workers record dependencies; the collection
        # plugin enforces exactly the selected node ids in the recorded order.
        tm.that(selection.splitlines(), has="tests/test_runtime.py::test_runtime")
        tm.that(command, has=c.Infra.PYTEST_SELECTED_COLLECTION_OPTION)
        tm.that(command, has="--no-cov")
        tm.that(command, has="--testmon --testmon-noselect")
        tm.fail((reports_root / latest_name / "coverage.xml").is_file())
        # A cold run has no database to inspect before pytest; its only cache
        # receipt is the post-run seed decision.
        tm.fail((reports_root / latest_name / "cache-before.json").exists())
        seeded = m.Infra.TestmonCacheState.model_validate_json(
            tm.ok(
                u.Cli.files_read_text(reports_root / latest_name / "cache-after.json"),
            ),
        )
        tm.ok(seeded.seed_needed)
        tm.ok(seeded.saveable)
