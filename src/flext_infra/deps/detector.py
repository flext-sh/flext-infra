"""Runtime vs dev dependency detector CLI with deptry, pip-check, and typing analysis."""

from __future__ import annotations

from flext_core import r
from flext_infra import (
    FlextInfraDependencyDetectionService,
    FlextInfraDependencyDetectorRuntime,
    FlextInfraModelsDeps,
    p,
    u,
)


class FlextInfraRuntimeDevDependencyDetector:
    """CLI tool for detecting runtime vs dev dependencies across workspace."""

    log: p.Logger = u.fetch_logger(__name__)
    reporting: p.Infra.ReportingService
    deps: p.Infra.DepsService
    runner: p.Infra.RunnerService

    def __init__(
        self,
        *,
        reporting: p.Infra.ReportingService | None = None,
        deps: p.Infra.DepsService | None = None,
        runner: p.Infra.RunnerService | None = None,
    ) -> None:
        """Initialize detector runtime services."""
        super().__init__()
        infra_instance = u.Infra()
        self.reporting = reporting or infra_instance
        self.deps = deps or FlextInfraDependencyDetectionService()
        self.runner = runner or u.Cli

    def run(
        self: FlextInfraRuntimeDevDependencyDetector,
        params: FlextInfraModelsDeps.DetectCommand,
    ) -> r[bool]:
        """Execute dependency detection and generate workspace report."""
        runtime = FlextInfraDependencyDetectorRuntime(
            detector=self,
            workspace_report_factory=FlextInfraModelsDeps.WorkspaceDependencyReport,
            dependency_limits_factory=FlextInfraModelsDeps.DependencyLimitsInfo,
            pip_check_factory=FlextInfraModelsDeps.PipCheckReport,
        )
        return runtime.run(params)


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = [
    "FlextInfraRuntimeDevDependencyDetector",
]
