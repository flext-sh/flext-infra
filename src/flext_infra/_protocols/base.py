"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

# Declaration-only protocol types stay
# behind one guard so structural contracts add no reverse runtime dependency.
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from flext_cli import p
    from flext_infra import c, m, t


@runtime_checkable
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
        """Structural contract for template renderers that expose ``render``."""

        def render(
            self,
            **kwargs: (
                t.JsonPayload
                | t.SequenceOf[t.JsonValue]
                | t.StrPairSequence
                | t.SequenceOf[t.StrSequencePair]
                | t.SequenceOf[t.StrPairSequencePair]
                | t.JsonMapping
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
            """Project name."""
            ...

        @property
        def path(self) -> Path:
            """Project path."""
            ...

        @property
        def package_name(self) -> str:
            """Primary Python package name."""
            ...

    # These declaration-only
    # contracts preserve config-model field types across the public p/u facades.
    @runtime_checkable
    class MiseToolSpec(Protocol):
        """One exact mise backend selector and immutable version."""

        @property
        def selector(self) -> str:
            """Canonical mise backend selector."""
            ...

        @property
        def version(self) -> str:
            """Exact tool version installed by mise."""
            ...

    @runtime_checkable
    class ProtectedMiseToolSpec(MiseToolSpec, Protocol):
        """Fleet-owned mise distribution identity."""

        @property
        def selector_patterns(self) -> t.StrSequence:
            """Glob patterns identifying equivalent distributions."""
            ...

    @runtime_checkable
    class BeadsToolSpec(ProtectedMiseToolSpec, Protocol):
        """Canonical Beads distribution and Gas City projection contract."""

        @property
        def endpoint_origin(self) -> str:
            """Gas City-owned endpoint inheritance mode."""
            ...

        @property
        def endpoint_status(self) -> str:
            """Canonical inherited endpoint status."""
            ...

        @property
        def required_custom_types(self) -> t.StrSequence:
            """Immutable custom bead types required by Gas City."""
            ...

    @runtime_checkable
    class RepositoryRef(Protocol):
        """Repository fields consumed by codegen path and profile selection."""

        @property
        def name(self) -> str:
            """Repository catalog name."""
            ...

        @property
        def distribution(self) -> str:
            """Python distribution name."""
            ...

        @property
        def url(self) -> str:
            """Canonical Git URL."""
            ...

        @property
        def path(self) -> Path:
            """Repository path relative to its workspace root."""
            ...

        @property
        def role(self) -> str:
            """Repository role in the declared topology."""
            ...

        @property
        def state(self) -> str:
            """Repository lifecycle state."""
            ...

        @property
        def provider(self) -> str:
            """Provider catalog key owning Git policy for this repository."""
            ...

        @property
        def checkout(self) -> str:
            """Physical checkout topology."""
            ...

        @property
        def codegen(self) -> str:
            """Repository code-generation policy."""
            ...

        @property
        def package(self) -> bool:
            """Whether the repository publishes a Python package."""
            ...

        @property
        def editable(self) -> bool:
            """Whether the repository is overlaid as editable."""
            ...

        @property
        def read_only(self) -> bool:
            """Whether generated mutations are forbidden."""
            ...

    @runtime_checkable
    class ProjectSpec(Protocol):
        """Scaffold-only project metadata consumed by initial generation."""

        @property
        def version(self) -> str:
            """Declared release version, the SSOT for ``[project].version``."""
            ...

    @runtime_checkable
    class BeadsProjectSpec(Protocol):
        """Repository-local Beads identity contract."""

        @property
        def version(self) -> int:
            """Configuration schema version."""
            ...

        @property
        def workspace(self) -> str:
            """Stable workspace identity."""
            ...

        @property
        def database(self) -> str:
            """Repository-owned Dolt database."""
            ...

        @property
        def issue_prefix(self) -> str:
            """Repository-owned issue prefix."""
            ...

        @property
        def custom_issue_types(self) -> t.StrSequence:
            """Repository-owned types beyond the Gas City baseline."""
            ...

    class WorkspaceSpec(Protocol):
        """Workspace topology fields consumed by repository selection."""

        @property
        def repository(self) -> FlextInfraProtocolsBase.RepositoryRef:
            """Local repository."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsBase.BeadsProjectSpec:
            """Repository-local Beads identity."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsBase.ProjectSpec | None:
            """Scaffold metadata; ``None`` for an existing repository."""
            ...

        @property
        def subprojects(self) -> t.SequenceOf[FlextInfraProtocolsBase.RepositoryRef]:
            """Direct governed repositories declared by local .gitmodules."""
            ...

        @property
        def external_dependency_paths(self) -> t.SequenceOf[Path]:
            """Observed external or fork Git submodule paths."""
            ...

    @runtime_checkable
    class ProviderSpec(Protocol):
        """Provider-owned repository and baseline contract."""

        @property
        def name(self) -> str:
            """Provider key."""
            ...

        @property
        def organization(self) -> str:
            """Canonical GitHub organization."""
            ...

        @property
        def base_url(self) -> str:
            """Canonical provider HTTPS base URL."""
            ...

        @property
        def branch(self) -> str:
            """Provider-owned integration baseline."""
            ...

    @runtime_checkable
    class GithubPullRequestFields(Protocol):
        """Shared PR execution fields accepted at the transport boundary."""

        @property
        def action(self) -> c.Infra.PullRequestAction:
            """Requested PR operation."""
            ...

        @property
        def base(self) -> str | None:
            """Target branch when explicitly selected."""
            ...

        @property
        def head(self) -> str | None:
            """Source branch when explicitly selected."""
            ...

        @property
        def title(self) -> str | None:
            """PR title used for creation."""
            ...

        @property
        def body(self) -> str | None:
            """PR body used for creation."""
            ...

        @property
        def draft(self) -> bool:
            """Whether creation requests a draft PR."""
            ...

    @runtime_checkable
    class WorkspaceEnvironmentRequest(Protocol):
        """Read-only workspace environment validation request."""

        @property
        def workspace_root(self) -> Path:
            """Workspace whose active interpreter provenance must be validated."""
            ...

    @runtime_checkable
    class ToolchainSpec(Protocol):
        """Toolchain fields consumed by pyproject conformance and templates."""

        # Keep the protocol
        # complete with the validated config model used by codegen consumers.
        @property
        def python_version(self) -> str:
            """Compatible Python major.minor line."""
            ...

        @property
        def python_selector(self) -> str:
            """Mise/pyenv-style selector for the Python minor line."""
            ...

        @property
        def python_required_version(self) -> str:
            """PEP 440 requirement for the compatible Python line."""
            ...

        @property
        def uv_link_mode(self) -> str:
            """Portable uv installation link mode."""
            ...

        @property
        def dependency_cooldown_days(self) -> int:
            """Supply-chain cooldown shared by dependency update tools."""
            ...

        @property
        def dependency_cooldown_exclusions(self) -> t.StrSequence:
            """Packages exempted from cooldown for urgent security floors."""
            ...

        @property
        def dependency_cooldown_overrides(self) -> t.StrMapping:
            """Per-package cooldown cutoffs as RFC 3339 timestamps."""
            ...

        @property
        def uv_exclude_newer(self) -> str:
            """Uv exclude-newer cooldown window for dependency resolution."""
            ...

        # `uv_exclude_newer_package` used to sit here, undocumented and with no
        # implementation on ToolchainSpec, so the model never satisfied its own
        # protocol. `dependency_cooldown_overrides` above is that concept, named
        # for the policy rather than the uv key it renders into.

        @property
        def kubectl_version(self) -> str:
            """Exact kubectl version."""
            ...

        @property
        def helm_version(self) -> str:
            """Exact Helm version."""
            ...

        @property
        def kind_version(self) -> str:
            """Exact kind version."""
            ...

        @property
        def environment_path_prepends(self) -> t.SequenceOf[str]:
            """Extra directories prepended to PATH by shell activation."""
            ...

        @property
        def taplo_version(self) -> str:
            """Exact Taplo formatter version."""
            ...

        @property
        def ast_grep_version(self) -> str:
            """Exact ast-grep analyzer version."""
            ...

        @property
        def gitleaks_version(self) -> str:
            """Exact Gitleaks scanner version."""
            ...

        @property
        def tokei_version(self) -> str:
            """Exact Tokei analyzer version."""
            ...

        @property
        def qlty_version(self) -> str:
            """Exact qlty code-smell scanner version."""
            ...

        @property
        def uv_version(self) -> str:
            """Compatible uv major.minor line."""
            ...

        @property
        def go_version(self) -> str:
            """Exact Go runtime version backing go: mise selectors."""
            ...

        @property
        def mise_version(self) -> str:
            """Exact mise binary version."""
            ...

        @property
        def mise_lock_platforms(self) -> t.StrSequence:
            """Platforms materialized into the project mise lockfile."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsBase.BeadsToolSpec:
            """Official Beads CLI installed through mise."""
            ...

        @property
        def protected_mise_tools(self) -> t.StrSequence:
            """Toolchain field names protected from alternate distributions."""
            ...

    @runtime_checkable
    class TemplateEntrySpec(Protocol):
        """Template-entry fields consumed by scaffold root selection."""

        @property
        def destination(self) -> str:
            """Tokenized repository-relative destination."""
            ...

        @property
        def profiles(self) -> t.StrSequence:
            """Make profiles that consume the template."""
            ...

        @property
        def delegate(self) -> str:
            """Canonical template rendering delegate."""
            ...

    @classmethod
    def is_public_python_module_file(cls, file_name: str) -> bool:
        """Return whether a file names a public Python module."""
        ...

    @staticmethod
    def runtime_singleton_export(file_name: str) -> str | None:
        """Return the public singleton exported by a runtime module."""
        ...

    @staticmethod
    def ordered_namespace_exports(*, export_names: t.StrSequence) -> t.StrSequence:
        """Order root-package exports with alias hierarchy preserved."""
        ...

    @classmethod
    def matches_project_namespace_package(cls, package_name: str) -> bool:
        """Return whether a package is a governed project namespace root."""
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
            self, project: str, gates: t.StrSequence
        ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
            """Run quality gates for one project."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self, request: m.Infra.DocsGenerateRequest
        ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self, workspace_root: Path
        ) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
            """Discover projects in a workspace root."""
            ...

    @runtime_checkable
    class TomlReader(Protocol):
        """Contract for TOML file readers used by dependency services."""

        def read_plain(self, path: Path) -> p.Result[t.JsonMapping]:
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

    @runtime_checkable
    class WorkspaceReport(Protocol):
        """Protocol for workspace dependency report model contract."""

        pip_check: m.Infra.PipCheckReport | None
        dependency_limits: m.Infra.DependencyLimitsInfo | None

        def model_dump(self) -> t.MappingKV[str, t.Infra.InfraValue]:
            """Serialize report model payload."""
            ...

    @runtime_checkable
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self, path: Path, payload: t.MappingKV[str, t.Infra.InfraValue]
        ) -> p.Result[bool]:
            """Write payload to JSON file."""
            ...

    @runtime_checkable
    class ProjectReportLike(Protocol):
        """Protocol for project-level dependency report contracts."""

        def model_dump(self) -> t.MappingKV[str, t.Infra.InfraValue]:
            """Serialize project report payload."""
            ...

    @runtime_checkable
    class DepsService(Protocol):
        """Service for dependency detection across projects."""

        def discover_project_paths(
            self, workspace_root: Path, *, projects_filter: t.StrSequence | None = None
        ) -> p.Result[t.SequenceOf[Path]]:
            """Discover project paths in workspace root."""
            ...

        def run_deptry(
            self, project_path: Path, venv_bin: Path
        ) -> p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]:
            """Run deptry on a project and return issues."""
            ...

        def build_project_report(
            self, project_name: str, deptry_issues: t.SequenceOf[t.JsonMapping]
        ) -> FlextInfraProtocolsBase.ProjectReportLike:
            """Build project report from deptry issues."""
            ...

    @runtime_checkable
    class TypingsDepsService(Protocol):
        """Service for typing-related dependency detection."""

        def load_dependency_limits(
            self, limits_path: Path | None = None
        ) -> t.MappingKV[str, t.Infra.InfraValue]:
            """Load dependency limits from TOML file."""
            ...

        def get_required_typings(
            self,
            project_path: Path,
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
            self, workspace_root: Path, venv_bin: Path
        ) -> p.Result[t.Pair[t.StrSequence, int]]:
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
        ) -> p.Result[p.Cli.CommandOutput]:
            """Run command and return raw output."""
            ...

    @runtime_checkable
    class DetectorRuntime(Protocol):
        """Protocol for detector runtime service dependencies."""

        deps: FlextInfraProtocolsBase.DepsService
        runner: FlextInfraProtocolsBase.RunnerService

        @property
        def log(self) -> p.Logger: ...

    @runtime_checkable
    class ViolationWithLine(Protocol):
        """Protocol for violations that have a line number."""

        def model_dump(self) -> t.JsonMapping:
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
        ) -> p.Result[t.SequenceOf[p.Cli.CommandOutput]]:
            """Execute one make verb across multiple projects."""
            ...

    @runtime_checkable
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
            projects: t.SequenceOf[FlextInfraProtocolsBase.ProjectInfo] | None = None,
        ) -> t.SequenceOf[m.Infra.CensusReport]:
            """Run census and return typed reports."""
            ...

    @runtime_checkable
    class PyprojectModernizer(Protocol):
        """Protocol for pyproject.toml modernization services."""

        def execute(self) -> p.Result[bool]:
            """Execute modernization pass."""
            ...

    @runtime_checkable
    class GithubService(Protocol):
        """Protocol for GitHub operations services."""

        def execute(self) -> p.Result[bool]:
            """Execute GitHub operations."""
            ...

    @runtime_checkable
    class RefactorService(Protocol):
        """Protocol for rope-based refactor services."""

        def execute(self) -> p.Result[bool]:
            """Execute refactoring pass."""
            ...

    @runtime_checkable
    class ReleaseOrchestrator(Protocol):
        """Protocol for release orchestration services."""

        def execute(self) -> p.Result[bool]:
            """Execute release orchestration."""
            ...

    @runtime_checkable
    class SafeTransformer(Protocol):
        """Contract for transformers that run with copy-on-write protection."""

        def transform(self, files: t.SequenceOf[Path]) -> p.Result[t.SequenceOf[Path]]:
            """Apply transformation to files, return paths of modified files."""
            ...

    @runtime_checkable
    class SafeValidator(Protocol):
        """Contract for post-transform quality gate validators."""

        def validate(
            self, files: t.SequenceOf[Path], project_dir: Path
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

    @runtime_checkable
    class RefactorCliArgs(Protocol):
        """Structural protocol for the parsed refactor CLI argument bag.

        Replaces the prior ``argparse.Namespace`` annotation: the orchestrator
        and renderer consume only attribute access, so a structural protocol
        captures the contract without binding to argparse.
        """

        project: Path | None
        workspace: Path | None
        file: Path | None
        files: t.SequenceOf[Path] | None
        pattern: str
        dry_run: bool
        show_diff: bool
        analysis_output: Path | None
        impact_map_output: Path | None

    @runtime_checkable
    class GithubCliHandlers(Protocol):
        """Protocol for GitHub CLI handler mixins."""

        def sync_github_workflows(
            self, params: m.Infra.GithubWorkflowSyncRequest
        ) -> p.Result[m.Infra.GithubWorkflowSyncReport]:
            """Sync GitHub workflow files."""
            ...

        def lint_github_workflows(
            self, params: m.Infra.GithubWorkflowLintRequest
        ) -> p.Result[m.Infra.GithubWorkflowLintOutcome]:
            """Lint GitHub workflow files."""
            ...

        def run_github_pull_request(
            self, params: m.Infra.GithubPullRequestRequest
        ) -> p.Result[m.Infra.GithubPullRequestOutcome]:
            """Manage pull request for a single project."""
            ...

        def run_github_workspace_pull_requests(
            self, params: m.Infra.GithubPullRequestWorkspaceRequest
        ) -> p.Result[m.Infra.GithubPullRequestWorkspaceReport]:
            """Manage pull requests across the workspace."""
            ...
