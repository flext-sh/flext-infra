from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestDetectorRunFailures:
    def test_run_with_no_projects_found(
        self,
        tmp_path: Path,
    ) -> None:
        deps = u.Infra.Tests.create_detector_deps_stub([])
        result = u.Infra.Tests.setup_detector_runtime(
            tmp_path,
            deps,
        ).run(u.Infra.Tests.detect_command(tmp_path))
        tm.fail(result, has="no projects found")

    def test_run_with_project_discovery_failure(
        self,
        tmp_path: Path,
    ) -> None:
        deps = u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.discovery_failure = "discovery failed"
        error = tm.fail(
            u.Infra.Tests.setup_detector_runtime(
                tmp_path,
                deps,
            ).run(u.Infra.Tests.detect_command(tmp_path)),
        )
        tm.that(
            "discovery failed" in error or "project discovery failed" in error,
            eq=True,
        )

    def test_run_with_deptry_failure(
        self,
        tmp_path: Path,
    ) -> None:
        deps = u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.deptry_failure = "deptry failed"
        error = tm.fail(
            u.Infra.Tests.setup_detector_runtime(tmp_path, deps).run(
                u.Infra.Tests.detect_command(tmp_path, no_pip_check=True),
            ),
        )
        tm.that("deptry failed" in error or "deptry run failed" in error, eq=True)

    def test_run_with_typings_detection_failure(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "proj-a" / "src").mkdir(parents=True)
        deps = u.Infra.Tests.create_detector_deps_stub([tmp_path / "proj-a"])
        deps.typings_failure = "typing detection failed"
        error = tm.fail(
            u.Infra.Tests.setup_detector_runtime(tmp_path, deps).run(
                u.Infra.Tests.detect_command(
                    tmp_path,
                    typings=True,
                    no_pip_check=True,
                ),
            ),
        )
        tm.that(
            "typing detection failed" in error
            or "typing dependency detection failed" in error,
            eq=True,
        )
