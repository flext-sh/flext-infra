from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestFlextInfraRuntimeDevDependencyDetectorRunDetect:
    def test_run_with_no_projects(
        self,
        tmp_path: Path,
    ) -> None:
        detector = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([]),
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.fail(result, has="no projects found")

    def test_run_with_deptry_missing(
        self,
        tmp_path: Path,
    ) -> None:
        detector = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
            deptry_exists=False,
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.fail(result, has="deptry executable not found")

    def test_run_with_projects_and_deptry(
        self,
        tmp_path: Path,
    ) -> None:
        detector = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
        ).model_copy(update={"no_pip_check": True})
        result = detector.execute()
        tm.that(tm.ok(result), eq=True)
