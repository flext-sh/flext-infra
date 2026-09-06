"""Canonical pytest argv for persistent testmon execution."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import config, t
from flext_infra.validate._pytest_runner.base import FlextInfraPytestRunnerBase


class FlextInfraPytestRunnerCommand(FlextInfraPytestRunnerBase):
    """Build the single supported pytest command."""

    def build_selection_command(self) -> tuple[str, ...]:
        """Build the read-only argv that resolves the testmon selection once.

        Every xdist worker otherwise resolves the selection itself, and two
        workers reading the database while a third writes it collect different
        sets, which xdist aborts with "Different tests were collected". This
        pass runs no test and writes nothing.
        """
        pytest = config.Infra.tooling.tools.pytest
        return (
            sys.executable,
            "-m",
            "pytest",
            str(self.target),
            "--testmon",
            "--testmon-nocollect",
            "--collect-only",
            "-q",
            "-p",
            pytest.enforcement_plugin,
            "-p",
            "no:metadata",
            "-p",
            "no:randomly",
            "-n",
            "0",
            "--no-cov",
        )

    def build_command(
        self, report_dir: Path, selected_node_ids: t.StrSequence | None = None
    ) -> tuple[str, ...]:
        """Build a whole-suite testmon argv without user selectors.

        ``selected_node_ids`` is the selection the controller already resolved:
        ``None`` when it resolved none, an empty sequence when testmon selected
        nothing, node ids otherwise. Explicit node ids also switch testmon to
        prioritize-only, which is what keeps every worker collecting one set.
        """
        pytest = config.Infra.tooling.tools.pytest
        targets: t.StrSequence = (
            tuple(selected_node_ids) if selected_node_ids else (str(self.target),)
        )
        # Nothing selected means nothing to distribute across workers.
        workers = "0" if selected_node_ids == () else str(
            self.parallel_worker_budget(pytest)
        )
        return (
            sys.executable,
            "-m",
            "pytest",
            *targets,
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
            workers,
            "--dist",
            pytest.parallel_distribution,
            "--benchmark-disable",
        )


__all__: list[str] = ["FlextInfraPytestRunnerCommand"]
