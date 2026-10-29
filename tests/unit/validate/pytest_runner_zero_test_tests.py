"""Empty test ownership remains red; only an audited testmon cache hit is green.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import time
from collections.abc import Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from threading import Barrier, Event, Thread

import pytest
from typing_extensions import TypeForm

from flext_infra import config, m
from flext_infra.validate import FlextInfraPytestRunner
from tests import c, tm, u


class TestsFlextInfraPytestRunnerZeroTest:
    """Preserve native empty-suite status and its typed accounting."""

    @staticmethod
    @contextmanager
    def _held_elsewhere(lock: Path) -> Generator[None]:
        """Hold the shared lock from another thread, as a concurrent run would.

        The shared lock is reentrant within its holding thread, so contention
        is only observable from a different thread or process.

        Yields:
            Control while the lock is held by the other thread.

        """
        acquired = Event()
        release = Event()

        def hold() -> None:
            with u.Cli.file_changes_lock(lock):
                acquired.set()
                release.wait()

        holder = Thread(target=hold)
        holder.start()
        acquired.wait()
        try:
            yield
        finally:
            release.set()
            holder.join()

    @staticmethod
    def _zero_test_project(tmp_path: Path) -> Path:
        """Build a real consumer project that owns no test module at all.

        The tracked tests root exists (the fleet scaffold materializes it and
        the invest root carries ``tests/fixtures``), but it holds no
        ``test_*.py``/``*_test.py`` module — an empty suite by design.

        Returns:
            The resulting ``Path``.

        """
        project_root = tmp_path / "zero_test_project"
        cache = config.Infra.codegen.make.testmon_cache
        package_root = project_root / c.Infra.DEFAULT_SRC_DIR / "zero_sample"
        package_root.mkdir(parents=True)
        (project_root / cache.target_directory).mkdir(exist_ok=True)
        # The consumer's pytest table carries the SSOT collection patterns and
        # marker registry exactly as generated projects do, so collection and
        # the runner's ownership check read the same declarations.
        pytest_settings = config.Infra.tooling.tools.pytest
        (project_root / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(
                u.Cli.toml_document_from_mapping({
                    "tool": {
                        "pytest": {
                            "ini_options": {
                                "pythonpath": [c.Infra.DEFAULT_SRC_DIR],
                                c.Infra.PYTHON_FILES: list(
                                    u.Infra.native_tool_setting(
                                        config.Infra.tooling,
                                        "pytest.ini_options",
                                        "python_files",
                                        TypeForm(Sequence[str]),
                                    ),
                                ),
                                "markers": list(pytest_settings.standard_markers),
                            },
                        },
                    },
                }),
            ),
            encoding="utf-8",
        )
        (package_root / "__init__.py").write_text("VALUE = 41\n", encoding="utf-8")
        return project_root

    @staticmethod
    def _runner(
        project_root: Path,
        tmp_path: Path,
        *,
        slow_phase: bool = False,
        elapsed_seconds: float = 0.0,
        target_file: Path | None = None,
    ) -> FlextInfraPytestRunner:
        """Build the public runner exactly as the make verbs do.

        Returns:
            The resulting ``FlextInfraPytestRunner``.

        """
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        testmon_db = tmp_path / ".testmon-cache" / cache.database_filename
        testmon_db.parent.mkdir(parents=True, exist_ok=True)
        return FlextInfraPytestRunner(
            repository_root=project_root,
            started_at_monotonic=time.monotonic() - elapsed_seconds,
            target=cache.target_directory,
            reports=cache.reports_directory,
            testmon_db=testmon_db,
            apply_changes=True,
            slow_phase=slow_phase,
            target_file=target_file,
            run_timeout_seconds=policy.run_timeout_seconds,
            termination_grace_seconds=policy.termination_grace_seconds,
        )

    @pytest.mark.slow
    def test_plural_module_form_still_owns_its_tests(
        self,
        tmp_path: Path,
    ) -> None:
        """A ``*_tests.py``-only suite owns tests: the SSOT patterns decide.

        The module patterns come from the pytest ``python-files`` SSOT; a
        hardcoded copy that omitted the plural form answered "owns no tests"
        for a live suite, and the accounting then rejected a fully green
        run (selected=0 vs executed=N, exit 1 on a cold checkout).
        """
        project_root = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        module = project_root / cache.target_directory / "sample_suite_tests.py"
        module.write_text(
            "def test_value() -> None:\n    from zero_sample import VALUE\n"
            "    tm_value = VALUE == 41\n    assert tm_value\n",
            encoding="utf-8",
        )
        outcome = tm.ok(self._runner(project_root, tmp_path).execute())

        tm.that(outcome, eq=pytest.ExitCode.OK.value)
        summary = self._latest_summary(project_root / cache.reports_directory)
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            self._read(summary.parent / "selection-plan.json"),
        )
        tm.fail(plan.owns_no_tests)
        tm.that(
            tm.ok(self._runner(project_root, tmp_path).execute()),
            eq=pytest.ExitCode.OK.value,
        )
        summary = self._latest_summary(project_root / cache.reports_directory)
        accounting = m.Infra.TestmonRunAccounting.model_validate_json(
            self._read(summary.parent / "run-accounting.json"),
        )
        tm.that(accounting.executed_count, eq=0)
        tm.that(accounting.inventory_count, eq=1)
        tm.that(accounting.deselected_count, eq=accounting.inventory_count)
        tm.ok(accounting.cache_restored)
        tm.fail(accounting.owns_no_tests)
        tm.that(self._read(summary), has=["outcome=cache_hit\n", "exit=0\n"])

    def test_held_testmon_database_lease_refuses_a_concurrent_run(
        self,
        tmp_path: Path,
    ) -> None:
        """A blocked run records its identity without touching the leased database."""
        project = self._zero_test_project(tmp_path)
        runner = self._runner(
            project,
            tmp_path,
            elapsed_seconds=config.Infra.tooling.tools.pytest.run_timeout_seconds,
        )

        lock = runner.testmon_db.with_name(f"{runner.testmon_db.name}.lock")
        with (
            self._held_elsewhere(lock),
            pytest.raises(TimeoutError, match=re.escape(str(lock))),
        ):
            runner.execute()

        reports_root = (
            project / config.Infra.codegen.make.testmon_cache.reports_directory
        )
        receipts = tuple(reports_root.glob("*/run-context.json"))
        tm.that(len(receipts), eq=1)
        context = m.Infra.PytestRunContext.model_validate_json(receipts[0].read_bytes())
        tm.that(context.testmon_db, eq=runner.testmon_db)
        tm.that(context.testmon_lease_acquired, eq=False)
        tm.that(context.report_directory, eq=receipts[0].parent)
        tm.that(
            tuple(path.name for path in receipts[0].parent.iterdir()),
            eq=("run-context.json",),
        )
        tm.fail(runner.testmon_db.exists())

    def test_held_latest_pointer_lease_preserves_context_and_deadline(
        self,
        tmp_path: Path,
    ) -> None:
        """Pointer contention expires without losing diagnostics or the old pointer."""
        project = self._zero_test_project(tmp_path)
        runner = self._runner(
            project,
            tmp_path,
            elapsed_seconds=config.Infra.tooling.tools.pytest.run_timeout_seconds,
        )
        reports = project / runner.reports
        reports.mkdir(parents=True)
        latest = reports / "latest.txt"
        tm.ok(u.Cli.atomic_write_text_file(latest, "previous-run\n"))
        lock = latest.with_name(f"{latest.name}.lock")
        with self._held_elsewhere(lock):
            before = lock.stat()
            with pytest.raises(TimeoutError, match=re.escape(str(lock))):
                runner.execute()
            receipts = tuple(reports.glob("*/run-context.json"))
            tm.that(len(receipts), eq=1)
            context = m.Infra.PytestRunContext.model_validate_json(
                receipts[0].read_bytes(),
            )
            tm.that(context.testmon_db, eq=runner.testmon_db)
            tm.that(context.testmon_lease_acquired, eq=False)
            tm.that(context.report_directory, eq=receipts[0].parent)
            tm.that(context.deadline_monotonic, none=False)
            tm.that(self._read(latest), eq="previous-run\n")
            tm.that(
                tuple(path.name for path in receipts[0].parent.iterdir()),
                eq=("run-context.json",),
            )
        with u.Cli.file_changes_lock(lock).acquire(timeout=0.0):
            after = lock.stat()
            tm.that(
                (after.st_dev, after.st_ino),
                eq=(before.st_dev, before.st_ino),
            )
        tm.fail(runner.testmon_db.exists())

    def test_concurrent_context_publication_precedes_shared_cache_timeout(
        self,
        tmp_path: Path,
    ) -> None:
        """Contenders publish unique contexts before waiting for the shared cache."""
        project = self._zero_test_project(tmp_path)
        policy = config.Infra.tooling.tools.pytest
        runners = tuple(
            self._runner(
                project,
                tmp_path,
                elapsed_seconds=(
                    policy.run_timeout_seconds - policy.termination_grace_seconds
                ),
            )
            for _ in range(2)
        )
        reports = project / runners[0].reports
        latest = reports / "latest.txt"
        cache_lock = runners[0].testmon_db.with_name(
            f"{runners[0].testmon_db.name}.lock",
        )
        pointer_lock = latest.with_name(f"{latest.name}.lock")
        with u.Cli.file_changes_lock(pointer_lock):
            pointer_before = pointer_lock.stat()
        start = Barrier(len(runners))

        def contend(runner: FlextInfraPytestRunner) -> None:
            start.wait(timeout=policy.run_timeout_seconds)
            with pytest.raises(TimeoutError, match=re.escape(str(cache_lock))):
                runner.execute()

        with u.Cli.file_changes_lock(cache_lock):
            cache_before = cache_lock.stat()
            with ThreadPoolExecutor(max_workers=len(runners)) as executor:
                tuple(executor.map(contend, runners))
        receipts = tuple(reports.glob("*/run-context.json"))
        tm.that(len(receipts), eq=len(runners))
        contexts = tuple(
            m.Infra.PytestRunContext.model_validate_json(path.read_bytes())
            for path in receipts
        )
        tm.that(
            {context.testmon_db for context in contexts},
            eq={runners[0].testmon_db},
        )
        tm.that({context.testmon_lease_acquired for context in contexts}, eq={False})
        tm.that(
            {context.report_directory for context in contexts},
            eq={path.parent for path in receipts},
        )
        tm.ok(self._read(latest).strip() in {path.parent.name for path in receipts})
        for lock, before in (
            (pointer_lock, pointer_before),
            (cache_lock, cache_before),
        ):
            after = lock.stat()
            tm.that(
                (after.st_dev, after.st_ino),
                eq=(before.st_dev, before.st_ino),
            )
        tm.fail(runners[0].testmon_db.exists())

    @pytest.mark.slow
    def test_empty_slow_scope_remains_red_with_accounting(
        self,
        tmp_path: Path,
    ) -> None:
        """A requested empty scope is not a successful test execution."""
        project = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        (project / cache.target_directory / "test_budgeted.py").write_text(
            "from zero_sample import VALUE\n\n\n"
            "def test_value() -> None:\n    assert VALUE\n",
            encoding="utf-8",
        )
        tm.that(
            tm.ok(self._runner(project, tmp_path).execute()),
            eq=pytest.ExitCode.OK.value,
        )

        outcome = tm.ok(self._runner(project, tmp_path, slow_phase=True).execute())

        tm.that(outcome, eq=pytest.ExitCode.NO_TESTS_COLLECTED.value)
        summary = self._latest_summary(project / cache.reports_directory)
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            self._read(summary.parent / "selection-plan.json"),
        )
        tm.ok(plan.owns_no_tests)
        accounting = m.Infra.TestmonRunAccounting.model_validate_json(
            self._read(summary.parent / "run-accounting.json"),
        )
        tm.that(accounting.executed_count, eq=0)
        suite = m.Cli.ProcessOutcome.model_validate_json(
            self._read(summary.parent / "suite-outcome.json"),
        )
        tm.that(suite.raw_return_code, eq=outcome)
        tm.that(self._read(summary), has=["outcome=failed\n", f"exit={outcome}\n"])

    @pytest.mark.slow
    def test_incremental_run_publishes_receipt_for_zero_test_project(
        self,
        tmp_path: Path,
    ) -> None:
        """Make test retains native empty-suite status with typed accounting."""
        project = self._zero_test_project(tmp_path)
        runner = self._runner(project, tmp_path)

        outcome = tm.ok(runner.execute())

        tm.that(outcome, eq=pytest.ExitCode.NO_TESTS_COLLECTED.value)
        cache = config.Infra.codegen.make.testmon_cache
        reports_root = project / cache.reports_directory
        summary = self._latest_summary(reports_root)
        context = m.Infra.PytestRunContext.model_validate_json(
            self._read(summary.parent / "run-context.json"),
        )
        tm.that(context.testmon_lease_acquired, eq=True)
        tm.that(context.testmon_db, eq=runner.testmon_db)
        tm.that(self._read(reports_root / "latest.txt"), eq=f"{summary.parent.name}\n")
        accounting = m.Infra.TestmonRunAccounting.model_validate_json(
            self._read(summary.parent / "run-accounting.json"),
        )
        tm.that(accounting.executed_count, eq=0)
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            self._read(summary.parent / "selection-plan.json"),
        )
        tm.ok(plan.owns_no_tests)

    @pytest.mark.slow
    def test_full_run_keeps_native_status_for_zero_test_project(
        self,
        tmp_path: Path,
    ) -> None:
        """One bounded full execution preserves the native empty-suite status.

        FULL derives its inventory from the suite's single collection and must
        execute a nonempty inventory, so an empty project keeps pytest's
        native status without a selection plan or promoted accounting.
        """
        project = self._zero_test_project(tmp_path)
        runner = self._runner(project, tmp_path)

        outcome = tm.ok(runner.execute_full())

        tm.that(outcome, eq=pytest.ExitCode.NO_TESTS_COLLECTED.value)
        cache = config.Infra.codegen.make.testmon_cache
        reports_root = project / cache.reports_directory
        report_dir = reports_root / self._read(reports_root / "latest.txt").strip()
        context = m.Infra.PytestRunContext.model_validate_json(
            self._read(report_dir / "run-context.json"),
        )
        tm.that(context.execution_mode, eq=c.Infra.PytestExecutionMode.FULL)
        tm.that(context.testmon_db, eq=runner.testmon_db)
        tm.that(context.testmon_lease_acquired, eq=True)
        tm.that(
            context.deadline_monotonic,
            eq=runner.started_at_monotonic
            + config.Infra.tooling.tools.pytest.run_timeout_seconds,
        )
        tm.that(len(tuple(reports_root.glob("*/run-context.json"))), eq=1)
        suite = m.Cli.ProcessOutcome.model_validate_json(
            self._read(report_dir / "suite-outcome.json"),
        )
        tm.that(suite.raw_return_code, eq=pytest.ExitCode.NO_TESTS_COLLECTED.value)
        for promoted in ("selection-plan.json", "run-accounting.json"):
            tm.fail((report_dir / promoted).exists())
        summary = self._read(report_dir / "summary.txt").splitlines()
        tm.that(summary, has=["phase=suite", f"exit={outcome}"])
        tm.that(summary, lacks="outcome=passed")

    @pytest.mark.slow
    def test_slow_only_declared_file_executes_its_slow_items(
        self,
        tmp_path: Path,
    ) -> None:
        """A declared file carries its slow items, so a slow-only file runs.

        The file scope never deselects the slow marker: a file whose items are
        all slow executes them instead of ending as an empty scope.
        """
        project = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "test_slow_only.py"
        slow_marker = config.Infra.tooling.tools.pytest.slow_marker
        (project / relative).write_text(
            f"import pytest\n\npytestmark = pytest.mark.{slow_marker}\n\n"
            "def test_slow_item() -> None:\n    assert True\n",
            encoding="utf-8",
        )

        outcome = tm.ok(
            self._runner(project, tmp_path, target_file=relative).execute(),
        )

        tm.that(outcome, eq=pytest.ExitCode.OK.value)
        summary = self._latest_summary(project / cache.reports_directory)
        tm.that(self._read(summary), has=["outcome=executed\n", "executed=1\n"])
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            self._read(summary.parent / "selection-plan.json"),
        )
        tm.fail(plan.owns_no_tests)

    @staticmethod
    @pytest.mark.slow
    def test_conftest_import_failure_preserves_native_startup_status(
        cached_runner_project: Path,
    ) -> None:
        """A failed real conftest import retains status without inventing a suite."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        proof = cached_runner_project / "suite-executed.txt"
        (cached_runner_project / runner.target / "test_runtime.py").write_text(
            "from pathlib import Path\n\n"
            "def test_runtime() -> None:\n"
            f"    Path({str(proof)!r}).write_text('executed', encoding='utf-8')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (cached_runner_project / "conftest.py").write_text(
            "from runner_sample import missing_startup_dependency\n",
            encoding=c.DEFAULT_ENCODING,
        )

        status = tm.ok(runner.execute_full())

        tm.that(status, eq=pytest.ExitCode.USAGE_ERROR.value)
        (context_path,) = (cached_runner_project / runner.reports).glob(
            "*/run-context.json",
        )
        report_dir = context_path.parent
        context = m.Infra.PytestRunContext.model_validate_json(
            context_path.read_bytes(),
        )
        tm.that(context.execution_mode, eq=c.Infra.PytestExecutionMode.FULL)
        tm.that(
            context.deadline_monotonic,
            eq=runner.started_at_monotonic
            + config.Infra.tooling.tools.pytest.run_timeout_seconds,
        )
        # FULL has no separate inventory phase: its one suite collection owns
        # the startup failure, the raw log and the native outcome.
        for phase in ("inventory", "selection"):
            tm.fail((report_dir / f"{phase}-outcome.json").exists())
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (report_dir / "suite-outcome.json").read_bytes(),
        )
        tm.that(outcome.raw_return_code, eq=status)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        raw_log = report_dir / "pytest.log"
        tm.that(
            raw_log.read_text(encoding=c.DEFAULT_ENCODING),
            has=["ImportError", "missing_startup_dependency"],
        )
        summary = (report_dir / "summary.txt").read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            summary.splitlines(),
            has=[
                "phase=suite",
                "inventory_complete=false",
                "diagnostics=not_produced",
                f"exit={status}",
                f"raw_log={raw_log}",
            ],
        )
        tm.that(summary, lacks="collection_errors=0")
        report_log = report_dir / "events.jsonl"
        warning_log = report_log.with_suffix(c.Infra.PYTEST_WARNING_EVENTS_SUFFIX)
        for missing_report in (report_log, warning_log):
            tm.fail(missing_report.exists())
            tm.that(summary.splitlines(), has=f"missing_report={missing_report}")
        tm.fail(proof.exists())
        for absent_artifact in (
            "junit.xml",
            "run-accounting.json",
            "selection-plan.json",
        ):
            tm.fail((report_dir / absent_artifact).exists())

    @pytest.mark.slow
    def test_target_file_collection_failure_stays_red(
        self,
        tmp_path: Path,
    ) -> None:
        """A declared file that fails to collect is not an empty scope."""
        project = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "test_broken.py"
        proof = project / "broken-suite-executed.txt"
        (project / relative).write_text(
            "import not_a_real_collection_module\n\n"
            "from pathlib import Path\n\n"
            "def test_broken() -> None:\n"
            f"    Path({str(proof)!r}).write_text('executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        runner = self._runner(project, tmp_path, target_file=relative)

        status = tm.ok(runner.execute())

        tm.that(status, eq=pytest.ExitCode.INTERRUPTED.value)
        summary = self._latest_summary(project / runner.reports)
        report_dir = summary.parent
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            self._read(report_dir / "inventory-outcome.json"),
        )
        tm.that(outcome.raw_return_code, eq=status)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        diagnostics = m.Infra.PytestDiagnostics.model_validate_json(
            self._read(report_dir / "diagnostics.json"),
        )
        tm.that(
            set(diagnostics.collection_failed_cases),
            eq={relative.as_posix()},
        )
        tm.that(diagnostics.collection_failed_count, gt=0)
        tm.that(diagnostics.reported_node_ids, eq=())
        tm.that(
            self._read(summary),
            has=[
                "outcome=collection_failed\n",
                "suite=not_executed\n",
                f"exit={status}\n",
            ],
        )
        tm.that(
            self._read(report_dir / "testmon-inventory.log"),
            has="not_a_real_collection_module",
        )
        tm.fail(proof.exists())
        tm.fail((report_dir / "suite-outcome.json").exists())
        tm.fail((report_dir / "junit.xml").exists())
        tm.fail((report_dir / "run-accounting.json").exists())

    @pytest.mark.slow
    def test_target_file_failure_stays_red(self, tmp_path: Path) -> None:
        """A declared file whose test fails still fails the phase."""
        project = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "test_red.py"
        (project / relative).write_text(
            "def test_red() -> None:\n    assert False\n",
            encoding="utf-8",
        )

        outcome = tm.ok(
            self._runner(project, tmp_path, target_file=relative).execute(),
        )

        tm.that(outcome, ne=0)

    @pytest.mark.slow
    def test_target_file_rerun_over_a_warm_cache_executes_again(
        self,
        tmp_path: Path,
    ) -> None:
        """A second run of one declared file executes it, never a cache hit.

        The declared file always runs under forceselect, so the restored cache
        selects nothing for it; that empty selection must not be read as a
        cache hit holding executed tests.
        """
        project = self._zero_test_project(tmp_path)
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "test_rerun.py"
        (project / relative).write_text(
            "def test_rerun() -> None:\n    assert True\n",
            encoding="utf-8",
        )
        for _ in range(2):
            outcome = tm.ok(
                self._runner(project, tmp_path, target_file=relative).execute(),
            )
            tm.that(outcome, eq=pytest.ExitCode.OK.value)
            summary = self._latest_summary(project / cache.reports_directory)
            accounting = m.Infra.TestmonRunAccounting.model_validate_json(
                self._read(summary.parent / "run-accounting.json"),
            )
            tm.that(accounting.executed_count, eq=1)

    @staticmethod
    def _read(path: Path) -> str:
        """Read one published receipt through the files facade.

        Returns:
            The resulting ``str``.

        """
        return tm.ok(u.Cli.files_read_text(path))

    @staticmethod
    def _latest_summary(reports_root: Path) -> Path:
        """Return the newest bounded report directory's summary receipt.

        Returns:
            The newest bounded report directory's summary receipt.

        """
        summaries = sorted(
            reports_root.glob("*/summary.txt"),
            key=lambda path: path.stat().st_mtime,
        )
        return summaries[-1]
