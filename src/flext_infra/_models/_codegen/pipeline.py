"""Phase analysis and pipeline state models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Annotated, Self

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import (
    FlextInfraModelsBase,
    FlextInfraModelsCheck,
    FlextInfraModelsMixins,
    FlextInfraModelsWorkspace,
)
from flext_infra._models._codegen import (
    FlextInfraModelsCodegenFixModels,
    FlextInfraModelsCodegenJournalModels,
    FlextInfraModelsCodegenLazyInitModels,
    FlextInfraModelsCodegenScaffoldModels,
)
from flext_infra._models._config import FlextInfraConfigModels


class FlextInfraModelsCodegenPipelineModels:
    """Phase analysis and pipeline state models."""

    class CodegenCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """CLI request shared by Rope-backed codegen operations."""

        check_only: Annotated[bool, m.Field(description="Validate without writing")] = (
            False
        )
        output_format: Annotated[
            str,
            m.Field(description="Output format (json|text)"),
        ] = "text"

    class CodegenAutoFixCommand(CodegenCommand):
        """Auto-fix request with its one additional rule selector."""

        rules_only: Annotated[
            bool,
            m.Field(description="Run only deterministic namespace rules"),
        ] = False

    class CandidateBootstrapCommand(m.ContractModel):
        """Typed public request for an atomic declared Makefile campaign."""

        repository_root: Annotated[
            Path,
            m.Field(description="Repository with the candidate declarations"),
        ]
        dry_run: Annotated[bool, m.Field(description="Validate without writing")] = (
            False
        )
        check_only: Annotated[bool, m.Field(description="Validate without writing")] = (
            False
        )
        apply_changes: Annotated[
            bool,
            m.Field(description="Apply the complete candidate campaign"),
        ] = True

    class CodegenSourceReceipt(
        FlextInfraModelsBase.FrozenArbitrary, strict=True, validate_default=True
    ):
        """Original native consumption evidence, independent of publication effects."""

        phase: Annotated[
            c.Infra.CodegenStagedFilePhase,
            m.Field(description="Generation phase that produced this receipt"),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(description="Ordered complete authenticated planner inputs"),
        ]
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryInventory] = m.Field(
            default=(), description="Native source election query receipts"
        )
        source_query_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = (
            m.Field(
                default=(),
                description="Physical ancestry of queried source directories",
            )
        )

    class CodegenPhaseAnalysis(CodegenSourceReceipt):
        """Immutable planner receipt reused for publication verification."""

        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan],
            m.Field(description="Ordered desired publication states"),
        ]
        failed_targets: t.VariadicTuple[t.Pair[Path, Self]] = m.Field(
            default=(),
            description=(
                "Rejected physical targets and their original consumption receipts"
            ),
        )
        generator_trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest] = m.Field(
            default=(), description="Authenticated producer resource membership"
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            default=(), description="Exact cold module election before planning"
        )
        generator_reference: FlextInfraModelsWorkspace.NativeImportReference | None = (
            m.Field(
                default=None,
                description="Shared authenticated pre-planning native epoch",
            )
        )
        publications: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenLazyInitModels.LazyInitPlan],
            m.Field(description="Resolved export contracts verified before commit"),
        ] = ()
        issues: t.VariadicTuple[FlextInfraModelsCheck.Issue] = m.Field(
            default=(),
            description="Target planning failures retained beside valid file plans",
        )
        exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native planning cause retained for publication",
        )

        @m.model_validator(mode="after")
        def _validate_unique_paths(self) -> Self:
            """Reject ambiguous receipts with competing path authorities.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If codegen phase receipt destination paths must be unique;
                    or if codegen phase receipt input paths must be unique.

            """
            file_paths = Counter(file.path for file in self.files)
            duplicates = tuple(path for path, count in file_paths.items() if count > 1)
            if duplicates:
                msg = (
                    "codegen phase receipt destination paths must be unique: "
                    + ", ".join(
                        f"{path} ({file_paths[path]} plans)" for path in duplicates
                    )
                )
                raise ValueError(msg)
            input_paths = tuple(state.path for state in self.inputs)
            if len(set(input_paths)) != len(input_paths):
                msg = "codegen phase receipt input paths must be unique"
                raise ValueError(msg)
            return self

    class CodegenPhaseOutcome(
        FlextInfraModelsBase.FrozenArbitrary, strict=True, validate_default=True
    ):
        """One fleet worker's phase analysis, or its failure as data."""

        _publication_birth: t.Pair[int, str] | None = m.PrivateAttr(default=None)

        analysis: Annotated[
            FlextInfraModelsCodegenPipelineModels.CodegenPhaseAnalysis | None,
            m.Field(description="Phase analysis on success"),
        ] = None
        admitted_states: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            default=(),
            exclude=True,
            description=(
                "Exact immutable inputs authenticated by native batch admission"
            ),
        )
        error: Annotated[
            str,
            m.Field(description="Phase failure, empty on success"),
        ] = ""
        written_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Destinations successfully published despite target failures",
        )
        published_files: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenStagedFile
        ] = m.Field(
            default=(), exclude=True, description="Actual admitted destination states"
        )
        retained_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description=(
                "Authored destinations retained because generation does not own "
                "their bodies"
            ),
        )
        effect_targets: t.VariadicTuple[Path] = m.Field(
            default=(),
            description=(
                "Destinations authorized for effects by this invocation's journal"
            ),
        )
        attempted_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Effect targets with an observed write, retention, or failure",
        )
        pending_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Authorized effect targets without a publication outcome",
        )
        issues: t.VariadicTuple[FlextInfraModelsCheck.Issue] = m.Field(
            default=(),
            description="Native publication failures keyed to their actual targets",
        )
        exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native cause retained for causal Result propagation",
        )
        root: Path | None = m.Field(
            default=None,
            description="Actual publication scope when supplied by its owner",
        )
        transaction_id: str | None = m.Field(
            default=None,
            description=(
                "Identity of the publication invocation that produced this receipt"
            ),
        )
        phase: str | None = m.Field(
            default=None,
            description="Last completed publication phase",
        )
        completed: bool = m.Field(
            default=False,
            description="Whether the entire invocation reached final accounting",
        )
        sources: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenJournalSource
        ] = m.Field(
            default=(), description="Captured source identities without raw bytes"
        )
        outputs: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenJournalSource
        ] = m.Field(default=(), description="Every planned output, including no-ops")
        generator_sources: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenJournalSource
        ] = m.Field(default=(), description="Loaded generator implementation identity")
        generator_trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest] = m.Field(
            default=(), description="Captured producer resource membership"
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            default=(), description="Captured producer module election"
        )
        generator_reference: FlextInfraModelsWorkspace.NativeImportReference | None = (
            m.Field(
                default=None, description="Same native epoch as producer and journal"
            )
        )
        source_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = m.Field(
            default=(),
            description="Captured source directory ancestry and presence",
        )
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryInventory] = m.Field(
            default=(), description="Native source election query receipts"
        )
        source_query_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = (
            m.Field(
                default=(),
                description="Historical ancestry inputs of native source queries",
            )
        )
        scope_roots: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Roots elected by this receipt's native source owner",
        )
        source_scope: Path | None = m.Field(
            default=None, description="Member elected by the native docs source owner"
        )
        surface: c.Infra.CodegenConformSurface | None = m.Field(
            default=None,
            description="Actual operation surface when composed by conform",
        )
        scope: c.Infra.CodegenConformScope | None = m.Field(
            default=None,
            description="Actual operation scope when composed by conform",
        )
        module: str | None = m.Field(
            default=None, description="Exact module selector of the publication"
        )
        batches: t.VariadicTuple[Self] = m.Field(
            default=(),
            description="Actual completed native scope-batch receipts",
        )

    class CodegenResult(FlextInfraModelsBase.FrozenArbitrary):
        """An actual generation plan or an authenticated observational receipt."""

        plan: FlextInfraConfigModels.CodegenPlan | None = m.Field(
            default=None,
            description="The plan actually used by the producer",
        )
        verified_publication: (
            FlextInfraModelsCodegenPipelineModels.CodegenPhaseOutcome | None
        ) = m.Field(
            default=None, description="Native publication proof verified by observer"
        )
        publication_receipt: (
            FlextInfraModelsCodegenPipelineModels.CodegenPhaseOutcome | None
        ) = m.Field(
            default=None,
            description="Exact settled operation receipt returned by its producer",
        )
        written_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Files atomically replaced by apply",
        )
        errors: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Fail-closed validation or write errors",
        )

        @m.model_validator(mode="after")
        def _validate_actual_capability(self) -> Self:
            if (self.plan is None) == (self.verified_publication is None):
                msg = "conform result requires exactly one actual capability"
                raise ValueError(msg)
            if self.publication_receipt is not None and self.plan is None:
                msg = "producer publication requires its actual generation plan"
                raise ValueError(msg)
            for receipt in (self.verified_publication, self.publication_receipt):
                if receipt is None:
                    continue
                incomplete = (
                    not receipt.completed
                    or receipt.error
                    or receipt.issues
                    or receipt.pending_files
                )
                unsettled = (
                    receipt.root is None
                    or receipt.transaction_id is None
                    or not (receipt.outputs or receipt.batches)
                )
                if incomplete or unsettled:
                    msg = "publication requires complete output evidence"
                    raise ValueError(msg)
            return self

    class CodegenConformPorts(m.ContractModel):
        """Collaborators the complete conform crosses into, wired by the facade.

        Docs rendering is another service family; the composition root binds
        its implementation once and conform only consumes this port. Participant
        authorization is likewise supplied before any journal lease or recovery.
        """

        docs_planner: Annotated[
            p.Infra.DocsArtifactPlannerFactory,
            m.Field(description="Builds the docs planner for one conform scope"),
        ]
        participant_policy: p.Infra.CodegenParticipantPolicyFactory = m.Field(
            description="Authorizes physical generation participants before recovery",
        )

    class CodegenConformState(m.ArbitraryTypesModel):
        """Mutable request-local data owned by one conform invocation."""

        request: FlextInfraConfigModels.CodegenConformRequest | None = m.Field(
            default=None,
            exclude=True,
            description="Validated conform request",
        )
        generation_only: bool = m.Field(
            default=False,
            exclude=True,
            description="Project outputs without repairing authored inputs",
        )
        provider_plans: (
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan] | None
        ) = m.Field(
            default=None,
            exclude=True,
            description="Original cohort plans available to native source reads",
        )
        completed_source_plans: (
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan] | None
        ) = m.Field(
            default=None,
            exclude=True,
            description=(
                "Authenticated complete source output, absent before validation"
            ),
        )
        repository_root: Path = m.Field(
            default=Path(),
            exclude=True,
            description="Generation tool repository",
        )
        initial_workspace: FlextInfraConfigModels.WorkspaceSpec | None = m.Field(
            default=None,
            exclude=True,
            description="Declared scaffold specification",
        )
        ports: t.Port[p.Infra.CodegenConformPorts | None] = m.Field(
            default=None,
            exclude=True,
            description="Facade-bound docs planning and participant authorization",
        )
        planning_issues: t.MutableSequenceOf[FlextInfraModelsCheck.Issue] = m.Field(
            default_factory=list[FlextInfraModelsCheck.Issue],
            exclude=True,
            description="Native file planning failures retained by this invocation",
        )
        planning_exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native file planning cause",
        )
        docs_planner: t.Port[p.Infra.DocsArtifactPlanner | None] = m.Field(
            default=None,
            exclude=True,
            description="Actual planner before effects",
        )
        _generation_issues: t.MutableSequenceOf[FlextInfraModelsCheck.Issue] = (
            m.PrivateAttr(default_factory=list[FlextInfraModelsCheck.Issue])
        )

    class CodegenPipelineState(m.ArbitraryTypesModel):
        """Typed inter-stage state for the codegen pipeline — Pydantic v2 model."""

        discovered_projects: Annotated[
            t.SequenceOf[p.Infra.ProjectInfo],
            m.Field(description="Projects discovered at pipeline start"),
        ] = ()
        census_service: Annotated[
            p.Infra.CodegenCensusService | None,
            m.Field(description="Cached census service for reuse across stages"),
        ] = None
        reports_before: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenScaffoldModels.CensusReport],
            m.Field(description="Census reports collected before fixes"),
        ] = ()
        reports_after: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenScaffoldModels.CensusReport],
            m.Field(description="Census reports collected after fixes"),
        ] = ()
        scaffold_results: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenScaffoldModels.ScaffoldResult],
            m.Field(description="Scaffolding stage results"),
        ] = ()
        fix_results: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenFixModels.AutoFixResult],
            m.Field(description="Auto-fix stage results"),
        ] = ()
        lazy_unmapped_count: Annotated[
            int | None,
            m.Field(
                ge=0,
                description="Observed lazy drift, absent before that stage executes",
            ),
        ] = None


__all__: list[str] = ["FlextInfraModelsCodegenPipelineModels"]
