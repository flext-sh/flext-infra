# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, p, t
from flext_infra._protocols import FlextInfraProtocolsCheck, FlextInfraProtocolsDeps


class FlextInfraProtocolsGates:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class SccFile(Protocol):
        """Structural data contract projected from the owning model."""

        location: str
        code: int

    @runtime_checkable
    class SccLanguage(Protocol):
        """Structural data contract projected from the owning model."""

        name: str
        files: tuple[FlextInfraProtocolsGates.SccFile, ...]

    @runtime_checkable
    class DeptryError(Protocol):
        """Structural data contract projected from the owning model."""

        code: str
        message: str

    @runtime_checkable
    class DeptryLocation(Protocol):
        """Structural data contract projected from the owning model."""

        file: str
        line: int | None
        column: int | None

    @runtime_checkable
    class DeptryDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        error: FlextInfraProtocolsGates.DeptryError
        module: str
        location: FlextInfraProtocolsGates.DeptryLocation

    @runtime_checkable
    class GateContext(Protocol):
        """Structural data contract projected from the owning model."""

        fail_fast: bool = ...
        repository_root: Path = ...
        runtime_root: Path | None = ...
        reports_dir: Path
        apply_fixes: bool = ...
        check_only: bool = ...
        runtime_dependency_inputs: p.Infra.RuntimeDependencyInputs | None = ...
        runtime_dependency_collector: (
            t.Port[FlextInfraProtocolsDeps.RuntimeDependencyCollector] | None
        ) = ...
        scope_facts: t.Port[FlextInfraProtocolsCheck.GitScopeFacts] | None = ...
        signal_wave: t.Port[p.Cli.SignalWave] | None = ...
        ruff_args: Sequence[str] = ...
        pyright_args: Sequence[str] = ...
        selected_files: tuple[Path, ...] = ...
        candidate_files: tuple[Path, ...] | None = ...
        check_progress: Callable[[Path, p.Infra.ProjectResult], None] | None = ...

    @runtime_checkable
    class MypyDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        file: str
        line: int
        column: int
        end_line: int | None = ...
        end_column: int | None = ...
        message: t.NonEmptyStr
        hint: str | None = ...
        code: str | None = ...
        severity: Literal["error", "note"]

    @runtime_checkable
    class PyrightPosition(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt
        character: t.NonNegativeInt

    @runtime_checkable
    class PyrightRange(Protocol):
        """Structural data contract projected from the owning model."""

        start: FlextInfraProtocolsGates.PyrightPosition
        end: FlextInfraProtocolsGates.PyrightPosition

    @runtime_checkable
    class PyrightDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        file: str
        severity: Literal["error", "warning", "information"]
        message: t.NonEmptyStr
        range: FlextInfraProtocolsGates.PyrightRange | None = ...
        rule: str | None = ...

    @runtime_checkable
    class PyrightSummary(Protocol):
        """Structural data contract projected from the owning model."""

        files_analyzed: t.NonNegativeInt
        error_count: t.NonNegativeInt
        warning_count: t.NonNegativeInt
        information_count: t.NonNegativeInt
        time_in_sec: float

    @runtime_checkable
    class PyrightReport(Protocol):
        """Structural data contract projected from the owning model."""

        version: t.NonEmptyStr
        time: t.NonEmptyStr
        general_diagnostics: Sequence[FlextInfraProtocolsGates.PyrightDiagnostic]
        summary: FlextInfraProtocolsGates.PyrightSummary

    @runtime_checkable
    class PyreflyDiagnostic(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt
        column: t.NonNegativeInt
        stop_line: t.NonNegativeInt
        stop_column: t.NonNegativeInt
        path: t.NonEmptyStr
        code: int
        name: t.NonEmptyStr
        description: t.NonEmptyStr
        concise_description: str
        severity: Literal["error", "warn", "info"]

    @runtime_checkable
    class PyreflyReport(Protocol):
        """Structural data contract projected from the owning model."""

        errors: Sequence[FlextInfraProtocolsGates.PyreflyDiagnostic]

    @runtime_checkable
    class GateReportEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        digest: str
        kind: c.Infra.GateEvidenceReportKind

    @runtime_checkable
    class GateTestIntent(Protocol):
        """Structural data contract projected from the owning model."""

        execution_mode: c.Infra.PytestExecutionMode
        target: Path
        target_file: Path | None
        ci_context: bool
        slow_phase: bool
        profile_enabled: bool

    @runtime_checkable
    class GateExecutionIntent(Protocol):
        """Structural data contract projected from the owning model."""

        phase: c.Infra.CheckPhase = ...
        requested_gates: t.StrTuple = ...
        test_selection: FlextInfraProtocolsGates.GateTestIntent | None = ...

    @runtime_checkable
    class GateExecutionFacts(Protocol):
        """Structural data contract projected from the owning model."""

        scope: Literal["workspace"]
        runtime_identity: str
        gate: t.NonEmptyStr
        command_digest: str
        process: m.Cli.ProcessOutcome
        native_outcome: c.Infra.ToolOutcome
        intent: FlextInfraProtocolsGates.GateExecutionIntent
        policy: c.Infra.GateAcceptancePolicy
        context_digest: str
        policy_digest: str
        reports: tuple[FlextInfraProtocolsGates.GateReportEvidence, ...]
        result_digest: t.NonEmptyStr
        started_at: t.NonEmptyStr
        completed_at: t.NonEmptyStr

    @runtime_checkable
    class GateCommandEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        scope: Literal["workspace"]
        runtime_identity: str
        gate: t.NonEmptyStr
        command_digest: str
        process: m.Cli.ProcessOutcome
        native_outcome: c.Infra.ToolOutcome
        intent: FlextInfraProtocolsGates.GateExecutionIntent
        policy: c.Infra.GateAcceptancePolicy
        context_digest: str
        policy_digest: str
        reports: tuple[FlextInfraProtocolsGates.GateReportEvidence, ...]
        result_digest: t.NonEmptyStr
        started_at: t.NonEmptyStr
        completed_at: t.NonEmptyStr
        repository: str | None
        commit_sha: str | None
        tree_sha: str | None
        dirty: bool | None
        after_repository: str | None
        after_commit_sha: str | None
        after_tree_sha: str | None
        after_dirty: bool | None

    @runtime_checkable
    class GateCaptureBeginRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        gate: t.NonEmptyStr
        command: t.StrTuple
        intent: FlextInfraProtocolsGates.GateExecutionIntent
        runtime_identity: str

    @runtime_checkable
    class GateCaptureStart(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        gate: t.NonEmptyStr
        intent: FlextInfraProtocolsGates.GateExecutionIntent
        command: t.StrTuple
        repository: str | None
        commit_sha: str | None
        tree_sha: str | None
        dirty: bool | None
        runtime_identity: str
        context_digest: str
        policy: c.Infra.GateAcceptancePolicy
        policy_digest: str
        started_at: t.NonEmptyStr
        issue: str | None

    @runtime_checkable
    class GateCaptureRequest(Protocol):
        """Structural data contract projected from the owning model."""

        phase: c.Infra.CheckPhase = ...
        repository_root: Path
        gates: t.NonEmptyStr | None = ...
        report_output: Path | None = ...

    @runtime_checkable
    class GateCaptureFinishRequest(Protocol):
        """Structural data contract projected from the owning model."""

        started: FlextInfraProtocolsGates.GateCaptureStart
        process: m.Cli.ProcessOutcome
        reports: tuple[FlextInfraProtocolsGates.GateReportEvidence, ...]
        report_root: Path
        runtime_identity: str

    @runtime_checkable
    class GateCaptureReport(Protocol):
        """Structural data contract projected from the owning model."""

        process: m.Cli.ProcessOutcome
        receipt: Path | None
        issues: tuple[p.Infra.Issue, ...] = ...

    @runtime_checkable
    class GateAttestationPredicate(Protocol):
        """Structural data contract projected from the owning model."""

        schema_version: c.Infra.GateAttestationSchema = ...
        anchor_oid: str
        signer: t.NonEmptyStr
        toolchain_digest: t.NonEmptyStr
        context_digest: str
        receipt: FlextInfraProtocolsGates.GateReportEvidence
        covered_gates: Sequence[str]
        commands: tuple[FlextInfraProtocolsGates.GateCommandEvidence, ...]

    @runtime_checkable
    class GateAttestationCreateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        workspace: str = ...
        signer: t.NonEmptyStr
        gates: Sequence[str]
        receipt: Path
        context_digest: str
        policy: c.Infra.GateAcceptancePolicy
        policy_digest: str
        allowed_signers: t.NonEmptyStr

    @runtime_checkable
    class GateAttestationVerifyRequest(Protocol):
        """Structural data contract projected from the owning model."""

        workspace: str = ...
        allowed_signers: t.NonEmptyStr
        expected_gates: Sequence[str]
        context_digest: str
        policy: c.Infra.GateAcceptancePolicy
        policy_digest: str
        receipt: Path
        output: str | None = ...

    @runtime_checkable
    class GateAttestationReport(Protocol):
        """Structural data contract projected from the owning model."""

        tag: t.NonEmptyStr
        anchor_oid: t.NonEmptyStr
        signer: t.NonEmptyStr
        covered_gates: Sequence[str]
        context_digest: str
        reused: bool = ...


__all__: list[str] = [
    "FlextInfraProtocolsGates",
]
