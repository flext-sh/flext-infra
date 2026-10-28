"""Real CLI startup and profile-publication failure contracts.

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

import io
import pstats
import sys
from pathlib import Path

import pytest

from tests import m, t, tm, u


class TestsFlextInfraCProfileCli:
    """Exercise native CLI processes independently of report rendering."""

    @staticmethod
    @pytest.mark.usefixtures("profiling_enabled")
    def test_cli_profiles_retain_each_run_and_measure_startup(tmp_path: Path) -> None:
        """Repeated public CLI launches preserve raw runs including CLI imports."""
        output = tmp_path / "profile.pstats"
        original: bytes | None = None
        for _ in range(2):
            tm.ok(
                u.Cli.run_checked(
                    (sys.executable, "-m", "flext_infra", "--help"),
                    cwd=tmp_path,
                    options=m.Cli.ProcessOptions(
                        env={"FLEXT_INFRA_PROFILE_OUTPUT": str(output)}
                    ),
                )
            )
            profiles = sorted(tmp_path.glob("profile-*.pstats"))
            if original is None:
                tm.that(len(profiles), eq=1)
                original = profiles[0].read_bytes()
            else:
                tm.that(len(profiles), eq=2)
                tm.ok(original in (path.read_bytes() for path in profiles))
                previous = tuple(tmp_path.glob("profile.previous-*.pstats"))
                tm.that(len(previous), eq=1)
                tm.that(previous[0].read_bytes(), eq=original)
            tm.that(
                output.read_bytes() in (path.read_bytes() for path in profiles), eq=True
            )
            for profile in profiles:
                rendered = io.StringIO()
                pstats.Stats(str(profile), stream=rendered).print_stats(
                    r"/flext_infra/cli\.py:\d+\(<module>\)"
                )
                tm.that(rendered.getvalue(), has="(<module>)")

    @staticmethod
    @pytest.mark.usefixtures("profiling_enabled")
    @pytest.mark.parametrize(
        "arguments",
        [("--help",), ("validate", "cprofile-report", "--invalid-profile-option")],
    )
    def test_profile_publication_failure_preserves_the_native_cli_status(
        tmp_path: Path, arguments: t.StrTuple
    ) -> None:
        """A destination failing at publication cannot replace the CLI status.

        The entrypoint admits the destination parent before the command runs;
        a destination occupied by a directory fails only when publishing.
        """
        occupied = tmp_path / "occupied.pstats"
        occupied.mkdir()
        reference = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-m", "flext_infra", *arguments), cwd=tmp_path
            )
        )
        profiled = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-m", "flext_infra", *arguments),
                cwd=tmp_path,
                env={"FLEXT_INFRA_PROFILE_OUTPUT": str(occupied)},
            )
        )
        tm.that(profiled.stdout, eq=reference.stdout)
        tm.that(profiled.stderr, has="previous profile artifact is not a regular file")
        if u.Cli.process_succeeded(reference.outcome):
            tm.fail(u.Cli.process_succeeded(profiled.outcome))
        else:
            tm.that(
                profiled.outcome.raw_return_code, eq=reference.outcome.raw_return_code
            )

    @staticmethod
    @pytest.mark.usefixtures("profiling_enabled")
    def test_profile_publication_failure_keeps_the_original_cli_exception(
        tmp_path: Path,
    ) -> None:
        """A closed native stdout raises first; a real flush failure remains a note."""
        occupied = tmp_path / "occupied.pstats"
        occupied.mkdir()
        consumer = (
            "import runpy, sys\n"
            "from flext_cli import cli\n"
            "from flext_infra import FlextInfraCli\n"
            "sys.stdout.close()\n"
            "module = sys.argv[1]\n"
            "sys.argv = sys.argv[1:]\n"
            "runpy.run_module(module, run_name='__main__')\n"
        )
        reference = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", consumer, "flext_infra", "--help"),
                cwd=tmp_path,
            )
        )
        profiled = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", consumer, "flext_infra", "--help"),
                cwd=tmp_path,
                env={"FLEXT_INFRA_PROFILE_OUTPUT": str(occupied)},
            )
        )
        tm.fail(u.Cli.process_succeeded(reference.outcome))
        tm.that(
            profiled.outcome.raw_return_code,
            eq=reference.outcome.raw_return_code,
            msg=reference.stderr + profiled.stderr,
        )
        tm.that(reference.stderr, lacks="KeyboardInterrupt")
        for executed in (reference, profiled):
            tm.fail(executed.outcome.timed_out)
            tm.that(executed.outcome.forwarded_signal, eq=None)
        tm.that(reference.stderr, has="ValueError: I/O operation on closed file.")
        primary_trace, secondary_trace = profiled.stderr.split(
            "profile finalization failed:\n", maxsplit=1
        )
        tm.that(primary_trace, has="ValueError: I/O operation on closed file.")
        tm.that(primary_trace, lacks="previous profile artifact")
        tm.that(secondary_trace, has="previous profile artifact is not a regular file")
        tm.that(secondary_trace, lacks="ValueError: I/O operation on closed file.")
