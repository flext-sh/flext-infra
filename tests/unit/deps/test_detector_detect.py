"""Test detector detect behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import u

from pathlib import Path



class TestsFlextInfraDepsDetectorDetect:
    """Test flext infra deps detector detect behavior."""

    def test_run_with_no_projects(self, tmp_path: Path) -> None:
        """Verify run with no projects."""
        detector = u.Tests.setup_detector_runtime(
            tmp_path, u.Tests.create_detector_deps_stub([])
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.fail(result, has="no projects found")

    def test_run_with_deptry_missing(self, tmp_path: Path) -> None:
        """Verify run with deptry missing."""
        detector = u.Tests.setup_detector_runtime(
            tmp_path,
            u.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
            deptry_exists=False,
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.fail(result, has="Deptry executable")

    def test_run_with_projects_and_deptry(self, tmp_path: Path) -> None:
        """Verify run with projects and deptry."""
        detector = u.Tests.setup_detector_runtime(
            tmp_path, u.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.that(tm.ok(result), eq=True)
