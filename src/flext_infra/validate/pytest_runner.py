"""Typed, profiled pytest execution under one absolute process deadline."""

from __future__ import annotations

import os
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Self, override

from flext_core import r
from pydantic import model_validator

from flext_infra import c, config, m, u
from flext_infra.base import s
from flext_infra.validate.cprofile_report import FlextInfraCProfileReport
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
from flext_infra.validate.pytest_selector import FlextInfraPytestSelectorValidator

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraPytestRunner(s[int]):
    """Run one exact pytest request and persist its performance evidence."""

    started_at_monotonic: Annotated[
        float,
        m.Field(gt=0, description="Monotonic timestamp captured before FLEXT imports."),
    ]
    file: Annotated[
        str | None, m.Field(default=None, description="Exact pytest file or nodeid.")
    ] = None
    match: Annotated[
        str | None, m.Field(default=None, description="Exact pytest -k expression.")
    ] = None
    what: Annotated[
        str | None, m.Field(default=None, description="Exact pytest execution mode.")
    ] = None
    target: Annotated[
        str, m.Field(min_length=1, description="Default repository-relative test root.")
    ]
    reports: Annotated[
        Path, m.Field(description="Repository-relative test report root.")
    ]
    fail_fast: Annotated[bool, m.Field(description="Stop after the first failure.")] = (
        False
    )
    verbose: Annotated[bool, m.Field(description="Expose child output live.")] = False
    diagnostic: Annotated[
        bool, m.Field(description="Use expanded pytest diagnostics.")
    ] = False

    @staticmethod
    def _environment_value(name: str) -> str:
        """Read one runner input through the canonical environment facade."""
        return u.Cli.env_read(name).unwrap().strip()

    @staticmethod
    def _environment_flag(name: str) -> bool:
        """Parse one strict Make boolean without accepting arbitrary text."""
        raw = FlextInfraPytestRunner._environment_value(name)
        if raw in {"", "0", "N"}:
            return False
        if raw in {"1", "Y"}:
            return True
        msg = f"{name} must be empty, 0, 1, N, or Y"
        raise ValueError(msg)

    @classmethod
    def from_environment(cls, *, started_at_monotonic: float) -> Self:
        """Parse the exact Make-owned environment boundary once."""
        raw_args = cls._environment_value(c.Infra.PYTEST_ENV_ARGS)
        raw_files = cls._environment_value(c.Infra.PYTEST_ENV_FILES)
        if raw_args:
            msg = "PYTEST_ARGS is forbidden; use typed FILE, MATCH, and WHAT selectors"
            raise ValueError(msg)
        if raw_files:
            msg = "FILES is forbidden for pytest; use one exact FILE selector"
            raise ValueError(msg)
        return cls(
            workspace_root=Path.cwd(),
            started_at_monotonic=started_at_monotonic,
            file=cls._environment_value(c.Infra.PYTEST_ENV_FILE) or None,
            match=cls._environment_value(c.Infra.PYTEST_ENV_MATCH) or None,
            what=cls._environment_value(c.Infra.PYTEST_ENV_WHAT) or None,
            target=cls._environment_value(c.Infra.PYTEST_ENV_TARGET),
            reports=Path(cls._environment_value(c.Infra.PYTEST_ENV_REPORTS)),
            fail_fast=cls._environment_flag(c.Infra.PYTEST_ENV_FAIL_FAST),
            verbose=cls._environment_flag(c.Infra.PYTEST_ENV_VERBOSE),
            diagnostic=cls._environment_flag(c.Infra.PYTEST_ENV_DIAG),
        )

    @model_validator(mode="after")
    def _validate_paths_and_selectors(self) -> Self:
        """Reject selector and output paths that escape the active project."""
        selector = FlextInfraPytestSelectorValidator(
            workspace_root=self.workspace_root,
            file=self.file,
            match=self.match,
            what=self.what,
        )
        resolved_selector = selector.execute()
        if resolved_selector.failure:
            raise ValueError(resolved_selector.error or "invalid pytest selector")
        paths: tuple[tuple[str, Path, str], ...] = (
            ("target", Path(self.target), self.target),
            ("reports", self.reports, self.reports.as_posix()),
        )
        for field_name, path, raw_value in paths:
            if (
                not path.parts
                or path.is_absolute()
                or any(part in {"", ".", ".."} for part in path.parts)
                or any(character in raw_value for character in "\0\r\n")
            ):
                msg = f"{field_name} must be a normalized repository-relative path"
                raise ValueError(msg)
        target_result = FlextInfraPytestSelectorValidator.resolve_file(
            self.workspace_root, self.target
        )
        if target_result.failure:
            raise ValueError(target_result.error or "invalid pytest target")
        return self

    def _report_directory(self) -> p.Result[Path]:
        """Create one collision-resistant report directory under the project."""
        run_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S.%fZ") + f"-{os.getpid()}"
        try:
            workspace_root = Path(self.workspace_root).resolve()
            report_root = (workspace_root / self.reports).resolve()
        except (OSError, RuntimeError) as exc:
            return r[Path].fail_op("resolve pytest report directory", exc)
        if not report_root.is_relative_to(workspace_root):
            return r[Path].fail(f"reports path escapes workspace: {self.reports}")
        report_dir = report_root / run_id
        return u.Cli.ensure_dir(report_dir)

    def build_command(self, report_dir: Path) -> tuple[str, ...]:
        """Build the exact child argv from the typed tooling policy."""
        pytest = config.Infra.tooling.tools.pytest
        focused = self.file is not None or self.match is not None
        target = self.file or self.target
        report_args = pytest.diagnostic_args if self.diagnostic else pytest.report_args
        coverage_args = (
            ("--no-cov",)
            if focused
            else ("--cov", f"--cov-report=xml:{report_dir / 'coverage.xml'}")
        )
        parallel_args = (
            ("-n", "0")
            if focused
            else (
                "-n",
                str(pytest.parallel_workers),
                "--dist",
                pytest.parallel_distribution,
                # pytest-benchmark disables itself under xdist and warns while
                # configuring. Projects run filterwarnings=["error"], which
                # turns that warning into an INTERNALERROR before collection.
                # Asking for the same outcome up front keeps the run truthful:
                # benchmarks are off because the run is parallel, not silenced.
                "--benchmark-disable",
            )
        )
        optional_args = (
            *(("-k", self.match) if self.match is not None else ()),
            *(("-x",) if self.fail_fast else ()),
        )
        return (
            sys.executable,
            "-m",
            "cProfile",
            "-o",
            str(report_dir / "pytest.pstats"),
            "-m",
            "pytest",
            target,
            *pytest.progress_args,
            *report_args,
            "-p",
            pytest.enforcement_plugin,
            "-p",
            "no:metadata",
            f"--timeout={pytest.case_timeout_seconds}",
            f"--junitxml={report_dir / 'junit.xml'}",
            *coverage_args,
            *parallel_args,
            *optional_args,
        )

    @staticmethod
    def _write_diagnostic_files(
        report_dir: Path, diagnostics: m.Infra.PytestDiagnostics
    ) -> None:
        """Persist the existing typed diagnostic model without another CLI process."""
        outputs: tuple[tuple[str, t.StrSequence, str], ...] = (
            ("failed-tests.txt", diagnostics.failed_cases, "\n\n"),
            ("errors.txt", diagnostics.error_traces, "\n\n"),
            ("warnings.txt", diagnostics.warning_lines, "\n"),
            ("slowest-tests.txt", diagnostics.slow_entries, "\n"),
            ("skipped-tests.txt", diagnostics.skip_cases, "\n"),
        )
        for filename, values, separator in outputs:
            u.Cli.atomic_write_text_file(
                report_dir / filename, separator.join(values) + ("\n" if values else "")
            ).unwrap()

    def _extract_diagnostics(
        self, report_dir: Path
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Compose the existing JUnit/log diagnostic owner in-process."""
        extractor = FlextInfraPytestDiagExtractor(
            workspace_root=self.root,
            junit=report_dir / "junit.xml",
            log_path=report_dir / "pytest.log",
        )
        return extractor.extract(extractor.junit, extractor.log_path)

    @override
    def execute(self) -> p.Result[int]:
        """Execute pytest, profile it, and preserve reports under one deadline."""
        pytest = config.Infra.tooling.tools.pytest
        report_dir_result = self._report_directory()
        if report_dir_result.failure:
            return r[int].fail(
                report_dir_result.error or "pytest report directory validation failed"
            )
        report_dir = report_dir_result.value
        command = self.build_command(report_dir)
        u.Cli.atomic_write_text_file(
            report_dir / "command.txt", f"{shlex.join(command)}\n"
        ).unwrap()
        deadline = m.Cli.ProcessDeadline(
            expires_at_monotonic=(
                self.started_at_monotonic + pytest.run_timeout_seconds
            ),
            termination_grace_seconds=pytest.termination_grace_seconds,
            timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
        )
        run_result = u.Cli.run_to_file(
            command,
            report_dir / "pytest.log",
            cwd=self.workspace_root,
            remove_env_keys=c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS,
            live=True,
            deadline=deadline,
        )
        if run_result.failure:
            return r[int].fail(run_result.error or "pytest process execution failed")
        exit_code = run_result.value
        profile_result = FlextInfraCProfileReport(
            workspace_root=self.root,
            profile=report_dir / "pytest.pstats",
            output=report_dir / "pytest-profile.txt",
            sort=pytest.profile_sort,
            limit=pytest.profile_limit,
        ).execute()
        if profile_result.failure and exit_code == 0:
            return r[int].fail(profile_result.error or "cProfile report failed")
        diagnostics_result = self._extract_diagnostics(report_dir)
        if diagnostics_result.failure:
            return r[int].fail(
                diagnostics_result.error or "pytest diagnostic extraction failed"
            )
        diagnostics = diagnostics_result.value
        self._write_diagnostic_files(report_dir, diagnostics)
        timed_out = exit_code in {
            c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
            c.Infra.PROCESS_SIGNAL_EXIT_OFFSET + 9,
        }
        timeout_state = "TIMED_OUT" if timed_out else "COMPLETED"
        junit_file = report_dir / "junit.xml"
        coverage_file = report_dir / "coverage.xml"
        junit_value = str(junit_file) if junit_file.is_file() else "not-generated"
        coverage_value = (
            str(coverage_file) if coverage_file.is_file() else "not-generated"
        )
        summary = (
            f"junit={junit_value}\n"
            f"coverage={coverage_value}\n"
            f"failed={diagnostics.failed_count}\n"
            f"errors={diagnostics.error_count}\n"
            f"warnings={diagnostics.warning_count}\n"
            f"skipped={diagnostics.skipped_count}\n"
            f"exit={exit_code}\n"
            f"state={timeout_state}\n"
        )
        u.Cli.atomic_write_text_file(report_dir / "summary.txt", summary).unwrap()
        latest_path = report_dir.parent / "latest.txt"
        u.Cli.atomic_write_text_file(latest_path, f"{report_dir.name}\n").unwrap()
        if exit_code == 0 and any((
            diagnostics.failed_count,
            diagnostics.error_count,
            diagnostics.warning_count,
            diagnostics.skipped_count,
        )):
            exit_code = 1
        if (
            exit_code == 0
            and self.file is None
            and self.match is None
            and (not coverage_file.is_file() or coverage_file.stat().st_size == 0)
        ):
            return r[int].fail(
                f"coverage report was not generated or is empty: {coverage_file}"
            )
        sys.stderr.write(f"Reports: {report_dir} (latest: {latest_path})\n")
        if timed_out:
            sys.stderr.write(
                "ERROR: pytest invocation reached the configured hard wall "
                f"{pytest.run_timeout_seconds}s (exit={exit_code})\n"
            )
        return r[int].ok(exit_code)


__all__: list[str] = ["FlextInfraPytestRunner"]
