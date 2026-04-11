"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_core import FlextProtocols, r

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraProtocolsBase(Protocol):
    """Base protocols for flext-infra project."""

    @runtime_checkable
    class OutputStream(Protocol):
        """Minimal text stream contract used by infrastructure output backends."""

        def write(self, msg: str, /) -> int:
            """Write a text fragment and return the number of characters written."""
            ...

        def flush(self) -> None:
            """Flush buffered text to the underlying sink."""
            ...

        def isatty(self) -> bool:
            """Return whether the stream is attached to a TTY."""
            ...

    @runtime_checkable
    class RenderableTemplate(Protocol):
        """Structural contract for template engines that expose ``render``."""

        def render(self, **kwargs: object) -> str:
            """Render a template with keyword context."""
            ...

    @runtime_checkable
    class ProjectInfo(Protocol):
        """Minimal project descriptor used by orchestration services."""

        @property
        def name(self) -> str:
            """Return the project name."""
            ...

        @property
        def path(self) -> Path:
            """Return the project path."""
            ...

    @runtime_checkable
    class Validator(Protocol):
        """Contract for validation services."""

        def validate(self, argv: t.StrSequence | None = None) -> r[int]:
            """Execute validation and return result."""
            ...

    @runtime_checkable
    class Checker(Protocol):
        """Contract for project and workspace quality checking services."""

        def run(
            self,
            project: str,
            gates: t.StrSequence,
        ) -> r[Sequence[m.Infra.ProjectResult]]:
            """Run quality gates for one project."""
            ...

    @runtime_checkable
    class Syncer(Protocol):
        """Contract for synchronization services."""

        def sync(
            self,
            _source: str | None = None,
            _target: str | None = None,
            *,
            workspace_root: Path | None = None,
            config: m.Infra.BaseMkConfig | None = None,
            canonical_root: Path | None = None,
        ) -> r[m.Infra.SyncResult]:
            """Synchronize generated workspace or project artifacts."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self,
            workspace_root: Path,
            *,
            project: str | None = None,
            projects: str | None = None,
            output_dir: str = "",
            apply: bool = False,
        ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self,
            workspace_root: Path,
        ) -> r[Sequence[m.Infra.ProjectInfo]]:
            """Discover projects in a workspace root."""
            ...

    @runtime_checkable
    class TomlReader(Protocol):
        """Contract for TOML file readers used by dependency services."""

        def read_plain(self, path: Path) -> r[t.Infra.ContainerDict]:
            """Read and parse a TOML file as a plain dict with r error handling."""
            ...

    @runtime_checkable
    class SafetyRunner(Protocol):
        """Protocol for command execution backends used by the safety manager."""

        def capture(
            self,
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
        ) -> r[str]:
            """Run a command and capture its stdout."""
            ...

        def run_checked(
            self,
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
        ) -> r[bool]:
            """Run a command and return success/failure."""
            ...

    @runtime_checkable
    class Scanner(Protocol):
        """Protocol for file scanners that detect violations."""

        def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
            """Scan a single file and return scan result."""
            ...

    class WorkspaceReport(Protocol):
        """Protocol for workspace dependency report model contract."""

        pip_check: m.Infra.PipCheckReport | None
        dependency_limits: m.Infra.DependencyLimitsInfo | None

        def model_dump(self) -> Mapping[str, t.Infra.InfraValue]:
            """Serialize report model payload."""
            ...

    @runtime_checkable
    class ReportingService(Protocol):
        """Service for reporting directory resolution."""

        def get_report_dir(
            self,
            workspace_root: Path,
            scope: str,
            verb: str,
        ) -> Path:
            """Resolve report output directory for given scope and verb."""
            ...

    @runtime_checkable
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self,
            path: Path,
            payload: Mapping[str, t.Infra.InfraValue],
        ) -> r[bool]:
            """Write payload to JSON file."""
            ...

    class ProjectReportLike(Protocol):
        """Protocol for project-level dependency report contracts."""

        def model_dump(self) -> Mapping[str, t.Infra.InfraValue]:
            """Serialize project report payload."""
            ...

    @runtime_checkable
    class DepsService(Protocol):
        """Service for dependency detection across projects."""

        def discover_project_paths(
            self,
            workspace_root: Path,
            *,
            projects_filter: t.StrSequence | None = None,
        ) -> r[Sequence[Path]]:
            """Discover project paths in workspace root."""
            ...

        def run_deptry(
            self,
            project_path: Path,
            venv_bin: Path,
        ) -> r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
            """Run deptry on a project and return issues."""
            ...

        def build_project_report(
            self,
            project_name: str,
            deptry_issues: Sequence[t.Infra.ContainerDict],
        ) -> FlextInfraProtocolsBase.ProjectReportLike:
            """Build project report from deptry issues."""
            ...

    @runtime_checkable
    class TypingsDepsService(Protocol):
        """Service for typing-related dependency detection."""

        def load_dependency_limits(
            self,
            limits_path: Path | None = None,
        ) -> Mapping[str, t.Infra.InfraValue]:
            """Load dependency limits from TOML file."""
            ...

        def get_required_typings(
            self,
            project_path: Path,
            venv_bin: Path,
            limits_path: Path | None = None,
            *,
            include_mypy: bool = True,
        ) -> r[m.Infra.TypingsReport]:
            """Get required typing libraries for a project."""
            ...

    @runtime_checkable
    class PipCheckDepsService(Protocol):
        """Service for pip-based dependency checking."""

        def run_pip_check(
            self,
            workspace_root: Path,
            venv_bin: Path,
        ) -> r[t.Infra.Pair[t.StrSequence, int]]:
            """Run pip check on workspace and return results."""
            ...

    @runtime_checkable
    class RunnerService(Protocol):
        """Service for running arbitrary commands."""

        def run_raw(
            self,
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
        ) -> r[m.Cli.CommandOutput]:
            """Run command and return raw output."""
            ...

    class DetectorRuntime(Protocol):
        """Protocol for detector runtime service dependencies."""

        reporting: FlextInfraProtocolsBase.ReportingService
        deps: FlextInfraProtocolsBase.DepsService
        runner: FlextInfraProtocolsBase.RunnerService
        log: FlextProtocols.Logger

    @runtime_checkable
    class TemplateRenderer(Protocol):
        """Protocol for template rendering engines."""

        def render_all(
            self,
            config: m.Infra.BaseMkConfig | None = None,
        ) -> r[str]:
            """Render all templates with given configuration."""
            ...

    @runtime_checkable
    class ViolationWithLine(Protocol):
        """Protocol for violations that have a line number."""

        def model_dump(self) -> t.Cli.JsonMapping:
            """Dump violation data to a dictionary."""
            ...

    @runtime_checkable
    class Orchestrator(Protocol):
        """Contract for multi-project orchestration services."""

        def orchestrate(
            self,
            projects: t.StrSequence,
            verb: str,
            *,
            fail_fast: bool = False,
            make_args: t.StrSequence = (),
        ) -> r[Sequence[m.Cli.CommandOutput]]:
            """Execute one make verb across multiple projects."""
            ...

    class CodegenFixer(Protocol):
        """Protocol for codegen namespace fixer services."""

        def execute(self) -> r[bool]:
            """Execute codegen fix pass."""
            ...

    @runtime_checkable
    class CodegenCensusService(Protocol):
        """Protocol for codegen census services reused across pipeline stages."""

        def run(
            self,
            workspace_root: Path | None = None,
            *,
            output_format: str = "json",
            projects: Sequence[FlextInfraProtocolsBase.ProjectInfo] | None = None,
        ) -> Sequence[m.Infra.CensusReport]:
            """Run census and return typed reports."""
            ...

    class PyprojectModernizer(Protocol):
        """Protocol for pyproject.toml modernization services."""

        def execute(self) -> r[bool]:
            """Execute modernization pass."""
            ...

    class GithubService(Protocol):
        """Protocol for GitHub operations services."""

        def execute(self) -> r[bool]:
            """Execute GitHub operations."""
            ...

    class RefactorEngine(Protocol):
        """Protocol for rope-based refactor engine services."""

        def execute(self) -> r[bool]:
            """Execute refactoring pass."""
            ...

    class ReleaseOrchestrator(Protocol):
        """Protocol for release orchestration services."""

        def execute(self) -> r[bool]:
            """Execute release orchestration."""
            ...

    @runtime_checkable
    class SafeTransformer(Protocol):
        """Contract for transformers that run with copy-on-write protection."""

        def transform(self, files: Sequence[Path]) -> r[Sequence[Path]]:
            """Apply transformation to files, return paths of modified files."""
            ...

    @runtime_checkable
    class SafeValidator(Protocol):
        """Contract for post-transform quality gate validators."""

        def validate(
            self,
            files: Sequence[Path],
            project_dir: Path,
        ) -> r[m.Infra.GateResult]:
            """Validate files pass quality gates after transformation."""
            ...
