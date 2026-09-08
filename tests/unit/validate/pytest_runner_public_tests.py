"""Observable public cached-pytest runtime contract."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraPytestRunner, config, u


class TestsFlextInfraPytestRunner:
    """Exercise the real pytest, testmon, coverage, and report lifecycle."""

    @staticmethod
    def _runner_for(cached_runner_project: Path) -> FlextInfraPytestRunner:
        """Bind one runner to the fixture project's canonical cache paths."""
        codegen = config.Infra.codegen
        cache = codegen.make.testmon_cache
        testmon_db = (
            cached_runner_project.parent
            / codegen.toolchain.state_directory_name
            / cached_runner_project.name
            / cache.namespace
            / cache.database_filename
        )
        return FlextInfraPytestRunner(
            repository_root=cached_runner_project,
            started_at_monotonic=time.monotonic(),
            target=cache.target_directory,
            reports=cache.reports_directory,
            testmon_db=testmon_db,
        )

    @staticmethod
    def _summary(reports_root: Path) -> str:
        """Read the latest report summary through the files facade."""
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        return tm.ok(u.Cli.files_read_text(reports_root / latest_name / "summary.txt"))

    @pytest.mark.slow
    @pytest.mark.slow
    def test_complete_suite_persists_cache_and_zero_diagnostic_evidence(
        self, cached_runner_project: Path
    ) -> None:
        """One public execution collects every test and publishes real evidence."""
        codegen = config.Infra.codegen
        cache = codegen.make.testmon_cache
        testmon_db = (
            cached_runner_project.parent
            / codegen.toolchain.state_directory_name
            / cached_runner_project.name
            / cache.namespace
            / cache.database_filename
        )
        runner = self._runner_for(cached_runner_project)

        exit_code = tm.ok(runner.execute())

        tm.that(exit_code, eq=0)
        tm.that(testmon_db.is_file(), eq=True)
        reports_root = cached_runner_project / cache.reports_directory
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        summary = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "summary.txt")
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
        tm.that((reports_root / latest_name / "junit.xml").is_file(), eq=True)
        # The testmon verb owns no coverage plugin (testmon 2.x refuses branch
        # coverage through the cov plugin), so its command carries --no-cov and
        # the coverage artifact belongs to the coverage verb alone.
        selection = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "testmon-selection.txt")
        )
        command = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "command.txt")
        )
        for node_id in (line for line in selection.splitlines() if line):
            tm.that(command, has=node_id)
        tm.that(command, has="--no-cov")
        tm.that((reports_root / latest_name / "coverage.xml").is_file(), eq=False)

    @pytest.mark.slow
    def test_coverage_verb_publishes_artifact_without_testmon(
        self, cached_runner_project: Path
    ) -> None:
        """The coverage pass runs its own process: real artifact, zero testmon."""
        codegen = config.Infra.codegen
        cache = codegen.make.testmon_cache
        reports_root = cached_runner_project / cache.reports_directory
        runner = self._runner_for(cached_runner_project)

        exit_code = tm.ok(runner.execute_coverage())

        tm.that(exit_code, eq=0)
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        coverage = reports_root / latest_name / "coverage.xml"
        tm.that(coverage.is_file(), eq=True)
        tm.that(coverage.stat().st_size > 0, eq=True)
        summary = self._summary(reports_root)
        tm.that(summary, has=["executed=1", "failed=0", "exit=0"])
        command = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "command.txt")
        )
        tm.that(command, has="--cov")
        tm.that("--testmon" in command, eq=False)


__all__: list[str] = []
