"""End-to-end contract for the profiled pytest runner.

The runner's job is to boot a profiled pytest stack in a child interpreter and
report honestly on what that run produced. Proving that requires a real child
run against a real project, so these cases live in the integration tier: they
exercise the public runner surface without patching the system under test.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


class TestsFlextInfraPytestRunnerEndToEnd:
    """Prove the runner's reporting contract against real child runs."""

    @staticmethod
    def _project(root: Path, body: str) -> FlextInfraPytestRunner:
        """Materialize a minimal real project and its runner."""
        tests_dir = root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "sample_test.py").write_text(body, encoding="utf-8")
        return FlextInfraPytestRunner(
            workspace_root=root,
            started_at_monotonic=time.monotonic(),
            what="all",
            target="tests",
            reports=".reports/tests",
        )

    @staticmethod
    def _summary(root: Path) -> str:
        """Read the summary the runner just published."""
        latest = (
            (root / ".reports" / "tests" / "latest.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        return (root / ".reports" / "tests" / latest / "summary.txt").read_text(
            encoding="utf-8"
        )

    # Measured (2026-08-07): ~85s. A real child run pays interpreter boot,
    # plugin import and cProfile instrumentation — that cost IS the behavior
    # under test. Ceiling override with measured evidence, never a hang mask.
    @pytest.mark.timeout(180)
    def test_green_run_reports_absent_coverage_artifact_honestly(
        self, tmp_path: Path
    ) -> None:
        """A green run exits 0 and records coverage as not generated."""
        # Why (15af1cd4): the runner always invokes pytest with --no-cov, so a
        # coverage artifact can never exist; the summary states that instead of
        # demanding a file no run can produce.
        runner = self._project(tmp_path, "def test_ok():\n    assert True\n")

        exit_code = tm.ok(runner.execute())

        tm.that(exit_code, eq=0)
        summary = self._summary(tmp_path)
        tm.that(summary, has="coverage=not-generated")
        tm.that(summary, has="failed=0")
        tm.that(summary, has="state=COMPLETED")

    # Measured (2026-08-07): ~85s, same child-run cost as the green case.
    @pytest.mark.timeout(180)
    def test_failing_child_run_surfaces_the_failure(self, tmp_path: Path) -> None:
        """A failing child run is reported as a failure, never masked."""
        runner = self._project(tmp_path, "def test_bad():\n    assert False\n")

        result = runner.execute()

        tm.that(result.success and result.value == 0, eq=False)
        summary = self._summary(tmp_path)
        tm.that(summary, has="failed=1")


__all__: list[str] = []
