"""Behavior contract for the profiled pytest runner.

Reference example for FLEXT test law: every case drives the public runner API
against real project trees on disk. Nothing about the system under test is
mocked, patched, or stubbed — argv contracts are asserted through the public
``build_command`` against the typed pytest policy, and side-effecting behavior
(cache maintenance, boundary rejection) is proven by real filesystem and
environment state. End-to-end child execution belongs to the integration
suite, because a profiled pytest child exceeds the unit case deadline.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config
from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

_PASSING_TEST_BODY = "def test_ok() -> None:\n    assert True\n"


class TestsFlextInfraPytestRunner:
    """Prove argv derivation, real execution artifacts, and cache maintenance."""

    @pytest.fixture(autouse=True)
    def _clear_make_ci_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Local contracts assume the Make CI token is unset unless a case sets it."""
        monkeypatch.delenv(c.Infra.PYTEST_ENV_CI, raising=False)

    @staticmethod
    def _project(root: Path) -> Path:
        """Materialize a real, runnable pytest project under ``root``."""
        tests_dir = root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / "test_sample.py"
        test_file.write_text(_PASSING_TEST_BODY, encoding="utf-8")
        return test_file

    @staticmethod
    def _runner(
        root: Path,
        *,
        file: str | None = None,
        match: str | None = None,
        what: str | None = None,
        started_at_monotonic: float | None = None,
    ) -> FlextInfraPytestRunner:
        """Build the runner exactly as the Make boundary constructs it."""
        (root / "tests").mkdir(parents=True, exist_ok=True)
        return FlextInfraPytestRunner(
            workspace_root=root,
            started_at_monotonic=(
                time.monotonic() if started_at_monotonic is None
                else started_at_monotonic
            ),
            file=file,
            match=match,
            what=what,
            target="tests",
            reports=".reports/tests",
        )

    @staticmethod
    def _runner_reports_root(root: Path) -> Path:
        """Return the reports root the runner owns for this project."""
        return root / ".reports" / "tests"

    def test_focused_argv_preserves_nodeid_and_disables_parallel_coverage(
        self, tmp_path: Path
    ) -> None:
        """A focused selector runs single-process and keeps the exact nodeid."""
        test_file = tmp_path / "tests" / "sample % test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(_PASSING_TEST_BODY, encoding="utf-8")
        nodeid = "tests/sample % test.py::TestsSample::test exact"
        runner = self._runner(tmp_path, file=nodeid, match="exact and not slow")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, has=[nodeid, "-k", "exact and not slow", "-n", "0"])
        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, lacks="--dist")
        tm.that(command, lacks="PYTEST_ARGS")

    def test_full_argv_is_config_derived_and_profiled(self, tmp_path: Path) -> None:
        """Every argv element comes from the typed pytest policy, never literals."""
        runner = self._runner(tmp_path)
        policy = config.Infra.tooling.tools.pytest

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(
            command,
            has=[
                "-m",
                "cProfile",
                "-m",
                "pytest",
                "--testmon",
                "--no-cov",
                "-n",
                str(policy.parallel_workers),
                "--dist",
                policy.parallel_distribution,
                f"--timeout={policy.case_timeout_seconds}",
                "-p",
                policy.enforcement_plugin,
            ],
        )
        tm.that(command, lacks="--cov-report")

    def test_parallel_run_disables_benchmarks(self, tmp_path: Path) -> None:
        """Benchmarks cannot measure under xdist, so the parallel argv disables them."""
        runner = self._runner(tmp_path)

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, has="--benchmark-disable")

    def test_focused_run_keeps_benchmarks_enabled(self, tmp_path: Path) -> None:
        """A focused run is single-process, so benchmarks stay measurable."""
        self._project(tmp_path)
        runner = self._runner(tmp_path, file="tests/test_sample.py")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, lacks="--benchmark-disable")

    def test_local_incremental_argv_keeps_testmon_without_coverage(
        self, tmp_path: Path
    ) -> None:
        """The incremental selector never enforces the full-suite coverage gate."""
        runner = self._runner(tmp_path, what="all")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, lacks="--cov-report")

    def test_ci_y_disables_coverage_and_deselects_docker_and_remote(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The Make CI token deselects environment-bound suites."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, config.Infra.codegen.make.ci.value)
        runner = self._runner(tmp_path, what="all")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, has=["-m", "not docker and not remote"])

    def test_ci_true_is_not_the_make_ci_token(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GitHub's default ``CI=true`` must not match the Make token ``CI=Y``."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, "true")
        runner = self._runner(tmp_path, what="all")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, lacks="not docker and not remote")

    def test_local_run_keeps_docker_remote_markers_selected(
        self, tmp_path: Path
    ) -> None:
        """Without the CI token the runner must not deselect any suite."""
        runner = self._runner(tmp_path, what="all")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        tm.that(command, lacks="not docker and not remote")

    def test_environment_rejects_free_form_pytest_args(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Free-form pytest arguments are refused at the environment boundary."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_ARGS, "-o addopts=")
        monkeypatch.setenv(c.Infra.PYTEST_ENV_FILES, "")

        with pytest.raises(ValueError, match="PYTEST_ARGS is forbidden"):
            FlextInfraPytestRunner.from_environment(started_at_monotonic=1.0)

    def test_ci_y_forbids_pytest_execute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CI workflows must never execute the suite through this runner."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, config.Infra.codegen.make.ci.value)
        runner = self._runner(tmp_path, what="all")

        tm.fail(runner.execute(), has="forbidden under CI=Y")

    def test_report_directory_is_created_under_the_project_reports_root(
        self, tmp_path: Path
    ) -> None:
        """Report directories stay inside the project's declared reports root."""
        runner = self._runner(tmp_path, what="all")

        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")

        junit_argument = next(
            argument for argument in command if argument.startswith("--junitxml=")
        )
        tm.that(junit_argument, has=str(tmp_path / ".reports" / "tests" / "run"))

    def test_reports_and_target_reject_paths_escaping_the_project(
        self, tmp_path: Path
    ) -> None:
        """A selector may never point outside the project it validates."""
        (tmp_path / "tests").mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="normalized repository-relative path"):
            FlextInfraPytestRunner(
                workspace_root=tmp_path,
                started_at_monotonic=time.monotonic(),
                target="../tests",
                reports=".reports/tests",
            )

    def test_cache_status_reports_the_database_without_running_pytest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Cache maintenance answers from the database and never spawns pytest."""
        database = tmp_path / ".testmondata"
        database.write_bytes(b"not-a-real-db-but-nonempty")
        runner = self._runner(tmp_path, what="cache-status")

        exit_code: int = tm.ok(runner.execute())

        tm.that(exit_code, eq=0)
        tm.that(capsys.readouterr().out, has=[str(database), "exists=True"])
        tm.that((tmp_path / ".reports" / "tests").exists(), eq=False)

    def test_cache_clear_requires_the_apply_token(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Destroying the local cache is guarded by the Make apply token."""
        monkeypatch.delenv(config.Infra.codegen.make.apply_variable, raising=False)
        runner = self._runner(tmp_path, what="cache-clear")

        tm.fail(runner.execute(), has="cache-clear requires")

    def test_cache_clear_removes_every_database_artifact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With the apply token the cache and its sidecars are removed."""
        database = tmp_path / ".testmondata"
        write_ahead_log = tmp_path / ".testmondata-wal"
        database.write_bytes(b"db")
        write_ahead_log.write_bytes(b"wal")
        monkeypatch.setenv(
            config.Infra.codegen.make.apply_variable,
            config.Infra.codegen.make.apply_value,
        )
        runner = self._runner(tmp_path, what="cache-clear")

        exit_code: int = tm.ok(runner.execute())

        tm.that(exit_code, eq=0)
        tm.that(database.exists(), eq=False)
        tm.that(write_ahead_log.exists(), eq=False)
