"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from types import FunctionType
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import p

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import c, m
    from flext_infra._protocols import (
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsRope,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsWorkspaceSnapshot,
    )


@runtime_checkable
class FlextInfraProtocolsBase(Protocol):
    """Base protocols for flext-infra project."""

    @runtime_checkable
    class CommandPayloadContext(Protocol):
        """Normalized command values consumed by the shared payload builder."""

        @property
        def repository_root(self) -> Path: ...

        @property
        def apply_changes(self) -> bool: ...

        @property
        def check_only(self) -> bool: ...

        @property
        def dry_run(self) -> bool: ...

        @property
        def output_format(self) -> str: ...

        @property
        def project_filter(self) -> str | None: ...

        @property
        def report_path(self) -> Path | None: ...

        @property
        def output_dir(self) -> Path | None: ...

    @runtime_checkable
    class ValidationReportOutcome(Protocol):
        """Validation facts consumed by the command execution boundary."""

        @property
        def passed(self) -> bool: ...

        @property
        def summary(self) -> str: ...

    @runtime_checkable
    class CodegenFilePublisher(Protocol):
        """Normalize and publish the same guarded generation plans.

        The composition root supplies the existing publication owner by
        reference; consumers never assemble the aggregate utility facade.
        """

        def normalized_codegen_changes(
            self,
            plans: Sequence[m.Infra.CodegenFilePlan],
        ) -> p.Result[tuple[m.Cli.FileChange, ...]]: ...

        def publish_codegen_plans(
            self,
            root: Path,
            plans: Sequence[m.Infra.CodegenFilePlan],
        ) -> p.Result[tuple[Path, ...]]: ...

    @runtime_checkable
    class CodegenConformPorts(Protocol):
        """Caller-bound cross-family capabilities consumed by conform."""

        @property
        def docs_planner(
            self,
        ) -> FlextInfraProtocolsBase.DocsArtifactPlannerFactory: ...

        @property
        def file_publisher(self) -> FlextInfraProtocolsBase.CodegenFilePublisher: ...

        @property
        def source_preview(self) -> FlextInfraProtocolsBase.SourcePreview: ...

        @property
        def candidate_validator(
            self,
        ) -> Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]: ...

        @property
        def imports_planner(
            self,
        ) -> FlextInfraProtocolsBase.SourceImportPlanner: ...

        @property
        def component_planner(
            self,
        ) -> FlextInfraProtocolsBase.SourceComponentPlanner: ...

    @runtime_checkable
    class CodegenGenerateRequest(Protocol):
        """Read-only selectors consumed by the projection execution boundary."""

        @property
        def root(self) -> Path: ...

        @property
        def what(self) -> c.Infra.CodegenConformSurface: ...

        @property
        def scope(self) -> c.Infra.CodegenConformScope: ...

        @property
        def module(self) -> str | None: ...

    @runtime_checkable
    class CodegenConformRequest(CodegenGenerateRequest, Protocol):
        """Explicit observation or repair of the selected projection surface."""

        @property
        def mode(self) -> c.Infra.CodegenConformMode: ...

        @property
        def declaration_kind(self) -> c.Infra.ProjectKind | None: ...

    @runtime_checkable
    class CodegenFileOutcome(Protocol):
        """Planned destination and bytes exposed to public generation consumers."""

        @property
        def path(self) -> Path: ...

        @property
        def desired_content(self) -> bytes | None: ...

    @runtime_checkable
    class CodegenPlanOutcome(Protocol):
        """Public plan membership, separate from the internal publication schema."""

        @property
        def files(self) -> Sequence[FlextInfraProtocolsBase.CodegenFileOutcome]: ...

        @property
        def repositories(
            self,
        ) -> Sequence[FlextInfraProtocolsBase.RepositoryRef]: ...

    @runtime_checkable
    class CodegenResult(Protocol):
        """Generation or observation facts consumed by public callers."""

        @property
        def plan(self) -> FlextInfraProtocolsBase.CodegenPlanOutcome: ...

        @property
        def written_files(self) -> tuple[Path, ...]: ...

        @property
        def errors(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class CodegenExecutionContext(Protocol):
        """Actual caller runtime and its explicitly bound conform capabilities."""

        @property
        def settings(self) -> p.Settings: ...

        @property
        def context(self) -> p.Context: ...

        def codegen_conform_collaborators(
            self,
        ) -> FlextInfraProtocolsBase.CodegenConformPorts | None: ...

    @runtime_checkable
    class CodegenService(CodegenExecutionContext, p.Service[t.JsonDict], Protocol):
        """Public codegen operations bound to the caller's execution context."""

        def codegen_generate(
            self,
            request: FlextInfraProtocolsBase.CodegenGenerateRequest,
        ) -> p.Result[FlextInfraProtocolsBase.CodegenResult]: ...

        def codegen_conform(
            self,
            request: FlextInfraProtocolsBase.CodegenConformRequest,
        ) -> p.Result[FlextInfraProtocolsBase.CodegenResult]: ...

    @runtime_checkable
    class FunctionDescriptor(Protocol):
        """Native descriptor capability used to authenticate its defining function."""

        __func__: FunctionType

    @runtime_checkable
    class GitIndexLock(Protocol):
        """Native gitdb LockedFD capability consumed by index publication."""

        def open(self, *, write: Literal[True], stream: Literal[False]) -> int:
            """Acquire the native index lock and return its owned raw descriptor."""
            ...

        def commit(self) -> None:
            """Close the descriptor and publish its locked replacement."""
            ...

        def rollback(self) -> None:
            """Close the descriptor and remove only its unpublished lock."""
            ...

    @runtime_checkable
    class SourceImportPlanner(Protocol):
        """Plan canonical imports from one proposed workspace source epoch."""

        def __call__(
            self,
            project_root: Path,
            files: Sequence[Path],
            *,
            sources: Mapping[Path, str],
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot,
        ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
            """Return source-preserving import plans without publishing them."""
            ...

    @runtime_checkable
    class SourceInitializerPlanner(Protocol):
        """Plan exports for a facade, an initializer/package, or the whole candidate."""

        def __call__(
            self,
            root: Path,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot,
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]: ...

    @runtime_checkable
    class SourceViewProvider(Protocol):
        """Borrow the caller-owned native view for one candidate source epoch.

        Identical effective bytes and tombstones under the same root share the
        invocation's existing view. Changed candidates require another binding;
        the caller retains original file witnesses, snapshot authority and teardown.
        """

        def __call__(
            self,
            root: Path,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        ) -> AbstractContextManager[
            tuple[
                FlextInfraProtocolsRopeRuntime.RopeProject,
                Mapping[Path, str],
            ]
        ]: ...

    @runtime_checkable
    class SourceComponentPlanner(Protocol):
        """Close a facade or package cohort; no selection means every family."""

        def __call__(
            self,
            root: Path,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot,
            planners: tuple[
                FlextInfraProtocolsBase.SourceInitializerPlanner,
                FlextInfraProtocolsBase.SourceViewProvider,
            ],
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]: ...

    @runtime_checkable
    class SourceImportNormalizer(Protocol):
        """Normalize source imports through the caller's explicit service binding."""

        def __call__(
            self,
            *,
            project_root: Path,
            file_path: Path,
            source: str,
            import_graph: Mapping[str, frozenset[str]],
            sources: Mapping[Path, str],
        ) -> str | None:
            """Return normalized source, or None when no import changes are needed."""
            ...

    @runtime_checkable
    class SourcePreview(Protocol):
        """Consumer-owned capability for validating authenticated source views."""

        def preview_sources[T](
            self,
            workspace: Path,
            updates: Mapping[Path, str | None],
            validator: Callable[[Path, Mapping[Path, Path]], T],
            *,
            options: m.Infra.CodegenSourcePreviewOptions | None = None,
        ) -> p.Result[T]:
            """Validate staged updates and retirements while preserving live sources."""
            ...

    @runtime_checkable
    class ExternalCacheDirectory(Protocol):
        """Shared consumer contract for declared tool cache placement."""

        @property
        def data_home_environment_variable(self) -> str: ...

        @property
        def user_home_environment_variable(self) -> str: ...

        @property
        def home_cache_directory(self) -> Path: ...

        @property
        def external_storage_directory(self) -> Path: ...

    @runtime_checkable
    class PytestStopController(Protocol):
        """Native distributed controller's mutable stop request."""

        shouldstop: bool | str

    @runtime_checkable
    class PytestWorkerConfig(Protocol):
        """Native xdist config's output channel for plugin-owned JSON payloads."""

        @property
        def workeroutput(self) -> MutableMapping[str, object]: ...

    @runtime_checkable
    class SupervisedProcess(Protocol):
        """Process lifecycle consumed by the infrastructure resource supervisor."""

        @property
        def pid(self) -> int:
            """Native process identifier."""
            ...

        def poll(self) -> int | None:
            """Return the native exit code once the process has ended."""
            ...

        def wait(self) -> p.Result[int]:
            """Reap the process and preserve its native result."""
            ...

    @runtime_checkable
    class RenameCampaignRunner(Protocol):
        """Apply or inspect one validated CSV rename campaign."""

        def run(
            self,
            params: m.Infra.ApplyRenamesInput,
        ) -> p.Result[m.Infra.ApplyRenamesReport]: ...

    @runtime_checkable
    class SemanticRenameCandidateProvider(Protocol):
        """Select meaningful names from actual declarations, never token counts."""

        def rename_decision(
            self,
            declaration: m.Infra.Object,
        ) -> m.Infra.SemanticRenameDecision | None: ...

    @runtime_checkable
    class GateAttestationRuntimeContext(Protocol):
        """Read-only elected resolution inputs the toolchain trust anchor hashes.

        The attestation layer never resolves the workspace itself: the caller
        elects the current runtime context once at the workspace boundary and
        provides it explicitly, keeping the dependency direction downward.
        """

        @property
        def runtime_root(self) -> Path:
            """Physical runtime owner of the elected resolution input."""
            ...

        @property
        def pyproject_path(self) -> Path:
            """Declaration file the resolver elected."""
            ...

        @property
        def lock_path(self) -> Path:
            """Lock file the resolver elected."""
            ...

    @runtime_checkable
    class RuleDeltaSpec(Protocol):
        """Read-only structural contract for rule delta comparison options."""

        @property
        def inventory(self) -> tuple[tuple[str, str], ...]: ...

        @property
        def repository_root(self) -> Path | None: ...

        @property
        def projects(self) -> Sequence[Path]: ...

    @runtime_checkable
    class ChainDeclarationSpec(Protocol):
        """Read-only structural contract for binding-chain declaration inputs."""

        @property
        def project(self) -> FlextInfraProtocolsRopeRuntime.RopeProject: ...

        @property
        def holder(self) -> FlextInfraProtocolsRopeRuntime.RopePyModule: ...

        @property
        def holder_text(self) -> str: ...

        @property
        def declaration(self) -> m.Infra.LogicalStatement: ...

        @property
        def holder_offset(self) -> int: ...

        @property
        def holder_scope(self) -> FlextInfraProtocolsRopeRuntime.RopeScope: ...

        @property
        def expression(self) -> str: ...

        @property
        def sources(self) -> Mapping[Path, str]: ...

    @runtime_checkable
    class ModProgress(Protocol):
        """Report long-running mod phases to the calling transport."""

        def emit(self, message: str) -> None: ...

        def emit_rename(self, report: m.Infra.ApplyRenamesReport) -> None: ...

    @runtime_checkable
    class ModExecutionContext(Protocol):
        """Capabilities supplied by the public API's MRO composition."""

        def rope_workspace(
            self,
            repository_root: Path | None = None,
            rope_repository_root: Path | None = None,
        ) -> FlextInfraProtocolsRope.RopeWorkspaceDsl: ...

        @staticmethod
        def source_preview(
            repository_root: Path,
        ) -> FlextInfraProtocolsBase.SourcePreview: ...

    @runtime_checkable
    class ModLoopPhase(Protocol):
        """One repair owner with pure planning and standalone publication ports.

        A phase receives the loop's current scan state and the shared Rope
        workspace, applies its own repairs, and returns whether it changed
        sources — the loop then refreshes Rope, rescans, and continues toward
        the joint fixed point.
        """

        name: str

        def plan(
            self,
            root: Path,
            preflight: m.Infra.ModScanReport,
            rope_workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
            *,
            sources: Mapping[Path, str],
        ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]: ...

        def apply(
            self,
            root: Path,
            preflight: m.Infra.ModScanReport,
            rope_workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
        ) -> p.Result[bool]: ...

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
                | Sequence[t.JsonValue]
                | t.StrPairSequence
                | Sequence[t.StrSequencePair]
                | Sequence[t.StrPairSequencePair]
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

    @runtime_checkable
    class ProjectSpec(Protocol):
        """Elected project identity consumed directly by source projections."""

        @property
        def repository_root_rel(self) -> str:
            """Declared relative path from the project to its workspace root."""
            ...

        @property
        def package_name(self) -> str: ...

        @property
        def class_stem(self) -> str: ...

        @property
        def upstream(self) -> str: ...

        @property
        def namespace(self) -> str: ...

    @runtime_checkable
    class CandidateBootstrapPlanner(Protocol):
        """Conform plan boundary consumed by the candidate campaign."""

        def surface_contract(
            self,
            surface: c.Infra.CodegenConformSurface,
            *,
            codegen: m.Infra.CodegenConfigSpec,
        ) -> m.Infra.CodegenConformSurfaceContract:
            """Resolve the declared output set for a recovery surface."""
            ...

        def plan_repositories(
            self,
            request: FlextInfraProtocolsBase.CodegenGenerateRequest,
            inputs: m.Infra.CodegenInputs,
        ) -> p.Result[m.Infra.CodegenPlan]:
            """Plan one declared target from its captured inputs without publishing."""
            ...

    @runtime_checkable
    class DocsArtifactPlanner(Protocol):
        """Docs render planned as file changes for the shared publisher."""

        def prepare_bundle(
            self,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
        ) -> p.Result[m.Infra.DocsGenerationBundle]:
            """Freeze one configured inventory and its consumed inputs."""
            ...

        def plan_files(
            self,
            bundle: m.Infra.DocsGenerationBundle,
        ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
            """Plan the rendered documentation as file changes."""
            ...

    @runtime_checkable
    class DocsArtifactPlannerFactory(Protocol):
        """Build the docs planner for one conform scope."""

        def __call__(
            self,
            *,
            repository_root: Path,
            projects: Sequence[str],
            include_root: bool,
        ) -> FlextInfraProtocolsBase.DocsArtifactPlanner:
            """Bind the planner to the repositories conform publishes."""
            ...

    @runtime_checkable
    class GateExecutionParams(Protocol):
        """Read-only assembly boundary separating acceptance and native outcome."""

        @property
        def project_dir(self) -> Path:
            """Project whose gate was executed."""
            ...

        @property
        def verdict(self) -> bool:
            """Acceptance decided by the caller."""
            ...

        @property
        def outcome(self) -> c.Infra.ToolOutcome | None:
            """Declared native tool outcome; absent derives it from findings."""
            ...

        @property
        def issues(self) -> Sequence[FlextInfraProtocolsCheck.Issue]:
            """Complete native diagnostics."""
            ...

        @property
        def raw_output(self) -> str:
            """Unmodified native output."""
            ...

        @property
        def started(self) -> float:
            """Monotonic execution start time."""
            ...

    @runtime_checkable
    class MarkdownFormatGate(Protocol):
        """Markdown formatting gate the docs formatter delegates to."""

        def check(
            self,
            project_dir: Path,
            ctx: m.Infra.GateContext,
        ) -> m.Infra.GateExecution:
            """Report pending formatting without writing."""
            ...

        def fix(
            self,
            project_dir: Path,
            ctx: m.Infra.GateContext,
        ) -> m.Infra.GateExecution:
            """Apply formatting."""
            ...

    @runtime_checkable
    class MarkdownFormatGateFactory(Protocol):
        """Build the markdown format gate for one docs scope."""

        def __call__(
            self,
            repository_root: Path,
        ) -> FlextInfraProtocolsBase.MarkdownFormatGate:
            """Bind the gate to the scope root."""
            ...

    # These declaration-only
    # contracts preserve config-model field types across the public p/u facades.
    @runtime_checkable
    class BeadsToolSpec(Protocol):
        """Beads ledger and Gas City projection contract."""

        @property
        def endpoint_origin(self) -> str:
            """Gas City-owned endpoint inheritance mode."""
            ...

        @property
        def endpoint_status(self) -> str:
            """Canonical inherited endpoint status."""
            ...

        @property
        def required_custom_types(self) -> Sequence[str]:
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
        def custom_issue_types(self) -> Sequence[str]:
            """Repository-owned types beyond the Gas City baseline."""
            ...

    @runtime_checkable
    class WorkspaceSpec(Protocol):
        """Workspace topology fields consumed by repository selection."""

        @property
        def repository(self) -> FlextInfraProtocolsBase.RepositoryRef:
            """Local repository."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsBase.BeadsProjectSpec | None:
            """Dormant auxiliary identity, absent from active topology."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsBase.ProjectSpec | None:
            """Scaffold metadata; ``None`` for an existing repository."""
            ...

        @property
        def subprojects(self) -> Sequence[FlextInfraProtocolsBase.RepositoryRef]:
            """Direct governed repositories declared by local .gitmodules."""
            ...

        @property
        def external_dependency_paths(self) -> Sequence[Path]:
            """Observed external or fork Git submodule paths."""
            ...

    @runtime_checkable
    class WorkspaceRequest(Protocol):
        """One explicit repository target for read-only workspace operations."""

        @property
        def repository_root(self) -> Path:
            """Repository whose owned environment or lock must be validated."""
            ...

    @runtime_checkable
    class ModRequest(WorkspaceRequest, Protocol):
        """Validated inputs consumed by the public codemod handler."""

        @property
        def apply(self) -> bool: ...

        @property
        def check(self) -> bool: ...

        @property
        def dry_run_mode(self) -> bool: ...

        @property
        def rename_plan(self) -> Path | None: ...

        @property
        def consumer_roots(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class WorkspaceEnvironmentContracts(Protocol):
        """Structural contract the direnv gate consumes for static lint.

        Declared here so the gate depends on the typed boundary rather than on
        the concrete workspace class; one implementor owns the behavior today.
        """

        @classmethod
        def envrc_contract_violations(
            cls,
            content: str,
            *,
            root: Path,
            resolve_home: bool = True,
        ) -> tuple[m.Infra.EnvironmentContractViolation, ...]:
            """Return one typed violation per direnv contract issue."""
            ...

        @classmethod
        def envrc_local_contract_violations(
            cls,
            content: str,
        ) -> tuple[m.Infra.EnvironmentContractViolation, ...]:
            """Return one typed violation per activation residue in overrides."""
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
        def dependency_cooldown_days(self) -> int:
            """Supply-chain cooldown in days honoured by every resolver."""
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
        def uv_environments(self) -> Sequence[str]:
            """Marker expressions limiting the uv-resolved lock environments."""
            ...

        @property
        def uv_constraint_dependencies(self) -> Sequence[str]:
            """SSOT-declared [tool.uv] constraints; empty exterminates the key."""
            ...

        @property
        def environment_path_prepends(self) -> Sequence[str]:
            """Extra directories prepended to PATH by shell activation."""
            ...

        @property
        def tool_versions(self) -> Mapping[str, str]:
            """Effective release selector per tool: pins layered over entries."""
            ...

        @property
        def tool_selectors(self) -> Mapping[str, str]:
            """Declared Mise selector of every selector-bearing fleet tool."""
            ...

    @runtime_checkable
    class TemplateEntrySpec(Protocol):
        """Template-entry fields consumed by scaffold root selection."""

        @property
        def destination(self) -> str:
            """Tokenized repository-relative destination."""
            ...

        @property
        def profiles(self) -> Sequence[str]:
            """Make profiles that consume the template."""
            ...

        @property
        def source(self) -> Path | None:
            """Catalog template source, absent for a specialized owner."""
            ...

    @runtime_checkable
    class Validator(Protocol):
        """Contract for validation services."""

        def validate(self, argv: Sequence[str] | None = None) -> p.Result[int]:
            """Execute validation and return result."""
            ...

    @runtime_checkable
    class Checker(Protocol):
        """Contract for project and workspace quality checking services."""

        def run(
            self,
            project: str,
            gates: Sequence[str],
        ) -> p.Result[Sequence[m.Infra.ProjectResult]]:
            """Run quality gates for one project."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self,
            request: m.Infra.DocsGenerateRequest,
        ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self,
            repository_root: Path,
        ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
            """Discover projects in a workspace root."""
            ...

    @runtime_checkable
    class SafetyRunner(Protocol):
        """Protocol for command execution backends used by the safety manager."""

        def capture(
            self,
            cmd: Sequence[str],
            cwd: Path | None = None,
            timeout: int | None = None,
        ) -> p.Result[str]:
            """Run a command and capture its stdout."""
            ...

        def run_checked(
            self,
            cmd: Sequence[str],
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

    @runtime_checkable
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self,
            path: Path,
            payload: Mapping[str, t.JsonValue],
        ) -> p.Result[bool]:
            """Write payload to JSON file."""
            ...

    @runtime_checkable
    class DepsService(Protocol):
        """Service for dependency detection across projects."""

        def discover_project_paths(
            self,
            repository_root: Path,
            *,
            projects_filter: Sequence[str] | None = None,
        ) -> p.Result[Sequence[Path]]:
            """Discover project paths in workspace root."""
            ...

        def run_deptry(
            self,
            project_path: Path,
            venv_bin: Path,
        ) -> p.Result[tuple[Sequence[t.JsonMapping], int]]:
            """Run deptry on a project and return issues."""
            ...

        def build_project_report(
            self,
            project_name: str,
            deptry_issues: Sequence[t.JsonMapping],
        ) -> m.Infra.ProjectDependencyReport:
            """Build project report from deptry issues."""
            ...

        def run_pip_check(
            self,
            repository_root: Path,
            venv_bin: Path,
        ) -> p.Result[tuple[Sequence[str], int]]:
            """Run pip check on workspace and return results."""
            ...

    @runtime_checkable
    class DetectorRuntime(Protocol):
        """Protocol for the detector command the runtime reports through."""

        @property
        def log(self) -> p.Logger: ...

    @runtime_checkable
    class ViolationWithLine(Protocol):
        """Protocol for violations that have a line number."""

        def model_dump(self) -> t.JsonMapping:
            """Dump violation data to a dictionary."""
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
            repository_root: Path | None = None,
            *,
            output_format: str = "json",
            projects: Sequence[FlextInfraProtocolsBase.ProjectInfo] | None = None,
        ) -> p.Result[tuple[m.Infra.CensusReport, ...]]:
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
    class CensusObjectRules(Protocol):
        """Object classification operations consumed by project reporting."""

        @staticmethod
        def _include_rule(
            rule: str,
            *,
            rule_names: Sequence[str] | None,
            selected_rules: frozenset[str] | None = None,
        ) -> bool: ...

        @staticmethod
        def unused(item: m.Infra.Object) -> bool: ...

        @staticmethod
        def _object_key(item: m.Infra.Object) -> str: ...

        @staticmethod
        def _violation(
            item: m.Infra.Object, *, kind: str, description: str
        ) -> m.Infra.Violation: ...

        @classmethod
        def _removal_candidate(
            cls, item: m.Infra.Object, *, include_unused: bool
        ) -> m.Infra.RemovalCandidate | None: ...

    @runtime_checkable
    class ReleaseOrchestrator(Protocol):
        """Protocol for release orchestration services."""

        def execute(self) -> p.Result[bool]:
            """Execute release orchestration."""
            ...

    @runtime_checkable
    class XmlElementLike(Protocol):
        """Typed read-only subset of the safe XML element API from defusedxml.

        ``attrib`` is a read-only property so concrete elements (whose real
        ``attrib`` is a mutable ``dict``) satisfy the protocol covariantly —
        consumers only read it.
        """

        @property
        def attrib(self) -> Mapping[str, str]: ...

        text: str | None

        def find(self, path: str) -> FlextInfraProtocolsBase.XmlElementLike | None:
            """Find first matching child element."""
            ...

        def iter(
            self,
            tag: str | None = None,
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
        files: Sequence[Path] | None
        pattern: str
        dry_run: bool
        show_diff: bool
        analysis_output: Path | None
        impact_map_output: Path | None


__all__: list[str] = ["FlextInfraProtocolsBase"]
