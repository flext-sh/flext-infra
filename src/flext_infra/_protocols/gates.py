# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/gates
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import FlextInfraProtocolsCheck, FlextInfraProtocolsDeps


class FlextInfraProtocolsGates:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SccFile(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        location: str
        code: int

    @runtime_checkable
    class SccLanguage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        name: str

        @property
        def files(self) -> tuple[FlextInfraProtocolsGates.SccFile, ...]:
            """Every scanned file in this language."""
            ...

    @runtime_checkable
    class SccReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> tuple[FlextInfraProtocolsGates.SccLanguage, ...]:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class DeptryError(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def code(self) -> str:
            """Deptry rule code."""
            ...

        @property
        def message(self) -> str:
            """Deptry diagnostic message."""
            ...

    @runtime_checkable
    class DeptryLocation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str:
            """Diagnostic file path."""
            ...

        @property
        def line(self) -> int | None:
            """Source line, null for declarations."""
            ...

        @property
        def column(self) -> int | None:
            """Source column, null for declarations."""
            ...

    @runtime_checkable
    class DeptryDiagnostic(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def error(self) -> FlextInfraProtocolsGates.DeptryError:
            """Deptry rule and diagnostic message."""
            ...

        @property
        def module(self) -> str:
            """Reported module or dependency."""
            ...

        @property
        def location(self) -> FlextInfraProtocolsGates.DeptryLocation:
            """Diagnostic file and nullable source positions."""
            ...

    @runtime_checkable
    class DeptryNativeReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> tuple[FlextInfraProtocolsGates.DeptryDiagnostic, ...]:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class DeptryScan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scanned_files(self) -> int:
            """Native extractor's executed file count."""
            ...

        @property
        def venv_bin(self) -> Path:
            """Explicit runtime binary directory owning the scanner."""
            ...

        @property
        def source(self) -> tuple[p.Cli.AtomicPhysicalTreeManifest, ...]:
            """Production trees consumed by the scanner."""
            ...

        @property
        def native(self) -> p.Cli.CommandOutput:
            """Native deptry process completion and raw output."""
            ...

        @property
        def settings(self) -> p.Cli.AtomicFileState:
            """Consumed pyproject state."""
            ...

        @property
        def report_state(self) -> p.Cli.AtomicFileState:
            """Fresh native report state."""
            ...

        @property
        def report_sha256(self) -> str:
            """Exact native report digest."""
            ...

        @property
        def report(self) -> FlextInfraProtocolsGates.DeptryNativeReport:
            """Complete native findings."""
            ...

    @runtime_checkable
    class GateContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def fail_fast(self) -> bool:
            """Stop on first failure."""
            ...

        @property
        def repository_root(self) -> Path:
            """Repository root directory."""
            ...

        @property
        def runtime_root(self) -> Path | None:
            """Explicit physical runtime owner for a staged candidate."""
            ...

        @property
        def reports_dir(self) -> Path:
            """Reports output directory."""
            ...

        @property
        def apply_fixes(self) -> bool:
            """Execute supported repairs instead of checking."""
            ...

        @property
        def check_only(self) -> bool:
            """Never write files even when fix mode is requested."""
            ...

        @property
        def runtime_dependency_inputs(
            self,
        ) -> FlextInfraProtocolsDeps.RuntimeDependencyInputs | None:
            """Target-runtime dependency proof injected at composition."""
            ...

        @property
        def runtime_dependency_collector(
            self,
        ) -> FlextInfraProtocolsDeps.RuntimeDependencyCollector | None:
            """Explicit composition-owned target supplier collector."""
            ...

        @property
        def scope_facts(self) -> FlextInfraProtocolsCheck.GitScopeFacts | None:
            """Structural member projected from the owning model.

            Invocation-owned Git scope facts shared by applicability and every gate;
            absent means each query reads Git.
            """
            ...

        @property
        def signal_wave(self) -> p.Cli.SignalWave | None:
            """Structural member projected from the owning model.

            Signal wave of the concurrent stage running this gate; absent on the
            main thread.
            """
            ...

        @property
        def ruff_args(self) -> Sequence[str]:
            """Extra arguments for Ruff."""
            ...

        @property
        def pyright_args(self) -> Sequence[str]:
            """Extra arguments for Pyright."""
            ...

        @property
        def selected_files(self) -> tuple[Path, ...]:
            """Validated literal file selection; empty means project."""
            ...

        @property
        def candidate_files(self) -> tuple[Path, ...] | None:
            """Complete sealed source-plan inventory for admission."""
            ...

        @property
        def check_progress(
            self,
        ) -> Callable[[Path, FlextInfraProtocolsCheck.ProjectResult], None] | None:
            """Invocation-owned observer of reached native gate results."""
            ...

    @runtime_checkable
    class MypyDiagnostic(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str:
            """Diagnostic source file path."""
            ...

        @property
        def line(self) -> int:
            """Diagnostic start line."""
            ...

        @property
        def column(self) -> int:
            """Diagnostic start column."""
            ...

        @property
        def end_line(self) -> int | None:
            """Diagnostic end line."""
            ...

        @property
        def end_column(self) -> int | None:
            """Diagnostic end column."""
            ...

        @property
        def message(self) -> t.NonEmptyStr:
            """Diagnostic message."""
            ...

        @property
        def hint(self) -> str | None:
            """Diagnostic hint."""
            ...

        @property
        def code(self) -> str | None:
            """Mypy diagnostic code."""
            ...

        @property
        def severity(self) -> Literal["error", "note"]:
            """Mypy diagnostic severity."""
            ...

    @runtime_checkable
    class PyrightPosition(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt:
            """Zero-based line index."""
            ...

        @property
        def character(self) -> t.NonNegativeInt:
            """Zero-based character index."""
            ...

    @runtime_checkable
    class PyrightRange(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> FlextInfraProtocolsGates.PyrightPosition:
            """Diagnostic range start position."""
            ...

        @property
        def end(self) -> FlextInfraProtocolsGates.PyrightPosition:
            """Diagnostic range end position."""
            ...

    @runtime_checkable
    class PyrightDiagnostic(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str:
            """Diagnostic source file path."""
            ...

        @property
        def severity(self) -> Literal["error", "warning", "information"]:
            """Pyright diagnostic severity."""
            ...

        @property
        def message(self) -> t.NonEmptyStr:
            """Diagnostic message."""
            ...

        @property
        def range(self) -> FlextInfraProtocolsGates.PyrightRange | None:
            """Diagnostic source range when available."""
            ...

        @property
        def rule(self) -> str | None:
            """Pyright diagnostic rule when available."""
            ...

    @runtime_checkable
    class PyrightSummary(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def files_analyzed(self) -> t.NonNegativeInt:
            """Number of analyzed files."""
            ...

        @property
        def error_count(self) -> t.NonNegativeInt:
            """Number of error diagnostics."""
            ...

        @property
        def warning_count(self) -> t.NonNegativeInt:
            """Number of warning diagnostics."""
            ...

        @property
        def information_count(self) -> t.NonNegativeInt:
            """Number of informational diagnostics."""
            ...

        @property
        def time_in_sec(self) -> float:
            """Analysis duration in seconds."""
            ...

    @runtime_checkable
    class PyrightReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> t.NonEmptyStr:
            """Pyright version."""
            ...

        @property
        def time(self) -> t.NonEmptyStr:
            """Report timestamp."""
            ...

        @property
        def general_diagnostics(
            self,
        ) -> Sequence[FlextInfraProtocolsGates.PyrightDiagnostic]:
            """Pyright diagnostics."""
            ...

        @property
        def summary(self) -> FlextInfraProtocolsGates.PyrightSummary:
            """Completed analysis summary."""
            ...

    @runtime_checkable
    class PyreflyDiagnostic(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt:
            """Diagnostic start line."""
            ...

        @property
        def column(self) -> t.NonNegativeInt:
            """Diagnostic start column."""
            ...

        @property
        def stop_line(self) -> t.NonNegativeInt:
            """Diagnostic end line."""
            ...

        @property
        def stop_column(self) -> t.NonNegativeInt:
            """Diagnostic end column."""
            ...

        @property
        def path(self) -> t.NonEmptyStr:
            """Diagnostic source file path."""
            ...

        @property
        def code(self) -> int:
            """Pyrefly diagnostic code."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Pyrefly diagnostic name."""
            ...

        @property
        def description(self) -> t.NonEmptyStr:
            """Full diagnostic description."""
            ...

        @property
        def concise_description(self) -> str:
            """Concise diagnostic description."""
            ...

        @property
        def severity(self) -> Literal["error", "warn", "info"]:
            """Pyrefly diagnostic severity."""
            ...

    @runtime_checkable
    class PyreflyReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def errors(self) -> Sequence[FlextInfraProtocolsGates.PyreflyDiagnostic]:
            """Native Pyrefly diagnostics."""
            ...

    @runtime_checkable
    class GateReportEvidence(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Repository-relative report path."""
            ...

        @property
        def digest(self) -> str:
            """Original report byte digest."""
            ...

        @property
        def kind(self) -> c.Infra.GateEvidenceReportKind:
            """Canonical producer report contract."""
            ...

    @runtime_checkable
    class GateTestIntent(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def execution_mode(self) -> c.Infra.PytestExecutionMode:
            """Native test operation."""
            ...

        @property
        def target(self) -> Path:
            """Repository-relative test root."""
            ...

        @property
        def target_file(self) -> Path | None:
            """Original selected test file."""
            ...

        @property
        def ci_context(self) -> bool:
            """Original CI selection."""
            ...

        @property
        def slow_phase(self) -> bool:
            """Original slow-test phase."""
            ...

        @property
        def profile_enabled(self) -> bool:
            """Original native process profiling."""
            ...

    @runtime_checkable
    class GateExecutionIntent(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> c.Infra.CheckPhase:
            """Original checker evidence phase, never inferred from gates."""
            ...

        @property
        def requested_gates(self) -> t.StrTuple:
            """Requested native checker gates."""
            ...

        @property
        def test_selection(self) -> FlextInfraProtocolsGates.GateTestIntent | None:
            """Original test selection; absent for checker."""
            ...

    @runtime_checkable
    class GateExecutionFacts(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope(self) -> Literal["workspace"]:
            """Execution evidence, never validation of a Git commit."""
            ...

        @property
        def runtime_identity(self) -> str:
            """Native runtime identity consumed by execution."""
            ...

        @property
        def gate(self) -> t.NonEmptyStr:
            """Canonical Make gate name."""
            ...

        @property
        def command_digest(self) -> str:
            """Digest of the private exact original process argv."""
            ...

        @property
        def process(self) -> p.Cli.ProcessOutcome:
            """Original Make process outcome, without normalization."""
            ...

        @property
        def native_outcome(self) -> c.Infra.ToolOutcome:
            """Original producer's native report classification."""
            ...

        @property
        def intent(self) -> FlextInfraProtocolsGates.GateExecutionIntent:
            """Portable original operation and selection."""
            ...

        @property
        def policy(self) -> c.Infra.GateAcceptancePolicy:
            """Exact recorded policy used to derive admission."""
            ...

        @property
        def context_digest(self) -> str:
            """Original runtime, platform and operation-context fingerprint."""
            ...

        @property
        def policy_digest(self) -> str:
            """Original acceptance policy."""
            ...

        @property
        def reports(self) -> tuple[FlextInfraProtocolsGates.GateReportEvidence, ...]:
            """Original report identities and byte digests."""
            ...

        @property
        def result_digest(self) -> t.NonEmptyStr:
            """SHA-256 digest of the gate result."""
            ...

        @property
        def started_at(self) -> t.NonEmptyStr:
            """UTC start timestamp."""
            ...

        @property
        def completed_at(self) -> t.NonEmptyStr:
            """UTC completion timestamp."""
            ...

    @runtime_checkable
    class GateCommandEvidence(GateExecutionFacts, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> str | None:
            """Observed start origin."""
            ...

        @property
        def commit_sha(self) -> str | None:
            """Observed start HEAD."""
            ...

        @property
        def tree_sha(self) -> str | None:
            """Observed start commit tree."""
            ...

        @property
        def dirty(self) -> bool | None:
            """Observed start WIP state."""
            ...

        @property
        def after_repository(self) -> str | None:
            """Observed end origin."""
            ...

        @property
        def after_commit_sha(self) -> str | None:
            """Observed end HEAD."""
            ...

        @property
        def after_tree_sha(self) -> str | None:
            """Observed end commit tree."""
            ...

        @property
        def after_dirty(self) -> bool | None:
            """Observed end WIP state."""
            ...

    @runtime_checkable
    class GateCaptureBeginRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Actual execution root."""
            ...

        @property
        def gate(self) -> t.NonEmptyStr:
            """Canonical stage identity."""
            ...

        @property
        def command(self) -> t.StrTuple:
            """Exact original process argv."""
            ...

        @property
        def intent(self) -> FlextInfraProtocolsGates.GateExecutionIntent:
            """Portable original operation and selection."""
            ...

        @property
        def runtime_identity(self) -> str:
            """Native runtime observed before execution."""
            ...

    @runtime_checkable
    class GateCaptureStart(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Actual execution root."""
            ...

        @property
        def gate(self) -> t.NonEmptyStr:
            """Canonical stage identity."""
            ...

        @property
        def intent(self) -> FlextInfraProtocolsGates.GateExecutionIntent:
            """Portable original operation and selection."""
            ...

        @property
        def command(self) -> t.StrTuple:
            """Exact original process argv."""
            ...

        @property
        def repository(self) -> str | None:
            """Observed origin."""
            ...

        @property
        def commit_sha(self) -> str | None:
            """Observed commit."""
            ...

        @property
        def tree_sha(self) -> str | None:
            """Observed committed tree."""
            ...

        @property
        def dirty(self) -> bool | None:
            """Observed tracked and untracked WIP."""
            ...

        @property
        def runtime_identity(self) -> str:
            """Original native runtime."""
            ...

        @property
        def context_digest(self) -> str:
            """Original context."""
            ...

        @property
        def policy(self) -> c.Infra.GateAcceptancePolicy:
            """Policy."""
            ...

        @property
        def policy_digest(self) -> str:
            """Policy digest."""
            ...

        @property
        def started_at(self) -> t.NonEmptyStr:
            """UTC native start."""
            ...

        @property
        def issue(self) -> str | None:
            """Original candidate inspection failure."""
            ...

    @runtime_checkable
    class GateCaptureRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> c.Infra.CheckPhase:
            """Primary source admission or complete check acceptance."""
            ...

        @property
        def repository_root(self) -> Path:
            """Actual root selected by the public Make verb."""
            ...

        @property
        def gates(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Explicit native checker gate inventory; omitted resolves the runtime
            check partition from the typed Make spec.
            """
            ...

        @property
        def report_output(self) -> Path | None:
            """Invocation-owned typed checker summary destination."""
            ...

    @runtime_checkable
    class GateCaptureFinishRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def started(self) -> FlextInfraProtocolsGates.GateCaptureStart:
            """Original pre-execution candidate checkpoint."""
            ...

        @property
        def process(self) -> p.Cli.ProcessOutcome:
            """Reaped original producer outcome."""
            ...

        @property
        def reports(self) -> tuple[FlextInfraProtocolsGates.GateReportEvidence, ...]:
            """Original producer report byte bindings."""
            ...

        @property
        def report_root(self) -> Path:
            """Original capture publication directory."""
            ...

        @property
        def runtime_identity(self) -> str:
            """Native runtime observed after execution."""
            ...

    @runtime_checkable
    class GateCaptureReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def process(self) -> p.Cli.ProcessOutcome:
            """Reaped original producer outcome."""
            ...

        @property
        def receipt(self) -> Path | None:
            """Published immutable original receipt."""
            ...

        @property
        def issues(self) -> tuple[FlextInfraProtocolsCheck.Issue, ...]:
            """Actual capture or candidate eligibility failures."""
            ...

    @runtime_checkable
    class GateAttestationPredicate(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def schema_version(self) -> c.Infra.GateAttestationSchema:
            """Predicate schema identity."""
            ...

        @property
        def anchor_oid(self) -> str:
            """Original receipt's Git blob."""
            ...

        @property
        def signer(self) -> t.NonEmptyStr:
            """Allowed-signers principal."""
            ...

        @property
        def toolchain_digest(self) -> t.NonEmptyStr:
            """SHA-256 toolchain digest."""
            ...

        @property
        def context_digest(self) -> str:
            """Exact execution context."""
            ...

        @property
        def receipt(self) -> FlextInfraProtocolsGates.GateReportEvidence:
            """Original private producer receipt identity and digest."""
            ...

        @property
        def covered_gates(self) -> Sequence[str]:
            """Exactly covered original stage."""
            ...

        @property
        def commands(self) -> tuple[FlextInfraProtocolsGates.GateCommandEvidence, ...]:
            """Original accepted execution."""
            ...

    @runtime_checkable
    class GateAttestationCreateRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> str:
            """Git repository root."""
            ...

        @property
        def signer(self) -> t.NonEmptyStr:
            """Allowed-signers principal."""
            ...

        @property
        def gates(self) -> Sequence[str]:
            """Original canonical Make stage."""
            ...

        @property
        def receipt(self) -> Path:
            """Original producer receipt JSON."""
            ...

        @property
        def context_digest(self) -> str:
            """Expected execution context."""
            ...

        @property
        def policy(self) -> c.Infra.GateAcceptancePolicy:
            """Exact policy requested for this original evidence."""
            ...

        @property
        def policy_digest(self) -> str:
            """Expected recorded policy."""
            ...

        @property
        def allowed_signers(self) -> t.NonEmptyStr:
            """Trust file used before new or repeated publication."""
            ...

    @runtime_checkable
    class GateAttestationVerifyRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> str:
            """Git repository root."""
            ...

        @property
        def allowed_signers(self) -> t.NonEmptyStr:
            """OpenSSH allowed_signers file."""
            ...

        @property
        def expected_gates(self) -> Sequence[str]:
            """Required original stage."""
            ...

        @property
        def context_digest(self) -> str:
            """Expected execution context."""
            ...

        @property
        def policy(self) -> c.Infra.GateAcceptancePolicy:
            """Required policy for stage reuse."""
            ...

        @property
        def policy_digest(self) -> str:
            """Required recorded policy."""
            ...

        @property
        def receipt(self) -> Path:
            """Exact original workspace receipt."""
            ...

        @property
        def output(self) -> str | None:
            """Optional path receiving the verified predicate JSON."""
            ...

    @runtime_checkable
    class GateAttestationReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tag(self) -> t.NonEmptyStr:
            """Full attestation tag."""
            ...

        @property
        def anchor_oid(self) -> t.NonEmptyStr:
            """Original receipt blob."""
            ...

        @property
        def signer(self) -> t.NonEmptyStr:
            """Verified signer principal."""
            ...

        @property
        def covered_gates(self) -> Sequence[str]:
            """Covered gates."""
            ...

        @property
        def context_digest(self) -> str:
            """Verified execution context."""
            ...

        @property
        def reused(self) -> bool:
            """Existing immutable proof was reused."""
            ...

    @runtime_checkable
    class GateCandidateIdentity(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr:
            """Observed origin remote URL."""
            ...

        @property
        def head_oid(self) -> str:
            """Candidate HEAD commit."""
            ...

        @property
        def base_oid(self) -> str | None:
            """Optional base commit for PR checks."""
            ...

        @property
        def tree_oid(self) -> str:
            """Candidate commit tree."""
            ...

        @property
        def merge_oid(self) -> str | None:
            """Optional synthetic merge commit for PR checks."""
            ...

        @property
        def dirty(self) -> bool:
            """Candidate has uncommitted WIP."""
            ...

        @property
        def changed_paths_digest(self) -> str | None:
            """Digest of changed paths when dirty."""
            ...

    @runtime_checkable
    class GateCandidateAdmissionRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> str:
            """Git repository root."""
            ...

        @property
        def candidate(self) -> FlextInfraProtocolsGates.GateCandidateIdentity:
            """Exact candidate identity."""
            ...

        @property
        def allowed_signers(self) -> t.NonEmptyStr:
            """OpenSSH allowed_signers file."""
            ...

        @property
        def expected_gates(self) -> Sequence[str]:
            """Required original stage."""
            ...

        @property
        def context_digest(self) -> str:
            """Expected execution context."""
            ...

        @property
        def policy(self) -> c.Infra.GateAcceptancePolicy:
            """Required policy for stage reuse."""
            ...

        @property
        def policy_digest(self) -> str:
            """Required recorded policy."""
            ...

        @property
        def receipt(self) -> Path:
            """Exact original workspace receipt."""
            ...

        @property
        def require_clean(self) -> bool:
            """Require native_outcome CLEAN (not just complete_execution)."""
            ...

        @property
        def merge_check(self) -> bool:
            """Admit for PR merge (requires clean candidate)."""
            ...

        @property
        def ttl_seconds(self) -> int:
            """Maximum attestation age in seconds."""
            ...

    @runtime_checkable
    class GateCandidateAdmissionReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def eligible(self) -> bool:
            """Candidate is eligible."""
            ...

        @property
        def reasons(self) -> tuple[str, ...]:
            """Human-readable admission reasons."""
            ...

        @property
        def attestation(self) -> FlextInfraProtocolsGates.GateAttestationReport | None:
            """Verified attestation if eligible."""
            ...

        @property
        def candidate_head(self) -> str | None:
            """Candidate head that was evaluated."""
            ...

        @property
        def attested_head(self) -> str | None:
            """Attested head from the proof."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGates",
]
