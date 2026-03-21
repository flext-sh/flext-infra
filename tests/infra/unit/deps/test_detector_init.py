from __future__ import annotations

from pathlib import Path

from flext_tests import u

from flext_infra import u
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector


class TestFlextInfraRuntimeDevDependencyDetectorInit:
    def test_detector_initialization(self) -> None:
        detector = FlextInfraRuntimeDevDependencyDetector()
        u.Tests.Matchers.that(
            detector.__class__.__name__,
            eq="FlextInfraRuntimeDevDependencyDetector",
        )

    def test_detector_has_required_services(self) -> None:
        detector = FlextInfraRuntimeDevDependencyDetector()
        u.Tests.Matchers.that(hasattr(detector, "paths"), eq=True)
        u.Tests.Matchers.that(hasattr(detector, "reporting"), eq=True)
        u.Tests.Matchers.that(hasattr(detector, "json"), eq=True)
        u.Tests.Matchers.that(hasattr(detector, "deps"), eq=True)
        u.Tests.Matchers.that(hasattr(detector, "runner"), eq=True)

    def test_parser_all_arguments(self, tmp_path: Path) -> None:
        parser = FlextInfraRuntimeDevDependencyDetector.parser(tmp_path / "limits.toml")
        args = parser.parse_args([
            "--project",
            "test",
            "--no-pip-check",
            "--dry-run",
            "--format",
            "json",
            "-o",
            "/tmp/out.json",
            "-q",
            "--no-fail",
            "--typings",
            "--apply-typings",
            "--limits",
            "/custom/limits.toml",
        ])
        u.Tests.Matchers.that(args.project, eq="test")
        u.Tests.Matchers.that(args.no_pip_check, eq=True)
        u.Tests.Matchers.that(args.dry_run, eq=True)
        u.Tests.Matchers.that(args.output_format, eq="json")
        u.Tests.Matchers.that(args.output, eq="/tmp/out.json")
        u.Tests.Matchers.that(args.quiet, eq=True)
        u.Tests.Matchers.that(args.no_fail, eq=True)
        u.Tests.Matchers.that(args.typings, eq=True)
        u.Tests.Matchers.that(args.apply_typings, eq=True)
        u.Tests.Matchers.that(args.limits, eq="/custom/limits.toml")

    def test_project_filter_with_single_project(self, tmp_path: Path) -> None:
        parser = FlextInfraRuntimeDevDependencyDetector.parser(tmp_path / "limits.toml")
        args = u.Infra.resolve(parser.parse_args(["--project", "test-proj"]))
        u.Tests.Matchers.that(
            FlextInfraRuntimeDevDependencyDetector.project_filter(args),
            eq=["test-proj"],
        )

    def test_project_filter_with_multiple_projects(self, tmp_path: Path) -> None:
        parser = FlextInfraRuntimeDevDependencyDetector.parser(tmp_path / "limits.toml")
        args = u.Infra.resolve(
            parser.parse_args(["--projects", "proj-a,proj-b,proj-c"]),
        )
        u.Tests.Matchers.that(
            FlextInfraRuntimeDevDependencyDetector.project_filter(args),
            eq=["proj-a", "proj-b", "proj-c"],
        )

    def test_project_filter_with_no_filter(self, tmp_path: Path) -> None:
        parser = FlextInfraRuntimeDevDependencyDetector.parser(tmp_path / "limits.toml")
        args = u.Infra.resolve(parser.parse_args([]))
        u.Tests.Matchers.that(
            FlextInfraRuntimeDevDependencyDetector.project_filter(args), eq=None
        )
