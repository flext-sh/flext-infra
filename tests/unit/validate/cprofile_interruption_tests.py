"""Native CLI profiling preserves current evidence across SIGTERM handlers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import cProfile
import io
import pstats
import signal
import sys
from pathlib import Path

import pytest

from flext_infra import FlextInfraPytestClock
from tests import c, tm, u


class TestsFlextInfraCProfileInterruption:
    """Exercise publication and continuation through real Python processes."""

    @staticmethod
    def test_sigterm_cleanup_preserves_replaced_staging_identity(
        tmp_path: Path,
    ) -> None:
        """Keep the handler failure primary without deleting a new cleanup inode."""
        output = tmp_path / "profile.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import os, signal\n"
            "from flext_tests import tm\n"
            "output = Path(sys.argv[1])\n"
            "sum(range(3))\n"
            "clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "before = output.read_bytes()\n"
            "staging = []\n"
            "def native(signum, frame):\n"
            "    raise RuntimeError('original native failure')\n"
            "signal.signal(signal.SIGTERM, native)\n"
            "clock.FlextInfraPytestClock.register_signal_checkpoint(profile, output)\n"
            "def interrupt(name, arguments):\n"
            "    if name == 'tempfile.mkstemp':\n"
            "        staging.append(Path(arguments[0]))\n"
            "    if name == 'marshal.dumps':\n"
            "        staging[0].rename(staging[0].with_suffix('.retained'))\n"
            "        staging[0].write_bytes(b'foreign inode')\n"
            "        os.kill(os.getpid(), signal.SIGTERM)\n"
            "sys.addaudithook(interrupt)\n"
            "try:\n"
            "    clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "except RuntimeError as failure:\n"
            "    assert str(failure) == 'original native failure'\n"
            "    assert 'profile staging cleanup failed' "
            "in '\\n'.join(failure.__notes__)\n"
            "else:\n"
            "    tm.reject('native failure was lost')\n"
            "assert len(staging) == 1, staging\n"
            "assert staging[0].read_bytes() == b'foreign inode'\n"
            "assert output.read_bytes() == before\n"
        )
        result = tm.ok(
            u.Cli.run_raw((sys.executable, "-c", script, str(output)), cwd=tmp_path)
        )
        tm.ok(u.Cli.process_succeeded(result.outcome), msg=result.stderr)

    @staticmethod
    @pytest.mark.parametrize("status", [0, 7])
    def test_public_command_retains_status_and_profile(
        tmp_path: Path, status: int
    ) -> None:
        """The flat public owner publishes readable invocation-owned evidence."""
        output = tmp_path / "command.pstats"
        tm.that(
            FlextInfraPytestClock.profile_command(lambda: status, output),
            eq=status,
        )
        tm.that(
            pstats.Stats(str(output)).get_stats_profile().func_profiles,
            truth=True,
        )
        retained = tuple(tmp_path.glob("command-*.pstats"))
        tm.that(len(retained), eq=1)
        tm.ok(retained[0].samefile(output))

    @staticmethod
    def test_public_command_preserves_first_exception(tmp_path: Path) -> None:
        """A real missing output parent cannot replace the command failure."""
        failure = RuntimeError("command failed")

        def command() -> int:
            raise failure

        with pytest.raises(RuntimeError) as raised:
            FlextInfraPytestClock.profile_command(
                command, tmp_path / "missing" / "command.pstats"
            )
        tm.ok(raised.value is failure)
        tm.that("\n".join(failure.__notes__), has="profile finalization failed")
        tm.fail((tmp_path / "missing").exists())

    @staticmethod
    @pytest.mark.usefixtures("profiling_enabled")
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
            "os.environ['FLEXT_INFRA_PROFILE_OUTPUT'] = sys.argv[1]\n"
            "sys.argv = ['flext_infra', '--help']\n"
            "runpy.run_module('flext_infra', run_name='__main__')\n"
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
        tm.fail(terminated.outcome.timed_out)
        tm.that(terminated.stderr, has="terminate_import")
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
            measured.print_stats(r"/flext_infra/cli\.py:\d+\(infra_main\)")
            tm.that(rendered.getvalue(), has="(infra_main)")
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
            tm.ok(completed[0].samefile(output))
            tm.ok(final_previous[0].samefile(checkpoints[0]))
