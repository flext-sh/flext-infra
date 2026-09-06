"""Canonical pytest argv for persistent testmon execution."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import config

from .base import FlextInfraPytestRunnerBase


class FlextInfraPytestRunnerCommand(FlextInfraPytestRunnerBase):
    """Build the single supported pytest command."""

    def build_command(self, report_dir: Path) -> tuple[str, ...]:
        """Build a whole-suite testmon argv without user selectors."""
        pytest = config.Infra.tooling.tools.pytest
        return (
            sys.executable,
            "-m",
            "pytest",
            str(self.target),
            *pytest.progress_args,
            *pytest.report_args,
            "-p",
            pytest.enforcement_plugin,
            "-p",
            "no:metadata",
            f"--timeout={pytest.case_timeout_seconds}",
            f"--maxfail={pytest.max_failures}",
            f"--junitxml={report_dir / 'junit.xml'}",
            "--testmon",
            "--cov",
            f"--cov-report=xml:{report_dir / 'coverage.xml'}",
            "--no-cov-on-fail",
            "-n",
            str(self.parallel_worker_budget(pytest)),
            "--dist",
            pytest.parallel_distribution,
            "--benchmark-disable",
        )


__all__: list[str] = ["FlextInfraPytestRunnerCommand"]
