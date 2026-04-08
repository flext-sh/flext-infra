from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests.unit.deps.test_detector_detect import _DepsStub, _setup_detector


class TestDetectorRunFailures:
    def test_run_with_no_projects_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        deps = _DepsStub([])
        result = _setup_detector(monkeypatch, tmp_path, deps).run([])
        tm.that(tm.ok(result), eq=2)

    def test_run_with_project_discovery_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        deps = _DepsStub([tmp_path / "proj-a"])
        deps.discovery_failure = "discovery failed"
        error = tm.fail(_setup_detector(monkeypatch, tmp_path, deps).run([]))
        tm.that(
            "discovery failed" in error or "project discovery failed" in error,
            eq=True,
        )

    def test_run_with_deptry_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        deps = _DepsStub([tmp_path / "proj-a"])
        deps.deptry_failure = "deptry failed"
        error = tm.fail(
            _setup_detector(monkeypatch, tmp_path, deps).run(["--no-pip-check"]),
        )
        tm.that("deptry failed" in error or "deptry run failed" in error, eq=True)

    def test_run_with_typings_detection_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "proj-a" / "src").mkdir(parents=True)
        deps = _DepsStub([tmp_path / "proj-a"])
        deps.typings_failure = "typing detection failed"
        error = tm.fail(
            _setup_detector(monkeypatch, tmp_path, deps).run([
                "--typings",
                "--no-pip-check",
            ]),
        )
        tm.that(
            "typing detection failed" in error
            or "typing dependency detection failed" in error,
            eq=True,
        )
