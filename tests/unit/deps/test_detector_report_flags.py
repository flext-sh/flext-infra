"""Test detector report flags behavior."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm
from tests import TestsFlextInfraUtilities as u

if TYPE_CHECKING:
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector


def _setup(tmp_path: Path, deps: u.Tests.DepsReportStub) -> FlextInfraRuntimeDevDependencyDetector:
    detector: FlextInfraRuntimeDevDependencyDetector = u.Tests.setup_detector_runtime(
        tmp_path, deps
    )
    return detector


class TestsFlextInfraDepsDetectorReportFlags:
    """Test flext infra deps detector report flags behavior."""

    def test_run_with_issues_and_pip_failure(self, tmp_path: Path) -> None:
        """Verify run with issues and pip failure."""
        detector = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 5, 1))
        tm.fail(detector.execute(), has="dependency issues detected")

    def test_run_with_no_fail_flag_with_issues(self, tmp_path: Path) -> None:
        """Verify run with no fail flag with issues."""
        detector = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 5, 1)).model_copy(
            update={"no_fail": True}
        )
        tm.that(tm.ok(detector.execute()), eq=True)

    def test_run_with_json_stdout_flag(self, tmp_path: Path) -> None:
        """Verify run with json stdout flag."""
        detector = _setup(tmp_path, u.Tests.DepsReportStub(tmp_path / "proj-a", 0, 0)).model_copy(
            update={"output_format": "json", "no_pip_check": True}
        )
        tm.that(tm.ok(detector.execute()), eq=True)
