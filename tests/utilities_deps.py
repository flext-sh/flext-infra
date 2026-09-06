"""Dependency detection stub test utilities for flext-infra."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_infra import r
from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
from tests import c, m, p, t
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
from tests.utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin


class TestsFlextInfraUtilitiesDepsMixin:
    """Typed dependency-service and detector stub helpers."""

    class DeptrySelector:
        """Protocol-compatible selector backed by a real Result."""

        def __init__(self, result: p.Result[Sequence[m.Infra.ProjectInfo]]) -> None:
            """Store the typed project-selection result."""
            self._result = result

        def resolve_projects(
            self, repository_root: Path, names: t.StrSequence
        ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
            """Return the configured project-selection result."""
            del repository_root, names
            return self._result

    class DepsReportStub(p.Infra.DepsService, p.Infra.PipCheckDepsService):
        """Protocol-compatible deps service replaying one fixed report."""

        def __init__(self, project: Path, raw_count: int, pip_exit: int) -> None:
            """Store the project path, raw issue count, and pip-check exit."""
            self._project = project
            self._raw_count = raw_count
            self._pip_exit = pip_exit

        @override
        def discover_project_paths(
            self,
            repository_root: Path,
            *,
            projects_filter: t.StrSequence | None = None,
        ) -> p.Result[Sequence[Path]]:
            del repository_root, projects_filter
            return r[Sequence[Path]].ok([self._project])

        @override
        def run_deptry(
            self, project_path: Path, venv_bin: Path
        ) -> p.Result[t.Pair[Sequence[t.JsonMapping], int]]:
            del project_path, venv_bin
            return r[t.Pair[Sequence[t.JsonMapping], int]].ok(([], 0))

        @override
        def build_project_report(
            self, project_name: str, deptry_issues: t.SequenceOf[t.JsonMapping]
        ) -> TestsFlextInfraUtilitiesDepsMixin.DetectorReportStub:
            del project_name, deptry_issues
            return TestsFlextInfraUtilitiesDepsMixin.DetectorReportStub(
                self._raw_count
            )

        @override
        def run_pip_check(
            self, repository_root: Path, venv_bin: Path
        ) -> p.Result[tuple[t.StrSequence, int]]:
            del repository_root, venv_bin
            return r[tuple[t.StrSequence, int]].ok(([], self._pip_exit))

    class DetectorReportStub:
        """Minimal report stub for dependency detector tests."""

        def __init__(self, raw_count: int) -> None:
            """Store the raw dependency count."""
            self._raw_count = raw_count

        def model_dump(self) -> t.JsonMapping:
            """Return the dependency-report payload."""
            return {"deptry": {"raw_count": self._raw_count}}

    class DetectorDepsStub(p.Infra.DepsService, p.Infra.TypingsDepsService):
        """Typed dependency service stub for detector tests."""

        def __init__(self, project_paths: t.SequenceOf[Path]) -> None:
            """Store project paths and injectable failure states."""
            self.project_paths = project_paths
            self.discovery_failure: str | None = None
            self.deptry_failure: str | None = None
            self.typings_failure: str | None = None

        @override
        def discover_project_paths(
            self,
            repository_root: Path,
            *,
            projects_filter: t.StrSequence | None = None,
        ) -> p.Result[Sequence[Path]]:
            del repository_root, projects_filter
            if self.discovery_failure is not None:
                return r[Sequence[Path]].fail(self.discovery_failure)
            return r[Sequence[Path]].ok(self.project_paths)

        @override
        def run_deptry(
            self, project_path: Path, venv_bin: Path
        ) -> p.Result[t.Pair[Sequence[t.JsonMapping], int]]:
            del project_path, venv_bin
            if self.deptry_failure is not None:
                return r[t.Pair[Sequence[t.JsonMapping], int]].fail(
                    self.deptry_failure
                )
            return r[t.Pair[Sequence[t.JsonMapping], int]].ok(((), 0))

        @override
        def build_project_report(
            self, project_name: str, deptry_issues: t.SequenceOf[t.JsonMapping]
        ) -> TestsFlextInfraUtilitiesDepsMixin.DetectorReportStub:
            del project_name, deptry_issues
            return TestsFlextInfraUtilitiesDepsMixin.DetectorReportStub(0)

        @override
        def get_required_typings(
            self,
            project_path: Path,
            limits_path: Path | None = None,
            *,
            include_mypy: bool = True,
        ) -> p.Result[m.Infra.TypingsReport]:
            del project_path, limits_path
            del include_mypy
            if self.typings_failure is not None:
                return r[m.Infra.TypingsReport].fail(self.typings_failure)
            return r[m.Infra.TypingsReport].ok(m.Infra.TypingsReport(to_add=[]))

        @override
        def load_dependency_limits(
            self, limits_path: Path | None = None
        ) -> t.StrMapping:
            del limits_path
            limits: dict[str, str] = {}
            return limits

    @staticmethod
    def create_deptry_service(
        *,
        projects: t.SequenceOf[m.Infra.ProjectInfo] | None = None,
        selection_error: str | None = None,
        command_output: m.Cli.CommandOutput | None = None,
        run_error: str | None = None,
    ) -> FlextInfraDependencyDetectionService:
        """Provide the typed test helper `create_deptry_service`."""
        service = FlextInfraDependencyDetectionService()
        service.selector = TestsFlextInfraUtilitiesDepsMixin.DeptrySelector(
            r[Sequence[m.Infra.ProjectInfo]].fail(selection_error)
            if selection_error is not None
            else r[Sequence[m.Infra.ProjectInfo]].ok(list(projects or []))
        )
        service.runner = TestsFlextInfraUtilitiesReplayRunnerMixin.DeptryRunner(
            r[m.Cli.CommandOutput].fail(run_error)
            if run_error is not None
            else r[m.Cli.CommandOutput].ok(
                command_output
                or TestsFlextInfraUtilitiesReplaySequenceMixin.create_command_output()
            )
        )
        return service

    @staticmethod
    def detect_command(
        workspace_root: Path, **overrides: t.Infra.InfraValue
    ) -> m.Infra.DetectCommand:
        """Create a validated dependency-detection command."""
        validated: m.Infra.DetectCommand = m.Infra.DetectCommand.model_validate({
            "workspace": str(workspace_root),
            **overrides,
        })
        return validated

    @staticmethod
    def create_detector_deps_stub(
        project_paths: t.SequenceOf[Path],
    ) -> TestsFlextInfraUtilitiesDepsMixin.DetectorDepsStub:
        """Provide the typed test helper `create_detector_deps_stub`."""
        return TestsFlextInfraUtilitiesDepsMixin.DetectorDepsStub(project_paths)

    @staticmethod
    def setup_detector_runtime(
        tmp_path: Path,
        deps: p.Infra.DepsService,
        *,
        deptry_exists: bool = True,
        runner: p.Infra.RunnerService | None = None,
    ) -> FlextInfraRuntimeDevDependencyDetector:
        """Provide the typed test helper `setup_detector_runtime`."""
        deptry_path = tmp_path / c.Infra.VENV_BIN_REL / c.Infra.DEPTRY
        deptry_path.parent.mkdir(parents=True, exist_ok=True)
        if deptry_exists:
            deptry_path.write_text("", encoding="utf-8")
        if runner is not None:
            return FlextInfraRuntimeDevDependencyDetector(
                repository_root=tmp_path, deps=deps, runner=runner
            )
        return FlextInfraRuntimeDevDependencyDetector(
            repository_root=tmp_path, deps=deps
        )


__all__: list[str] = ["TestsFlextInfraUtilitiesDepsMixin"]
