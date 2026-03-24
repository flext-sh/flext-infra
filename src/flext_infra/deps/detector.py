"""Runtime vs dev dependency detector CLI with deptry, pip-check, and typing analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flext_core import FlextLogger

from flext_infra import (
    FlextInfraDependencyDetectionService,
    FlextInfraDependencyDetectorRuntime,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraRuntimeDevDependencyDetector:
    """CLI tool for detecting runtime vs dev dependencies across workspace."""

    log: p.Logger = FlextLogger.create_module_logger(__name__)
    reporting: p.Infra.ReportingService
    json: p.Infra.JsonService
    deps: p.Infra.DepsService
    runner: p.Infra.RunnerService

    def __init__(self) -> None:
        """Initialize detector runtime services."""
        super().__init__()
        infra_instance = u.Infra()
        self.reporting = infra_instance
        self.json = infra_instance
        self.deps = FlextInfraDependencyDetectionService()
        self.runner = infra_instance
        self.log = self.log

    @staticmethod
    def parser(default_limits_path: Path) -> argparse.ArgumentParser:
        """Create argument parser for CLI with deptry, pip-check, and typing options."""
        parser = u.Infra.create_parser(
            prog="flext-infra deps detect",
            description="Detect runtime vs dev dependencies (deptry + pip check).",
            include_apply=True,
            include_project=True,
            include_format=True,
        )
        _ = parser.add_argument(
            "--no-pip-check",
            action="store_true",
            help="Skip pip check (workspace-level).",
        )
        _ = parser.add_argument(
            "-o",
            "--output",
            metavar="FILE",
            help="Write report to this path (default: .reports/dependencies/detect-runtime-dev-latest.json).",
        )
        _ = parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Minimal output (summary only).",
        )
        _ = parser.add_argument(
            "--no-fail",
            action="store_true",
            help="Always exit 0 (report only).",
        )
        _ = parser.add_argument(
            "--typings",
            action="store_true",
            help="Detect required typing libraries (types-*).",
        )
        _ = parser.add_argument(
            "--apply-typings",
            action="store_true",
            help="Add missing typings with poetry add --group typings.",
        )
        _ = parser.add_argument(
            "--limits",
            metavar="FILE",
            default=str(default_limits_path),
            help="Path to dependency_limits.toml.",
        )
        return parser

    @staticmethod
    def project_filter(cli: u.Infra.CliArgs) -> t.StrSequence | None:
        """Extract project filter list from parsed CLI arguments."""
        return cli.project_names()

    def run(
        self: FlextInfraRuntimeDevDependencyDetector,
        argv: t.StrSequence | None = None,
    ) -> r[int]:
        """Execute dependency detection and generate workspace report."""
        runtime = FlextInfraDependencyDetectorRuntime(
            detector=self,
            workspace_report_factory=m.Infra.WorkspaceDependencyReport,
            dependency_limits_factory=m.Infra.DependencyLimitsInfo,
            pip_check_factory=m.Infra.PipCheckReport,
        )
        return runtime.run(argv=argv)

    @staticmethod
    def main() -> int:
        """Entry point for dependency detector CLI."""
        detector_type: type[FlextInfraRuntimeDevDependencyDetector] = (
            FlextInfraRuntimeDevDependencyDetector
        )
        deps_module = sys.modules.get("flext_infra.deps")
        if deps_module is not None:
            deps_type = getattr(
                deps_module,
                "FlextInfraRuntimeDevDependencyDetector",
                detector_type,
            )
            if isinstance(deps_type, type):
                detector_type = deps_type
        root_module = sys.modules.get("flext_infra")
        if (
            root_module is not None
            and detector_type is FlextInfraRuntimeDevDependencyDetector
        ):
            root_type = getattr(
                root_module,
                "FlextInfraRuntimeDevDependencyDetector",
                detector_type,
            )
            if isinstance(root_type, type):
                detector_type = root_type
        detector_obj = detector_type()
        if not isinstance(detector_obj, p.Infra.RunnableDetector):
            return 1
        detector = detector_obj
        result = detector.run()
        if result.is_failure:
            logger = getattr(detector, "log", None)
            if logger is not None and hasattr(logger, "error"):
                logger.error(
                    "deps_detector_failed",
                    error=result.error or "unknown error",
                )
            return 1
        return result.value


main = FlextInfraRuntimeDevDependencyDetector.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraRuntimeDevDependencyDetector.main())


__all__ = [
    "FlextInfraRuntimeDevDependencyDetector",
    "main",
]
