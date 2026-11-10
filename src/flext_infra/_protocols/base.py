# AUTO-GENERATED FILE - Source bootstrap legacy protocol holder.
"""Base protocols for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra._protocols import (
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsDeps,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsDocsGeneration,
        FlextInfraProtocolsGates,
        FlextInfraProtocolsRefactor,
        FlextInfraProtocolsScan,
        FlextInfraProtocolsWorkspace,
    )
    from flext_infra._protocols._codegen import (
        FlextInfraProtocolsCodegenPipeline,
        FlextInfraProtocolsCodegenScaffold,
        FlextInfraProtocolsCodegenTransaction,
    )
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigArtifact,
        FlextInfraProtocolsConfigRepository,
    )


from collections.abc import Callable, Iterator, Mapping, MutableMapping, Sequence
from pathlib import Path
from types import FunctionType
from typing import Literal

from flext_cli import FlextCliProtocols, t

if TYPE_CHECKING:
    from flext_infra import c
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
            plans: Sequence[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan],
        ) -> p.Result[tuple[p.Cli.FileChange, ...]]: ...

        def publish_codegen_plans(
            self,
            root: Path,
            plans: Sequence[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan],
        ) -> p.Result[tuple[Path, ...]]: ...

        def publish_normalized_codegen_plans(
            self,
            root: Path,
            plans: Sequence[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan],
            changes: Sequence[p.Cli.FileChange],
        ) -> p.Result[tuple[Path, ...]]: ...

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
        ) -> Sequence[FlextInfraProtocolsConfigRepository.RepositoryRef]: ...

    @runtime_checkable
    class CodegenExecutionContext(Protocol):
        """Actual caller runtime and its explicitly bound conform capabilities."""

        @property
        def settings(self) -> p.Settings: ...

        @property
        def context(self) -> p.Context: ...

        def codegen_conform_collaborators(
            self,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenConformPorts: ...

    @runtime_checkable
    class CodegenService(
        CodegenExecutionContext, FlextCliProtocols.Service[t.JsonDict], Protocol
    ):
        """Public codegen operations bound to the caller's execution context."""

        def codegen_generate(
            self,
            request: FlextInfraProtocolsConfigArtifact.CodegenGenerateRequest,
        ) -> p.Result[FlextInfraProtocolsCodegenPipeline.CodegenResult]: ...

        def codegen_conform(
            self,
            request: FlextInfraProtocolsConfigArtifact.CodegenConformRequest,
        ) -> p.Result[FlextInfraProtocolsCodegenPipeline.CodegenResult]: ...

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
    class SourceInitializerPlanner(Protocol):
        """Plan exports for a facade, an initializer/package, or the whole candidate."""

        def __call__(
            self,
            root: Path,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ],
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot,
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> p.Result[
            tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]
        ]: ...

    @runtime_checkable
    class SourceComponentPlanner(Protocol):
        """Close a facade or package cohort; no selection means every family."""

        def __call__(
            self,
            workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ],
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenRepositoryPlanOutcome: ...

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
        ) -> p.Result[str]:
            """Return the canonical source, the unchanged source, or the failure."""
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
            options: (FlextInfraProtocolsCodegenTransaction.StageSourceOptions)
            | None = None,
            storage_root: Path | None = None,
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
            params: FlextInfraProtocolsRefactor.ApplyRenamesInput,
        ) -> p.Result[FlextInfraProtocolsRefactor.ApplyRenamesReport]: ...

    @runtime_checkable
    class SemanticRenameCandidateProvider(Protocol):
        """Select meaningful names from actual declarations, never token counts."""

        def rename_decision(
            self,
            declaration: FlextInfraProtocolsCensus.Object,
        ) -> FlextInfraProtocolsRefactor.SemanticRenameDecision | None: ...

    @runtime_checkable
    class NativeSemanticRenamePlanner(Protocol):
        """Native rename capabilities supplied by the application composition root."""

        def inventoried_declaration(
            self,
            workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
            qualified_name: str,
        ) -> FlextInfraProtocolsCensus.Object: ...

        def plan_native_candidates(
            self,
            projects: Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeProject],
            sources: Mapping[Path, str],
            decisions: Sequence[FlextInfraProtocolsRefactor.SemanticRenameDecision],
        ) -> tuple[Mapping[Path, str | None], tuple[tuple[Path, Path], ...]]: ...

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
        def declaration(self) -> FlextInfraProtocolsRope.LogicalStatement: ...

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

        def emit_rename(
            self, report: (FlextInfraProtocolsRefactor.ApplyRenamesReport)
        ) -> None: ...

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
            preflight: FlextInfraProtocolsScan.ModScanReport,
            rope_workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
            *,
            sources: Mapping[Path, str],
        ) -> p.Result[
            tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]
        ]: ...

        def apply(
            self,
            root: Path,
            preflight: FlextInfraProtocolsScan.ModScanReport,
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
    class CandidateBootstrapPlanner(Protocol):
        """Conform plan boundary consumed by the candidate campaign."""

        def surface_contract(
            self,
            surface: c.Infra.CodegenConformSurface,
            *,
            codegen: FlextInfraProtocolsConfigArtifact.CodegenConfigSpec,
        ) -> FlextInfraProtocolsConfigArtifact.CodegenConformSurfaceContract:
            """Resolve the declared output set for a recovery surface."""
            ...

        def plan_repositories(
            self,
            request: FlextInfraProtocolsConfigArtifact.CodegenGenerateRequest,
            inputs: FlextInfraProtocolsConfigArtifact.CodegenInputs,
        ) -> p.Result[FlextInfraProtocolsCodegenPipeline.CodegenPlan]:
            """Plan one declared target from its captured inputs without publishing."""
            ...

    @runtime_checkable
    class DocsArtifactPlanner(Protocol):
        """Docs render planned as file changes for the shared publisher."""

        def prepare_bundle(
            self,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ] = (),
        ) -> p.Result[FlextInfraProtocolsDocsGeneration.DocsGenerationBundle]:
            """Freeze one configured inventory and its consumed inputs."""
            ...

        def plan_files(
            self,
            bundle: FlextInfraProtocolsDocsGeneration.DocsGenerationBundle,
        ) -> p.Result[
            tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]
        ]:
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
    class MarkdownFormatGate(Protocol):
        """Markdown formatting gate the docs formatter delegates to."""

        def check(
            self,
            project_dir: Path,
            ctx: FlextInfraProtocolsGates.GateContext,
        ) -> FlextInfraProtocolsCheck.GateExecution:
            """Report pending formatting without writing."""
            ...

        def fix(
            self,
            project_dir: Path,
            ctx: FlextInfraProtocolsGates.GateContext,
        ) -> FlextInfraProtocolsCheck.GateExecution:
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
    class ModRuleOwnerRunner(Protocol):
        """Pure semantic/callback owner planned by a focused mod route."""

        name: str

        def plan(
            self,
            root: Path,
            preflight: FlextInfraProtocolsScan.ModScanReport,
            rope_workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl,
            *,
            sources: Mapping[Path, str],
        ) -> p.Result[
            tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]
        ]: ...

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
        ) -> tuple[FlextInfraProtocolsWorkspace.EnvironmentContractViolation, ...]:
            """Return one typed violation per direnv contract issue."""
            ...

        @classmethod
        def envrc_local_contract_violations(
            cls,
            content: str,
        ) -> tuple[FlextInfraProtocolsWorkspace.EnvironmentContractViolation, ...]:
            """Return one typed violation per activation residue in overrides."""
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
        ) -> p.Result[Sequence[FlextInfraProtocolsCheck.ProjectResult]]:
            """Run quality gates for one project."""
            ...

    @runtime_checkable
    class Generator(Protocol):
        """Contract for artifact and documentation generation services."""

        def generate(
            self,
            request: FlextInfraProtocolsDocs.DocsGenerateRequest,
        ) -> p.Result[Sequence[FlextInfraProtocolsDocs.DocsPhaseReport]]:
            """Generate project-scoped artifacts for the workspace."""
            ...

    @runtime_checkable
    class Discovery(Protocol):
        """Contract for project discovery services."""

        def discover_projects(
            self,
            repository_root: Path,
        ) -> p.Result[Sequence[FlextInfraProtocolsWorkspace.ProjectInfo]]:
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

        def scan_file(self, *, file_path: Path) -> FlextInfraProtocolsScan.ScanResult:
            """Scan a single file and return scan result."""
            ...

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
        ) -> FlextInfraProtocolsDeps.ProjectDependencyReport:
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
            projects: Sequence[FlextInfraProtocolsWorkspace.ProjectInfo] | None = None,
        ) -> p.Result[tuple[FlextInfraProtocolsCodegenScaffold.CensusReport, ...]]:
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
        def unused(item: FlextInfraProtocolsCensus.Object) -> bool: ...

        @staticmethod
        def _object_key(item: FlextInfraProtocolsCensus.Object) -> str: ...

        @staticmethod
        def _violation(
            item: FlextInfraProtocolsCensus.Object, *, kind: str, description: str
        ) -> FlextInfraProtocolsCensus.Violation: ...

        @classmethod
        def _removal_candidate(
            cls, item: FlextInfraProtocolsCensus.Object, *, include_unused: bool
        ) -> FlextInfraProtocolsCensus.RemovalCandidate | None: ...

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

    @runtime_checkable
    class FrozenArbitrary(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class ProcessExit(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exit_code(self) -> int:
            """Exact subprocess return code without remapping."""
            ...

        @property
        def classification(self) -> t.NonEmptyStr:
            """Failure, timeout, or terminating signal."""
            ...

    @runtime_checkable
    class SummaryStats(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def verb(self) -> str:
            """Verb label for the summary block."""
            ...

        @property
        def total(self) -> int:
            """Total processed items."""
            ...

        @property
        def success(self) -> int:
            """Successful items."""
            ...

        @property
        def failed(self) -> int:
            """Failed items."""
            ...

        @property
        def skipped(self) -> int:
            """Skipped items."""
            ...

        @property
        def elapsed(self) -> float:
            """Elapsed time in seconds."""
            ...

    @runtime_checkable
    class ProtectedSourceWriteRequest(FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> Path:
            """Repository root used for lint and pytest checks."""
            ...

        @property
        def updated_source(self) -> str:
            """Replacement source content to write."""
            ...

        @property
        def gates(self) -> Sequence[str] | None:
            """Optional lint gate selection for validation."""
            ...

    @runtime_checkable
    class LintGateResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool_name(self) -> t.NonEmptyStr:
            """Canonical lint tool name."""
            ...

        @property
        def errors(self) -> Sequence[str]:
            """Diagnostic lines reported by the lint tool."""
            ...

        @property
        def output(self) -> p.Cli.CommandOutput | None:
            """Original native streams, duration and process outcome."""
            ...

        @property
        def execution_error(self) -> t.NonEmptyStr | None:
            """Execution or report failure, independent of findings."""
            ...

    @runtime_checkable
    class TransformStep(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def detector(self) -> str:
            """Detector rule_id to run."""
            ...

        @property
        def transformer(self) -> str:
            """Transformer class name to apply."""
            ...

        @property
        def gates(self) -> str:
            """Structural member projected from the owning model.

            Comma-separated gate names for post-validation; empty selects the SSOT
            snapshot gates (make.check_gates_ci).
            """
            ...

    @runtime_checkable
    class CommandContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        apply_changes: bool
        check_only: bool
        dry_run: bool
        output_format: str
        project_filter: str | None
        report_path: Path | None
        output_dir: Path | None

        @property
        def root(self) -> Path:
            """Canonical normalized repository root."""
            ...

        @property
        def effective_dry_run(self) -> bool:
            """Derive the write-mode decision from this request's flags."""
            ...

    @runtime_checkable
    class ProtectedSourceWritesRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        workspace: Path
        expected_sources: Mapping[Path, str | None]
        gates: Sequence[str] | None
        post_write: Callable[[], None] | None
        skip_pytest: bool

    @runtime_checkable
    class ProtectedFileEditRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        workspace: Path
        before_source: str
        edit_fn: Callable[[], None]
        gates: Sequence[str] | None


__all__: list[str] = ["FlextInfraProtocolsBase"]
