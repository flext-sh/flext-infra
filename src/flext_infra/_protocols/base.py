"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterator,
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_core import FlextProtocols

if TYPE_CHECKING:
    from flext_infra import m, p, t


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

        def render(
            self,
            **kwargs: (
                t.ValueOrModel
                | t.Cli.JsonPayload
                | Sequence[t.Cli.JsonLikeValue]
                | Sequence[tuple[str, str]]
                | Sequence[tuple[str, Sequence[str]]]
                | Sequence[tuple[str, Sequence[tuple[str, str]]]]
                | Mapping[str, t.Cli.JsonLikeValue]
                | type
            ),
        ) -> str:
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

        @property
        def package_name(self) -> str:
            """Return the primary Python package name."""
            ...

    @runtime_checkable
    class Validator(Protocol):
        """Contract for validation services."""

        def validate(self, argv: t.StrSequence | None = None) -> p.Result[int]:
            """Execute validation and return result."""
            ...

    @runtime_checkable
    class Checker(Protocol):
        """Contract for project and workspace quality checking services."""

        def run(
            self,
            project: str,
            gates: t.StrSequence,
        ) -> p.Result[Sequence[m.Infra.ProjectResult]]:
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
            settings: m.Infra.BaseMkConfig | None = None,
            canonical_root: Path | None = None,
        ) -> p.Result[m.Infra.SyncResult]:
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
        ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self,
            workspace_root: Path,
        ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
            """Discover projects in a workspace root."""
            ...

    @runtime_checkable
    class TomlReader(Protocol):
        """Contract for TOML file readers used by dependency services."""

        def read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]:
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
        ) -> p.Result[str]:
            """Run a command and capture its stdout."""
            ...

        def run_checked(
            self,
            cmd: t.StrSequence,
            cwd: Path | None = None,
            timeout: int | None = None,
        ) -> p.Result[bool]:
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
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self,
            path: Path,
            payload: Mapping[str, t.Infra.InfraValue],
        ) -> p.Result[bool]:
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
        ) -> p.Result[Sequence[Path]]:
            """Discover project paths in workspace root."""
            ...

        def run_deptry(
            self,
            project_path: Path,
            venv_bin: Path,
        ) -> p.Result[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
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
        ) -> p.Result[m.Infra.TypingsReport]:
            """Get required typing libraries for a project."""
            ...

    @runtime_checkable
    class PipCheckDepsService(Protocol):
        """Service for pip-based dependency checking."""

        def run_pip_check(
            self,
            workspace_root: Path,
            venv_bin: Path,
        ) -> p.Result[t.Infra.Pair[t.StrSequence, int]]:
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
        ) -> p.Result[m.Cli.CommandOutput]:
            """Run command and return raw output."""
            ...

    class DetectorRuntime(Protocol):
        """Protocol for detector runtime service dependencies."""

        deps: FlextInfraProtocolsBase.DepsService
        runner: FlextInfraProtocolsBase.RunnerService
        log: FlextProtocols.Logger

    @runtime_checkable
    class TemplateRenderer(Protocol):
        """Protocol for template rendering engines."""

        def render_all(
            self,
            settings: m.Infra.BaseMkConfig | None = None,
        ) -> p.Result[str]:
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
        ) -> p.Result[Sequence[m.Cli.CommandOutput]]:
            """Execute one make verb across multiple projects."""
            ...

    class CodegenFixer(Protocol):
        """Protocol for codegen namespace fixer services."""

        def execute(self) -> p.Result[bool]:
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

        def execute(self) -> p.Result[bool]:
            """Execute modernization pass."""
            ...

    class GithubService(Protocol):
        """Protocol for GitHub operations services."""

        def execute(self) -> p.Result[bool]:
            """Execute GitHub operations."""
            ...

    class RefactorEngine(Protocol):
        """Protocol for rope-based refactor engine services."""

        def execute(self) -> p.Result[bool]:
            """Execute refactoring pass."""
            ...

    class ReleaseOrchestrator(Protocol):
        """Protocol for release orchestration services."""

        def execute(self) -> p.Result[bool]:
            """Execute release orchestration."""
            ...

    @runtime_checkable
    class SafeTransformer(Protocol):
        """Contract for transformers that run with copy-on-write protection."""

        def transform(self, files: Sequence[Path]) -> p.Result[Sequence[Path]]:
            """Apply transformation to files, return paths of modified files."""
            ...

    @runtime_checkable
    class SafeValidator(Protocol):
        """Contract for post-transform quality gate validators."""

        def validate(
            self,
            files: Sequence[Path],
            project_dir: Path,
        ) -> p.Result[m.Infra.GateResult]:
            """Validate files pass quality gates after transformation."""
            ...

    @runtime_checkable
    class XmlElementLike(Protocol):
        """Typed subset of the safe XML element API returned by defusedxml."""

        attrib: dict[str, str]
        text: str | None

        def find(self, path: str) -> FlextInfraProtocolsBase.XmlElementLike | None:
            """Find first matching child element."""
            ...

        def iter(
            self, tag: str | None = None
        ) -> Iterator[FlextInfraProtocolsBase.XmlElementLike]:
            """Iterate over matching elements."""
            ...

    class GithubCliHandlers(Protocol):
        """Protocol for GitHub CLI handler mixins."""

        def sync_github_workflows(
            self,
            params: m.Infra.GithubWorkflowSyncRequest,
        ) -> p.Result[m.Infra.GithubWorkflowSyncReport]:
            """Sync GitHub workflow files."""
            ...

        def lint_github_workflows(
            self,
            params: m.Infra.GithubWorkflowLintRequest,
        ) -> p.Result[m.Infra.GithubWorkflowLintOutcome]:
            """Lint GitHub workflow files."""
            ...

        def run_github_pull_request(
            self,
            params: m.Infra.GithubPullRequestRequest,
        ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
            """Manage pull request for a single project."""
            ...

        def run_github_workspace_pull_requests(
            self,
            params: m.Infra.GithubPullRequestWorkspaceRequest,
        ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]:
            """Manage pull requests across the workspace."""
            ...
