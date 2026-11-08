# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/refactor
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
)
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase, FlextInfraProtocolsMixins
from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenTransaction

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import (
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsRefactorAstGrep,
        FlextInfraProtocolsScan,
        FlextInfraProtocolsTransformers,
    )


class FlextInfraProtocolsRefactor:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class NamespaceRelocationRequest(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Selected owning project."""
            ...

        @property
        def findings(
            self,
        ) -> Sequence[
            tuple[c.Infra.CodemodRelocation, FlextInfraProtocolsScan.ModScanFinding]
        ]:
            """Native relocation selections."""
            ...

        @property
        def py_files(self) -> Sequence[Path]:
            """Selected Python sources."""
            ...

        @property
        def sources(self) -> Mapping[Path, str]:
            """Immutable input sources."""
            ...

    @runtime_checkable
    class NamespaceRelocationState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        working: MutableMapping[Path, str]

        originals: MutableMapping[Path, p.Cli.AtomicFileState]

        modes: MutableMapping[Path, int | None]

    @runtime_checkable
    class SemanticBehaviorOwners(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def modules(self) -> Mapping[str, tuple[str, bool]]:
            """Qualified source text and package identities."""
            ...

        @property
        def owners(self) -> Mapping[tuple[str, str], tuple[tuple[str, str], ...]]:
            """Utility class candidates by package and method."""
            ...

        @property
        def contextual(self) -> frozenset[tuple[str, str, str, str]]:
            """Methods requiring dispatch through their facade."""
            ...

    @runtime_checkable
    class SemanticBehaviorResolution(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        path: Path

        @property
        def inventory(self) -> FlextInfraProtocolsRefactor.SemanticBehaviorOwners:
            """Declared behavior owners."""
            ...

        typing_directory: str
        identities: frozenset[tuple[str, str]]
        lineages: MutableMapping[tuple[str, str], tuple[tuple[str, str], ...]]
        obsolete: MutableSet[tuple[str, str]]

    @runtime_checkable
    class ModTextCommand(FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class ModuleMoveCommand(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Owning repository root."""
            ...

        @property
        def source_file(self) -> Path:
            """Existing Python module."""
            ...

        @property
        def destination_directory(self) -> Path | None:
            """Existing destination package directory."""
            ...

        @property
        def destination_file(self) -> Path | None:
            """Exact Python file destination for joint semantic publication."""
            ...

    @runtime_checkable
    class RopeRenameOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def resources(self) -> Sequence[t.Infra.RopeResource]:
            """Resources included in the semantic rename scope."""
            ...

        in_hierarchy: bool
        docs: bool

    @runtime_checkable
    class SemanticRenameDecision(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declaration(self) -> FlextInfraProtocolsCensus.Object:
            """Actual introducing declaration from semantic discovery."""
            ...

        @property
        def replacement_name(self) -> t.NonEmptyStr:
            """Explicit canonical domain name."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Domain evidence supporting this name."""
            ...

        @property
        def contracts(self) -> tuple[FlextInfraProtocolsCensus.Object, ...]:
            """Observed independent typing declarations of this contract."""
            ...

    @runtime_checkable
    class SemanticRenameSelection(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def qualified_name(self) -> t.NonEmptyStr:
            """Introducing class, callable, or module identity."""
            ...

        @property
        def replacement_name(self) -> t.NonEmptyStr:
            """Canonical domain name."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Semantic justification."""
            ...

        @property
        def contracts(self) -> Sequence[str]:
            """Independent typing identities."""
            ...

    @runtime_checkable
    class SemanticRenameSelections(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def decisions(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.SemanticRenameSelection, ...]:
            """Explicit domain names for inventoried owners."""
            ...

        @property
        def consumer_roots(self) -> tuple[Path, ...]:
            """Explicit external consumer checkout roots for this run."""
            ...

    @runtime_checkable
    class SemanticRenamePlan(
        FlextInfraProtocolsCodegenTransaction.SemanticSourcePlan, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def decisions(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.SemanticRenameDecision, ...]:
            """Resolved declarations and their domain naming decisions."""
            ...

        @property
        def edits(
            self,
        ) -> tuple[FlextInfraProtocolsTransformers.SemanticMigrationEdit, ...]:
            """Exact source bytes before and after the native rename."""
            ...

        @property
        def moves(self) -> tuple[tuple[Path, Path], ...]:
            """Native module source and destination effects."""
            ...

    @runtime_checkable
    class RuleDeltaOptions(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inventory(self) -> tuple[tuple[str, str], ...]:
            """Declared repository and rule pairs included in the delta."""
            ...

        @property
        def repository_root(self) -> Path | None:
            """Root resolving text finding paths into the topology."""
            ...

        @property
        def projects(self) -> Sequence[Path]:
            """Declared project topology owning text findings."""
            ...

    @runtime_checkable
    class ViolationsTotals(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def findings(self) -> int:
            """Total mod scan findings."""
            ...

        @property
        def actionable(self) -> int:
            """Findings a mod rewrite would repair."""
            ...

        @property
        def detection_only(self) -> int:
            """Findings no rewrite repairs."""
            ...

        @property
        def non_actionable_with_fix(self) -> int:
            """Findings whose rewrite matches the current source."""
            ...

        @property
        def deferred(self) -> int:
            """Findings deferred because their source drifted."""
            ...

    @runtime_checkable
    class ViolationsRuleDelta(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> str:
            """Owning repository identity."""
            ...

        @property
        def rule_id(self) -> str:
            """Exact detector rule identity."""
            ...

        @property
        def engine(self) -> str:
            """Native detector owning this rule identity."""
            ...

        @property
        def before(self) -> t.NonNegativeInt:
            """Before occurrences."""
            ...

        @property
        def after(self) -> t.NonNegativeInt:
            """After occurrences."""
            ...

        @property
        def resolved(self) -> t.NonNegativeInt:
            """Removed occurrences."""
            ...

        @property
        def persisted(self) -> t.NonNegativeInt:
            """Unchanged occurrences."""
            ...

        @property
        def introduced(self) -> t.NonNegativeInt:
            """New occurrences."""
            ...

        @property
        def before_entries(self) -> tuple[t.NonNegativeInt, ...]:
            """Finding indexes in the before evidence snapshot."""
            ...

        @property
        def after_entries(self) -> tuple[t.NonNegativeInt, ...]:
            """Finding indexes in the after evidence snapshot."""
            ...

        @property
        def semantic_correspondence_proven(self) -> bool:
            """Text multiplicity does not prove semantic identity."""
            ...

    @runtime_checkable
    class ProjectEnforcementReport(
        FlextInfraProtocolsMixins.ProjectNameMixin, Protocol
    ):
        """Structural data contract projected from the owning model."""

        project_root: str

        @property
        def rule_deltas(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsRuleDelta, ...]:
            """Full catalog occurrence comparison, including zero rows."""
            ...

        relocation_resolved: t.NonNegativeInt
        relocation_persisted: t.NonNegativeInt
        relocation_introduced: t.NonNegativeInt
        relocation_findings: t.NonNegativeInt
        files_scanned: t.NonNegativeInt

        @property
        def before_rule_counts(self) -> Mapping[str, t.NonNegativeInt]:
            """Structural member projected from the owning model.

            Complete per-rule counts before relocation, including zero findings.
            """
            ...

        @property
        def after_rule_counts(self) -> Mapping[str, t.NonNegativeInt]:
            """Structural member projected from the owning model.

            Complete per-rule counts after relocation, including zero findings.
            """
            ...

        @property
        def cross_rule_delta(self) -> Mapping[str, int]:
            """Structural member projected from the owning model.

            Net changes; introduced occurrence counts remain in the shared rows.
            """
            ...

        @property
        def has_violations(self) -> bool:
            """Whether catalog findings remain or new occurrences appeared."""
            ...

    @runtime_checkable
    class WorkspaceEnforcementReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        workspace: t.NonEmptyStr

        @property
        def projects(
            self,
        ) -> Sequence[FlextInfraProtocolsRefactor.ProjectEnforcementReport]:
            """Per-project enforcement reports for the workspace."""
            ...

        @property
        def has_violations(self) -> bool:
            """Whether any project carries a violation."""
            ...

    @runtime_checkable
    class ViolationsSweepSources(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_verified(self) -> bool:
            """Atomic inputs reverified after native observations."""
            ...

        @property
        def plan(self) -> FlextInfraProtocolsRefactorAstGrep.CodemodRulePlan:
            """Elected full rule catalog and provider digests."""
            ...

        @property
        def scope(self) -> Sequence[str]:
            """Governed Python scan scope."""
            ...

        @property
        def states(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Scan authentication states; receipts retain byte digests."""
            ...

        @property
        def sha256(self) -> Mapping[str, str]:
            """Source and catalog byte digests."""
            ...

        @property
        def repository_roots(self) -> tuple[Path, ...]:
            """Observed governed project topology."""
            ...

        @property
        def ast_report(self) -> FlextInfraProtocolsScan.ModScanEvidence | None:
            """Complete normalized scan evidence, None if unobserved."""
            ...

        @property
        def text_report(self) -> FlextInfraProtocolsScan.ModTextReport | None:
            """Actual native text scan, None if unobserved."""
            ...

        @property
        def lint(
            self,
        ) -> (
            Mapping[str, t.Infra.LintSnapshot[FlextInfraProtocolsBase.LintGateResult]]
            | None
        ):
            """Canonical Ruff snapshots by source path."""
            ...

        @property
        def observation_errors(self) -> Sequence[str]:
            """Native observation failures, never empty success proof."""
            ...

    @runtime_checkable
    class ViolationsRuleEvaluation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> str:
            """Observed repository identity."""
            ...

        @property
        def rule_id(self) -> str:
            """Exact requested rule identity."""
            ...

        @property
        def engine(self) -> str:
            """Native detector owning this rule identity."""
            ...

        @property
        def catalog_digest(self) -> str | None:
            """Elected native rule document digest."""
            ...

        @property
        def provider(self) -> str | None:
            """Elected native rule provider."""
            ...

        @property
        def resource(self) -> Path | None:
            """Elected native rule document resource."""
            ...

        @property
        def detection_only(self) -> bool | None:
            """Native rule lacks an automated repair."""
            ...

        @property
        def status(
            self,
        ) -> Literal["observed", "not_applicable", "failed", "NOT_EXECUTED"]:
            """Native observation or explicit unavailable disposition."""
            ...

        @property
        def delta(self) -> FlextInfraProtocolsRefactor.ViolationsRuleDelta | None:
            """Occurrence evidence only for successful native scans."""
            ...

        @property
        def error(self) -> str | None:
            """Original observation failure."""
            ...

    @runtime_checkable
    class ViolationsEngineCoverage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> str:
            """Governed project identity."""
            ...

        @property
        def engine(self) -> str:
            """Actual native engine name."""
            ...

        @property
        def status(self) -> Literal["observed", "incomplete", "NOT_EXECUTED"]:
            """Complete rule audit or explicit unavailable evidence."""
            ...

        @property
        def cause(self) -> str | None:
            """Why complete native coverage is unavailable."""
            ...

    @runtime_checkable
    class ViolationsSweepStage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Operation's project root."""
            ...

        @property
        def cwd(self) -> Path:
            """Actual Make working directory."""
            ...

        @property
        def command(self) -> Sequence[str]:
            """Exact invoked Make argv."""
            ...

        @property
        def verb(self) -> str:
            """Canonical Make operation."""
            ...

        @property
        def duration(self) -> t.NonNegativeFloat:
            """Elapsed monotonic seconds."""
            ...

        @property
        def invoked(self) -> bool:
            """Whether Make was invoked."""
            ...

        @property
        def outcome(self) -> p.Cli.ProcessOutcome | None:
            """Original process exit, timeout and signal state."""
            ...

        @property
        def error(self) -> str | None:
            """Original operation or inspection failure."""
            ...

        @property
        def audit_before(
            self,
        ) -> FlextInfraProtocolsRefactor.ViolationsSweepSources | None:
            """Authenticated source snapshot immediately before audit."""
            ...

        @property
        def audit_after(
            self,
        ) -> FlextInfraProtocolsRefactor.ViolationsSweepSources | None:
            """After audit snapshot, retained for failed operations."""
            ...

        @property
        def source_inventory_unchanged(self) -> bool | None:
            """Source, inventory and plan equality; None is unproven."""
            ...

        @property
        def inspection_error(self) -> str | None:
            """Inspection failure independent of process error."""
            ...

        @property
        def rule_evaluations(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsRuleEvaluation, ...]:
            """Every rule's actual disposition in this repository."""
            ...

        @property
        def engine_coverage(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsEngineCoverage, ...]:
            """Native coverage, including engines without an audit."""
            ...

        @property
        def introduced_lint(
            self,
        ) -> Mapping[str, t.Infra.LintSnapshot[Sequence[str]]] | None:
            """Introduced Ruff occurrences, None if unobserved."""
            ...

        @property
        def introduced_text(
            self,
        ) -> tuple[FlextInfraProtocolsScan.ModTextFinding, ...] | None:
            """Introduced text occurrences, None if unobserved."""
            ...

    @runtime_checkable
    class ViolationsSweepScope(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def schema_version(self) -> int:
            """Report schema version."""
            ...

        @property
        def repository_root(self) -> Path:
            """Repository the sweep repaired and proved."""
            ...

        @property
        def repair_verbs(self) -> Sequence[str]:
            """Canonical verbs the sweep ran, in order."""
            ...

        @property
        def focused_rule_ids(self) -> Sequence[str]:
            """Requested focus; full catalog stays observed."""
            ...

        @property
        def repository_roots(self) -> tuple[Path, ...]:
            """Discovered governed project topology."""
            ...

        @property
        def stages(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsSweepStage, ...]:
            """Independent operation receipts in invocation order."""
            ...

    @runtime_checkable
    class ViolationsSweepReport(ViolationsSweepScope, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def before(self) -> FlextInfraProtocolsRefactor.ViolationsTotals | None:
            """Scan totals before the repair sequence."""
            ...

        @property
        def after(self) -> FlextInfraProtocolsRefactor.ViolationsTotals | None:
            """Scan totals after the repair sequence."""
            ...

        @property
        def rule_deltas(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsRuleDelta, ...]:
            """Occurrence-aware rule and repository comparisons."""
            ...

        @property
        def rule_evaluations(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsRuleEvaluation, ...]:
            """Final project and native rule coverage dispositions."""
            ...

        @property
        def engine_coverage(
            self,
        ) -> tuple[FlextInfraProtocolsRefactor.ViolationsEngineCoverage, ...]:
            """Complete native audits or explicit missing capabilities."""
            ...

        @property
        def completed_verbs(self) -> Sequence[str]:
            """Successfully completed repair verbs."""
            ...

        @property
        def failed_verb(self) -> str | None:
            """First failed repair verb."""
            ...

        @property
        def repair_error(self) -> str | None:
            """Original repair failure diagnostic."""
            ...

        @property
        def after_scan_error(self) -> str | None:
            """After scan failure diagnostic."""
            ...

        @property
        def before_scan_error(self) -> str | None:
            """Initial scan failure; native audits still observe members."""
            ...

        @property
        def before_evidence(
            self,
        ) -> FlextInfraProtocolsScan.ModScanEvidenceReceipt | None:
            """Invocation-local full before evidence and byte digest."""
            ...

        @property
        def after_evidence(
            self,
        ) -> FlextInfraProtocolsScan.ModScanEvidenceReceipt | None:
            """Invocation-local full after evidence and byte digest."""
            ...

        @property
        def before_plan(
            self,
        ) -> FlextInfraProtocolsRefactorAstGrep.CodemodRulePlan | None:
            """Before elected rules, providers, sources and digests."""
            ...

        @property
        def after_plan(
            self,
        ) -> FlextInfraProtocolsRefactorAstGrep.CodemodRulePlan | None:
            """After elected rules, providers, sources and digests."""
            ...

        @property
        def before_source_sha256(self) -> Mapping[str, str] | None:
            """Authenticated before source and catalog inventory."""
            ...

        @property
        def after_source_sha256(self) -> Mapping[str, str] | None:
            """Authenticated after inventory, or None when unobserved."""
            ...

        @property
        def increased_totals(self) -> Sequence[str]:
            """Names of the totals that increased, empty when none did."""
            ...

    @runtime_checkable
    class RefactorNamespaceEnforceInput(
        FlextInfraProtocolsMixins.WriteMixin,
        FlextInfraProtocolsMixins.ModuleSelectionMixin,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class CensusOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def consumer_roots(self) -> tuple[Path, ...]:
            """Explicit external consumer checkout roots for this census."""
            ...

        @property
        def source_plan_output(self) -> Path | None:
            """Destination for the same authenticated SemanticSourcePlan."""
            ...

        @property
        def json_output(self) -> str | None:
            """Path to write JSON report."""
            ...

        @property
        def impact_map_output(self) -> str | None:
            """Path to write impact map JSON."""
            ...

        @property
        def kinds(self) -> Sequence[str] | None:
            """Optional symbol-kind filters."""
            ...

        @property
        def census_kinds(self) -> Sequence[str] | None:
            """Optional extermination-kind filters."""
            ...

        @property
        def rules(self) -> Sequence[str] | None:
            """Optional violation-rule filters."""
            ...

        @property
        def families(self) -> Sequence[str] | None:
            """Optional namespace-family filters."""
            ...

        @property
        def include_local_scopes(self) -> bool:
            """Include locals, parameters and nested scopes."""
            ...

    @runtime_checkable
    class CensusInput(CensusOptions, FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check_only(self) -> bool:
            """Validate without writing."""
            ...

        @property
        def dry_run_mode(self) -> bool:
            """Inspect without writing."""
            ...

        @property
        def output_format(self) -> str:
            """Output format (json|text)."""
            ...

    @runtime_checkable
    class AccessorMigrationInput(
        FlextInfraProtocolsMixins.WriteMixin,
        FlextInfraProtocolsMixins.ModuleSelectionMixin,
        FlextInfraProtocolsMixins.NamespaceSelectionMixin,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def preview_limit(self) -> t.PositiveInt:
            """Maximum number of file previews to include in the report."""
            ...

    @runtime_checkable
    class Result(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path
        success: bool
        modified: bool
        error: str | None
        changes: Sequence[str]
        refactored_code: str | None

    @runtime_checkable
    class RefactorProjectInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        path: Path
        src_path: Path
        package_roots: MutableSet[str]

    @runtime_checkable
    class FileImportData(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        imported_modules: MutableSet[str]
        imported_symbols: MutableSet[str]

    @runtime_checkable
    class ProjectClassification(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_kind(self) -> t.NonEmptyStr:
            """Project kind (core, domain, platform, integration, app)."""
            ...

        @property
        def family_chains(self) -> Mapping[str, Sequence[str]]:
            """Family letter to FLEXT chain mapping."""
            ...

    @runtime_checkable
    class WrapperRewriteAccumulator(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        updates: MutableMapping[Path, str]
        expected_sources: MutableMapping[Path, str]
        changed_files: MutableSequence[str]
        total_replacements: int
        total_core_replacements: int
        import_rewrite_candidates: int
        per_project_changes: defaultdict[str, int]
        per_project_replacements: defaultdict[str, int]

    @runtime_checkable
    class ModRuleRoute(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def selector(self) -> t.NonEmptyStr:
            """Exact ``--rule`` selector."""
            ...

        @property
        def owner(self) -> Literal["ast", "text", "csv", "semantic", "callback"]:
            """Elected owner family."""
            ...

        @property
        def callback(self) -> str | None:
            """Selected callback owner when applicable."""
            ...

    @runtime_checkable
    class ModCommand(FlextInfraProtocolsMixins.ScopeMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> bool:
            """Validate without writing."""
            ...

        @property
        def dry_run_mode(self) -> bool:
            """Inspect without writing."""
            ...

        @property
        def rename_plan(self) -> Path | None:
            """Authenticated semantic rename artifact to consume."""
            ...

        @property
        def consumer_roots(self) -> tuple[Path, ...]:
            """Explicit external consumer checkout roots for this run."""
            ...

        @property
        def rule_id(self) -> t.NonEmptyStr | None:
            """One exact concrete codemod rule ID."""
            ...

        @property
        def rule_ids(self) -> tuple[t.NonEmptyStr, ...] | None:
            """Exact ast-grep catalog rule IDs; repeat for each selection."""
            ...

        @property
        def laws(self) -> tuple[t.Infra.EnforcementId, ...] | None:
            """Theme law ids (ENFORCE-NNN); repeat --laws for each law."""
            ...

        @property
        def apply(self) -> bool:
            """Whether this invocation writes: neither check nor dry-run."""
            ...

    @runtime_checkable
    class SemanticRenamePlanCommand(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Complete governed workspace."""
            ...

        @property
        def decisions(self) -> t.NonEmptyStr:
            """SemanticRenameSelections JSON."""
            ...

        @property
        def output(self) -> Path:
            """Workspace-contained plan artifact destination."""
            ...

    @runtime_checkable
    class SemanticRenamePreviewCommand(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Complete governed workspace."""
            ...

        @property
        def plan(self) -> Path:
            """Authenticated semantic rename artifact."""
            ...

    @runtime_checkable
    class ApplyRenamesInput(FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rename_definitions(self) -> bool:
            """Atomically rename owned declarations and references."""
            ...

        @property
        def csv(self) -> t.NonEmptyStr:
            """Path to the old,new rename-list CSV."""
            ...

        @property
        def roots(self) -> Sequence[str]:
            """Directories to scan for rename targets."""
            ...

        @property
        def bindings(self) -> Mapping[str, Sequence[str]]:
            """Structural member projected from the owning model.

            CSV expression prefixes mapped to current public Rope owner identities.
            """
            ...

        @property
        def text_globs(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Explicit root-relative non-Python documentation and configuration text
            surfaces.
            """
            ...

        @property
        def python_documentation(self) -> bool:
            """Structural member projected from the owning model.

            Rename comments and actual Python docstrings, preserving executable
            string payloads.
            """
            ...

        @property
        def exclude_globs(self) -> Sequence[str]:
            """Declared generated projections excluded from campaign targets."""
            ...

    @runtime_checkable
    class ApplyRenamesReport(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def preview_diff(self) -> str:
            """Unified diff from authenticated planned source bytes."""
            ...

        @property
        def label(self) -> t.NonEmptyStr:
            """Rename-list label."""
            ...

        @property
        def files_scanned(self) -> t.NonNegativeInt:
            """Text files scanned."""
            ...

        @property
        def occurrences(self) -> t.NonNegativeInt:
            """Pending authenticated source edit spans from the current scan."""
            ...

        @property
        def files_changed(self) -> t.NonNegativeInt:
            """Files rewritten in apply mode."""
            ...

        @property
        def applied(self) -> bool:
            """Whether changes were applied."""
            ...

        @property
        def published_states(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Authenticated states of the acknowledged published paths."""
            ...

    @runtime_checkable
    class ParsedPythonModule(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> str:
            """Raw source text."""
            ...

        @property
        def tree(self) -> t.Infra.RopePyModule:
            """Parsed PyObject module representation."""
            ...

    @runtime_checkable
    class ImportLawScope(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Governed project root."""
            ...

        @property
        def file_path(self) -> Path:
            """Normalized module path."""
            ...

        @property
        def namespace_dir(self) -> Path:
            """Directory of the namespace owning the module."""
            ...

        @property
        def module(self) -> str:
            """Dotted name of the module."""
            ...

        @property
        def layer(self) -> int:
            """Module's import-layer rank."""
            ...

        @property
        def own_exports(self) -> frozenset[str]:
            """Names the module declares in its own __all__."""
            ...

        @property
        def facade_dependencies(self) -> frozenset[str]:
            """Facade aliases whose runtime providers depend on this module."""
            ...

        @property
        def family_letter(self) -> str | None:
            """Structural member projected from the owning model.

            Facade letter of the family package holding the module, or None outside
            every family package.
            """
            ...

        @property
        def direct_imports(self) -> bool:
            """Structural member projected from the owning model.

            Whether the module keeps direct leaf imports: a settings/config module
            or a family base.py, which must never route through the namespace root
            or a lazy package.
            """
            ...

        @property
        def bootstrap_dependency(self) -> bool:
            """Whether the captured root graph bootstraps this module."""
            ...

        @property
        def namespace(self) -> str:
            """Structural member projected from the owning model.

            Qualified publishing package derived from the explicit module facts.
            """
            ...

    @runtime_checkable
    class ImportLawPass(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope(self) -> FlextInfraProtocolsRefactor.ImportLawScope:
            """Module facts of the pass."""
            ...

        @property
        def tree(self) -> ast.Module:
            """Parsed module."""
            ...

        @property
        def parents(self) -> Mapping[int, ast.AST]:
            """Child node id to parent node map."""
            ...

        @property
        def bindings(self) -> Mapping[str, ast.stmt]:
            """Module-level statement binding each top name."""
            ...

        @property
        def root_exports(self) -> Mapping[str, str]:
            """Names the namespace root publishes lazily."""
            ...

        @property
        def sources(self) -> Mapping[Path, str] | None:
            """Captured sources used by this normalization pass."""
            ...

        @property
        def source_project(self) -> t.Infra.RopeProject | None:
            """Native source view owning this pass."""
            ...

        @property
        def deferred_class_lines(self) -> frozenset[int]:
            """Class declarations with proven ordinary construction."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsRefactor",
]
