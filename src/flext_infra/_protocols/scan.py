# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/scan
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import (
        FlextInfraProtocolsCodemod,
        FlextInfraProtocolsRefactorAstGrep,
    )


class FlextInfraProtocolsScan:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModScanPublication(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def command(self) -> c.Infra.ModScanCommand:
            """Actual native scan operation."""
            ...

        @property
        def scope(self) -> Sequence[str]:
            """Actual governed scan scope."""
            ...

        @property
        def relative_path(self) -> Path:
            """Invocation evidence destination under root."""
            ...

        @property
        def repositories(self) -> Sequence[str]:
            """Observed repository inventory."""
            ...

        @property
        def rule_ids(self) -> Sequence[str]:
            """Actual elected rule inventory."""
            ...

    @runtime_checkable
    class ScanViolation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

        @property
        def message(self) -> str:
            """Human-readable violation description."""
            ...

        @property
        def severity(self) -> str:
            """Violation severity level."""
            ...

        @property
        def rule_id(self) -> str | None:
            """Optional rule identifier."""
            ...

    @runtime_checkable
    class ScanResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path

        @property
        def violations(self) -> Sequence[FlextInfraProtocolsScan.ScanViolation]:
            """Violations found in the file."""
            ...

        detector_name: str

    @runtime_checkable
    class ModNativeRecord(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def offset(self) -> int:
            """Record start byte in the native artifact."""
            ...

        @property
        def length(self) -> int:
            """Complete native record byte length."""
            ...

        @property
        def sha256(self) -> str:
            """Digest of the complete native record bytes."""
            ...

    @runtime_checkable
    class ModReplacementOffsets(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> int:
            """Inclusive start byte."""
            ...

        @property
        def end(self) -> int:
            """Exclusive end byte."""
            ...

    @runtime_checkable
    class ModOccurrence(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_file(self) -> t.NonEmptyStr:
            """Rule document file producing the finding."""
            ...

        @property
        def rule_id(self) -> t.NonEmptyStr:
            """Exact ast-grep rule identifier."""
            ...

        @property
        def repository(self) -> t.NonEmptyStr:
            """Workspace repository owning the file."""
            ...

        @property
        def catalog_digest(self) -> str | None:
            """Authenticated native rule document digest."""
            ...

        @property
        def message(self) -> str | None:
            """Rule catalog message for the finding, when declared."""
            ...

        @property
        def module_absence(self) -> bool:
            """Occurrence anchored by native module absence predicate."""
            ...

        @property
        def file(self) -> Path:
            """Workspace-relative finding path."""
            ...

        @property
        def source_owner(self) -> Literal["authored", "generator"]:
            """Writable authority for the finding source."""
            ...

        @property
        def source_state(self) -> p.Cli.AtomicFileState | None:
            """Live source snapshot; evidence stores its input once."""
            ...

        @property
        def range(self) -> t.JsonMapping:
            """Exact ast-grep source range payload."""
            ...

        @property
        def text(self) -> str:
            """Exact matched source text."""
            ...

        @property
        def replacement(self) -> str | None:
            """Exact replacement when the rule provides one."""
            ...

        @property
        def actionable(self) -> bool:
            """Whether applying the rule changes source bytes."""
            ...

        @property
        def classification(self) -> c.Infra.ModScanFindingClass:
            """Rule mutability and byte-change classification."""
            ...

        @property
        def replacement_offsets(
            self,
        ) -> FlextInfraProtocolsScan.ModReplacementOffsets | None:
            """Native byte span for the proposed replacement."""
            ...

    @runtime_checkable
    class ModScanFinding(ModOccurrence, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def severity(self) -> Literal["error", "warning", "info", "hint"]:
            """Severity supplied by the native rule result."""
            ...

        @property
        def origin(
            self,
        ) -> Literal[
            c.Infra.ModFindingOrigin.AST_GREP, c.Infra.ModFindingOrigin.OWNED_PATH
        ]:
            """Syntax scan or owned inventory admission."""
            ...

        @property
        def native_record(self) -> FlextInfraProtocolsScan.ModNativeRecord:
            """Authenticated range and digest of the complete finding record."""
            ...

        @property
        def native_receipt(self) -> p.Cli.AtomicFileReceipt | None:
            """Shared native artifact; persisted by index."""
            ...

    @runtime_checkable
    class ModScanSourceContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        project_source_roots: Mapping[Path, Path] | None

        @property
        def inventory(self) -> Mapping[Path, p.Cli.AtomicFileState]:
            """Exact sources captured before the native scan."""
            ...

        repository_roots: tuple[Path, ...]

        @property
        def authenticated(
            self,
        ) -> Mapping[str, p.Result[tuple[Path, p.Cli.AtomicFileState]]]:
            """One authentication per file."""
            ...

        repositories: MutableMapping[Path, str]

    @runtime_checkable
    class ModScanFindingReference(ModScanFinding, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_path(self) -> Path | None:
            """Authenticated source input, or absent on source drift."""
            ...

        @property
        def native_artifact(self) -> int:
            """Complete native artifact index."""
            ...

    @runtime_checkable
    class ModScanCounts[FindingT: ModOccurrence](FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(self) -> tuple[FindingT, ...]:
            """Every validated ast-grep finding in stable order."""
            ...

        @property
        def findings(self) -> t.NonNegativeInt:
            """Complete native occurrence count, including source drift."""
            ...

        @property
        def actionable(self) -> t.NonNegativeInt:
            """Native occurrences whose admitted fix changes source bytes."""
            ...

        @property
        def detection_only(self) -> t.NonNegativeInt:
            """Native occurrences produced by rules without a fix."""
            ...

        @property
        def non_actionable_with_fix(self) -> t.NonNegativeInt:
            """Native occurrences whose declared fix leaves identical bytes."""
            ...

        @property
        def deferred(self) -> t.NonNegativeInt:
            """Structural member projected from the owning model.

            Drifted native occurrences retained as evidence, never admitted edits.
            """
            ...

    @runtime_checkable
    class ModOccurrenceReport[FindingT: ModOccurrence](
        ModScanCounts[FindingT], Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def files(self) -> frozenset[Path]:
            """Files containing findings."""
            ...

    @runtime_checkable
    class ModScanReport(ModOccurrenceReport[ModScanFinding], Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(self) -> tuple[FlextInfraProtocolsScan.ModScanFinding, ...]:
            """Every validated ast-grep finding in stable order."""
            ...

        @property
        def repository_root(self) -> Path | None:
            """Repository elected by the original native scan."""
            ...

        @property
        def source_files(self) -> tuple[Path, ...] | None:
            """Explicit original source selection, when supplied."""
            ...

        @property
        def rule_plan(
            self,
        ) -> FlextInfraProtocolsRefactorAstGrep.CodemodRulePlan | None:
            """Actual rule plan consumed by the native scan."""
            ...

        @property
        def catalog_states(self) -> tuple[p.Cli.AtomicFileState, ...] | None:
            """Original rule and configuration input snapshots."""
            ...

        @property
        def native_artifacts(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Complete authenticated native output inventory."""
            ...

    @runtime_checkable
    class ModModuleQuarantine(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Absolute source module the failure names."""
            ...

        @property
        def cause(self) -> str:
            """Original failure message of the planner."""
            ...

        @property
        def error_code(self) -> str | None:
            """Original failure code, when declared."""
            ...

    @runtime_checkable
    class ModQuarantineExclusion(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> str:
            """Phase whose complete contribution was dropped."""
            ...

        @property
        def modules(self) -> tuple[Path, ...]:
            """Quarantined modules the dropped change touched."""
            ...

        @property
        def paths(self) -> tuple[Path, ...]:
            """Every target of the dropped coherent change."""
            ...

    @runtime_checkable
    class ModPhaseAdvance(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def report(self) -> FlextInfraProtocolsScan.ModScanReport:
            """Scan of the post-iteration sources."""
            ...

        phase_states: tuple[tuple[tuple[str, str], ...], ...]
        drifted: tuple[Path, ...]

        @property
        def quarantined(self) -> FlextInfraProtocolsScan.ModModuleQuarantine | None:
            """Module whose attributed failure voided the plan."""
            ...

    @runtime_checkable
    class ModTextRule(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> t.NonEmptyStr:
            """Exact unique text-rule identifier."""
            ...

        @property
        def description(self) -> str:
            """Human-readable rewrite intent."""
            ...

        @property
        def include(self) -> Sequence[str]:
            """Fnmatch globs a target path must match."""
            ...

        @property
        def exclude(self) -> Sequence[str]:
            """Fnmatch globs a target path must not match."""
            ...

        @property
        def distributions(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Declared project distributions selected for this rule; empty selects
            all.
            """
            ...

        @property
        def find(self) -> t.NonEmptyStr:
            """Regex source pattern to locate."""
            ...

        @property
        def replace(self) -> str:
            """Expansion template replacing each match."""
            ...

        @property
        def flags(self) -> Sequence[str]:
            """Regex flag names from the SSOT map."""
            ...

        @property
        def capture_equals(self) -> Mapping[str, str]:
            """Named regex captures and their required exact values."""
            ...

        @property
        def expected(self) -> int | None:
            """Exact finding count the rule must produce when set."""
            ...

        @property
        def render(self) -> c.Infra.ModTextRender | None:
            """Declared renderer replacing each match instead."""
            ...

    @runtime_checkable
    class ModTextFinding(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> t.NonEmptyStr:
            """Exact text-rule identifier."""
            ...

        @property
        def file(self) -> Path:
            """Workspace-relative target path."""
            ...

        @property
        def line(self) -> t.NonNegativeInt:
            """One-based match line."""
            ...

        @property
        def text(self) -> str:
            """Exact matched source text."""
            ...

        @property
        def replacement(self) -> str:
            """Expanded replacement for the match."""
            ...

    @runtime_checkable
    class ModTextReport(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def findings(self) -> t.NonNegativeInt:
            """Complete finding count."""
            ...

        @property
        def actionable(self) -> t.NonNegativeInt:
            """Matches whose replacement differs from the text."""
            ...

        @property
        def files(self) -> frozenset[Path]:
            """Files containing findings."""
            ...

        @property
        def entries(self) -> tuple[FlextInfraProtocolsScan.ModTextFinding, ...]:
            """Every validated text finding in stable order."""
            ...

    @runtime_checkable
    class ModScanEvidence(ModScanCounts[ModScanFindingReference], Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(
            self,
        ) -> tuple[FlextInfraProtocolsScan.ModScanFindingReference, ...]:
            """Every validated ast-grep finding in stable order."""
            ...

        @property
        def schema_version(self) -> int:
            """Exact structured evidence schema."""
            ...

        @property
        def inputs(self) -> FlextInfraProtocolsCodemod.CodemodBindingSnapshot:
            """Single authenticated inventory for all occurrences."""
            ...

        @property
        def native_artifacts(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Structural member projected from the owning model.

            Durable native artifacts stored once for all occurrence references.
            """
            ...

        @property
        def command(self) -> c.Infra.ModScanCommand:
            """Public mod scan mode."""
            ...

        @property
        def root(self) -> Path:
            """Absolute scanned workspace root."""
            ...

        @property
        def scope(self) -> tuple[t.NonEmptyStr, ...]:
            """Exact ast-grep target scope."""
            ...

        @property
        def totals_by_class(
            self,
        ) -> Mapping[c.Infra.ModScanFindingClass, t.NonNegativeInt]:
            """Complete finding totals by mutability class."""
            ...

        @property
        def totals_by_repository(self) -> Mapping[str, t.NonNegativeInt]:
            """Complete finding totals by repository."""
            ...

        @property
        def totals_by_rule(self) -> Mapping[str, t.NonNegativeInt]:
            """Complete finding totals by rule identifier."""
            ...

    @runtime_checkable
    class ModScanEvidenceReceipt(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Published evidence destination."""
            ...

        @property
        def sha256(self) -> t.NonEmptyStr:
            """Published byte digest."""
            ...

        @property
        def evidence(self) -> FlextInfraProtocolsScan.ModScanEvidence:
            """Exact structured evidence that was published."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsScan",
]
