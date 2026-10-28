"""Graceful suite stop keeps pytest-testmon progress across bounded runs.

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

import ast
import sqlite3
import time
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.validate import FlextInfraPytestRunner
from tests import c, m, t, tm, u


class TestsFlextInfraPytestRunnerSuiteStop:
    """Exercise the real runner around its graceful-stop boundary."""

    @staticmethod
    def _read(path: Path) -> str:
        """Read one published receipt through the files facade.

        Returns:
            The resulting ``str``.

        """
        return tm.ok(u.Cli.files_read_text(path))

    @staticmethod
    def _spent_runner(project: Path, *, serial: bool) -> FlextInfraPytestRunner:
        """Build the real slow-phase runner whose stop instant has already passed.

        An ordinary phase stops at the instant no child may start (its stop
        reserve is the termination grace itself), so only a phase carrying
        slow items keeps a drain reserve beyond the grace. The entrypoint
        clock spends exactly that reserve: selection still starts, and pytest
        stops dispatch at a durable testmon batch checkpoint, never through the
        deadline SIGTERM.

        Returns:
            The resulting ``FlextInfraPytestRunner``.

        """
        policy = config.Infra.tooling.tools.pytest
        reserve = (
            policy.slow_serial_suite_stop_reserve_seconds
            if serial
            else policy.slow_suite_stop_reserve_seconds
        )
        runner = u.Tests.PytestRunner.runner_for(project, slow_phase=True)
        return runner.model_copy(
            update={
                "started_at_monotonic": time.monotonic()
                - policy.run_timeout_seconds
                + reserve,
            },
        )

    @staticmethod
    def _slow_module(test_names: Sequence[str]) -> str:
        """Render one slow-marked module exercising the fixture package.

        Returns:
            The module source the slow phase selects.

        """
        marker = config.Infra.tooling.tools.pytest.slow_marker
        return (
            "import pytest\n"
            "from runner_sample import answer\n\n"
            f"pytestmark = pytest.mark.{marker}\n\n"
            + "".join(
                f"def {name}() -> None:\n    assert answer() == 42\n\n"
                for name in test_names
            )
        )

    def _published_run(
        self,
        project: Path,
        *,
        expected_raw_exit: pytest.ExitCode,
    ) -> tuple[Path, t.StrTuple, int]:
        """Return the published run, its selection and its executed count.

        Returns:
            The published run, its selection and its executed count.

        """
        reports = config.Infra.codegen.make.testmon_cache.reports_directory
        (bounded,) = (path.parent for path in (project / reports).glob("*/summary.txt"))
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            self._read(bounded / "suite-outcome.json"),
        )
        tm.that(outcome.raw_return_code, eq=expected_raw_exit.value)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        selected = m.Infra.PytestCollectionManifest.model_validate_json(
            self._read(bounded / "testmon-selection.json"),
        ).node_ids
        executed = m.Infra.TestmonRunAccounting.model_validate_json(
            self._read(bounded / "run-accounting.json"),
        ).executed_count
        return bounded, selected, executed

    @staticmethod
    @pytest.mark.slow
    def test_interrupted_startup_preserves_exit_without_completed_reports(
        cached_runner_project: Path,
    ) -> None:
        """An actual startup interruption is not a completed failing suite."""
        abort_message = "suite interrupted before session startup completed"
        (cached_runner_project / "conftest.py").write_text(
            "import pytest\n"
            "def pytest_sessionstart(session: pytest.Session) -> None:\n"
            "    if not session.config.option.collectonly:\n"
            f"        pytest.exit({abort_message!r}, "
            "returncode=pytest.ExitCode.INTERRUPTED)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)

        result = runner.execute()

        tm.that(tm.ok(result), eq=pytest.ExitCode.INTERRUPTED.value)
        reports = config.Infra.codegen.make.testmon_cache.reports_directory
        (outcome_path,) = (cached_runner_project / reports).glob(
            "*/suite-outcome.json",
        )
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            tm.ok(u.Cli.files_read_text(outcome_path)),
        )
        tm.that(outcome.raw_return_code, eq=pytest.ExitCode.INTERRUPTED.value)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        tm.that(
            tm.ok(u.Cli.files_read_text(outcome_path.parent / "pytest.log")),
            has=abort_message,
        )
        tm.fail((outcome_path.parent / "junit.xml").exists())
        tm.fail((outcome_path.parent / "summary.txt").exists())
        tm.fail((outcome_path.parent / "run-accounting.json").exists())

    def _testmon_batch_size(self) -> int:
        """Read the installed testmon batch size from its source declaration.

        Returns:
            The positive literal batch size declared by the installed distribution.

        Raises:
            TypeError: If the declaration is not a literal positive integer.

        """
        distribution = u.Infra.codemod_distributions()["pytest-testmon"]
        installed_files = tm.not_none(distribution.files)
        (batch_owner,) = (
            entry
            for entry in installed_files
            if entry.as_posix() == "testmon/testmon_core.py"
        )
        batch_source = Path(str(distribution.locate_file(batch_owner)))
        tree = ast.parse(self._read(batch_source), filename=str(batch_source))
        (declaration,) = (
            statement
            for statement in tree.body
            if isinstance(statement, ast.Assign)
            and any(
                isinstance(name, ast.Name) and name.id == "TEST_BATCH_SIZE"
                for name in statement.targets
            )
        )
        literal = declaration.value
        if not isinstance(literal, ast.Constant):
            msg = "TEST_BATCH_SIZE must be a literal constant"
            raise TypeError(msg)
        batch_size = literal.value
        if not isinstance(batch_size, int) or isinstance(batch_size, bool):
            msg = "TEST_BATCH_SIZE must be an integer"
            raise TypeError(msg)
        tm.that(batch_size > 0, truth=True)
        return batch_size

    @pytest.mark.slow
    @pytest.mark.parametrize("distributed", [True, False], ids=["xdist", "serial"])
    def test_suite_stop_instant_persists_the_executed_prefix(
        self,
        cached_runner_project: Path,
        *,
        distributed: bool,
    ) -> None:
        """A run reaching its stop instant ends itself and testmon keeps progress.

        pytest must report a red incomplete run, and the testmon database must
        hold every executed test, so the next selection excludes them.
        """
        if distributed:
            u.Tests.PytestRunner.declare_parallel_project(cached_runner_project)
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        workers = (
            runner.parallel_worker_budget(config.Infra.tooling.tools.pytest)
            if distributed
            else 1
        )
        batch_size = self._testmon_batch_size()
        target = config.Infra.codegen.make.testmon_cache.target_directory
        (cached_runner_project / target / "test_budget.py").write_text(
            self._slow_module(
                tuple(
                    f"test_budget_{index}"
                    for index in range(
                        batch_size * workers * (2 if distributed else 1) + 1,
                    )
                ),
            ),
            encoding="utf-8",
        )
        runner = self._spent_runner(cached_runner_project, serial=not distributed)
        tm.that(tm.ok(runner.execute()), eq=pytest.ExitCode.INTERRUPTED.value)

        bounded, selected, executed = self._published_run(
            cached_runner_project,
            expected_raw_exit=pytest.ExitCode.INTERRUPTED,
        )
        tm.that(executed, gt=0)
        tm.that(executed, lt=len(selected))
        if distributed:
            tm.that(workers, gt=1)
            tm.that(self._read(bounded / "command.txt"), has=f"-n {workers}")
            tm.that(
                self._read(bounded / "pytest.log"),
                has=["[gw0]", "[gw1]", "suite stop instant"],
            )
        tm.that(
            self._read(bounded / "summary.txt"),
            has=[
                "outcome=incomplete",
                f"selected={len(selected)}",
                f"executed={executed}",
                "accounting_complete=False",
                "failed=0",
            ],
        )

        # pytest-testmon's durable record is what the next selection excludes:
        # collected-but-unexecuted tests keep a row without a measured duration.
        with closing(
            sqlite3.connect(f"file:{runner.testmon_db}?mode=ro", uri=True),
        ) as connection:
            persisted = {
                name
                for (name,) in connection.execute(
                    "SELECT test_name FROM test_execution"
                    " WHERE failed = 0 AND duration IS NOT NULL",
                )
            }
        tm.that(len(persisted), eq=executed)
        tm.ok(persisted <= set(selected))

    @pytest.mark.slow
    def test_stop_instant_after_the_last_selected_test_completes_the_run(
        self,
        cached_runner_project: Path,
    ) -> None:
        """A stop requested on the last selected test's teardown ends nothing.

        The slow phase selects one slow test, so the serial dispatch applies
        and the stop request lands after the whole selection executed and
        passed: the accounting is complete and the run is green although
        pytest still reports its interrupt.
        """
        target = config.Infra.codegen.make.testmon_cache.target_directory
        (cached_runner_project / target / "test_last_selected.py").write_text(
            self._slow_module(("test_last_selected",)),
            encoding="utf-8",
        )
        runner = self._spent_runner(cached_runner_project, serial=True)

        tm.that(tm.ok(runner.execute()), eq=pytest.ExitCode.OK.value)

        bounded, selected, executed = self._published_run(
            cached_runner_project,
            expected_raw_exit=pytest.ExitCode.OK,
        )
        tm.that(executed, eq=len(selected))
        tm.that(
            self._read(bounded / "summary.txt"),
            has=[
                "outcome=executed",
                f"selected={len(selected)}",
                f"executed={executed}",
                "accounting_complete=True",
                "failed=0",
                "exit=0",
            ],
        )
