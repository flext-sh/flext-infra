"""Profiled pytest runner boundary contracts."""

from __future__ import annotations

import marshal
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_core import r
from flext_infra import c, config, u
from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
from flext_tests import tm

if TYPE_CHECKING:
    from flext_infra import p, t


def _dump_real_profile(path: Path) -> None:
    """Write a .pstats file the stdlib can actually load.

    ``cProfile.Profile().dump_stats(...)`` on a profiler that was never enabled
    emits a 2-byte marshal payload, and ``pstats.Stats`` rejects it with
    "Cannot create or construct a <class 'pstats.Stats'> object". The runner
    renders a real report from this artifact, so the fixture must produce a
    loadable profile.

    The payload is marshalled directly instead of running a live profiler:
    the canonical runner already executes the whole suite under
    ``python -m cProfile``, and CPython allows only one active profiler, so
    enabling a second one raises "Another profiling tool is already active"
    and the fixture would fail for a reason that has nothing to do with the
    behaviour under test.
    """
    callers: dict[tuple[str, int, str], tuple[int, int, float, float]] = {}
    stats = {("tests/sample_test.py", 1, "test_ok"): (1, 1, 0.001, 0.001, callers)}
    path.write_bytes(marshal.dumps(stats))


def _stub_zero_test_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install the single green-zero child fixture used by selection contracts."""

    def fake_run_to_file(*args: object, **kwargs: object) -> p.Result[int]:
        del kwargs
        output_file = args[1]
        assert isinstance(output_file, (str, Path))
        report_dir = Path(output_file).parent
        Path(output_file).write_text("0 selected in 0.01s\n", encoding="utf-8")
        (report_dir / "junit.xml").write_text(
            (
                '<?xml version="1.0"?>'
                '<testsuites><testsuite tests="0" failures="0" errors="0" '
                'skipped="0" time="0.01"/></testsuites>'
            ),
            encoding="utf-8",
        )
        _dump_real_profile(report_dir / "pytest.pstats")
        return r[int].ok(0)

    monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))


def _seed_testmon_execution(root: Path, test_name: str) -> None:
    """Seed the official execution tables for one runner-boundary contract."""
    test_file = root / test_name.partition("::")[0]
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("", encoding="utf-8")
    connection = sqlite3.connect(root / ".testmondata")
    connection.executescript(
        """
        CREATE TABLE test_execution (
            id INTEGER PRIMARY KEY,
            environment_id INTEGER,
            test_name TEXT,
            duration FLOAT,
            failed BIT,
            forced BIT
        );
        CREATE TABLE test_execution_file_fp (
            test_execution_id INTEGER,
            fingerprint_id INTEGER
        );
        """
    )
    connection.execute(
        "INSERT INTO test_execution VALUES (1, 1, ?, 0.01, 0, 0)", (test_name,)
    )
    connection.execute("INSERT INTO test_execution_file_fp VALUES (1, 1)")
    connection.commit()
    connection.close()


class TestsFlextInfraPytestRunner:
    @pytest.fixture(autouse=True)
    def _clear_make_ci_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Local argv contracts assume CI/COV unset unless a test sets them."""
        monkeypatch.delenv(c.Infra.PYTEST_ENV_CI, raising=False)
        monkeypatch.delenv(c.Infra.PYTEST_ENV_COV, raising=False)

    """Prove exact argv, hard deadline propagation, and durable artifacts."""

    @staticmethod
    def _runner(
        root: Path,
        *,
        file: str | None = None,
        match: str | None = None,
        what: str | None = None,
        fail_fast: bool = False,
        started_at_monotonic: float = 100.0,
    ) -> FlextInfraPytestRunner:
        (root / "tests").mkdir(parents=True, exist_ok=True)
        return FlextInfraPytestRunner(
            workspace_root=root,
            started_at_monotonic=started_at_monotonic,
            file=file,
            match=match,
            what=what,
            target="tests",
            reports=".reports/tests",
            fail_fast=fail_fast,
        )

    def test_focused_argv_preserves_nodeid_and_disables_parallel_coverage(
        self, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "tests" / "sample % test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        nodeid = "tests/sample % test.py::TestsSample::test exact"
        runner = self._runner(tmp_path, file=nodeid, match="exact")
        report_dir = tmp_path / ".reports" / "tests" / "run"

        command = runner.build_command(report_dir)

        tm.that(command, has=[nodeid, "-k", "exact", "-n", "0"])
        tm.that(command, has="--no-cov")
        tm.that(command, has=["--testmon", "--testmon-forceselect"])
        tm.that(command, lacks="--dist")
        tm.that(command, lacks="PYTEST_ARGS")

    def test_focused_green_child_with_zero_executed_tests_fails_loudly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = tmp_path / "tests" / "sample_test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        runner = self._runner(tmp_path, file="tests/sample_test.py")
        _stub_zero_test_run(monkeypatch)

        result = runner.execute()

        tm.fail(result, has="pytest completed without executing tests")

    def test_unfiltered_testmon_cache_hit_rejects_zero_executed_tests(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_testmon_execution(tmp_path, "tests/unit/test_fast.py::test_fast")
        runner = self._runner(tmp_path, what="full")
        _stub_zero_test_run(monkeypatch)

        result = runner.execute()

        tm.fail(result, has="pytest completed without executing tests")

    def test_full_argv_is_config_derived_and_profiled(self, tmp_path: Path) -> None:
        runner = self._runner(tmp_path)
        report_dir = tmp_path / ".reports" / "tests" / "run"
        policy = config.Infra.tooling.tools.pytest

        command = runner.build_command(report_dir)

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
        """pytest-benchmark warns at configure time when xdist is active.

        Projects set ``filterwarnings = ["error"]``, which promotes that warning
        to an INTERNALERROR before a single test runs, so the whole suite is
        unrunnable in parallel. pytest-benchmark cannot measure anything under
        xdist anyway, so the parallel argv asks for that outcome explicitly
        instead of letting the plugin abort the session announcing it.
        """
        runner = self._runner(tmp_path)
        report_dir = tmp_path / ".reports" / "tests" / "run"

        command = runner.build_command(report_dir)

        tm.that(command, has="--benchmark-disable")

    def test_fail_fast_full_run_uses_one_process_and_stops_after_first_failure(
        self, tmp_path: Path
    ) -> None:
        """Prevent already-running xdist workers from reporting later failures."""
        runner = self._runner(tmp_path, fail_fast=True)
        report_dir = tmp_path / ".reports" / "tests" / "run"

        command = runner.build_command(report_dir)

        tm.that(command, has=["-x", "-n", "0"])
        tm.that(command, lacks="--dist")
        tm.that(command, lacks="--benchmark-disable")

    def test_focused_run_keeps_benchmarks_enabled(self, tmp_path: Path) -> None:
        """A focused run is single-process, so benchmarks stay measurable."""
        test_file = tmp_path / "tests" / "sample.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        runner = self._runner(tmp_path, file="tests/sample.py")
        report_dir = tmp_path / ".reports" / "tests" / "run"

        command = runner.build_command(report_dir)

        tm.that(command, lacks="--benchmark-disable")

    def test_environment_rejects_free_form_pytest_args(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(c.Infra.PYTEST_ENV_ARGS, "-o addopts=")
        monkeypatch.setenv(c.Infra.PYTEST_ENV_FILES, "")

        with pytest.raises(ValueError, match="PYTEST_ARGS is forbidden"):
            FlextInfraPytestRunner.from_environment(started_at_monotonic=1.0)

    def test_execute_passes_one_absolute_deadline_and_writes_regular_latest_pointer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        started = 100.0
        runner = self._runner(tmp_path, started_at_monotonic=started)
        captured: dict[str, p.Cli.ProcessDeadline] = {}
        observed_live: t.MutableSequenceOf[bool] = []
        observed_pythonpath: t.MutableSequenceOf[str] = []

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            del cwd, timeout, input_data, remove_env_keys
            tm.that(cmd, has=["-m", "cProfile", "-m", "pytest"])
            tm.that(deadline is not None, eq=True)
            if deadline is not None:
                captured["deadline"] = deadline
            observed_live.append(live)
            assert env is not None
            observed_pythonpath.append(env[c.Infra.ORCHESTRATOR_ENV_PYTHONPATH])
            log_path = Path(output_file)
            report_dir = log_path.parent
            log_path.write_text("1 passed in 0.01s\n", encoding="utf-8")
            (report_dir / "junit.xml").write_text(
                (
                    '<?xml version="1.0"?>'
                    '<testsuites><testsuite tests="1" failures="0" errors="0" '
                    'skipped="0" time="0.01"><testcase classname="Tests" '
                    'name="test_ok" time="0.01"/></testsuite></testsuites>'
                ),
                encoding="utf-8",
            )
            (report_dir / "coverage.xml").write_text("<coverage/>", encoding="utf-8")
            _dump_real_profile(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code: int = tm.ok(runner.execute())

        policy = config.Infra.tooling.tools.pytest
        deadline = captured["deadline"]
        tm.that(exit_code, eq=0)
        tm.that(deadline.expires_at_monotonic, eq=started + policy.run_timeout_seconds)
        tm.that(deadline.termination_grace_seconds, eq=policy.termination_grace_seconds)
        tm.that(observed_live, eq=[True])
        tm.that(observed_pythonpath, eq=[str(tmp_path / c.Infra.DEFAULT_SRC_DIR)])
        latest = tmp_path / ".reports" / "tests" / "latest.txt"
        tm.that(latest.is_file(), eq=True)
        tm.that(latest.is_symlink(), eq=False)

    def test_full_run_fails_when_coverage_artifact_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A zero pytest status cannot mask a missing full-suite coverage report."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_COV, "Y")
        runner = self._runner(tmp_path, what="all")

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            del cmd, cwd, timeout, env, remove_env_keys, input_data, live, deadline
            log_path = Path(output_file)
            report_dir = log_path.parent
            log_path.write_text("1 passed in 0.01s\n", encoding="utf-8")
            (report_dir / "junit.xml").write_text(
                (
                    '<?xml version="1.0"?>'
                    '<testsuites><testsuite tests="1" failures="0" errors="0" '
                    'skipped="0" time="0.01"><testcase classname="Tests" '
                    'name="test_ok" time="0.01"/></testsuite></testsuites>'
                ),
                encoding="utf-8",
            )
            _dump_real_profile(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        result = runner.execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="coverage report was not generated or is empty")

    def test_full_run_fails_when_coverage_fail_under_prints_with_exit_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pytest-cov under xdist must not hide fail-under behind a zero exit."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_COV, "Y")
        runner = self._runner(tmp_path, what="all")

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            del cmd, cwd, timeout, env, remove_env_keys, input_data, live, deadline
            log_path = Path(output_file)
            report_dir = log_path.parent
            log_path.write_text(
                "ERROR: Coverage failure: total of 43.04 is less than fail-under=45.00\n",
                encoding="utf-8",
            )
            (report_dir / "junit.xml").write_text(
                (
                    '<?xml version="1.0"?>'
                    '<testsuites><testsuite tests="1" failures="0" errors="0" '
                    'skipped="0" time="0.01"><testcase classname="Tests" '
                    'name="test_ok" time="0.01"/></testsuite></testsuites>'
                ),
                encoding="utf-8",
            )
            (report_dir / "coverage.xml").write_text("<coverage/>", encoding="utf-8")
            _dump_real_profile(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        result = runner.execute()

        tm.that(result.failure, eq=True)
        tm.that(
            result.error or "",
            has="coverage fail-under reported while pytest exit was 0",
        )

    def test_focused_run_records_coverage_as_not_generated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Focused selectors remain truthful while intentionally disabling coverage."""
        test_file = tmp_path / "tests" / "sample_test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        runner = self._runner(tmp_path, file="tests/sample_test.py")

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            del cmd, cwd, timeout, env, remove_env_keys, input_data, live, deadline
            log_path = Path(output_file)
            report_dir = log_path.parent
            log_path.write_text("1 passed in 0.01s\n", encoding="utf-8")
            (report_dir / "junit.xml").write_text(
                (
                    '<?xml version="1.0"?>'
                    '<testsuites><testsuite tests="1" failures="0" errors="0" '
                    'skipped="0" time="0.01"><testcase classname="Tests" '
                    'name="test_ok" time="0.01"/></testsuite></testsuites>'
                ),
                encoding="utf-8",
            )
            _dump_real_profile(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code: int = tm.ok(runner.execute())
        latest = (
            (tmp_path / ".reports" / "tests" / "latest.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        summary = (tmp_path / ".reports" / "tests" / latest / "summary.txt").read_text(
            encoding="utf-8"
        )

        tm.that(exit_code, eq=0)
        tm.that(summary, has="coverage=not-generated")

    def test_timeout_preserves_exit_124_without_partial_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A killed child remains a precise timeout instead of a report error."""
        runner = self._runner(tmp_path)

        def fake_run_to_file(
            cmd: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            del cmd, cwd, timeout, env, remove_env_keys, input_data, live, deadline
            Path(output_file).write_text(
                "pytest invocation reached hard timeout\n", encoding="utf-8"
            )
            return r[int].ok(c.Infra.PROCESS_TIMEOUT_EXIT_CODE)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code: int = tm.ok(runner.execute())
        latest = (
            (tmp_path / ".reports" / "tests" / "latest.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        summary = (tmp_path / ".reports" / "tests" / latest / "summary.txt").read_text(
            encoding="utf-8"
        )

        tm.that(exit_code, eq=c.Infra.PROCESS_TIMEOUT_EXIT_CODE)
        tm.that(
            summary,
            has=[
                f"exit={c.Infra.PROCESS_TIMEOUT_EXIT_CODE}",
                "state=TIMED_OUT",
                "junit=not-generated",
                "coverage=not-generated",
            ],
        )

    def test_summary_uses_effective_failure_exit_from_diagnostics(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A zero child status cannot produce a green summary for failed JUnit."""
        runner = self._runner(tmp_path)

        def fake_run_to_file(*args: object, **kwargs: object) -> p.Result[int]:
            del kwargs
            output_file = args[1]
            assert isinstance(output_file, (str, Path))
            log_path = Path(output_file)
            report_dir = log_path.parent
            log_path.write_text("1 failed in 0.01s\n", encoding="utf-8")
            (report_dir / "junit.xml").write_text(
                (
                    '<?xml version="1.0"?>'
                    '<testsuites><testsuite tests="1" failures="1" errors="0" '
                    'skipped="0" time="0.01"><testcase classname="Tests" '
                    'name="test_bad" time="0.01"><failure message="boom">'
                    "assert false</failure></testcase></testsuite></testsuites>"
                ),
                encoding="utf-8",
            )
            _dump_real_profile(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code: int = tm.ok(runner.execute())
        summary_path = next((tmp_path / ".reports" / "tests").glob("*/summary.txt"))
        summary = summary_path.read_text(encoding="utf-8")

        tm.that(exit_code, eq=1)
        tm.that(summary, has=["failed=1", "exit=1", "state=COMPLETED"])

    def test_local_full_argv_keeps_testmon_without_coverage(
        self, tmp_path: Path
    ) -> None:
        runner = self._runner(tmp_path, what="all")
        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")
        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, lacks="--cov-report")
        tm.that(any(arg == "--cov" for arg in command), eq=False)

    def test_cov_y_disables_testmon_and_enables_coverage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(c.Infra.PYTEST_ENV_COV, "Y")
        runner = self._runner(tmp_path, what="all")
        report_dir = tmp_path / ".reports" / "tests" / "run"
        command = runner.build_command(report_dir)
        tm.that(command, has=["--cov", "--no-cov-on-fail"])
        tm.that(any(arg.startswith("--cov-report=xml:") for arg in command), eq=True)
        tm.that(command, lacks="--testmon")
        tm.that(command, lacks="--no-cov")

    def test_cov_y_forbids_focused_selectors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(c.Infra.PYTEST_ENV_COV, "Y")
        test_file = tmp_path / "tests" / "sample_test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        runner = self._runner(tmp_path, file="tests/sample_test.py", what="all")
        with pytest.raises(ValueError, match="COV=Y forbids FILE=/MATCH="):
            runner.build_command(tmp_path / ".reports" / "tests" / "run")

    def test_ci_y_keeps_unfiltered_testmon(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, config.Infra.codegen.make.ci.value)
        runner = self._runner(tmp_path, what="all")
        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")
        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, lacks="--cov-report")
        tm.that("not docker and not remote" not in command, eq=True)

    def test_ci_true_keeps_default_testmon_without_coverage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GitHub default CI=true must not match the Make token CI=Y."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, "true")
        runner = self._runner(tmp_path, what="all")
        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")
        tm.that(command, has=["--testmon", "--no-cov"])
        tm.that(command, lacks="not docker and not remote")

    def test_local_full_argv_keeps_docker_remote_markers_selected(
        self, tmp_path: Path
    ) -> None:
        """Without CI=Y the runner must not deselect docker/remote suites."""
        runner = self._runner(tmp_path, what="all")
        command = runner.build_command(tmp_path / ".reports" / "tests" / "run")
        tm.that(command, lacks="not docker and not remote")

    def test_cache_status_skips_pytest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db = tmp_path / ".testmondata"
        db.write_bytes(b"not-a-real-db-but-nonempty")
        runner = self._runner(tmp_path, what="cache-status")
        called: list[bool] = []

        def fake_run_to_file(*args: object, **kwargs: object) -> p.Result[int]:
            del args, kwargs
            called.append(True)
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))
        exit_code: int = tm.ok(runner.execute())
        tm.that(exit_code, eq=0)
        tm.that(called, eq=[])
