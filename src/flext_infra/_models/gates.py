"""Domain models for quality gate execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, p

from flext_infra import c, t
from flext_infra._models import (
    FlextInfraModelsCheck,
    FlextInfraModelsDeps,
    FlextInfraModelsDuplication,
)
from flext_infra._protocols import FlextInfraProtocolsCheck, FlextInfraProtocolsDeps


class FlextInfraModelsGates(FlextInfraModelsDuplication):
    """Quality gate execution domain models."""

    class SccFile(m.FlexibleModel):
        """Required per-file SCC fields; unrelated scanner metrics are ignored."""

        location: Annotated[
            str,
            m.Field(
                alias="Location",
                min_length=1,
                strict=True,
                description="Scanned file path",
            ),
        ]
        code: Annotated[
            int,
            m.Field(alias="Code", ge=0, strict=True, description="Logical code lines"),
        ]

    class SccLanguage(m.FlexibleModel):
        """Required language group from SCC's JSON by-file output."""

        name: Annotated[
            str,
            m.Field(
                alias="Name",
                min_length=1,
                strict=True,
                description="Scanner language name",
            ),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraModelsGates.SccFile],
            m.Field(alias="Files", description="Every scanned file in this language"),
        ]

    class SccReport(m.RootModel[tuple[SccLanguage, ...]]):
        """Native SCC groups, including an empty scan; malformed JSON fails."""

    class DeptryError(m.ContractModel):
        """Native deptry rule identity and complete diagnostic message."""

        code: Annotated[
            str,
            m.Field(min_length=1, strict=True, description="Deptry rule code"),
        ]
        message: Annotated[
            str,
            m.Field(min_length=1, strict=True, description="Deptry diagnostic message"),
        ]

    class DeptryLocation(m.ContractModel):
        """Native deptry location; dependency declarations have null positions."""

        file: Annotated[
            str,
            m.Field(min_length=1, strict=True, description="Diagnostic file path"),
        ]
        line: Annotated[
            int | None,
            m.Field(
                ge=0, strict=True, description="Source line, null for declarations"
            ),
        ]
        column: Annotated[
            int | None,
            m.Field(
                ge=0, strict=True, description="Source column, null for declarations"
            ),
        ]

    class DeptryDiagnostic(m.ContractModel):
        """Required deptry JSON record, never a partially recognized mapping."""

        error: Annotated[
            FlextInfraModelsGates.DeptryError,
            m.Field(description="Deptry rule and diagnostic message"),
        ]
        module: Annotated[
            str,
            m.Field(
                min_length=1, strict=True, description="Reported module or dependency"
            ),
        ]
        location: Annotated[
            FlextInfraModelsGates.DeptryLocation,
            m.Field(description="Diagnostic file and nullable source positions"),
        ]

    class DeptryNativeReport(m.RootModel[tuple[DeptryDiagnostic, ...]]):
        """Native deptry JSON array; only a valid empty array means no findings."""

    class DeptryScan(m.Value):
        """Native findings bound to the exact settings and report bytes."""

        scanned_files: Annotated[
            int,
            m.Field(
                ge=1, strict=True, description="Native extractor's executed file count"
            ),
        ]
        venv_bin: Annotated[
            Path,
            m.Field(description="Explicit runtime binary directory owning the scanner"),
        ]
        source: Annotated[
            t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
            m.Field(
                min_length=1, description="Production trees consumed by the scanner"
            ),
        ]
        native: Annotated[
            m.Cli.CommandOutput,
            m.Field(description="Native deptry process completion and raw output"),
        ]
        settings: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Consumed pyproject state"),
        ]
        report_state: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Fresh native report state"),
        ]
        report_sha256: Annotated[
            str,
            m.Field(
                pattern=r"^[0-9a-f]{64}$", description="Exact native report digest"
            ),
        ]
        report: Annotated[
            FlextInfraModelsGates.DeptryNativeReport,
            m.Field(description="Complete native findings"),
        ]

    class GateContext(m.ContractModel):
        """Quality gate execution context and configuration."""

        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = (
            c.Infra.CHECK_FAIL_FAST_DEFAULT
        )
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            arbitrary_types_allowed=True,
            populate_by_name=True,
        )
        repository_root: Path = m.Field(description="Repository root directory")
        runtime_root: Annotated[
            Path | None,
            m.Field(
                description="Explicit physical runtime owner for a staged candidate"
            ),
        ] = None
        reports_dir: Annotated[Path, m.Field(description="Reports output directory")]
        apply_fixes: Annotated[
            bool,
            m.Field(description="Execute supported repairs instead of checking"),
        ] = False
        check_only: Annotated[
            bool,
            m.Field(description="Never write files even when fix mode is requested"),
        ] = False
        runtime_dependency_inputs: Annotated[
            FlextInfraModelsDeps.RuntimeDependencyInputs | None,
            m.Field(
                description="Target-runtime dependency proof injected at composition"
            ),
        ] = None
        runtime_dependency_collector: Annotated[
            t.Port[FlextInfraProtocolsDeps.RuntimeDependencyCollector] | None,
            m.Field(description="Explicit composition-owned target supplier collector"),
        ] = None
        scope_facts: Annotated[
            t.Port[FlextInfraProtocolsCheck.GitScopeFacts] | None,
            m.Field(
                description=(
                    "Invocation-owned Git scope facts shared by applicability "
                    "and every gate; absent means each query reads Git"
                ),
                exclude=True,
            ),
        ] = None
        signal_wave: Annotated[
            t.Port[p.Cli.SignalWave] | None,
            m.Field(
                description=(
                    "Signal wave of the concurrent stage running this gate; "
                    "absent on the main thread"
                ),
                exclude=True,
            ),
        ] = None
        ruff_args: Annotated[
            t.StrSequence,
            m.Field(description="Extra arguments for Ruff"),
        ] = ()
        pyright_args: Annotated[
            t.StrSequence,
            m.Field(description="Extra arguments for Pyright"),
        ] = ()
        selected_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(
                description="Validated literal file selection; empty means project"
            ),
        ] = ()
        candidate_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Complete sealed source-plan inventory for admission"),
        ] = ()
        check_progress: Annotated[
            Callable[[Path, FlextInfraModelsCheck.ProjectResult], None] | None,
            m.Field(
                description="Invocation-owned observer of reached native gate results",
                exclude=True,
            ),
        ] = None

        @m.model_validator(mode="after")
        def dependency_provenance_selection(self) -> Self:
            """Reject competing dependency suppliers at the composition boundary.

            Returns:
                The validated model instance.

            Raises:
                ValueError: If both a runtime dependency input and a collector
                    are supplied.

            """
            if (
                self.runtime_dependency_inputs is not None
                and self.runtime_dependency_collector is not None
            ):
                msg = "dependency provenance has competing providers"
                raise ValueError(msg)
            return self

    class MypyDiagnostic(m.ContractModel):
        """One complete record from Mypy's native JSON formatter."""

        file: Annotated[str, m.Field(description="Diagnostic source file path")]
        line: Annotated[int, m.Field(description="Diagnostic start line")]
        column: Annotated[int, m.Field(description="Diagnostic start column")]
        end_line: Annotated[int | None, m.Field(description="Diagnostic end line")] = (
            None
        )
        end_column: Annotated[
            int | None, m.Field(description="Diagnostic end column")
        ] = None
        message: Annotated[t.NonEmptyStr, m.Field(description="Diagnostic message")]
        hint: Annotated[str | None, m.Field(description="Diagnostic hint")] = None
        code: Annotated[str | None, m.Field(description="Mypy diagnostic code")] = None
        severity: Annotated[
            Literal["error", "note"],
            m.Field(description="Mypy diagnostic severity"),
        ]

    class PyrightPosition(m.ContractModel):
        """Zero-based native diagnostic position."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Zero-based line index")]
        character: Annotated[
            t.NonNegativeInt,
            m.Field(description="Zero-based character index"),
        ]

    class PyrightRange(m.ContractModel):
        """Native diagnostic source range."""

        start: Annotated[
            FlextInfraModelsGates.PyrightPosition,
            m.Field(description="Diagnostic range start position"),
        ]
        end: Annotated[
            FlextInfraModelsGates.PyrightPosition,
            m.Field(description="Diagnostic range end position"),
        ]

    class PyrightDiagnostic(m.ContractModel):
        """Pyright's documented JSON diagnostic, including optional location."""

        file: Annotated[str, m.Field(description="Diagnostic source file path")]
        severity: Annotated[
            Literal["error", "warning", "information"],
            m.Field(description="Pyright diagnostic severity"),
        ]
        message: Annotated[t.NonEmptyStr, m.Field(description="Diagnostic message")]
        range: Annotated[
            FlextInfraModelsGates.PyrightRange | None,
            m.Field(description="Diagnostic source range when available"),
        ] = None
        rule: Annotated[
            str | None,
            m.Field(description="Pyright diagnostic rule when available"),
        ] = None

    class PyrightSummary(m.ContractModel):
        """Native completed-analysis counters.

        The model accepts ``filesAnalyzed=0``; the gate layer decides that an
        empty analysis of a project with Python targets is a failure.
        """

        files_analyzed: Annotated[
            t.NonNegativeInt,
            m.Field(alias="filesAnalyzed", description="Number of analyzed files"),
        ]
        error_count: Annotated[
            t.NonNegativeInt,
            m.Field(alias="errorCount", description="Number of error diagnostics"),
        ]
        warning_count: Annotated[
            t.NonNegativeInt,
            m.Field(alias="warningCount", description="Number of warning diagnostics"),
        ]
        information_count: Annotated[
            t.NonNegativeInt,
            m.Field(
                alias="informationCount",
                description="Number of informational diagnostics",
            ),
        ]
        time_in_sec: Annotated[
            float,
            m.Field(
                alias="timeInSec",
                ge=0,
                description="Analysis duration in seconds",
            ),
        ]

    class PyrightReport(m.ContractModel):
        """Complete native Pyright report with reconciled diagnostic counts."""

        version: Annotated[t.NonEmptyStr, m.Field(description="Pyright version")]
        time: Annotated[t.NonEmptyStr, m.Field(description="Report timestamp")]
        general_diagnostics: Annotated[
            t.SequenceOf[FlextInfraModelsGates.PyrightDiagnostic],
            m.Field(alias="generalDiagnostics", description="Pyright diagnostics"),
        ]
        summary: Annotated[
            FlextInfraModelsGates.PyrightSummary,
            m.Field(description="Completed analysis summary"),
        ]

        @m.model_validator(mode="after")
        def _validate_counts(self) -> Self:
            for severity, count in (
                ("error", self.summary.error_count),
                ("warning", self.summary.warning_count),
                ("information", self.summary.information_count),
            ):
                if (
                    sum(item.severity == severity for item in self.general_diagnostics)
                    != count
                ):
                    msg = f"Pyright {severity} count does not match its diagnostics"
                    raise ValueError(msg)
            return self

    class PyreflyDiagnostic(m.ContractModel):
        """Native Pyrefly JSON error entry, without path-based suppression."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Diagnostic start line")]
        column: Annotated[
            t.NonNegativeInt,
            m.Field(description="Diagnostic start column"),
        ]
        stop_line: Annotated[
            t.NonNegativeInt,
            m.Field(description="Diagnostic end line"),
        ]
        stop_column: Annotated[
            t.NonNegativeInt,
            m.Field(description="Diagnostic end column"),
        ]
        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Diagnostic source file path"),
        ]
        code: Annotated[int, m.Field(description="Pyrefly diagnostic code")]
        name: Annotated[t.NonEmptyStr, m.Field(description="Pyrefly diagnostic name")]
        description: Annotated[
            t.NonEmptyStr,
            m.Field(description="Full diagnostic description"),
        ]
        concise_description: Annotated[
            str,
            m.Field(description="Concise diagnostic description"),
        ]
        severity: Annotated[
            Literal["error", "warn", "info"],
            m.Field(description="Pyrefly diagnostic severity"),
        ]

    class PyreflyReport(m.ContractModel):
        """Required native Pyrefly JSON envelope, including a clean empty list."""

        errors: Annotated[
            t.SequenceOf[FlextInfraModelsGates.PyreflyDiagnostic],
            m.Field(description="Native Pyrefly diagnostics"),
        ]

    class GateReportEvidence(m.ContractModel):
        """One original report bound to its repository-relative identity."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        path: Annotated[
            Path,
            m.Field(description="Repository-relative report path"),
        ]
        digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Original report byte digest",
            ),
        ]
        kind: Annotated[
            c.Infra.GateEvidenceReportKind,
            m.Field(description="Canonical producer report contract"),
        ]

        @m.model_validator(mode="after")
        def _validate_report_path(self) -> Self:
            if self.path.is_absolute() or ".." in self.path.parts:
                msg = "attestation report path must remain inside its repository"
                raise ValueError(msg)
            return self

    class GateTestIntent(m.ContractModel):
        """Portable original test selection bound to the execution proof."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        execution_mode: Annotated[
            c.Infra.PytestExecutionMode, m.Field(description="Native test operation")
        ]
        target: Annotated[Path, m.Field(description="Repository-relative test root")]
        target_file: Annotated[
            Path | None, m.Field(description="Original selected test file")
        ]
        ci_context: Annotated[bool, m.Field(description="Original CI selection")]
        slow_phase: Annotated[bool, m.Field(description="Original slow-test phase")]
        profile_enabled: Annotated[
            bool, m.Field(description="Original native process profiling")
        ]

        @m.model_validator(mode="after")
        def _validate_targets(self) -> Self:
            for path in (self.target, self.target_file):
                if path is not None and (path.is_absolute() or ".." in path.parts):
                    msg = "original test selection must remain repository-relative"
                    raise ValueError(msg)
            return self

    class GateExecutionIntent(m.ContractModel):
        """Producer-owned operation coverage, independent of local argv paths."""

        requested_gates: Annotated[
            t.StrTuple, m.Field(description="Requested native checker gates")
        ] = ()
        test_selection: Annotated[
            FlextInfraModelsGates.GateTestIntent | None,
            m.Field(description="Original test selection; absent for checker"),
        ] = None

        @m.model_validator(mode="after")
        def _validate_producer(self) -> Self:
            if bool(self.requested_gates) == (self.test_selection is not None):
                msg = "original operation must declare exactly one producer intent"
                raise ValueError(msg)
            return self

    class GateExecutionFacts(m.ContractModel):
        """Public original execution facts, excluding local machine identities."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        scope: Annotated[
            Literal["workspace"],
            m.Field(description="Execution evidence, never validation of a Git commit"),
        ]
        runtime_identity: Annotated[
            str, m.Field(description="Native runtime identity consumed by execution")
        ]

        gate: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[a-z][a-z0-9-]*$",
                description="Canonical Make gate name",
            ),
        ]
        command_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Digest of the private exact original process argv",
            ),
        ]
        process: Annotated[
            m.Cli.ProcessOutcome,
            m.Field(description="Original Make process outcome, without normalization"),
        ]
        native_outcome: Annotated[
            c.Infra.ToolOutcome,
            m.Field(description="Original producer's native report classification"),
        ]
        intent: Annotated[
            FlextInfraModelsGates.GateExecutionIntent,
            m.Field(description="Portable original operation and selection"),
        ]
        policy: Annotated[
            c.Infra.GateAcceptancePolicy,
            m.Field(description="Exact recorded policy used to derive admission"),
        ]
        context_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description=(
                    "Original runtime, platform and operation-context fingerprint"
                ),
            ),
        ]
        policy_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Original acceptance policy",
            ),
        ]
        reports: Annotated[
            t.VariadicTuple[FlextInfraModelsGates.GateReportEvidence],
            m.Field(
                min_length=1, description="Original report identities and byte digests"
            ),
        ]
        result_digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 digest of the gate result"),
        ]
        started_at: Annotated[t.NonEmptyStr, m.Field(description="UTC start timestamp")]
        completed_at: Annotated[
            t.NonEmptyStr,
            m.Field(description="UTC completion timestamp"),
        ]

        @m.model_validator(mode="after")
        def _validate_evidence(self) -> Self:
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.result_digest):
                msg = "result_digest must be sha256:<64 lowercase hex>"
                raise ValueError(msg)
            started = datetime.fromisoformat(self.started_at)
            completed = datetime.fromisoformat(self.completed_at)
            if started.tzinfo != UTC or completed.tzinfo != UTC or completed < started:
                msg = "gate timestamps must be ordered UTC timestamps"
                raise ValueError(msg)
            return self

    class GateCommandEvidence(GateExecutionFacts):
        """Workspace execution with observational, non-gating Git metadata."""

        repository: Annotated[str | None, m.Field(description="Observed start origin")]
        commit_sha: Annotated[
            str | None,
            m.Field(pattern=r"^[a-f0-9]{40}$", description="Observed start HEAD"),
        ]
        tree_sha: Annotated[
            str | None,
            m.Field(
                pattern=r"^[a-f0-9]{40}$", description="Observed start commit tree"
            ),
        ]
        dirty: Annotated[bool | None, m.Field(description="Observed start WIP state")]
        after_repository: Annotated[
            str | None, m.Field(description="Observed end origin")
        ]
        after_commit_sha: Annotated[
            str | None,
            m.Field(pattern=r"^[a-f0-9]{40}$", description="Observed end HEAD"),
        ]
        after_tree_sha: Annotated[
            str | None,
            m.Field(pattern=r"^[a-f0-9]{40}$", description="Observed end commit tree"),
        ]
        after_dirty: Annotated[
            bool | None, m.Field(description="Observed end WIP state")
        ]

    class GateCaptureBeginRequest(m.ContractModel):
        """Original producer operation and runtime before candidate inspection."""

        repository_root: Annotated[Path, m.Field(description="Actual execution root")]
        gate: Annotated[t.NonEmptyStr, m.Field(description="Canonical stage identity")]
        command: Annotated[
            t.StrTuple, m.Field(min_length=1, description="Exact original process argv")
        ]
        intent: Annotated[
            FlextInfraModelsGates.GateExecutionIntent,
            m.Field(description="Portable original operation and selection"),
        ]
        runtime_identity: Annotated[
            str, m.Field(description="Native runtime observed before execution")
        ]

    class GateCaptureStart(m.ContractModel):
        """Private candidate checkpoint preceding the original native process."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        repository_root: Annotated[Path, m.Field(description="Actual execution root")]
        gate: Annotated[t.NonEmptyStr, m.Field(description="Canonical stage identity")]
        intent: Annotated[
            FlextInfraModelsGates.GateExecutionIntent,
            m.Field(description="Portable original operation and selection"),
        ]
        command: Annotated[
            t.StrTuple, m.Field(min_length=1, description="Exact original process argv")
        ]
        repository: Annotated[str | None, m.Field(description="Observed origin")]
        commit_sha: Annotated[str | None, m.Field(description="Observed commit")]
        tree_sha: Annotated[str | None, m.Field(description="Observed committed tree")]
        dirty: Annotated[
            bool | None, m.Field(description="Observed tracked and untracked WIP")
        ]
        runtime_identity: Annotated[str, m.Field(description="Original native runtime")]
        context_digest: Annotated[
            str,
            m.Field(pattern=r"^sha256:[a-f0-9]{64}$", description="Original context"),
        ]
        policy: Annotated[c.Infra.GateAcceptancePolicy, m.Field(description="Policy")]
        policy_digest: Annotated[
            str,
            m.Field(pattern=r"^sha256:[a-f0-9]{64}$", description="Policy digest"),
        ]
        started_at: Annotated[t.NonEmptyStr, m.Field(description="UTC native start")]
        issue: Annotated[
            str | None, m.Field(description="Original candidate inspection failure")
        ]

    class GateCaptureRequest(m.ContractModel):
        """Capture the original read-only checker invocation exactly once."""

        repository_root: Annotated[
            Path, m.Field(description="Actual root selected by the public Make verb")
        ]
        gates: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Explicit native checker gate inventory; omitted resolves "
                    "the runtime check partition from the typed Make spec"
                ),
            ),
        ] = None
        report_output: Annotated[
            Path | None,
            m.Field(description="Invocation-owned typed checker summary destination"),
        ] = None

    class GateCaptureFinishRequest(m.ContractModel):
        """Reaped producer facts and publication context for one original capture."""

        started: Annotated[
            FlextInfraModelsGates.GateCaptureStart,
            m.Field(description="Original pre-execution candidate checkpoint"),
        ]
        process: Annotated[
            m.Cli.ProcessOutcome,
            m.Field(description="Reaped original producer outcome"),
        ]
        reports: Annotated[
            t.VariadicTuple[FlextInfraModelsGates.GateReportEvidence],
            m.Field(description="Original producer report byte bindings"),
        ]
        report_root: Annotated[
            Path, m.Field(description="Original capture publication directory")
        ]
        runtime_identity: Annotated[
            str, m.Field(description="Native runtime observed after execution")
        ]

    class GateCaptureReport(m.ContractModel):
        """Original process and publication outcome, independent of acceptance."""

        process: Annotated[
            m.Cli.ProcessOutcome,
            m.Field(description="Reaped original producer outcome"),
        ]
        receipt: Annotated[
            Path | None, m.Field(description="Published immutable original receipt")
        ]
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Actual capture or candidate eligibility failures"),
        ] = ()

    class GateAttestationPredicate(m.ContractModel):
        """Signed workspace execution, stored on an observational Git anchor."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=False,
            use_enum_values=False,
        )

        schema_version: Annotated[
            c.Infra.GateAttestationSchema,
            m.Field(description="Predicate schema identity"),
        ] = c.Infra.GateAttestationSchema.V3
        anchor_oid: Annotated[
            str,
            m.Field(
                pattern=r"^[a-f0-9]{40}$", description="Original receipt's Git blob"
            ),
        ]
        signer: Annotated[
            t.NonEmptyStr,
            m.Field(description="Allowed-signers principal"),
        ]
        toolchain_digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 toolchain digest"),
        ]
        context_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$", description="Exact execution context"
            ),
        ]
        receipt: Annotated[
            FlextInfraModelsGates.GateReportEvidence,
            m.Field(
                description="Original private producer receipt identity and digest"
            ),
        ]
        covered_gates: Annotated[
            t.StrSequence,
            m.Field(
                min_length=1, max_length=1, description="Exactly covered original stage"
            ),
        ]
        commands: Annotated[
            t.VariadicTuple[FlextInfraModelsGates.GateCommandEvidence],
            m.Field(
                min_length=1, max_length=1, description="Original accepted execution"
            ),
        ]

        @m.model_validator(mode="after")
        def _validate_predicate(self) -> Self:
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.toolchain_digest):
                msg = "toolchain_digest must be sha256:<64 lowercase hex>"
                raise ValueError(msg)
            gates = tuple(item.gate for item in self.commands)
            covered_gates = tuple(self.covered_gates)
            if (
                len(gates) != len(set(gates))
                or len(covered_gates) != len(set(covered_gates))
                or gates != covered_gates
            ):
                msg = "covered_gates and command evidence must match one-to-one"
                raise ValueError(msg)
            return self

    class GateAttestationCreateRequest(m.ContractModel):
        """Consume one original receipt and create its immutable signed stage proof."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        workspace: Annotated[str, m.Field(description="Git repository root")] = "."
        signer: Annotated[
            t.NonEmptyStr,
            m.Field(description="Allowed-signers principal"),
        ]
        gates: Annotated[
            t.StrSequence,
            m.Field(
                min_length=1, max_length=1, description="Original canonical Make stage"
            ),
        ]
        receipt: Annotated[Path, m.Field(description="Original producer receipt JSON")]
        context_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Expected execution context",
            ),
        ]
        policy: Annotated[
            c.Infra.GateAcceptancePolicy,
            m.Field(description="Exact policy requested for this original evidence"),
        ]
        policy_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$", description="Expected recorded policy"
            ),
        ]
        allowed_signers: Annotated[
            t.NonEmptyStr,
            m.Field(description="Trust file used before new or repeated publication"),
        ]

        @m.model_validator(mode="after")
        def _validate_gates(self) -> Self:
            if len(self.gates) != len(set(self.gates)):
                msg = "attestation gates must be unique"
                raise ValueError(msg)
            return self

    class GateAttestationVerifyRequest(m.ContractModel):
        """Verify one original workspace receipt and its signed storage anchor."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        workspace: Annotated[str, m.Field(description="Git repository root")] = "."
        allowed_signers: Annotated[
            t.NonEmptyStr,
            m.Field(description="OpenSSH allowed_signers file"),
        ]
        expected_gates: Annotated[
            t.StrSequence,
            m.Field(min_length=1, max_length=1, description="Required original stage"),
        ]
        context_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Expected execution context",
            ),
        ]
        policy: Annotated[
            c.Infra.GateAcceptancePolicy,
            m.Field(description="Required policy for stage reuse"),
        ]
        policy_digest: Annotated[
            str,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$", description="Required recorded policy"
            ),
        ]
        receipt: Annotated[
            Path, m.Field(description="Exact original workspace receipt")
        ]
        output: Annotated[
            str | None,
            m.Field(description="Optional path receiving the verified predicate JSON"),
        ] = None

        @m.model_validator(mode="after")
        def _validate_expected_gates(self) -> Self:
            if len(self.expected_gates) != len(set(self.expected_gates)):
                msg = "expected attestation gates must be unique"
                raise ValueError(msg)
            return self

    class GateAttestationReport(m.ContractModel):
        """Verified or newly created signed gate attestation."""

        tag: Annotated[t.NonEmptyStr, m.Field(description="Full attestation tag")]
        anchor_oid: Annotated[
            t.NonEmptyStr, m.Field(description="Original receipt blob")
        ]
        signer: Annotated[
            t.NonEmptyStr,
            m.Field(description="Verified signer principal"),
        ]
        covered_gates: Annotated[t.StrSequence, m.Field(description="Covered gates")]
        context_digest: Annotated[
            str, m.Field(description="Verified execution context")
        ]
        reused: Annotated[
            bool, m.Field(description="Existing immutable proof was reused")
        ] = False


__all__: list[str] = ["FlextInfraModelsGates"]
