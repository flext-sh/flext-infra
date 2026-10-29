"""Domain models for the refactor subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
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
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import (
    FlextInfraModelsBase,
    FlextInfraModelsCensus,
    FlextInfraModelsMixins,
    FlextInfraModelsNamespaceEnforcer,
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsScan,
    FlextInfraModelsTransformers,
)
from flext_infra._models._codegen import FlextInfraModelsCodegenTransaction


class FlextInfraModelsRefactor(
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsNamespaceEnforcer,
):
    """Models for refactor workflows and related tools.

    Canonical base policy:
    - ``ContractModel`` for configuration/policy contracts.
    - ``ArbitraryTypesModel`` for mutable report/result payloads.
    """

    class NamespaceRelocationRequest(FlextInfraModelsBase.FrozenArbitrary):
        """Selected source view and authenticated inputs for native relocation."""

        project_root: Path = m.Field(description="Selected owning project")
        findings: Sequence[
            tuple[c.Infra.CodemodRelocation, FlextInfraModelsScan.ModScanFinding]
        ] = m.Field(description="Native relocation selections")
        py_files: Sequence[Path] = m.Field(description="Selected Python sources")
        sources: Mapping[Path, str] = m.Field(description="Immutable input sources")

    class NamespaceRelocationState(m.ArbitraryTypesModel):
        """Mutable candidate bytes with the original states they replace."""

        working: MutableMapping[Path, str] = m.Field(
            description="Candidate sources changed only by native planning effects"
        )
        originals: MutableMapping[Path, m.Cli.AtomicFileState] = m.Field(
            description="Complete original dependency closure"
        )
        modes: MutableMapping[Path, int | None] = m.Field(
            description="Authenticated file modes preserved by publication"
        )

    class SemanticBehaviorOwners(m.ImmutableValueModel):
        """Declared modules and unique owners used for behavior relocation."""

        modules: Annotated[
            Mapping[str, tuple[str, bool]],
            m.Field(description="Qualified source text and package identities"),
        ]
        owners: Annotated[
            Mapping[
                tuple[str, str],
                tuple[tuple[str, str], ...],
            ],
            m.Field(description="Utility class candidates by package and method"),
        ]
        contextual: Annotated[
            frozenset[tuple[str, str, str, str]],
            m.Field(description="Methods requiring dispatch through their facade"),
        ]

    class SemanticBehaviorResolution(m.ArbitraryTypesModel):
        """One consumer's mutable relocation state over immutable owner facts."""

        path: Annotated[Path, m.Field(description="Consumer source identity")]
        inventory: Annotated[
            FlextInfraModelsRefactor.SemanticBehaviorOwners,
            m.Field(description="Declared behavior owners"),
        ]
        typing_directory: Annotated[
            str, m.Field(description="Canonical typing family directory")
        ]
        identities: Annotated[
            frozenset[tuple[str, str]],
            m.Field(description="Imported module and receiver identities"),
        ]
        lineages: Annotated[
            MutableMapping[tuple[str, str], tuple[tuple[str, str], ...]],
            m.Field(description="Consumer-local ancestry cache"),
        ]
        obsolete: Annotated[
            MutableSet[tuple[str, str]],
            m.Field(description="Imports superseded by canonical owner references"),
        ]

    class ModTextCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """Repository-scoped request for authenticated Sed rule replay."""

    class ModuleMoveCommand(m.ContractModel):
        """Move a declared source module and its semantic import references."""

        repository_root: Annotated[Path, m.Field(description="Owning repository root")]
        source_file: Annotated[Path, m.Field(description="Existing Python module")]
        destination_directory: Annotated[
            Path | None,
            m.Field(description="Existing destination package directory"),
        ] = None
        destination_file: Annotated[
            Path | None,
            m.Field(
                description=(
                    "Exact Python file destination for joint semantic publication"
                )
            ),
        ] = None

        @m.model_validator(mode="after")
        def exclusive_destination(self) -> Self:
            """Require one explicit destination without inferring an execution mode.

            Returns:
                The validated module relocation facts.

            Raises:
                ValueError: If neither or both destination forms are supplied.

            """
            if (self.destination_directory is None) == (self.destination_file is None):
                msg = (
                    "module move requires exactly one destination_directory "
                    "or destination_file"
                )
                raise ValueError(msg)
            return self

    class RopeRenameOptions(m.ArbitraryTypesModel):
        """Declared search scope and hierarchy policy for one semantic rename."""

        resources: Annotated[
            Sequence[t.Port[t.Infra.RopeResource]],
            m.Field(description="Resources included in the semantic rename scope"),
        ]
        in_hierarchy: Annotated[
            bool,
            m.Field(description="Whether the rename includes inherited declarations"),
        ] = False
        docs: Annotated[
            bool,
            m.Field(
                description=(
                    "Include native identity-visible string and comment occurrences"
                ),
            ),
        ] = False

    class SemanticRenameDecision(m.ImmutableValueModel):
        """Domain-selected name for an observed introducing declaration."""

        declaration: Annotated[
            FlextInfraModelsCensus.Object,
            m.Field(
                description="Actual introducing declaration from semantic discovery"
            ),
        ]
        replacement_name: Annotated[
            t.NonEmptyStr, m.Field(description="Explicit canonical domain name")
        ]
        reason: Annotated[
            t.NonEmptyStr, m.Field(description="Domain evidence supporting this name")
        ]
        contracts: Annotated[
            tuple[FlextInfraModelsCensus.Object, ...],
            m.Field(
                description="Observed independent typing declarations of this contract"
            ),
        ] = ()

    class SemanticRenameSelection(m.ImmutableValueModel):
        """Explicit domain naming intent, resolved by the actual object inventory."""

        qualified_name: t.NonEmptyStr = m.Field(
            description="Introducing class, callable, or module identity"
        )
        replacement_name: t.NonEmptyStr = m.Field(description="Canonical domain name")
        reason: t.NonEmptyStr = m.Field(description="Semantic justification")
        contracts: Sequence[str] = m.Field(
            default=(), description="Independent typing identities"
        )

    class SemanticRenameSelections(m.ImmutableValueModel):
        """JSON input carrying explicit decisions, not a lexical naming policy."""

        decisions: tuple[FlextInfraModelsRefactor.SemanticRenameSelection, ...] = (
            m.Field(description="Explicit domain names for inventoried owners")
        )
        consumer_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Explicit external consumer checkout roots for this run",
        )

    class SemanticRenamePlan(FlextInfraModelsCodegenTransaction.SemanticSourcePlan):
        """Reversible native rename artifact with its complete authenticated closure."""

        decisions: tuple[FlextInfraModelsRefactor.SemanticRenameDecision, ...] = (
            m.Field(
                min_length=1,
                description="Resolved declarations and their domain naming decisions",
            )
        )
        edits: tuple[FlextInfraModelsTransformers.SemanticMigrationEdit, ...] = m.Field(
            description="Exact source bytes before and after the native rename"
        )
        moves: tuple[tuple[Path, Path], ...] = m.Field(
            default=(), description="Native module source and destination effects"
        )

    class RuleDeltaOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Optional scope and authentication inputs for one rule delta comparison."""

        inventory: tuple[tuple[str, str], ...] = m.Field(
            default=(),
            description="Declared repository and rule pairs included in the delta.",
        )
        repository_root: Path | None = m.Field(
            default=None,
            description="Root resolving text finding paths into the topology.",
        )
        projects: Sequence[Path] = m.Field(
            default=(),
            description="Declared project topology owning text findings.",
        )

    class ViolationsTotals(m.ContractModel):
        """One mod scan's violation totals as the sweep compares them."""

        findings: Annotated[
            int,
            m.Field(description="Total mod scan findings"),
        ]
        actionable: Annotated[
            int,
            m.Field(description="Findings a mod rewrite would repair"),
        ]
        detection_only: Annotated[
            int,
            m.Field(description="Findings no rewrite repairs"),
        ]
        non_actionable_with_fix: Annotated[
            int,
            m.Field(description="Findings whose rewrite matches the current source"),
        ]
        deferred: Annotated[
            int,
            m.Field(description="Findings deferred because their source drifted"),
        ] = 0

    class ViolationsRuleDelta(m.ContractModel):
        """Occurrence counts for one repository and exact rule identity."""

        repository: Annotated[str, m.Field(description="Owning repository identity")]
        rule_id: Annotated[str, m.Field(description="Exact detector rule identity")]
        engine: Annotated[
            str, m.Field(description="Native detector owning this rule identity")
        ] = "ast-grep"
        before: Annotated[t.NonNegativeInt, m.Field(description="Before occurrences")]
        after: Annotated[t.NonNegativeInt, m.Field(description="After occurrences")]
        resolved: Annotated[
            t.NonNegativeInt, m.Field(description="Removed occurrences")
        ]
        persisted: Annotated[
            t.NonNegativeInt, m.Field(description="Unchanged occurrences")
        ]
        introduced: Annotated[t.NonNegativeInt, m.Field(description="New occurrences")]
        before_entries: Annotated[
            tuple[t.NonNegativeInt, ...],
            m.Field(description="Finding indexes in the before evidence snapshot"),
        ] = ()
        after_entries: Annotated[
            tuple[t.NonNegativeInt, ...],
            m.Field(description="Finding indexes in the after evidence snapshot"),
        ] = ()
        semantic_correspondence_proven: Annotated[
            bool,
            m.Field(description="Text multiplicity does not prove semantic identity"),
        ] = False

    class ProjectEnforcementReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Full rule-catalog comparison, separate from scoped relocation progress."""

        project_root: Annotated[str, m.Field(description="Project root path")]
        rule_deltas: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsRuleDelta, ...],
            m.Field(
                description="Full catalog occurrence comparison, including zero rows"
            ),
        ]
        relocation_resolved: Annotated[
            t.NonNegativeInt,
            m.Field(description="Removed scoped relocation occurrences"),
        ]
        relocation_persisted: Annotated[
            t.NonNegativeInt,
            m.Field(description="Unchanged scoped relocation occurrences"),
        ]
        relocation_introduced: Annotated[
            t.NonNegativeInt, m.Field(description="New scoped relocation occurrences")
        ]
        relocation_findings: Annotated[
            t.NonNegativeInt,
            m.Field(description="Scoped relocation findings remaining after the pass"),
        ]
        files_scanned: Annotated[
            t.NonNegativeInt,
            m.Field(description="Files in the namespace relocation scope before apply"),
        ]

        @m.computed_field
        @property
        def before_rule_counts(self) -> Mapping[str, t.NonNegativeInt]:
            """Complete per-rule counts before relocation, including zero findings."""
            return {row.rule_id: row.before for row in self.rule_deltas}

        @m.computed_field
        @property
        def after_rule_counts(self) -> Mapping[str, t.NonNegativeInt]:
            """Complete per-rule counts after relocation, including zero findings."""
            return {row.rule_id: row.after for row in self.rule_deltas}

        @m.computed_field
        @property
        def cross_rule_delta(self) -> Mapping[str, int]:
            """Net changes; introduced occurrence counts remain in the shared rows."""
            return {row.rule_id: row.after - row.before for row in self.rule_deltas}

        @m.computed_field
        @property
        def has_violations(self) -> bool:
            """Whether catalog findings remain or new occurrences appeared."""
            return any(row.after or row.introduced for row in self.rule_deltas)

    class WorkspaceEnforcementReport(m.ArbitraryTypesModel):
        """Workspace enforcement report."""

        workspace: Annotated[t.NonEmptyStr, m.Field(description="Repository root path")]
        projects: Annotated[
            Sequence[FlextInfraModelsRefactor.ProjectEnforcementReport],
            m.Field(description="Per-project enforcement reports for the workspace"),
        ] = m.Field(default_factory=tuple)

        @m.computed_field
        @property
        def has_violations(self) -> bool:
            """Whether any project carries a violation."""
            return any(project.has_violations for project in self.projects)

    class ViolationsSweepSources(m.ContractModel):
        """Authenticated inventory shared by full scans and audit observations."""

        source_verified: Annotated[
            bool,
            m.Field(description="Atomic inputs reverified after native observations"),
        ] = False

        plan: Annotated[
            FlextInfraModelsRefactorGrep.CodemodRulePlan,
            m.Field(description="Elected full rule catalog and provider digests"),
        ]
        scope: Annotated[
            Sequence[str], m.Field(description="Governed Python scan scope")
        ]
        states: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Scan authentication states; receipts retain byte digests",
            ),
        ] = ()
        sha256: Annotated[
            Mapping[str, str], m.Field(description="Source and catalog byte digests")
        ]
        repository_roots: Annotated[
            tuple[Path, ...],
            m.Field(description="Observed governed project topology"),
        ]
        ast_report: Annotated[
            FlextInfraModelsScan.ModScanEvidence | None,
            m.Field(
                description="Complete normalized scan evidence, None if unobserved"
            ),
        ] = None
        text_report: Annotated[
            FlextInfraModelsScan.ModTextReport | None,
            m.Field(description="Actual native text scan, None if unobserved"),
        ] = None
        lint: Annotated[
            Mapping[str, t.Infra.LintSnapshot[FlextInfraModelsBase.LintGateResult]]
            | None,
            m.Field(description="Canonical Ruff snapshots by source path"),
        ] = None
        observation_errors: Annotated[
            Sequence[str],
            m.Field(
                description="Native observation failures, never empty success proof"
            ),
        ] = ()

    class ViolationsRuleEvaluation(m.ContractModel):
        """Actual elected rule disposition, without inventing counts on failure."""

        repository: Annotated[str, m.Field(description="Observed repository identity")]
        rule_id: Annotated[str, m.Field(description="Exact requested rule identity")]
        engine: Annotated[
            str, m.Field(description="Native detector owning this rule identity")
        ] = "ast-grep"
        catalog_digest: Annotated[
            str | None, m.Field(description="Elected native rule document digest")
        ] = None
        provider: Annotated[
            str | None, m.Field(description="Elected native rule provider")
        ] = None
        resource: Annotated[
            Path | None, m.Field(description="Elected native rule document resource")
        ] = None
        detection_only: Annotated[
            bool | None, m.Field(description="Native rule lacks an automated repair")
        ] = None
        status: Annotated[
            Literal["observed", "not_applicable", "failed", "NOT_EXECUTED"],
            m.Field(
                description="Native observation or explicit unavailable disposition"
            ),
        ]
        delta: Annotated[
            FlextInfraModelsRefactor.ViolationsRuleDelta | None,
            m.Field(description="Occurrence evidence only for successful native scans"),
        ]
        error: Annotated[
            str | None, m.Field(description="Original observation failure")
        ]

    class ViolationsEngineCoverage(m.ContractModel):
        """Engine-level completeness without inventing native rule identities."""

        repository: Annotated[str, m.Field(description="Governed project identity")]
        engine: Annotated[str, m.Field(description="Actual native engine name")]
        status: Annotated[
            Literal["observed", "incomplete", "NOT_EXECUTED"],
            m.Field(description="Complete rule audit or explicit unavailable evidence"),
        ]
        cause: Annotated[
            str | None,
            m.Field(description="Why complete native coverage is unavailable"),
        ]

    class ViolationsSweepStage(m.ContractModel):
        """One invoked canonical operation, including independent audit evidence."""

        repository_root: Annotated[
            Path, m.Field(description="Operation's project root")
        ]
        cwd: Annotated[Path, m.Field(description="Actual Make working directory")]
        command: Annotated[
            Sequence[str], m.Field(description="Exact invoked Make argv")
        ]
        verb: Annotated[str, m.Field(description="Canonical Make operation")]
        duration: Annotated[
            t.NonNegativeFloat,
            m.Field(description="Elapsed monotonic seconds"),
        ]
        invoked: Annotated[
            bool,
            m.Field(description="Whether Make was invoked"),
        ] = True
        outcome: Annotated[
            m.Cli.ProcessOutcome | None,
            m.Field(description="Original process exit, timeout and signal state"),
        ]
        error: Annotated[
            str | None,
            m.Field(description="Original operation or inspection failure"),
        ]
        audit_before: Annotated[
            FlextInfraModelsRefactor.ViolationsSweepSources | None,
            m.Field(
                description="Authenticated source snapshot immediately before audit"
            ),
        ] = None
        audit_after: Annotated[
            FlextInfraModelsRefactor.ViolationsSweepSources | None,
            m.Field(description="After audit snapshot, retained for failed operations"),
        ] = None
        source_inventory_unchanged: Annotated[
            bool | None,
            m.Field(
                description="Source, inventory and plan equality; None is unproven"
            ),
        ] = None
        inspection_error: Annotated[
            str | None,
            m.Field(description="Inspection failure independent of process error"),
        ] = None
        rule_evaluations: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsRuleEvaluation, ...],
            m.Field(description="Every rule's actual disposition in this repository"),
        ] = ()
        engine_coverage: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsEngineCoverage, ...],
            m.Field(description="Native coverage, including engines without an audit"),
        ] = ()
        introduced_lint: Annotated[
            Mapping[str, t.Infra.LintSnapshot[Sequence[str]]] | None,
            m.Field(description="Introduced Ruff occurrences, None if unobserved"),
        ] = None
        introduced_text: Annotated[
            tuple[FlextInfraModelsScan.ModTextFinding, ...] | None,
            m.Field(description="Introduced text occurrences, None if unobserved"),
        ] = None

    class ViolationsSweepReport(m.ContractModel):
        """Before/after receipt of one violations sweep.

        Published for successful and partial failed repair sequences.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        schema_version: Annotated[
            int,
            m.Field(description="Report schema version"),
        ]
        repository_root: Annotated[
            Path,
            m.Field(description="Repository the sweep repaired and proved"),
        ]
        repair_verbs: Annotated[
            Sequence[str],
            m.Field(description="Canonical verbs the sweep ran, in order"),
        ]
        focused_rule_ids: Annotated[
            Sequence[str],
            m.Field(description="Requested focus; full catalog stays observed"),
        ] = ()
        repository_roots: Annotated[
            tuple[Path, ...],
            m.Field(description="Discovered governed project topology"),
        ] = ()
        stages: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsSweepStage, ...],
            m.Field(description="Independent operation receipts in invocation order"),
        ] = ()
        before: Annotated[
            FlextInfraModelsRefactor.ViolationsTotals | None,
            m.Field(description="Scan totals before the repair sequence"),
        ]
        after: Annotated[
            FlextInfraModelsRefactor.ViolationsTotals | None,
            m.Field(description="Scan totals after the repair sequence"),
        ]
        rule_deltas: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsRuleDelta, ...],
            m.Field(description="Occurrence-aware rule and repository comparisons"),
        ] = ()
        rule_evaluations: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsRuleEvaluation, ...],
            m.Field(description="Final project and native rule coverage dispositions"),
        ] = ()
        engine_coverage: Annotated[
            tuple[FlextInfraModelsRefactor.ViolationsEngineCoverage, ...],
            m.Field(
                description="Complete native audits or explicit missing capabilities"
            ),
        ] = ()
        completed_verbs: Annotated[
            Sequence[str], m.Field(description="Successfully completed repair verbs")
        ] = ()
        failed_verb: Annotated[
            str | None, m.Field(description="First failed repair verb")
        ] = None
        repair_error: Annotated[
            str | None, m.Field(description="Original repair failure diagnostic")
        ] = None
        after_scan_error: Annotated[
            str | None, m.Field(description="After scan failure diagnostic")
        ] = None
        before_scan_error: Annotated[
            str | None,
            m.Field(
                description="Initial scan failure; native audits still observe members"
            ),
        ] = None
        before_evidence: Annotated[
            FlextInfraModelsScan.ModScanEvidenceReceipt | None,
            m.Field(
                description="Invocation-local full before evidence and byte digest"
            ),
        ] = None
        after_evidence: Annotated[
            FlextInfraModelsScan.ModScanEvidenceReceipt | None,
            m.Field(description="Invocation-local full after evidence and byte digest"),
        ] = None
        before_plan: Annotated[
            FlextInfraModelsRefactorGrep.CodemodRulePlan | None,
            m.Field(description="Before elected rules, providers, sources and digests"),
        ] = None
        after_plan: Annotated[
            FlextInfraModelsRefactorGrep.CodemodRulePlan | None,
            m.Field(description="After elected rules, providers, sources and digests"),
        ] = None
        before_source_sha256: Annotated[
            Mapping[str, str] | None,
            m.Field(description="Authenticated before source and catalog inventory"),
        ] = m.Field()
        after_source_sha256: Annotated[
            Mapping[str, str] | None,
            m.Field(
                description="Authenticated after inventory, or None when unobserved"
            ),
        ] = m.Field()

        @property
        def increased_totals(self) -> Sequence[str]:
            """Names of the totals that increased, empty when none did.

            Returns:
                The resulting ``Sequence[str]``.

            Raises:
                ValueError: The after scan or its source inventory is unobserved.

            """
            if (
                self.before is None
                or self.before_source_sha256 is None
                or self.after is None
                or self.after_source_sha256 is None
            ):
                msg = "violations sweep comparison requires an authenticated after scan"
                raise ValueError(msg)
            return tuple(
                name
                for name in (
                    "findings",
                    "actionable",
                    "detection_only",
                    "non_actionable_with_fix",
                )
                if getattr(self.after, name) > getattr(self.before, name)
            )

    class RefactorNamespaceEnforceInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextInfraModelsMixins.ModuleSelectionMixin,
        m.ContractModel,
    ):
        """CLI/service request for namespace enforcement."""

    class CensusOptions(m.ContractModel):
        """Declared census filters and report destinations."""

        consumer_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Explicit external consumer checkout roots for this census",
        )
        source_plan_output: Path | None = m.Field(
            default=None,
            description="Destination for the same authenticated SemanticSourcePlan",
        )
        json_output: Annotated[
            str | None, m.Field(description="Path to write JSON report")
        ] = None
        impact_map_output: Annotated[
            str | None, m.Field(description="Path to write impact map JSON")
        ] = None
        kinds: Annotated[
            Sequence[str] | None, m.Field(description="Optional symbol-kind filters")
        ] = None
        rules: Annotated[
            Sequence[str] | None, m.Field(description="Optional violation-rule filters")
        ] = None
        families: Annotated[
            Sequence[str] | None,
            m.Field(description="Optional namespace-family filters"),
        ] = None
        include_local_scopes: Annotated[
            bool, m.Field(description="Include locals, parameters and nested scopes")
        ] = True

    class CensusInput(
        CensusOptions,
        FlextInfraModelsMixins.WriteMixin,
    ):
        """Public census request separated from injected execution capabilities."""

        check_only: Annotated[
            bool, m.Field(alias="check", description="Validate without writing")
        ] = False
        dry_run_mode: Annotated[
            bool, m.Field(alias="dry-run", description="Inspect without writing")
        ] = False
        output_format: Annotated[
            str, m.Field(description="Output format (json|text)")
        ] = "text"

    class AccessorMigrationInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextInfraModelsMixins.ModuleSelectionMixin,
        FlextInfraModelsMixins.NamespaceSelectionMixin,
        m.ContractModel,
    ):
        """CLI/service request for accessor migration dry-runs and applies."""

        preview_limit: Annotated[
            t.PositiveInt,
            m.Field(
                alias="preview-limit",
                description="Maximum number of file previews to include in the report",
            ),
        ] = 10

    class Result(m.ArbitraryTypesModel):
        """Result of applying refactor rules to a single file."""

        file_path: Annotated[Path, m.Field(description="Target file path")]
        success: Annotated[bool, m.Field(description="Whether the operation succeeded")]
        modified: Annotated[
            bool,
            m.Field(description="Whether the file was actually modified"),
        ]
        error: Annotated[
            str | None,
            m.Field(description="Error message on failure"),
        ] = None
        changes: Annotated[
            Sequence[str],
            m.Field(description="Human-readable change descriptions"),
        ] = m.Field(default_factory=tuple)
        refactored_code: Annotated[
            str | None,
            m.Field(description="Resulting source code after transformation"),
        ] = None

    class RefactorProjectInfo(m.ArbitraryTypesModel):
        """Project metadata with mutable package-root set.

        Enforcement exemption: ``package_roots`` is a ``set[str]``
        accumulator populated during scanning.
        """

        name: Annotated[t.NonEmptyStr, m.Field(description="Project directory name")]
        path: Annotated[Path, m.Field(description="Absolute project path")]
        src_path: Annotated[Path, m.Field(description="Absolute src/ path")]
        package_roots: Annotated[
            MutableSet[str],
            m.Field(description="Top-level Python package roots in src/"),
        ] = m.Field(default_factory=set[str])

    class FileImportData(m.ArbitraryTypesModel):
        """File-level import data with mutable set accumulators.

        Enforcement exemption: ``imported_modules``/``imported_symbols``
        accumulate during a scan; keep ``set[str]`` as the declared type.
        """

        imported_modules: Annotated[
            MutableSet[str],
            m.Field(description="Imported module roots"),
        ] = m.Field(default_factory=set[str])
        imported_symbols: Annotated[
            MutableSet[str],
            m.Field(description="Imported symbol names"),
        ] = m.Field(default_factory=set[str])

    class ProjectClassification(FlextInfraModelsBase.FrozenArbitrary):
        """Result of classifying a project by kind and family chains."""

        project_kind: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Project kind (core, domain, platform, integration, app)",
            ),
        ]
        family_chains: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(description="Family letter to FLEXT chain mapping"),
        ]

    # NOTE (multi-agent): the model below replaces the dataclass payload that
    # lived in refactor/_wrapper_rewrite.py (deep-FLEXT: models only in m).
    class WrapperRewriteAccumulator(m.ArbitraryTypesModel):
        """Aggregates per-file rewrite stats across the wrapper-root verb run.

        Mutable accumulator (never frozen): every field is appended to or
        incremented while the run scans candidate files.
        """

        updates: Annotated[
            MutableMapping[Path, str],
            m.Field(description="Pending file content updates keyed by path"),
        ] = m.Field(default_factory=dict[Path, str])
        expected_sources: Annotated[
            MutableMapping[Path, str],
            m.Field(description="Original content keyed by every pending update path"),
        ] = m.Field(default_factory=dict[Path, str])
        changed_files: Annotated[
            MutableSequence[str],
            m.Field(description="String paths of files changed by the run"),
        ] = m.Field(default_factory=list[str])
        total_replacements: Annotated[
            int,
            m.Field(description="Total replacements applied across the run"),
        ] = 0
        total_core_replacements: Annotated[
            int,
            m.Field(description="Total Core.Tests chain rewrites applied"),
        ] = 0
        import_rewrite_candidates: Annotated[
            int,
            m.Field(description="Count of wrapper import rewrite candidates"),
        ] = 0
        per_project_changes: Annotated[
            defaultdict[str, int],
            m.Field(description="Changed file count keyed by project name"),
        ] = m.Field(default_factory=lambda: defaultdict[str, int](int))
        per_project_replacements: Annotated[
            defaultdict[str, int],
            m.Field(description="Replacement count keyed by project name"),
        ] = m.Field(default_factory=lambda: defaultdict[str, int](int))

    # -- CSV-driven Rename Models ---------------------------------------------

    class ModCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """CLI request for the shared AST, semantic, and text codemod cascade."""

        check: Annotated[bool, m.Field(description="Validate without writing")] = False
        dry_run_mode: Annotated[
            bool,
            m.Field(alias="dry-run", description="Inspect without writing"),
        ] = False
        rename_plan: Annotated[
            Path | None,
            m.Field(description="Authenticated semantic rename artifact to consume"),
        ] = None
        consumer_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Explicit external consumer checkout roots for this run",
        )

    class SemanticRenamePlanCommand(m.ContractModel):
        """Produce an inventory-derived rename artifact without applying changes."""

        repository_root: Path = m.Field(description="Complete governed workspace")
        decisions: t.NonEmptyStr = m.Field(description="SemanticRenameSelections JSON")
        output: Path = m.Field(
            description="Workspace-contained plan artifact destination"
        )

    class SemanticRenamePreviewCommand(m.ContractModel):
        """Read and validate a complete rename artifact without source effects."""

        repository_root: Path = m.Field(description="Complete governed workspace")
        plan: Path = m.Field(description="Authenticated semantic rename artifact")

    class ApplyRenamesInput(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """Validated CLI request for CSV-driven symbol renames."""

        rename_definitions: Annotated[
            bool,
            m.Field(description="Atomically rename owned declarations and references"),
        ] = False

        csv: Annotated[
            t.NonEmptyStr,
            m.Field(description="Path to the old,new rename-list CSV"),
        ]
        roots: Annotated[
            Sequence[str],
            m.Field(min_length=1, description="Directories to scan for rename targets"),
        ]
        bindings: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(
                description=(
                    "CSV expression prefixes mapped to current"
                    " public Rope owner identities"
                ),
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, Sequence[str]]({}))
        text_globs: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Explicit root-relative non-Python documentation"
                    " and configuration text surfaces"
                ),
            ),
        ] = ()
        python_documentation: Annotated[
            bool,
            m.Field(
                description=(
                    "Rename comments and actual Python docstrings,"
                    " preserving executable string payloads"
                ),
            ),
        ] = False
        exclude_globs: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Declared generated projections excluded from campaign targets"
                ),
            ),
        ] = ()

    class ApplyRenamesReport(FlextInfraModelsBase.FrozenArbitrary):
        """Summary of one CSV-driven rename pass."""

        preview_diff: Annotated[
            str,
            m.Field(description="Unified diff from authenticated planned source bytes"),
        ] = ""
        label: Annotated[t.NonEmptyStr, m.Field(description="Rename-list label")]
        files_scanned: Annotated[
            t.NonNegativeInt,
            m.Field(description="Text files scanned"),
        ]
        occurrences: Annotated[
            t.NonNegativeInt,
            m.Field(
                description=(
                    "Pending authenticated source edit spans from the current scan"
                ),
            ),
        ] = 0
        files_changed: Annotated[
            t.NonNegativeInt,
            m.Field(description="Files rewritten in apply mode"),
        ] = 0
        applied: Annotated[bool, m.Field(description="Whether changes were applied")]
        published_states: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Authenticated states of the acknowledged published paths",
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_published_states(self) -> Self:
            """Require one actual state per acknowledged published file.

            Returns:
                The report with a complete, unique publication inventory.

            Raises:
                ValueError: If publication counts and states disagree.

            """
            paths = {state.path for state in self.published_states}
            if len(paths) != len(self.published_states) or (
                len(paths) != self.files_changed
                or (not self.applied and self.published_states)
            ):
                msg = "rename publication states disagree with acknowledged files"
                raise ValueError(msg)
            return self

    # -- Namespace Enforcer Models ---------------------------------------------

    class ParsedPythonModule(FlextInfraModelsBase.FrozenArbitrary):
        """Result of parsing a Python source file into AST."""

        source: Annotated[str, m.Field(description="Raw source text")]
        tree: Annotated[
            t.Port[t.Infra.RopePyModule],
            m.Field(description="Parsed PyObject module representation"),
        ]

    class ImportLawScope(FlextInfraModelsBase.FrozenArbitrary):
        """Immutable facts one import-law pass decides a module's imports on."""

        project_root: Annotated[Path, m.Field(description="Governed project root")]
        file_path: Annotated[Path, m.Field(description="Normalized module path")]
        namespace_dir: Annotated[
            Path,
            m.Field(description="Directory of the namespace owning the module"),
        ]
        module: Annotated[str, m.Field(description="Dotted name of the module")]
        layer: Annotated[int, m.Field(description="Module's import-layer rank")]
        own_exports: Annotated[
            frozenset[str],
            m.Field(description="Names the module declares in its own __all__"),
        ]
        facade_dependencies: Annotated[
            frozenset[str],
            m.Field(
                description="Facade aliases whose runtime providers depend on this "
                "module",
            ),
        ] = frozenset()
        family_letter: Annotated[
            str | None,
            m.Field(
                description=(
                    "Facade letter of the family package holding the module, "
                    "or None outside every family package"
                ),
            ),
        ] = None
        direct_imports: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the module keeps direct leaf imports: a "
                    "settings/config module or a family base.py, which must "
                    "never route through the namespace root or a lazy package"
                ),
            ),
        ] = False
        bootstrap_dependency: Annotated[
            bool,
            m.Field(
                description="Whether the captured root graph bootstraps this module"
            ),
        ] = False

        @m.computed_field
        @property
        def namespace(self) -> str:
            """Qualified publishing package derived from the explicit module facts.

            Returns:
                The namespace package name.

            """
            depth = len(self.file_path.relative_to(self.namespace_dir).parts) - (
                self.file_path.name == c.Infra.INIT_PY
            )
            parts = self.module.split(".")
            return ".".join(parts[: len(parts) - depth])

    class ImportLawPass(FlextInfraModelsBase.FrozenArbitrary):
        """One parsed module and the facts one import-law pass reads from it."""

        scope: Annotated[
            FlextInfraModelsRefactor.ImportLawScope,
            m.Field(description="Module facts of the pass"),
        ]
        tree: Annotated[t.Port[ast.Module], m.Field(description="Parsed module")]
        parents: Annotated[
            Mapping[int, t.Port[ast.AST]],
            m.Field(description="Child node id to parent node map"),
        ]
        bindings: Annotated[
            Mapping[str, t.Port[ast.stmt]],
            m.Field(description="Module-level statement binding each top name"),
        ]
        root_exports: Annotated[
            Mapping[str, str],
            m.Field(description="Names the namespace root publishes lazily"),
        ]
        sources: Annotated[
            Mapping[Path, str] | None,
            m.Field(description="Captured sources used by this normalization pass"),
        ] = None
        source_project: Annotated[
            t.Port[t.Infra.RopeProject] | None,
            m.Field(description="Native source view owning this pass"),
        ] = None
        deferred_class_lines: Annotated[
            frozenset[int],
            m.Field(description="Class declarations with proven ordinary construction"),
        ] = frozenset()


__all__: list[str] = ["FlextInfraModelsRefactor"]
