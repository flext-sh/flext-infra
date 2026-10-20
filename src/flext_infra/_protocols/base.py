"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from types import FunctionType
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    import ast

    from flext_infra import c, m, p, t


@runtime_checkable
class FlextInfraProtocolsBase(Protocol):
    """Base protocols for flext-infra project."""

    @runtime_checkable
    class CodegenProtocolModelRenderer(Protocol):
        """Source-bound annotation resolver consumed by model selection."""

        @property
        def workspace(self) -> p.Infra.RopeWorkspaceDsl: ...

        @property
        def declarations(self) -> t.MappingKV[str, p.Infra.RopePyName]: ...

        @property
        def dependencies(self) -> set[str]: ...

        @property
        def imports(self) -> t.MutableMappingKV[str, str]: ...

        def alias_definition(
            self, binding: p.Infra.RopePyName
        ) -> t.Pair[ast.TypeAlias, p.Infra.RopeScope] | None: ...

        def source(self, annotation: str, scope: p.Infra.RopeScope) -> str: ...

        def render_protocol(
            self, name: str, model: p.Infra.RopePyName, scope: p.Infra.RopeScope
        ) -> str: ...

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
    class CodegenConformPorts(Protocol):
        """Caller-bound cross-family capabilities consumed by conform."""

        @property
        def docs_planner(
            self,
        ) -> FlextInfraProtocolsBase.DocsArtifactPlannerFactory: ...

        @property
        def participant_policy(
            self,
        ) -> FlextInfraProtocolsBase.CodegenParticipantPolicyFactory: ...

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
    class StageSourceReceipt(Protocol):
        """Closed prepared-source evidence carried without a model dependency cycle."""

        @property
        def version(self) -> Literal[1]: ...

        @property
        def workspace(self) -> Path: ...

        @property
        def workspaces(self) -> t.VariadicTuple[Path]: ...

        @property
        def roots(self) -> t.VariadicTuple[Path]: ...

        @property
        def inputs(self) -> t.VariadicTuple[m.Cli.AtomicFileState]: ...

        @property
        def source_directories(
            self,
        ) -> t.VariadicTuple[m.Cli.AtomicDirectoryInventory]: ...

        @property
        def source_query_topology(
            self,
        ) -> t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan]: ...

        @property
        def updates(self) -> t.MappingKV[Path, str | None]: ...

        @property
        def modes(self) -> t.MappingKV[Path, int]: ...

        @property
        def prepared_hashes(self) -> t.VariadicTuple[t.Pair[Path, str | None]]: ...

        @property
        def layouts(self) -> t.VariadicTuple[m.Infra.RopeProjectLayout]: ...

        @property
        def workspace_packages(self) -> t.VariadicTuple[str]: ...

    @runtime_checkable
    class CodegenPlanOutcome(Protocol):
        """Public plan membership, separate from the internal publication schema."""

        @property
        def files(self) -> t.SequenceOf[FlextInfraProtocolsBase.CodegenFileOutcome]: ...

        @property
        def repositories(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsBase.RepositoryRef]: ...

    @runtime_checkable
    class CodegenPublicationOutcome(Protocol):
        """Physical scopes covered by an actual generation publication receipt."""

        @property
        def scope_roots(self) -> t.VariadicTuple[Path]: ...

        @property
        def completed(self) -> bool: ...

        @property
        def issues(self) -> t.VariadicTuple[p.Infra.Issue]: ...

        @property
        def exception(self) -> BaseException | None: ...

    @runtime_checkable
    class CodegenResult(Protocol):
        """Generation or observation facts consumed by public callers."""

        @property
        def plan(self) -> FlextInfraProtocolsBase.CodegenPlanOutcome | None: ...

        @property
        def verified_publication(
            self,
        ) -> FlextInfraProtocolsBase.CodegenPublicationOutcome | None: ...

        @property
        def publication_receipt(
            self,
        ) -> FlextInfraProtocolsBase.CodegenPublicationOutcome | None: ...

        @property
        def written_files(self) -> t.VariadicTuple[Path]: ...

        @property
        def errors(self) -> t.VariadicTuple[str]: ...

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
    class CodegenHandlerContext(CodegenExecutionContext, Protocol):
        """API handler context that also exposes native conform execution."""

        def codegen_conform(
            self,
            request: FlextInfraProtocolsBase.CodegenConformRequest,
            initial_workspace: p.Infra.WorkspaceSpec | None = None,
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
    class SourceImportNormalizer(Protocol):
        """Normalize source imports through the caller's explicit service binding."""

        def __call__(
            self,
            *,
            project_root: Path,
            file_path: Path,
            source: str,
            import_graph: t.MappingKV[str, frozenset[str]],
            sources: t.MappingKV[Path, str],
        ) -> str | None:
            """Return normalized source, or None when no import changes are needed."""
            ...

    @runtime_checkable
    class SourcePreview(Protocol):
        """Consumer-owned capability for validating authenticated source views."""

        def preview_sources[T](
            self,
            workspace: Path,
            updates: t.MappingKV[Path, str | None],
            validator: Callable[[Path, t.MappingKV[Path, Path]], T],
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
        def inventory(self) -> t.VariadicTuple[t.Pair[str, str]]: ...

        @property
        def repository_root(self) -> Path | None: ...

        @property
        def projects(self) -> t.SequenceOf[Path]: ...

        @property
        def publication_chain(
            self,
        ) -> t.VariadicTuple[m.Infra.CodegenStagedFile] | None: ...

    @runtime_checkable
    class ChainDeclarationSpec(Protocol):
        """Read-only structural contract for binding-chain declaration inputs."""

        @property
        def project(self) -> p.Infra.RopeProject: ...

        @property
        def holder(self) -> p.Infra.RopePyModule: ...

        @property
        def holder_text(self) -> str: ...

        @property
        def declaration(self) -> m.Infra.LogicalStatement: ...

        @property
        def holder_offset(self) -> int: ...

        @property
        def holder_scope(self) -> p.Infra.RopeScope: ...

        @property
        def expression(self) -> str: ...

        @property
        def sources(self) -> t.MappingKV[Path, str]: ...

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
        ) -> p.Infra.RopeWorkspaceDsl: ...

        @staticmethod
        def source_preview(repository_root: Path) -> p.Infra.SourcePreview: ...

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
            rope_workspace: p.Infra.RopeWorkspaceDsl,
            *,
            sources: t.MappingKV[Path, str],
            receipt: m.Infra.CodegenPhaseAnalysis,
        ) -> p.Result[m.Infra.CodegenPhaseAnalysis]: ...

        def apply(
            self,
            root: Path,
            preflight: m.Infra.ModScanReport,
            rope_workspace: p.Infra.RopeWorkspaceDsl,
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
    class MiseArtifactsOwner(Protocol):
        """Owner contract consumed by the atomic generation transaction."""

        @property
        def repository_root(self) -> Path:
            """Repository whose generated Mise surfaces are transacted."""
            ...

        def validate_artifacts(
            self,
            project_root: Path,
            runtime_root: Path,
        ) -> p.Result[bool]:
            """Validate one project's generated Mise declaration."""
            ...

    @runtime_checkable
    class CodegenPendingPhase(Protocol):
        """Read-only pending-phase contract across the transaction mixins."""

        @property
        def phase(self) -> str: ...

        @property
        def changed(self) -> t.VariadicTuple[m.Infra.CodegenFilePlan]: ...

        @property
        def all_plans(self) -> t.VariadicTuple[m.Infra.CodegenFilePlan]: ...

        @property
        def staged_validator(
            self,
        ) -> (
            Callable[
                [
                    m.Infra.CodegenTransactionSession,
                    t.VariadicTuple[m.Infra.CodegenStagedFile],
                ],
                p.Result[m.Infra.CodegenTransactionSession],
            ]
            | None
        ): ...

        @property
        def batch_admission(self) -> m.Infra.CodegenPhaseOutcome | None: ...

    @runtime_checkable
    class CodegenParticipantRoot(Protocol):
        """Physical root selector retaining the producer's native proof value."""

        @property
        def target(self) -> Path: ...

    @runtime_checkable
    class CodegenParticipantPolicy(Protocol):
        """Read-only physical authority consumed by generation transactions."""

        @property
        def scope_root(self) -> Path: ...

        @property
        def roots(
            self,
        ) -> t.VariadicTuple[FlextInfraProtocolsBase.CodegenParticipantRoot]: ...

    @runtime_checkable
    class CodegenParticipantPolicyFactory(Protocol):
        """Composition-root authorization for one generation request."""

        def __call__(
            self,
            root: Path,
            *,
            initial_workspace: FlextInfraProtocolsBase.WorkspaceSpec | None,
        ) -> p.Result[FlextInfraProtocolsBase.CodegenParticipantPolicy]:
            """Read the request's physical topology without acquiring a lease.

            ``initial_workspace`` is the declared topology of a scaffold whose
            own workspace configuration is not rendered yet; ``None`` reads
            the repository's committed declaration.
            """
            ...

    @runtime_checkable
    class CandidateBootstrapPlanner(Protocol):
        """Conform plan boundary consumed by the candidate campaign."""

        def continue_after_publication(
            self,
            receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        ) -> p.Result[bool]:
            """Continue planning through the invocation's verified effects."""
            ...

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
            request: m.Infra.CodegenConformRequest,
            inputs: m.Infra.CodegenInputs,
        ) -> p.Result[m.Infra.CodegenPlan]:
            """Plan one declared target from its captured inputs without publishing."""
            ...

    @runtime_checkable
    class DocsArtifactPlanner(Protocol):
        """Captured scope batches published by the owning docs service."""

        def prepare_batches(
            self,
            *,
            publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
            | None = None,
        ) -> Iterator[p.Result[m.Infra.DocsGenerationBundle]]:
            """Capture each scope after the preceding publication settles."""
            ...

        def publish_batch(
            self,
            bundle: m.Infra.DocsGenerationBundle,
            *,
            publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
            | None = None,
        ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
            """Admit, publish and settle one captured scope batch."""
            ...

        def prepare_bundle(self) -> p.Result[m.Infra.DocsGenerationBundle]:
            """Freeze one configured inventory and its consumed inputs."""
            ...

        def required_directories(
            self,
            bundle: m.Infra.DocsGenerationBundle,
        ) -> p.Result[t.VariadicTuple[Path]]:
            """Derive the parent directories the render needs."""
            ...

        def plan_files(
            self,
            bundle: m.Infra.DocsGenerationBundle,
        ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
            """Bind the render to exact live destination states."""
            ...

    @runtime_checkable
    class DocsArtifactPlannerFactory(Protocol):
        """Build the docs planner for one conform scope."""

        def __call__(
            self,
            *,
            repository_root: Path,
            projects: t.StrSequence,
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
        def outcome(self) -> c.Infra.ToolOutcome:
            """Native tool outcome, independent of acceptance."""
            ...

        @property
        def issues(self) -> t.SequenceOf[p.Infra.Issue]:
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

    @runtime_checkable
    class CandidateBootstrapTransaction(Protocol):
        """Atomic multi-root file publisher consumed by the campaign."""

        def capability_roots(
            self,
            label: str,
            paths: t.SequenceOf[Path],
        ) -> t.MappingKV[str, Path]:
            """Key physical roots by their file capability selector."""
            ...

        def run_files_locked[T](
            self,
            roots: t.MappingKV[str, Path],
            operation: Callable[[Path], p.Result[T]],
        ) -> p.Result[T]:
            """Hold destination leases while the campaign plans and publishes."""
            ...

        def publish_file_phase_locked(
            self,
            scope_root: Path,
            roots: t.MappingKV[str, Path],
            analysis: m.Infra.CodegenPhaseAnalysis,
            policy: m.Infra.CodegenPhasePublicationPolicy,
            *,
            publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
            | None = None,
        ) -> p.Result[t.VariadicTuple[Path]]:
            """Publish one recoverable multi-root phase and verify before commit."""
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
        def subprojects(self) -> t.SequenceOf[FlextInfraProtocolsBase.RepositoryRef]:
            """Direct governed repositories declared by local .gitmodules."""
            ...

        @property
        def external_dependency_paths(self) -> t.SequenceOf[Path]:
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
        def consumer_roots(self) -> t.VariadicTuple[Path]: ...

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
        ) -> t.VariadicTuple[m.Infra.EnvironmentContractViolation]:
            """Return one typed violation per direnv contract issue."""
            ...

        @classmethod
        def envrc_local_contract_violations(
            cls,
            content: str,
        ) -> t.VariadicTuple[m.Infra.EnvironmentContractViolation]:
            """Return one typed violation per activation residue in overrides."""
            ...

    @runtime_checkable
    class CodegenConform(Protocol):
        """Complete state and collaboration contract for conform partials."""

        request: m.Infra.CodegenConformRequest | None
        repository_root: Path
        initial_workspace: m.Infra.WorkspaceSpec | None

        def plan(
            self,
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[m.Infra.CodegenPlan]: ...

        def conform_workspace_beads_routes(
            self,
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[bool]: ...

        @classmethod
        def surface_contract(
            cls,
            surface: c.Infra.CodegenConformSurface,
            *,
            codegen: m.Infra.CodegenConfigSpec,
        ) -> m.Infra.CodegenConformSurfaceContract: ...

        @classmethod
        def retired_projection_plans(
            cls,
            root: Path,
            profile: c.Infra.MakeProfile,
            *,
            inputs: m.Infra.CodegenInputs | None = None,
        ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]: ...

        @staticmethod
        def uv_environment_plan(
            *,
            root: Path,
            target: m.Infra.RepositoryConformTarget,
            workspace: m.Infra.WorkspaceSpec,
            config: m.Infra.CodegenConfigSpec,
        ) -> m.Infra.UvEnvironmentPlan: ...

        @staticmethod
        def _scaffold_python_dirs(
            entries: t.SequenceOf[m.Infra.TemplateEntrySpec],
            profile: c.Infra.MakeProfile,
        ) -> t.StrSequence: ...

        @staticmethod
        def mise_config_plans(
            plan: m.Infra.CodegenPlan,
        ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]: ...

        @classmethod
        def owned_docs_files(
            cls,
            request: m.Infra.CodegenConformRequest,
            files: t.SequenceOf[m.Infra.CodegenFilePlan],
        ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]: ...

        @classmethod
        def _owned_docs_directories(
            cls,
            request: m.Infra.CodegenConformRequest,
            plan: m.Infra.CodegenPlan,
            directories: t.SequenceOf[Path],
        ) -> t.VariadicTuple[Path]: ...

        def _project_render_context(
            self,
            render_inputs: m.Infra.CodegenRenderInputs,
        ) -> p.Result[m.Infra.ProjectRenderContext]: ...

        def _rendered_artifact_source(
            self,
            render_inputs: m.Infra.CodegenRenderInputs,
            *,
            template_relpath: Path,
            destination: str,
            failure_prefix: str,
            project_context: m.Infra.ProjectRenderContext | None,
        ) -> p.Result[m.Infra.CodegenArtifactComposition]: ...

        @classmethod
        def compose_project_artifact(
            cls,
            repository_root: Path,
            destination: str,
            rendered: str,
            *,
            render_inputs: m.Infra.CodegenRenderInputs | None = None,
            source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
        ) -> p.Result[m.Infra.CodegenArtifactComposition]: ...

        @staticmethod
        def validate_custom_make(
            content: str,
            policy: m.Infra.CustomHandlerPolicy,
        ) -> p.Result[bool]: ...

        @staticmethod
        def _absent_file_plan(
            root: Path,
            path: Path,
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...

        @staticmethod
        def _repository_provider(
            repository: m.Infra.RepositoryRef,
        ) -> p.Result[m.Infra.ProviderIdentitySpec]: ...

        @staticmethod
        def _repository_root_rel(workspace: m.Infra.WorkspaceSpec) -> str: ...

        @staticmethod
        def _merge_extra_verbs(
            declared: t.VariadicTuple[m.Infra.MakeVerbSpec],
            discovered: t.VariadicTuple[m.Infra.MakeVerbSpec],
            canonical_names: frozenset[str],
        ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]: ...

        @staticmethod
        def _discover_script_verbs(
            repository_root: Path,
        ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]: ...

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
        def uv_environments(self) -> t.StrSequence:
            """Marker expressions limiting the uv-resolved lock environments."""
            ...

        @property
        def uv_constraint_dependencies(self) -> t.StrSequence:
            """SSOT-declared [tool.uv] constraints; empty exterminates the key."""
            ...

        @property
        def environment_path_prepends(self) -> t.SequenceOf[str]:
            """Extra directories prepended to PATH by shell activation."""
            ...

        @property
        def tool_versions(self) -> t.MappingKV[str, str]:
            """Effective release selector per tool: pins layered over entries."""
            ...

        @property
        def tool_selectors(self) -> t.MappingKV[str, str]:
            """Declared Mise selector of every selector-bearing fleet tool."""
            ...

        @property
        def tool_version_prefixes(self) -> t.MappingKV[str, str]:
            """Declared release tag prefix of every prefix-bearing tool."""
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
        ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
            """Run quality gates for one project."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self,
            request: m.Infra.DocsGenerateRequest,
        ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self,
            repository_root: Path,
        ) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
            """Discover projects in a workspace root."""
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

    @runtime_checkable
    class JsonService(Protocol):
        """Service for JSON serialization and persistence."""

        def write_json(
            self,
            path: Path,
            payload: t.MappingKV[str, t.JsonValue],
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
            projects_filter: t.StrSequence | None = None,
        ) -> p.Result[t.SequenceOf[Path]]:
            """Discover project paths in workspace root."""
            ...

        def run_deptry(
            self,
            project_path: Path,
            venv_bin: Path,
        ) -> p.Result[t.Pair[t.SequenceOf[t.JsonMapping], int]]:
            """Run deptry on a project and return issues."""
            ...

        def build_project_report(
            self,
            project_name: str,
            deptry_issues: t.SequenceOf[t.JsonMapping],
        ) -> m.Infra.ProjectRuntimeReport:
            """Build project report from deptry issues."""
            ...

        def load_dependency_limits(
            self,
            limits_path: Path | None = None,
        ) -> t.MappingKV[str, t.JsonValue]:
            """Load dependency limits from TOML file."""
            ...

        def analyze_required_typings(
            self,
            project_path: Path,
            limits_path: Path | None = None,
        ) -> p.Result[m.Infra.TypingsReport]:
            """Get required typing libraries for a project."""
            ...

        def run_pip_check(
            self,
            repository_root: Path,
            venv_bin: Path,
        ) -> p.Result[t.Pair[t.StrSequence, int]]:
            """Run pip check on workspace and return results."""
            ...

        def generate_typing_packages(
            self,
            repository_root: Path,
            modules: t.StrSequence,
            policy: m.Infra.TypingGenerationPolicy,
        ) -> p.Result[t.VariadicTuple[Path]]:
            """Generate and install PEP 561 packages in the owning environment."""
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
            projects: t.SequenceOf[FlextInfraProtocolsBase.ProjectInfo] | None = None,
        ) -> p.Result[t.VariadicTuple[m.Infra.CensusReport]]:
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
        files: t.SequenceOf[Path] | None
        pattern: str
        dry_run: bool
        show_diff: bool
        analysis_output: Path | None
        impact_map_output: Path | None

    @runtime_checkable
    class MiseRoleRequest(Protocol):
        """Authenticated native role inputs and the isolated installation scope."""

        @property
        def declaration(self) -> p.Cli.AtomicFileReceipt: ...

        @property
        def reader(self) -> p.Cli.AtomicFileReceipt: ...

        @property
        def reader_manifest(self) -> p.Cli.AtomicFileReceipt: ...

        @property
        def reader_lock(self) -> p.Cli.AtomicFileReceipt: ...

        @property
        def scope_root(self) -> Path: ...

        @property
        def target_root(self) -> Path: ...

    @runtime_checkable
    class MiseRolePlan(Protocol):
        """Role projection and lock accepted before native installation."""

        @property
        def request(self) -> FlextInfraProtocolsBase.MiseRoleRequest: ...

        @property
        def manifest(self) -> p.Cli.AtomicFileReceipt: ...

        @property
        def lock(self) -> p.Cli.AtomicFileReceipt: ...

    @runtime_checkable
    class MiseRoleInstallation(Protocol):
        """Installed binaries pinned to the declaration and native lock."""

        @property
        def plan(self) -> FlextInfraProtocolsBase.MiseRolePlan: ...

        @property
        def executables(self) -> Mapping[str, p.Cli.AtomicFileReceipt]: ...


__all__: list[str] = ["FlextInfraProtocolsBase"]
