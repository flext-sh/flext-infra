"""A suite whose process cleanup failed still publishes its outcome.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ctypes
import os
import signal
import sys
import time
from pathlib import Path

from flext_infra import config
from tests import c, m, t, tm, u


class TestsFlextInfraPytestRunnerCleanupOutcome:
    """The runner records the process owner's outcome of a failed cleanup."""

    @staticmethod
    @c.Tests.MARK.slow
    @c.Tests.MARK.skipif(sys.platform != "linux", reason="prctl child subreaper")
    def test_timed_out_suite_with_an_unreaped_member_keeps_its_receipt(
        cached_runner_project: Path,
        capfd: t.Tests.CaptureFixture[str],
    ) -> None:
        """A suite whose cleanup leaves a member behind still records its outcome.

        The test leaves a same-group child that ignores the soft signals, and
        the suite clock is nearly spent, so the deadline kills the suite.
        While this process is the child subreaper and does not wait, the
        orphan stays a zombie member: the process owner fails the run with
        the timeout in ``error_data``, and the runner records that outcome as
        a timed-out suite instead of crashing without ``suite-outcome.json``.
        """
        cache = config.Infra.codegen.make.testmon_cache
        pid_file = cached_runner_project.parent / "orphan.pid"
        (cached_runner_project / cache.target_directory / "test_orphan.py").write_text(
            "import signal, subprocess, sys, time\n\n"
            "def test_orphan() -> None:\n"
            "    signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
            "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "    child = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
            "signal.signal(signal.SIGINT,signal.SIG_IGN);time.sleep(60)'])\n"
            f"    open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
            "    time.sleep(60)\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        policy = runner.pytest_policy()
        runner = runner.model_copy(
            update={
                "started_at_monotonic": time.monotonic()
                - (policy.run_timeout_seconds - policy.termination_grace_seconds - 10),
            },
        )
        prctl = ctypes.CDLL(None, use_errno=True).prctl
        set_child_subreaper, get_child_subreaper = 36, 37
        previous = ctypes.c_int(0)
        tm.that(prctl(get_child_subreaper, ctypes.byref(previous), 0, 0, 0), eq=0)
        tm.that(prctl(set_child_subreaper, 1, 0, 0, 0), eq=0)
        try:
            exit_code = tm.ok(runner.execute())
        finally:
            tm.that(prctl(set_child_subreaper, previous.value, 0, 0, 0), eq=0)
            if pid_file.is_file():
                os.waitpid(int(pid_file.read_text(encoding="utf-8")), 0)

        tm.that(exit_code, ne=0)
        reports_root = cached_runner_project / cache.reports_directory
        (receipt,) = reports_root.glob("*/suite-outcome.json")
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            tm.ok(u.Cli.files_read_text(receipt)),
        )
        tm.ok(outcome.timed_out)
        tm.that(outcome.raw_return_code, eq=-signal.SIGKILL)
        tm.that(
            capfd.readouterr().err,
            has="pytest suite process cleanup: owned process boundary was not empty",
        )
