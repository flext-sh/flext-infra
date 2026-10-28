"""Phase analysis and pipeline state models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Callable, MutableSequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import (
    FlextInfraModelsBase,
    FlextInfraModelsCheck,
    FlextInfraModelsMixins,
)
from flext_infra._models._config import (
    FlextInfraModelsConfig,
    FlextInfraModelsConfigContract,
)


class FlextInfraModelsCodegenPipeline:
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

    class CodegenRepositoryPlanOutcome(FlextInfraModelsConfigContract.ConfigContract):
        """One repository's planned files and environment, or its failure."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True,
        )
        exception: t.Port[BaseException] | None = m.Field(
            default=None,
            exclude=True,
            description="First native target planning cause",
        )
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Planned repository name"),
        ]
        files: Annotated[
            tuple[FlextInfraModelsConfig.CodegenFilePlan, ...],
            m.Field(description="Governed and retired file plans"),
        ] = ()
        environment: Annotated[
            FlextInfraModelsConfig.UvEnvironmentPlan | None,
            m.Field(description="uv environment plan of the repository"),
        ] = None
        error: Annotated[
            str,
            m.Field(description="Planning failure, empty on success"),
        ] = ""
        error_type: Annotated[
            str,
            m.Field(description="Original qualified exception type, when raised"),
        ] = ""
        error_traceback: Annotated[
            str,
            m.Field(description="Original planning traceback, without local variables"),
        ] = ""
        issues: Annotated[
            tuple[FlextInfraModelsCheck.Issue, ...],
            m.Field(description="Native failures attributed to individual targets"),
        ] = ()
        elapsed: Annotated[
            float,
            m.Field(ge=0, description="Planning wall seconds"),
        ] = 0.0

        @m.computed_field
        @property
        def failed(self) -> bool:
            """Include native causes even when no diagnostic was constructed."""
            return bool(
                self.error
                or self.error_type
                or self.error_traceback
                or self.issues
                or self.exception is not None
            )

    class CodegenPlan(FlextInfraModelsConfigContract.ConfigContract):
        """Fully validated plan produced before any managed-file write."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True,
        )
        exception: t.Port[BaseException] | None = m.Field(
            default=None,
            exclude=True,
            description="First native target failure carried into publication",
        )
        request: Annotated[
            t.Port[p.Infra.CodegenGenerateRequest],
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            tuple[FlextInfraModelsConfig.RepositoryRef, ...],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraModelsConfig.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        uv_environments: Annotated[
            tuple[FlextInfraModelsConfig.UvEnvironmentPlan, ...],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            tuple[FlextInfraModelsConfig.CodegenFilePlan, ...],
            m.Field(description="All render results validated before application"),
        ]
        issues: Annotated[
            tuple[FlextInfraModelsCheck.Issue, ...],
            m.Field(description="Planning failures retained alongside valid outputs"),
        ] = ()

    class CodegenResult(FlextInfraModelsBase.FrozenArbitrary):
        """The generation plan and the files its publication changed."""

        plan: Annotated[
            FlextInfraModelsCodegenPipeline.CodegenPlan,
            m.Field(description="The plan actually used by the producer"),
        ]
        written_files: tuple[Path, ...] = m.Field(
            default=(),
            description="Files atomically replaced by apply",
        )
        errors: tuple[str, ...] = m.Field(
            default=(),
            description="Fail-closed validation or write errors",
        )

    class CodegenConformPorts(m.ContractModel):
        """Collaborators the complete conform crosses into, wired by the facade.

        The composition root binds document planning and guarded file publication
        once. The same staged candidate must pass the native cold-import validator
        before either check accepts it or apply publishes it. Conform retains those
        capabilities by reference rather than assembling utility implementations.
        """

        docs_planner: Annotated[
            t.Port[p.Infra.DocsArtifactPlannerFactory],
            m.Field(
                exclude=True,
                description="Builds the docs planner for one conform scope",
            ),
        ]
        file_publisher: Annotated[
            t.Port[p.Infra.CodegenFilePublisher],
            m.Field(
                exclude=True,
                description="Shared guarded normalization and publication owner",
            ),
        ]
        source_preview: Annotated[
            t.Port[p.Infra.SourcePreview],
            m.Field(exclude=True, description="Native staged source-view owner"),
        ]
        candidate_validator: Annotated[
            t.Port[Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]],
            m.Field(
                exclude=True,
                description="Native cold-import admission in the source runtime",
            ),
        ]
        imports_planner: Annotated[
            t.Port[p.Infra.SourceImportPlanner],
            m.Field(
                exclude=True,
                description=(
                    "Shared import planner over the authenticated source candidate"
                ),
            ),
        ]
        component_planner: Annotated[
            t.Port[p.Infra.SourceComponentPlanner],
            m.Field(
                exclude=True,
                description="Shared recursive facade composition planner",
            ),
        ]

    class CodegenConformState(m.ArbitraryTypesModel):
        """Mutable request-local data owned by one projection invocation."""

        request: t.Port[p.Infra.CodegenGenerateRequest] | None = m.Field(
            default=None,
            exclude=True,
            description="Validated projection request retained by reference",
        )
        provider_plans: tuple[FlextInfraModelsConfig.CodegenFilePlan, ...] | None = (
            m.Field(
                default=None,
                exclude=True,
                description="Original cohort plans available to native source reads",
            )
        )
        completed_source_plans: (
            tuple[FlextInfraModelsConfig.CodegenFilePlan, ...] | None
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
        initial_workspace: FlextInfraModelsConfig.WorkspaceSpec | None = m.Field(
            default=None,
            exclude=True,
            description="Declared scaffold specification",
        )
        ports: t.Port[p.Infra.CodegenConformPorts] | None = m.Field(
            default=None,
            exclude=True,
            description="Facade-bound docs planning",
        )
        planning_issues: MutableSequence[FlextInfraModelsCheck.Issue] = m.Field(
            default_factory=list[FlextInfraModelsCheck.Issue],
            exclude=True,
            description="Native file planning failures retained by this invocation",
        )
        planning_exception: t.Port[BaseException] | None = m.Field(
            default=None,
            exclude=True,
            description="First native file planning cause",
        )
        docs_planner: t.Port[p.Infra.DocsArtifactPlanner] | None = m.Field(
            default=None,
            exclude=True,
            description="Actual planner before effects",
        )
        snapshot: t.Port[p.Infra.WorkspaceSnapshot] | None = m.Field(
            default=None,
            exclude=True,
            description=(
                "The run's one workspace snapshot; present while repositories plan"
            ),
        )
        _generation_issues: MutableSequence[FlextInfraModelsCheck.Issue] = (
            m.PrivateAttr(default_factory=list[FlextInfraModelsCheck.Issue])
        )


__all__: list[str] = ["FlextInfraModelsCodegenPipeline"]
