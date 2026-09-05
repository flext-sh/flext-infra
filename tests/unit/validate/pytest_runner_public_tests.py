"""Observable public cached-pytest runtime contract."""

from __future__ import annotations

import time
from pathlib import Path

from flext_infra import FlextInfraPytestRunner, config, u
from flext_tests import tm


class TestsFlextInfraPytestRunner:
    """Exercise the real pytest, testmon, coverage, and report lifecycle."""

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
        runner = FlextInfraPytestRunner(
            repository_root=cached_runner_project,
            started_at_monotonic=time.monotonic(),
            target=cache.target_directory.as_posix(),
            reports=cache.reports_directory.as_posix(),
            testmon_db=testmon_db,
        )

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
        tm.that((reports_root / latest_name / "coverage.xml").is_file(), eq=True)


__all__: list[str] = []
