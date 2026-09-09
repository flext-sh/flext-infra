"""Domain models for quality gate execution."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import u

from flext_core import m
from flext_infra import c, t

from .duplication import FlextInfraModelsDuplication


class FlextInfraModelsGates(FlextInfraModelsDuplication):
    """Quality gate execution domain models."""

    class GateContext(m.ContractModel):
        """Quality gate execution context and configuration."""

        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = True
        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            extra="forbid", arbitrary_types_allowed=True, populate_by_name=True
        )
        repository_root: Path = m.Field(description="Repository root directory")
        reports_dir: Annotated[Path, m.Field(description="Reports output directory")]
        apply_fixes: Annotated[
            bool, m.Field(description="Apply supported fixes before checking")
        ] = False
        check_only: Annotated[
            bool,
            m.Field(description="Never write files even when fix mode is requested"),
        ] = False
        gate_mode: Annotated[
            Literal["error", "warn"],
            m.Field(
                description="Diagnostic presentation mode; errors and warnings always fail"
            ),
        ] = "error"
        ruff_args: Annotated[
            t.StrSequence, m.Field(description="Extra arguments for Ruff")
        ] = ()
        pyright_args: Annotated[
            t.StrSequence, m.Field(description="Extra arguments for Pyright")
        ] = ()

    class MypyDiagnostic(m.ContractModel):
        """One complete record from Mypy's native JSON formatter."""

        file: str
        line: int
        column: int
        end_line: int | None
        end_column: int | None
        message: t.NonEmptyStr
        hint: str | None
        code: str | None
        severity: Literal["error", "note"]

    class MypyCoverageReport(m.ContractModel):
        """Native linecoverage report, including files with no covered lines."""

        lines: Annotated[
            t.MappingKV[str, t.SequenceOf[t.PositiveInt]], m.Field(min_length=1)
        ]

        @u.model_validator(mode="after")
        def _validate_sources(self) -> Self:
            if any(not Path(path).is_absolute() for path in self.lines):
                msg = "Mypy coverage must identify absolute source paths"
                raise ValueError(msg)
            return self

    class PyrightPosition(m.ContractModel):
        """Zero-based native diagnostic position."""

        line: t.NonNegativeInt
        character: t.NonNegativeInt

    class PyrightRange(m.ContractModel):
        """Native diagnostic source range."""

        start: FlextInfraModelsGates.PyrightPosition
        end: FlextInfraModelsGates.PyrightPosition

    class PyrightDiagnostic(m.ContractModel):
        """Pyright's documented JSON diagnostic, including optional location."""

        file: str
        severity: Literal["error", "warning", "information"]
        message: t.NonEmptyStr
        range: FlextInfraModelsGates.PyrightRange | None = None
        rule: str | None = None

    class PyrightSummary(m.ContractModel):
        """Native completed-analysis counters; zero collection is not success."""

        files_analyzed: Annotated[t.PositiveInt, m.Field(alias="filesAnalyzed")]
        error_count: Annotated[t.NonNegativeInt, m.Field(alias="errorCount")]
        warning_count: Annotated[t.NonNegativeInt, m.Field(alias="warningCount")]
        information_count: Annotated[
            t.NonNegativeInt, m.Field(alias="informationCount")
        ]
        time_in_sec: Annotated[float, m.Field(alias="timeInSec", ge=0)]

    class PyrightReport(m.ContractModel):
        """Complete native Pyright report with reconciled diagnostic counts."""

        version: t.NonEmptyStr
        time: t.NonEmptyStr
        general_diagnostics: Annotated[
            t.SequenceOf[FlextInfraModelsGates.PyrightDiagnostic],
            m.Field(alias="generalDiagnostics"),
        ]
        summary: FlextInfraModelsGates.PyrightSummary

        @u.model_validator(mode="after")
        def _validate_counts(self) -> Self:
            for severity, count in (
                ("error", self.summary.error_count),
                ("warning", self.summary.warning_count),
                ("information", self.summary.information_count),
            ):
                if sum(
                    item.severity == severity for item in self.general_diagnostics
                ) != count:
                    msg = f"Pyright {severity} count does not match its diagnostics"
                    raise ValueError(msg)
            return self

    class PyreflyDiagnostic(m.ContractModel):
        """Native Pyrefly JSON error entry, without path-based suppression."""

        line: t.NonNegativeInt
        column: t.NonNegativeInt
        stop_line: t.NonNegativeInt
        stop_column: t.NonNegativeInt
        path: t.NonEmptyStr
        code: int
        name: t.NonEmptyStr
        description: t.NonEmptyStr
        concise_description: str
        severity: Literal["error", "warn", "warning", "info"]

    class PyreflyReport(m.ContractModel):
        """Required native Pyrefly JSON envelope, including a clean empty list."""

        errors: t.SequenceOf[FlextInfraModelsGates.PyreflyDiagnostic]

    class GateCommandEvidence(m.ContractModel):
        """One canonical Make invocation covered by an attestation."""

        gate: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[a-z][a-z0-9-]*$", description="Canonical Make gate name"
            ),
        ]
        command: Annotated[t.NonEmptyStr, m.Field(description="Exact Make command")]
        cwd: Annotated[t.NonEmptyStr, m.Field(description="Absolute working directory")]
        exit_code: Annotated[Literal[0], m.Field(description="Successful exit code")]
        result_digest: Annotated[
            t.NonEmptyStr, m.Field(description="SHA-256 digest of the gate result")
        ]
        started_at: Annotated[t.NonEmptyStr, m.Field(description="UTC start timestamp")]
        completed_at: Annotated[
            t.NonEmptyStr, m.Field(description="UTC completion timestamp")
        ]

        @u.model_validator(mode="after")
        def _validate_evidence(self) -> Self:
            if not self.command.startswith(f"make {self.gate}"):
                msg = "gate evidence command must use canonical make <gate>"
                raise ValueError(msg)
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.result_digest):
                msg = "result_digest must be sha256:<64 lowercase hex>"
                raise ValueError(msg)
            started = datetime.fromisoformat(self.started_at)
            completed = datetime.fromisoformat(self.completed_at)
            if started.tzinfo != UTC or completed.tzinfo != UTC or completed < started:
                msg = "gate timestamps must be ordered UTC timestamps"
                raise ValueError(msg)
            return self

    class GateAttestationPredicate(m.ContractModel):
        """Canonical signed statement for locally completed gates."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            extra="forbid", frozen=True, strict=False
        )

        schema_version: Annotated[
            str, m.Field(description="Predicate schema identity")
        ] = c.Infra.GATE_ATTESTATION_SCHEMA
        repository: Annotated[t.NonEmptyStr, m.Field(description="Origin repository")]
        commit_sha: Annotated[t.NonEmptyStr, m.Field(description="Full commit SHA")]
        tree_sha: Annotated[t.NonEmptyStr, m.Field(description="Full tree SHA")]
        signer: Annotated[
            t.NonEmptyStr, m.Field(description="Allowed-signers principal")
        ]
        toolchain_digest: Annotated[
            t.NonEmptyStr, m.Field(description="SHA-256 toolchain digest")
        ]
        covered_gates: Annotated[
            t.StrSequence, m.Field(min_length=1, description="Exactly covered gates")
        ]
        commands: Annotated[
            t.VariadicTuple[FlextInfraModelsGates.GateCommandEvidence],
            m.Field(min_length=1, description="Successful canonical invocations"),
        ]

        @u.model_validator(mode="after")
        def _validate_predicate(self) -> Self:
            if self.schema_version != c.Infra.GATE_ATTESTATION_SCHEMA:
                msg = "schema_version must match the canonical gate attestation schema"
                raise ValueError(msg)
            for name, value in (
                ("commit_sha", self.commit_sha),
                ("tree_sha", self.tree_sha),
            ):
                if not re.fullmatch(r"[0-9a-f]{40}", value):
                    msg = f"{name} must be a full lowercase Git SHA"
                    raise ValueError(msg)
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
        """Run required gates and transparently create the signed HEAD proof."""

        workspace: Annotated[str, m.Field(description="Git repository root")] = "."
        signer: Annotated[
            t.NonEmptyStr, m.Field(description="Allowed-signers principal")
        ]
        gates: Annotated[
            t.StrSequence, m.Field(min_length=1, description="Canonical Make gates")
        ]

        @u.model_validator(mode="after")
        def _validate_gates(self) -> Self:
            if len(self.gates) != len(set(self.gates)):
                msg = "attestation gates must be unique"
                raise ValueError(msg)
            return self

    class GateAttestationVerifyRequest(m.ContractModel):
        """Verify the signed attestation for the repository HEAD."""

        workspace: Annotated[str, m.Field(description="Git repository root")] = "."
        allowed_signers: Annotated[
            t.NonEmptyStr, m.Field(description="OpenSSH allowed_signers file")
        ]
        expected_gates: Annotated[
            t.StrSequence, m.Field(min_length=1, description="Required gate coverage")
        ]
        commit_sha: Annotated[
            t.NonEmptyStr, m.Field(description="Exact attested commit SHA")
        ]
        output: Annotated[
            str | None,
            m.Field(description="Optional path receiving the verified predicate JSON"),
        ] = None

        @u.model_validator(mode="after")
        def _validate_expected_gates(self) -> Self:
            if len(self.expected_gates) != len(set(self.expected_gates)):
                msg = "expected attestation gates must be unique"
                raise ValueError(msg)
            if not re.fullmatch(r"[0-9a-f]{40}", self.commit_sha):
                msg = "commit_sha must be a full lowercase Git SHA"
                raise ValueError(msg)
            return self

    class GateAttestationReport(m.ContractModel):
        """Verified or newly created signed gate attestation."""

        tag: Annotated[t.NonEmptyStr, m.Field(description="Full attestation tag")]
        commit_sha: Annotated[t.NonEmptyStr, m.Field(description="Attested commit SHA")]
        tree_sha: Annotated[t.NonEmptyStr, m.Field(description="Attested tree SHA")]
        signer: Annotated[
            t.NonEmptyStr, m.Field(description="Verified signer principal")
        ]
        covered_gates: Annotated[t.StrSequence, m.Field(description="Covered gates")]


__all__: list[str] = ["FlextInfraModelsGates"]
