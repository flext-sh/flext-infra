from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraRuntimeDevDependencyDetector
from tests import u


class TestsFlextInfraDepsDetectorInit:
    def test_detector_initialization(self) -> None:
        detector = FlextInfraRuntimeDevDependencyDetector()
        tm.that(
            detector.__class__.__name__,
            eq="FlextInfraRuntimeDevDependencyDetector",
        )

    def test_detector_has_required_services(self) -> None:
        detector = FlextInfraRuntimeDevDependencyDetector()
        tm.that(detector.deps is not None, eq=True)
        tm.that(detector.runner is not None, eq=True)

    def test_detect_command_normalizes_public_fields(self, tmp_path: Path) -> None:
        params = u.Tests.detect_command(
            tmp_path,
            projects=["test"],
            no_pip_check=True,
            output_format="json",
            output="/tmp/out.json",
            quiet=True,
            no_fail=True,
            typings=True,
            apply_typings=True,
            limits="/custom/limits.toml",
        )
        tm.that(params.project_names, eq=["test"])
        tm.that(params.no_pip_check, eq=True)
        tm.that(params.dry_run, eq=True)
        tm.that(params.output_format, eq="json")
        tm.that(str(params.output_path), eq=str(Path("/tmp/out.json").resolve()))
        tm.that(params.quiet, eq=True)
        tm.that(params.no_fail, eq=True)
        tm.that(params.typings, eq=True)
        tm.that(params.apply_typings, eq=True)
        tm.that(str(params.limits_path), eq=str(Path("/custom/limits.toml").resolve()))

    def test_detect_command_project_names_with_single_project(
        self,
        tmp_path: Path,
    ) -> None:
        params = u.Tests.detect_command(tmp_path, projects=["test-proj"])
        tm.that(params.project_names, eq=["test-proj"])

    def test_detect_command_project_names_split_csv(self, tmp_path: Path) -> None:
        params = u.Tests.detect_command(
            tmp_path,
            projects=["proj-a,proj-b", "proj-c"],
        )
        tm.that(params.project_names, eq=["proj-a", "proj-b", "proj-c"])

    def test_detect_command_without_project_filter(self, tmp_path: Path) -> None:
        params = u.Tests.detect_command(tmp_path)
        tm.that(params.project_names, eq=None)
