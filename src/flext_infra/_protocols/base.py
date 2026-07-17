"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

# NOTE (multi-agent, mro-wkii.17.9.2.1): declaration-only protocol types stay
# behind one guard so structural contracts add no reverse runtime dependency.
if TYPE_CHECKING:
    # mro-wkii.17.26.2 (codex): these names are annotation-only reverse
    # edges; runtime imports create the proven p -> m/t facade cycle.
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from flext_cli import p as pc
    from flext_infra import p, t


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

    # NOTE (multi-agent, mro-wkii.17.16 / agent: codex): these declaration-only
    # contracts preserve config-model field types across the public p/u facades.
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
        def branch(self) -> str:
            """Canonical Git branch."""
            ...

        @property
        def path(self) -> Path:
            """Repository path relative to its workspace root."""
            ...

        @property
        def profile(self) -> str | None:
            """Generated Make profile when the repository is active."""
            ...

    @runtime_checkable
    class WorkspaceSpec(Protocol):
        """Workspace topology fields consumed by repository selection."""

        @property
        def repository(self) -> FlextInfraProtocolsBase.RepositoryRef:
            """Workspace root repository."""
            ...

        @property
        def members(self) -> t.SequenceOf[FlextInfraProtocolsBase.RepositoryRef]:
            """Attached workspace member repositories."""
            ...

        @property
        def content_only(self) -> t.SequenceOf[FlextInfraProtocolsBase.RepositoryRef]:
            """Declared content-only repositories."""
            ...

    @runtime_checkable
    class ToolchainSpec(Protocol):
        """Toolchain fields consumed by pyproject conformance."""

        # NOTE (multi-agent, mro-wkii.17 / agent: codex): keep the protocol
        # complete with the validated config model used by codegen consumers.
        @property
        def uv_link_mode(self) -> str:
            """Portable uv installation link mode."""
            ...

        @property
        def uv_required_version(self) -> str:
            """Required uv version expression."""
            ...

    @runtime_checkable
    class ScaffoldBuildSpec(Protocol):
        """Build backend fields consumed by pyproject conformance."""

        @property
        def backend(self) -> str:
            """PEP 517 backend import path."""
            ...

        @property
        def requirements(self) -> t.StrSequence:
            """Build-system requirements."""
            ...

    # mro-qc84 (fix-forward): protocol-of-model for the lazy-init policy config
    # (m.Infra.LazyInitConfig). Consumed at runtime by the lazy-init planner
    # pydantic field and by namespace policy utilities.
    @runtime_checkable
    class LazyInitConfig(Protocol):
        """Declarative lazy-init generation policy consumed by codegen."""

        @property
        def root_namespace_files(self) -> t.StrSequence:
            """Governed root facade filenames enforced by gen-init."""
            ...

        @property
        def public_file_aliases(self) -> t.StrMapping:
            """Canonical alias by governed root facade filename."""
            ...

        @property
        def public_file_suffixes(self) -> t.StrMapping:
            """Canonical class suffix by governed root facade filename."""
            ...

        @property
        def private_family_tokens(self) -> t.StrSequenceMapping:
            """Accepted family markers for private namespace packages."""
            ...

        @property
        def surface_prefixes(self) -> t.StrMapping:
            """Class prefixes by wrapper surface such as tests/examples/scripts."""
            ...

        @property
        def inherited_exports(self) -> t.StrSequenceMapping:
            """Allowed inherited exports from parent package by root surface."""
            ...

        @property
        def main_export_files(self) -> t.StrSequence:
            """Root files allowed to export module-level main()."""
            ...

        @property
        def side_effect_free_packages(self) -> t.StrSequence:
            """Package basenames whose generated initializer must not import siblings."""
            ...

    @runtime_checkable
    class ResourceSpec(Protocol):
        """Repository resource fields consumed by wheel conformance."""

        @property
        def source(self) -> Path:
            """Repository-relative resource directory."""
            ...

        @property
        def required(self) -> bool:
            """Whether the resource directory is mandatory."""
            ...

        @property
        def wheel_destination(self) -> str | None:
            """Package-relative wheel destination template."""
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
    def matches_root_namespace_file(cls, file_name: str) -> bool:
        """Return whether a file belongs to the governed root namespace."""
        ...

    @staticmethod
    def runtime_singleton_export(file_name: str) -> str | None:
        """Return the public singleton exported by a runtime module."""
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
        ) -> p.Result[t.SequenceOf[p.Infra.ProjectResult]]:
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
            settings: p.Infra.BaseMkConfig | None = None,
            canonical_root: Path | None = None,
        ) -> p.Result[p.Infra.SyncResult]:
            """Synchronize generated workspace or project artifacts."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self, request: p.Infra.DocsGenerateRequest
        ) -> p.Result[t.SequenceOf[p.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self, workspace_root: Path
        ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
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

        def scan_file(self, *, file_path: Path) -> p.Infra.ScanResult:
            """Scan a single file and return scan result."""
            ...

    @runtime_checkable
    class WorkspaceReport(Protocol):
        """Protocol for workspace dependency report model contract."""

        pip_check: p.Infra.PipCheckReport | None
        dependency_limits: p.Infra.DependencyLimitsInfo | None

        def model_dump(self) -> t.MappingKV[str, t.JsonValue]:
            """Serialize report model payload."""
            ...

    @runtime_checkable
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self, path: Path, payload: t.MappingKV[str, t.JsonValue]
        ) -> p.Result[bool]:
            """Write payload to JSON file."""
            ...

    @runtime_checkable
    class ProjectReportLike(Protocol):
        """Protocol for project-level dependency report contracts."""

        def model_dump(self) -> t.MappingKV[str, t.JsonValue]:
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
        ) -> p.Result[t.Pair[t.SequenceOf[t.Infra.ContainerDict], int]]:
            """Run deptry on a project and return issues."""
            ...

        def build_project_report(
            self, project_name: str, deptry_issues: t.SequenceOf[t.Infra.ContainerDict]
        ) -> FlextInfraProtocolsBase.ProjectReportLike:
            """Build project report from deptry issues."""
            ...

    @runtime_checkable
    class TypingsDepsService(Protocol):
        """Service for typing-related dependency detection."""

        def load_dependency_limits(
            self, limits_path: Path | None = None
        ) -> t.MappingKV[str, t.JsonValue]:
            """Load dependency limits from TOML file."""
            ...

        def get_required_typings(
            self,
            project_path: Path,
            limits_path: Path | None = None,
            *,
            include_mypy: bool = True,
        ) -> p.Result[p.Infra.TypingsReport]:
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
        ) -> p.Result[pc.Cli.CommandOutput]:
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
    class TemplateRenderer(Protocol):
        """Protocol for template renderers."""

        def render_all(
            self, settings: p.Infra.BaseMkConfig | None = None
        ) -> p.Result[str]:
            """Render all templates with given configuration."""
            ...

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
        ) -> p.Result[t.SequenceOf[pc.Cli.CommandOutput]]:
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
        ) -> t.SequenceOf[p.Infra.CensusReport]:
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
        ) -> p.Result[p.Infra.GateResult]:
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
            self, params: p.Infra.GithubWorkflowSyncRequest
        ) -> p.Result[p.Infra.GithubWorkflowSyncReport]:
            """Sync GitHub workflow files."""
            ...

        def lint_github_workflows(
            self, params: p.Infra.GithubWorkflowLintRequest
        ) -> p.Result[p.Infra.GithubWorkflowLintOutcome]:
            """Lint GitHub workflow files."""
            ...

        def run_github_pull_request(
            self, params: p.Infra.GithubPullRequestRequest
        ) -> p.Result[p.Infra.GithubPullRequestOutcome]:
            """Manage pull request for a single project."""
            ...

        def run_github_workspace_pull_requests(
            self, params: p.Infra.GithubPullRequestWorkspaceRequest
        ) -> p.Result[p.Infra.GithubPullRequestWorkspaceReport]:
            """Manage pull requests across the workspace."""
            ...

    # mro-qc84 (fix-forward): protocol-of-model namespace mirroring the census
    # model namespace (m.Infra.Census). Consumed at runtime by the census
    # service base ``s[p.Infra.Census.WorkspaceReport]`` and quality gates.
    @runtime_checkable
    class Census(Protocol):
        """Structural namespace for workspace census report contracts."""

        @runtime_checkable
        class ReferenceSite(Protocol):
            """Single reference site for a workspace object."""

            @property
            def line(self) -> int: ...

            @property
            def file_path(self) -> str: ...

            @property
            def surface(self) -> str: ...

        @runtime_checkable
        class Object(Protocol):
            """Single workspace object with tier and reference metadata."""

            @property
            def class_path(self) -> str: ...

            @property
            def project(self) -> str: ...

            @property
            def line(self) -> int: ...

            @property
            def file_path(self) -> str: ...

            @property
            def name(self) -> str: ...

            @property
            def kind(self) -> str: ...

            @property
            def module_name(self) -> str: ...

            @property
            def scope_path(self) -> str: ...

            @property
            def actual_tier(self) -> str: ...

            @property
            def expected_tier(self) -> str: ...

            @property
            def is_facade_member(self) -> bool: ...

            @property
            def references_count(self) -> int: ...

            @property
            def runtime_references_count(self) -> int: ...

            @property
            def example_references_count(self) -> int: ...

            @property
            def script_references_count(self) -> int: ...

            @property
            def runtime_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

            @property
            def example_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

            @property
            def script_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

            @property
            def fingerprint(self) -> str: ...

        @runtime_checkable
        class Violation(Protocol):
            """Single namespace or tier violation for an object."""

            @property
            def project(self) -> str: ...

            @property
            def object_name(self) -> str: ...

            @property
            def object_kind(self) -> str: ...

            @property
            def kind(self) -> str: ...

            @property
            def severity(self) -> str: ...

            @property
            def file_path(self) -> str: ...

            @property
            def line(self) -> int: ...

            @property
            def fixable(self) -> bool: ...

            @property
            def fix_action(self) -> str: ...

            @property
            def description(self) -> str: ...

        @runtime_checkable
        class Fix(Protocol):
            """Single applied or planned fix for a workspace object."""

            @property
            def object_name(self) -> str: ...

            @property
            def action(self) -> str: ...

            @property
            def source_file(self) -> str: ...

            @property
            def target_file(self) -> str: ...

            @property
            def files_changed(self) -> int: ...

            @property
            def applied(self) -> bool: ...

            @property
            def dry_run_diff(self) -> str: ...

        @runtime_checkable
        class RemovalCandidate(Protocol):
            """Single dead-code removal candidate object."""

            @property
            def project(self) -> str: ...

            @property
            def line(self) -> int: ...

            @property
            def file_path(self) -> str: ...

            @property
            def object_name(self) -> str: ...

            @property
            def object_kind(self) -> str: ...

            @property
            def scope_path(self) -> str: ...

            @property
            def reason(self) -> str: ...

            @property
            def suggested_action(self) -> str: ...

            @property
            def runtime_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

            @property
            def example_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

            @property
            def script_reference_sites(
                self,
            ) -> t.SequenceOf[p.Infra.Census.ReferenceSite]: ...

        @runtime_checkable
        class DuplicateGroup(Protocol):
            """Group of duplicate object definitions sharing one name."""

            @property
            def name(self) -> str: ...

            @property
            def kind(self) -> str: ...

            @property
            def definitions(self) -> t.SequenceOf[p.Infra.Census.Object]: ...

            @property
            def canonical(self) -> str: ...

            @property
            def value_identical(self) -> bool: ...

        @runtime_checkable
        class ScanConfig(Protocol):
            """Selection policy applied to a census scan."""

            @property
            def kind_names(self) -> t.StrSequence | None: ...

            @property
            def rule_names(self) -> t.StrSequence | None: ...

            @property
            def selected_families(self) -> frozenset[str]: ...

            @property
            def selected_kinds(self) -> frozenset[str] | None: ...

            @property
            def selected_rules(self) -> frozenset[str] | None: ...

            @property
            def collect_object_inventory(self) -> bool: ...

            @property
            def include_object_references(self) -> bool: ...

            @property
            def include_local_scopes(self) -> bool: ...

            @property
            def applied(self) -> frozenset[str]: ...

        @runtime_checkable
        class ProjectReport(Protocol):
            """Per-project census aggregate."""

            @property
            def project(self) -> str: ...

            @property
            def objects(self) -> t.SequenceOf[p.Infra.Census.Object]: ...

            @property
            def objects_total(self) -> int: ...

            @property
            def objects_by_kind(self) -> t.IntMapping: ...

            @property
            def violations(self) -> t.SequenceOf[p.Infra.Census.Violation]: ...

            @property
            def fixes(self) -> t.SequenceOf[p.Infra.Census.Fix]: ...

            @property
            def violations_total(self) -> int: ...

            @property
            def fixes_applied(self) -> int: ...

            @property
            def unused_count(self) -> int: ...

            @property
            def removal_candidate_count(self) -> int: ...

            @property
            def removal_candidates(
                self,
            ) -> t.SequenceOf[p.Infra.Census.RemovalCandidate]: ...

        @runtime_checkable
        class WorkspaceReport(Protocol):
            """Workspace-wide census aggregate report."""

            @property
            def projects(self) -> t.SequenceOf[p.Infra.Census.ProjectReport]: ...

            @property
            def total_objects(self) -> int: ...

            @property
            def total_violations(self) -> int: ...

            @property
            def total_fixable(self) -> int: ...

            @property
            def fixes_total(self) -> int: ...

            @property
            def duplicates(self) -> t.SequenceOf[p.Infra.Census.DuplicateGroup]: ...

            @property
            def unused_count(self) -> int: ...

            @property
            def removal_candidate_count(self) -> int: ...

            @property
            def removal_candidates(
                self,
            ) -> t.SequenceOf[p.Infra.Census.RemovalCandidate]: ...

            @property
            def scan_duration_seconds(self) -> float: ...

            @property
            def parse_errors(self) -> int: ...

    # mro-qc84 (fix-forward): protocol-of-model for a workspace sync outcome
    # (m.Infra.SyncResult). Consumed at runtime by ``s[p.Infra.SyncResult]``.
    @runtime_checkable
    class SyncResult(Protocol):
        """Result payload for workspace sync operations."""

        @property
        def files_changed(self) -> int: ...

        @property
        def source(self) -> Path: ...

        @property
        def target(self) -> Path: ...

        @property
        def timestamp(self) -> datetime: ...

    # mro-qc84 (fix-forward): protocol-of-model for a workspace migration
    # outcome (m.Infra.MigrationResult). Consumed at runtime by the migrator
    # service ``s[t.SequenceOf[p.Infra.MigrationResult]]``.
    @runtime_checkable
    class MigrationResult(Protocol):
        """Migration operation outcome with applied changes and errors."""

        @property
        def project(self) -> str: ...

        @property
        def changes(self) -> t.StrSequence: ...

        @property
        def errors(self) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for one accessor-migration file
    # entry (m.Infra.AccessorMigrationFile).
    @runtime_checkable
    class AccessorMigrationFile(Protocol):
        """Per-file accessor-migration outcome entry."""

        @property
        def path(self) -> str: ...

        @property
        def automated_changes(self) -> int: ...

        @property
        def warnings(self) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for the accessor-migration
    # workspace report (m.Infra.AccessorMigrationReport). Consumed at runtime by
    # ``FlextInfraProjectSelectionServiceBase[p.Infra.AccessorMigrationReport]``.
    @runtime_checkable
    class AccessorMigrationReport(Protocol):
        """Workspace-scale accessor-migration orchestration report."""

        @property
        def workspace(self) -> str: ...

        @property
        def dry_run(self) -> bool: ...

        @property
        def files_scanned(self) -> int: ...

        @property
        def files_with_changes(self) -> int: ...

        @property
        def automated_change_count(self) -> int: ...

        @property
        def warning_count(self) -> int: ...

        @property
        def lint_tools(self) -> t.SequenceOf[str]: ...

        @property
        def lint_before_totals(self) -> t.IntMapping: ...

        @property
        def lint_after_totals(self) -> t.IntMapping: ...

        @property
        def new_lint_error_totals(self) -> t.IntMapping: ...

        @property
        def files(self) -> t.SequenceOf[p.Infra.AccessorMigrationFile]: ...

    # mro-qc84 (fix-forward): protocol-of-model for the canonical Make contract
    # embedded in a codegen plan (m.Infra.MakeSpec).
    @runtime_checkable
    class MakeSpec(Protocol):
        """Canonical Make contract fields consumed by codegen conformance."""

        @property
        def selector(self) -> str: ...

        @property
        def apply_variable(self) -> str: ...

        @property
        def apply_value(self) -> str: ...

        @property
        def verbs(self) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for a per-project uv plan
    # (m.Infra.UvEnvironmentPlan).
    @runtime_checkable
    class UvEnvironmentPlan(Protocol):
        """uv environment plan paired with one selected repository."""

        @property
        def project_root(self) -> Path: ...

        @property
        def environment_root(self) -> Path: ...

        @property
        def lock_path(self) -> Path: ...

        @property
        def python_version(self) -> str: ...

        @property
        def uv_version(self) -> str: ...

        @property
        def groups(self) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for a single managed-file render
    # plan (m.Infra.CodegenFilePlan).
    @runtime_checkable
    class CodegenFilePlan(Protocol):
        """Validated render result for one managed file."""

        @property
        def path(self) -> Path: ...

        @property
        def operation(self) -> str: ...

        @property
        def source_path(self) -> Path | None: ...

        @property
        def rendered(self) -> str: ...

        @property
        def expected_sha256(self) -> str: ...

    # mro-qc84 (fix-forward): protocol-of-model for the public codegen conform
    # request (m.Infra.CodegenConformRequest).
    @runtime_checkable
    class CodegenConformRequest(Protocol):
        """Validated public request governing a conformance run."""

        @property
        def root(self) -> Path: ...

        @property
        def what(self) -> str: ...

        @property
        def scope(self) -> str: ...

        @property
        def mode(self) -> str: ...

    # mro-qc84 (fix-forward): protocol-of-model for the fully validated codegen
    # plan (m.Infra.CodegenPlan).
    @runtime_checkable
    class CodegenPlan(Protocol):
        """Fully validated plan produced before any managed-file write."""

        @property
        def request(self) -> p.Infra.CodegenConformRequest: ...

        @property
        def repositories(self) -> t.SequenceOf[p.Infra.RepositoryRef]: ...

        @property
        def workspace(self) -> p.Infra.WorkspaceSpec: ...

        @property
        def make_spec(self) -> p.Infra.MakeSpec: ...

        @property
        def uv_environments(self) -> t.SequenceOf[p.Infra.UvEnvironmentPlan]: ...

        @property
        def files(self) -> t.SequenceOf[p.Infra.CodegenFilePlan]: ...

    # mro-qc84 (fix-forward): protocol-of-model for the codegen conformance
    # outcome (m.Infra.CodegenResult). Consumed at runtime by the conform
    # service base ``s[p.Infra.CodegenResult]``.
    @runtime_checkable
    class CodegenResult(Protocol):
        """Public conformance outcome for check and apply modes."""

        @property
        def plan(self) -> p.Infra.CodegenPlan: ...

        @property
        def written_files(self) -> t.SequenceOf[Path]: ...

        @property
        def errors(self) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for one lazy-init package context
    # (m.Infra.LazyInitPackageContext). Consumed by the lazy-init planner and the
    # import-facade gate; annotation-only, resolves a pre-existing missing-attr.
    @runtime_checkable
    class LazyInitPackageContext(Protocol):
        """Declarative package context for one lazy-init directory."""

        @property
        def pkg_dir(self) -> Path: ...

        @property
        def init_path(self) -> Path: ...

        @property
        def current_pkg(self) -> str: ...

        @property
        def surface(self) -> str: ...

        @property
        def generated_init(self) -> bool: ...

        @property
        def importable(self) -> bool: ...
