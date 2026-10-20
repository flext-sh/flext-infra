"""Native CLI profiling preserves current evidence across SIGTERM handlers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import io
import pstats
import signal
import sys
from pathlib import Path

import pytest

from tests import tm, u


class TestsFlextInfraCProfileInterruption:
    """Exercise publication and continuation through real Python processes."""

    @staticmethod
    @pytest.mark.parametrize("handler", ["default", "raise", "return", "ignore"])
    def test_cli_termination_replaces_stale_report_and_preserves_previous_run(
        tmp_path: Path,
        handler: str,
    ) -> None:
        """The report path follows interrupted work without hiding native SIGTERM."""
        output = tmp_path / "profile.pstats"
        previous_profile = cProfile.Profile()
        previous_profile.runcall(sum, range(3))
        previous_profile.dump_stats(str(output))
        original = output.read_bytes()
        consumer = (
            "import os, runpy, signal, sys\n"
            "def prior_handler(signum, frame):\n"
            + (
                "    raise RuntimeError('native handler failure')\n"
                if handler == "raise"
                else "    return\n"
            )
            + (
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                if handler == "ignore"
                else "signal.signal(signal.SIGTERM, prior_handler)\n"
                if handler != "default"
                else ""
            )
            + "def terminate_import(event, arguments):\n"
            "    if event == 'exec' and arguments[0].co_filename.endswith(\n"
            "        '/flext_infra/cli.py'\n"
            "    ):\n"
            "        os.kill(os.getpid(), signal.SIGTERM)\n"
            "sys.addaudithook(terminate_import)\n"
            "sys.argv = ['flext_infra._profile_entry', sys.argv[1], '--help']\n"
            "runpy.run_module('flext_infra._profile_entry', run_name='__main__')\n"
        )
        terminated = tm.ok(
            u.Cli.run_raw((sys.executable, "-c", consumer, str(output)), cwd=tmp_path)
        )
        tm.that(
            terminated.outcome.raw_return_code,
            eq=-signal.SIGTERM
            if handler == "default"
            else 1
            if handler == "raise"
            else 0,
            msg=terminated.stderr,
        )
        tm.that(terminated.outcome.timed_out, eq=False)
        checkpoints = tuple(tmp_path.glob("profile-*.checkpoint.pstats"))
        previous = tuple(tmp_path.glob("profile.previous-*.checkpoint.pstats"))
        tm.that(len(checkpoints), eq=1)
        tm.that(len(previous), eq=1)
        tm.that(previous[0].read_bytes(), eq=original)
        tm.that(output.read_bytes(), ne=original)
        tm.that(checkpoints[0].samefile(output), eq=handler == "default")
        rendered = io.StringIO()
        measured = pstats.Stats(str(output), stream=rendered)
        measured.print_stats("importlib")
        tm.that(rendered.getvalue(), has="import_module")
        for retained in tmp_path.glob("*.pstats"):
            tm.that(
                pstats.Stats(str(retained)).get_stats_profile().func_profiles,
                truth=True,
            )
        if handler == "raise":
            tm.that(terminated.stderr, has="RuntimeError: native handler failure")
            tm.that(terminated.stderr, lacks="FileExistsError")
        elif handler in {"return", "ignore"}:
            rendered.truncate(0)
            rendered.seek(0)
            measured.print_stats(r"/flext_infra/cli\.py:\d+\(main\)")
            tm.that(rendered.getvalue(), has="(main)")
        if handler != "default":
            completed = tuple(
                path
                for path in tmp_path.glob("profile-*.pstats")
                if path != checkpoints[0]
            )
            final_previous = tuple(
                path
                for path in tmp_path.glob("profile.previous-*.pstats")
                if path != previous[0]
            )
            tm.that(len(completed), eq=1)
            tm.that(len(final_previous), eq=1)
            tm.that(completed[0].samefile(output), eq=True)
            tm.that(final_previous[0].samefile(checkpoints[0]), eq=True)
