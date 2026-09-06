"""Dependency detector report behavior tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra.deps.detector_runtime import FlextInfraDependencyDetectorRuntime
from flext_tests import tm
from tests import TestsFlextInfraUtilities as u, m, p, t


class _DetectorStub:
    """Minimal stub satisfying p.Infra.DetectorRuntime for report tests."""

    def __init__(self, deps: u.Tests.DepsReportStub) -> None:
        self.deps: p.Infra.DepsService = deps
        self.runner: p.Infra.RunnerService = u.Cli
        self.log: p.Logger = u.fetch_logger(__name__)


def _setup(
    tmp_path: Path, deps: u.Tests.DepsReportStub
) -> FlextInfraDependencyDetectorRuntime:
    deptry_path = tmp_path / ".venv" / "bin" / "deptry"
    deptry_path.parent.mkdir(parents=True, exist_ok=True)
    deptry_path.write_text("", encoding="utf-8")
    return FlextInfraDependencyDetectorRuntime(
        detector=_DetectorStub(deps),
        workspace_report_factory=m.Infra.WorkspaceDependencyReport,
        dependency_limits_factory=m.Infra.DependencyLimitsInfo,
        pip_check_factory=m.Infra.PipCheckReport,
    )


class TestsFlextInfraDepsDetectorReport:
    """Validate report persistence through the detector public runtime."""

    def test_run_without_output_flag_writes_default_report(
        self, tmp_path: Path
    ) -> None:
        """Write the default report when no output path is supplied."""
        default_output = (
            tmp_path / ".reports" / "dependencies" / "detect-runtime-dev-latest.json"
        )
        runtime = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 0, 0))
        tm.that(
            tm.ok(runtime.run(u.Tests.detect_command(tmp_path, no_pip_check=True))),
            eq=True,
        )
        tm.that(default_output.exists(), eq=True)
        payload: t.JsonMapping = u.Cli.json_as_mapping(
            tm.ok(u.Cli.json_read(default_output))
        )
        tm.that(u.Cli.json_as_mapping(payload.get("projects")), keys=["proj-a"])

    def test_run_with_output_flag(self, tmp_path: Path) -> None:
        """Write the report to the requested output path."""
        custom_output = tmp_path / "custom_report.json"
        runtime = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 0, 0))
        tm.that(
            tm.ok(
                runtime.run(
                    u.Tests.detect_command(
                        tmp_path, output=str(custom_output), no_pip_check=True
                    )
                )
            ),
            eq=True,
        )
        tm.that(custom_output.exists(), eq=True)
        payload: t.JsonMapping = u.Cli.json_as_mapping(
            tm.ok(u.Cli.json_read(custom_output))
        )
        tm.that(u.Cli.json_as_mapping(payload.get("projects")), keys=["proj-a"])

    def test_run_with_output_to_blocked_path_fails(self, tmp_path: Path) -> None:
        """Surface the canonical JSON write failure for a blocked path."""
        blocked_parent = tmp_path / "blocked-output"
        blocked_parent.write_text("not-a-directory", encoding="utf-8")
        blocked_output = blocked_parent / "report.json"

        runtime = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 0, 0))
        error = tm.fail(
            runtime.run(
                u.Tests.detect_command(
                    tmp_path, output=str(blocked_output), no_pip_check=True
                )
            )
        )
        tm.that(error, has="json_write failed")

    def test_run_with_json_write_failure(self, tmp_path: Path) -> None:
        """Preserve the JSON writer operation name in persistence failures."""
        blocked_parent = tmp_path / "blocked-parent"
        blocked_parent.write_text("not-a-directory", encoding="utf-8")
        blocked_output = blocked_parent / "report.json"

        runtime = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 0, 0))
        error = tm.fail(
            runtime.run(
                u.Tests.detect_command(
                    tmp_path, output=str(blocked_output), no_pip_check=True
                )
            )
        )
        tm.that(error, has="json_write failed")
