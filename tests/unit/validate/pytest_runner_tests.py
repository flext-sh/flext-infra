"""Profiled pytest runner boundary contracts."""

from __future__ import annotations

import cProfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_core import r
from flext_infra import c, config, u
from flext_infra.validate.pytest_runner import FlextInfraPytestRunner
from flext_tests import tm

if TYPE_CHECKING:
    from flext_infra import p, t


class TestsFlextInfraPytestRunner:
    """Prove exact argv, hard deadline propagation, and durable artifacts."""

    @staticmethod
    def _runner(
        root: Path,
        *,
        file: str | None = None,
        match: str | None = None,
        started_at_monotonic: float = 100.0,
    ) -> FlextInfraPytestRunner:
        (root / "tests").mkdir(parents=True, exist_ok=True)
        return FlextInfraPytestRunner(
            workspace_root=root,
            started_at_monotonic=started_at_monotonic,
            file=file,
            match=match,
            target="tests",
            reports=".reports/tests",
        )

    def test_focused_argv_preserves_nodeid_and_disables_parallel_coverage(
        self, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "tests" / "sample % test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("", encoding="utf-8")
        nodeid = "tests/sample % test.py::TestsSample::test exact"
        runner = self._runner(tmp_path, file=nodeid, match="exact and not slow")
        report_dir = tmp_path / ".reports" / "tests" / "run"

        command = runner.build_command(report_dir)

        tm.that(command, has=[nodeid, "-k", "exact and not slow", "-n", "0"])
        tm.that(command, has="--no-cov")
        tm.that(command, lacks="--dist")
        tm.that(command, lacks="PYTEST_ARGS")

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
                "--cov",
                "-n",
                str(policy.parallel_workers),
                "--dist",
                policy.parallel_distribution,
                f"--timeout={policy.case_timeout_seconds}",
                "-p",
                policy.enforcement_plugin,
            ],
        )

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
        observed_remove_keys: t.MutableSequenceOf[t.StrSequence] = []

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
            del cwd, timeout, env, input_data
            tm.that(cmd, has=["-m", "cProfile", "-m", "pytest"])
            tm.that(deadline is not None, eq=True)
            if deadline is not None:
                captured["deadline"] = deadline
            observed_live.append(live)
            observed_remove_keys.append(tuple(remove_env_keys))
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
            cProfile.Profile().dump_stats(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code = tm.ok(runner.execute())

        policy = config.Infra.tooling.tools.pytest
        deadline = captured["deadline"]
        tm.that(exit_code, eq=0)
        tm.that(deadline.expires_at_monotonic, eq=started + policy.run_timeout_seconds)
        tm.that(deadline.termination_grace_seconds, eq=policy.termination_grace_seconds)
        tm.that(observed_live, eq=[True])
        tm.that(
            observed_remove_keys, eq=[tuple(c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS)]
        )
        latest = tmp_path / ".reports" / "tests" / "latest.txt"
        tm.that(latest.is_file(), eq=True)
        tm.that(latest.is_symlink(), eq=False)

    def test_full_run_fails_when_coverage_artifact_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A zero pytest status cannot mask a missing full-suite coverage report."""
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
            cProfile.Profile().dump_stats(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        result = runner.execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="coverage report was not generated or is empty")

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
            cProfile.Profile().dump_stats(report_dir / "pytest.pstats")
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))

        exit_code = tm.ok(runner.execute())
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

        exit_code = tm.ok(runner.execute())
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
