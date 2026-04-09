from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from tests import u


class TestFlextInfraRuntimeDevDependencyDetectorRunDetect:
    def test_run_with_no_projects(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            monkeypatch,
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([]),
        ).run(["--no-pip-check"])
        tm.that(tm.ok(result), eq=2)

    def test_run_with_deptry_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            monkeypatch,
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
            deptry_exists=False,
        ).run(["--no-pip-check"])
        tm.that(tm.ok(result), eq=3)

    def test_run_with_projects_and_deptry(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            monkeypatch,
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
        ).run(
            ["--no-pip-check", "--dry-run"],
        )
        tm.that(tm.ok(result), eq=0)
