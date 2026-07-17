"""Test detector detect failures behavior."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from tests import u


class TestsFlextInfraDepsDetectorDetectFailures:
    """Test flext infra deps detector detect failures behavior."""

    def test_run_with_no_projects_found(self, tmp_path: Path) -> None:
        """Verify run with no projects found."""
        deps = u.Tests.create_detector_deps_stub([])
        result = u.Tests.setup_detector_runtime(tmp_path, deps).execute()
        tm.fail(result, has="no projects found")

    def test_run_with_project_discovery_failure(self, tmp_path: Path) -> None:
        """Verify run with project discovery failure."""
        deps = u.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.discovery_failure = "discovery failed"
        error = tm.fail(u.Tests.setup_detector_runtime(tmp_path, deps).execute())
        tm.that(
            "discovery failed" in error or "project discovery failed" in error, eq=True
        )

    def test_run_with_deptry_failure(self, tmp_path: Path) -> None:
        """Verify run with deptry failure."""
        deps = u.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.deptry_failure = "deptry failed"
        error = tm.fail(
            u.Tests
            .setup_detector_runtime(tmp_path, deps)
            .model_copy(update={"no_pip_check": True})
            .execute()
        )
        tm.that("deptry failed" in error or "deptry run failed" in error, eq=True)

    def test_run_with_typings_detection_failure(self, tmp_path: Path) -> None:
        """Verify run with typings detection failure."""
        (tmp_path / "proj-a" / "src").mkdir(parents=True)
        deps = u.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.typings_failure = "typing detection failed"
        error = tm.fail(
            u.Tests
            .setup_detector_runtime(tmp_path, deps)
            .model_copy(update={"typings": True, "no_pip_check": True})
            .execute()
        )
        tm.that(
            "typing detection failed" in error
            or "typing dependency detection failed" in error,
            eq=True,
        )
