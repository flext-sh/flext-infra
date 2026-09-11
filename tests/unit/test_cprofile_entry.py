"""Contracts for the canonical focused cProfile report entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config, u
from flext_tests import tm


class TestsCProfileEntry:
    # Why (suite budget): spawns a fresh interpreter to render the report;
    # cold interpreter start under xdist contention exceeds the case wall.
    @pytest.mark.slow
    def test_report_uses_typed_pytest_policy(self, tmp_path: Path) -> None:
        """Render a real profile with the same typed policy production consumes."""
        report_root = tmp_path / ".reports" / "cprofile"
        report_root.mkdir(parents=True)
        profile_target = tmp_path / "profile_target.py"
        profile_target.write_text("_ = sum(range(10))\n", encoding="utf-8")
        profiled = u.Cli.run_checked(
            [
                sys.executable,
                "-m",
                "cProfile",
                "-o",
                str(report_root / "pytest.pstats"),
                str(profile_target),
            ],
            cwd=tmp_path,
        )
        tm.ok(profiled)

        rendered = u.Cli.run_checked(
            [sys.executable, "-m", "flext_infra._cprofile_entry"], cwd=tmp_path
        )
        tm.ok(rendered)

        report = (report_root / "pytest.txt").read_text(encoding="utf-8")
        policy = config.Infra.tooling.tools.pytest
        tm.that(bool(report.strip()), eq=True)
        tm.that(len(report.splitlines()) <= policy.profile_limit + 10, eq=True)


__all__: list[str] = []
