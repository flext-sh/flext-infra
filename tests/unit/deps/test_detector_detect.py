from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestFlextInfraRuntimeDevDependencyDetectorRunDetect:
    def test_run_with_no_projects(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([]),
        ).run(u.Infra.Tests.detect_command(tmp_path, no_pip_check=True))
        tm.fail(result, has="no projects found")

    def test_run_with_deptry_missing(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
            deptry_exists=False,
        ).run(u.Infra.Tests.detect_command(tmp_path, no_pip_check=True))
        tm.fail(result, has="deptry executable not found")

    def test_run_with_projects_and_deptry(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"]),
        ).run(u.Infra.Tests.detect_command(tmp_path, no_pip_check=True))
        tm.that(tm.ok(result), eq=True)
