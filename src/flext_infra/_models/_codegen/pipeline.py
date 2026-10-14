"""Phase analysis and pipeline state models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsMixins
from flext_infra._models._codegen.fix import FlextInfraModelsCodegenFixModels
from flext_infra._models._codegen.journal import FlextInfraModelsCodegenJournalModels
from flext_infra._models._codegen.lazy_init import FlextInfraModelsCodegenLazyInitModels
from flext_infra._models._codegen.scaffold import FlextInfraModelsCodegenScaffoldModels
from flext_infra._models._config.base import FlextInfraConfigModels
from flext_infra._models._config.contract import FlextInfraConfigModelsContract
from flext_infra._models.check import FlextInfraModelsCheck


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

    class CodegenSourceAuthority(m.ArbitraryTypesModel):
        """Cold authority permits reference staging, never project publication."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")
        runtime: Path = m.Field(description="Authenticated native interpreter")
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            description="Pinned producer sources, resources and distribution records",
        )
        generator_trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest] = m.Field(
            description="Authenticated physical producer resource membership",
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            description="Cold-elected physical producer namespaces",
        )

    class CodegenPhaseAnalysis(m.ArbitraryTypesModel):
        """Immutable planner receipt reused for publication verification."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        phase: Annotated[
            c.Infra.CodegenStagedFilePhase,
            m.Field(description="Generation phase that produced this receipt"),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan],
            m.Field(description="Ordered desired publication states"),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(description="Ordered complete authenticated planner inputs"),
        ]
        generator_trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest] = m.Field(
            default=(), description="Authenticated producer resource membership"
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            default=(), description="Exact cold module election before planning"
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

    class CodegenPhaseOutcome(m.ArbitraryTypesModel):
        """One fleet worker's phase analysis, or its failure as data."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

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
        source_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = m.Field(
            default=(),
            description="Captured source directory ancestry and presence",
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

    class CodegenResult(FlextInfraConfigModelsContract.ConfigContract):
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
                if receipt is not None and (
                    not receipt.completed
                    or receipt.error
                    or receipt.issues
                    or receipt.pending_files
                    or receipt.root is None
                    or receipt.transaction_id is None
                    or not (receipt.outputs or receipt.batches)
                ):
                    msg = "publication requires complete output evidence"
                    raise ValueError(msg)
            return self

    class CodegenConformPorts(m.ArbitraryTypesModel):
        """Collaborators the complete conform crosses into, wired by the facade.

        Docs rendering is another service family; the composition root binds
        its implementation once and conform only consumes this port. Participant
        authorization is likewise supplied before any journal lease or recovery.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            extra="forbid",
            arbitrary_types_allowed=True,
        )

        docs_planner: Annotated[
            p.Infra.DocsArtifactPlannerFactory,
            m.Field(description="Builds the docs planner for one conform scope"),
        ]
        participant_policy: p.Infra.CodegenParticipantPolicyFactory = m.Field(
            description="Authorizes physical generation participants before recovery",
        )

    class CodegenPipelineState(m.ArbitraryTypesModel):
        """Typed inter-stage state for the codegen pipeline — Pydantic v2 model."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            arbitrary_types_allowed=True,
        )

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
