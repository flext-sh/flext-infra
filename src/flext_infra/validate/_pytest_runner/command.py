"""Canonical pytest argv for persistent testmon execution."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

from flext_infra import c, config, t

from .base import FlextInfraPytestRunnerBase

_NO_COVERAGE: Final[t.VariadicTuple[str]] = ("--no-cov",)


class FlextInfraPytestRunnerCommand(FlextInfraPytestRunnerBase):
    """Build the single supported pytest command family.

    One suite builder owns every flag; the testmon and coverage verbs are two
    selections over it (testmon 2.x refuses branch coverage through the cov
    plugin, so the two never share a process).
    """

    def build_selection_command(self, *, complete: bool = False) -> t.VariadicTuple[str]:
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
            *(("--testmon-noselect",) if complete else ()),
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
        self,
        report_dir: Path,
        selected_node_ids: t.StrSequence | None = None,
        *,
        serialize: bool = False,
    ) -> t.VariadicTuple[str]:
        """Build the testmon suite argv (never the cov plugin)."""
        pytest = config.Infra.tooling.tools.pytest
        selection = selected_node_ids or None
        # Nothing selected means nothing to distribute across workers; a cold
        # cache serializes the seeding run so every worker would otherwise see
        # a different testmon set.
        workers = (
            "0"
            if serialize or selected_node_ids == ()
            else str(self.parallel_worker_budget(pytest))
        )
        return self._suite_argv(
            report_dir,
            targets=(tuple(selection) if selection else (str(self.target),)),
            workers=workers,
            trailing=(
                "--testmon",
                *(("--testmon-noselect",) if selection else ()),
                *_NO_COVERAGE,
            ),
        )

    def build_coverage_command(
        self, report_dir: Path, *, serialize: bool = False
    ) -> t.VariadicTuple[str]:
        """Build the whole-suite coverage argv (never the testmon plugin).

        The measurement source is the declared package source directory — the
        same boundary every fleet coverage config declares — so imported
        third-party/Cython modules can never emit parse warnings.
        """
        pytest = config.Infra.tooling.tools.pytest
        workers = "0" if serialize else str(self.parallel_worker_budget(pytest))
        return self._suite_argv(
            report_dir,
            targets=(str(self.target),),
            workers=workers,
            trailing=(
                f"--cov={self.root / c.Infra.DEFAULT_SRC_DIR}",
                f"--cov-report=xml:{report_dir / 'coverage.xml'}",
                "--no-cov-on-fail",
            ),
        )

    def _suite_argv(
        self,
        report_dir: Path,
        *,
        targets: t.StrSequence,
        workers: str,
        trailing: t.StrSequence,
    ) -> t.VariadicTuple[str]:
        """Assemble one suite invocation; ``trailing`` owns the plugin split."""
        pytest = config.Infra.tooling.tools.pytest
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
            *trailing,
            "-n",
            workers,
            "--dist",
            pytest.parallel_distribution,
            "--benchmark-disable",
        )


__all__: list[str] = ["FlextInfraPytestRunnerCommand"]
