"""Phase analysis and pipeline state models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
    FlextInfraConfigModels,
    FlextInfraConfigModelsContract,
)


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

    class CodegenRepositoryPlanOutcome(FlextInfraConfigModelsContract.ConfigContract):
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
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan],
            m.Field(description="Governed and retired file plans"),
        ] = ()
        environment: Annotated[
            FlextInfraConfigModels.UvEnvironmentPlan | None,
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
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
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

    class CodegenPlan(FlextInfraConfigModelsContract.ConfigContract):
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
            t.VariadicTuple[FlextInfraConfigModels.RepositoryRef],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraConfigModels.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        uv_environments: Annotated[
            t.VariadicTuple[FlextInfraConfigModels.UvEnvironmentPlan],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan],
            m.Field(description="All render results validated before application"),
        ]
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Planning failures retained alongside valid outputs"),
        ] = ()

    class CodegenResult(FlextInfraModelsBase.FrozenArbitrary):
        """The generation plan and the files its publication changed."""

        plan: Annotated[
            FlextInfraModelsCodegenPipelineModels.CodegenPlan,
            m.Field(description="The plan actually used by the producer"),
        ]
        written_files: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="Files atomically replaced by apply",
        )
        errors: t.VariadicTuple[str] = m.Field(
            default=(),
            description="Fail-closed validation or write errors",
        )

    class CodegenConformPorts(m.ContractModel):
        """Collaborators the complete conform crosses into, wired by the facade.

        Docs rendering is another service family; the composition root binds
        its implementation once and conform only consumes this port.
        """

        docs_planner: Annotated[
            t.Port[p.Infra.DocsArtifactPlannerFactory],
            m.Field(
                exclude=True,
                description="Builds the docs planner for one conform scope",
            ),
        ]

    class CodegenConformState(m.ArbitraryTypesModel):
        """Mutable request-local data owned by one projection invocation."""

        request: t.Port[p.Infra.CodegenGenerateRequest] | None = m.Field(
            default=None,
            exclude=True,
            description="Validated projection request retained by reference",
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
        ports: t.Port[p.Infra.CodegenConformPorts] | None = m.Field(
            default=None,
            exclude=True,
            description="Facade-bound docs planning",
        )
        planning_issues: t.MutableSequenceOf[FlextInfraModelsCheck.Issue] = m.Field(
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
        _generation_issues: t.MutableSequenceOf[FlextInfraModelsCheck.Issue] = (
            m.PrivateAttr(default_factory=list[FlextInfraModelsCheck.Issue])
        )


__all__: list[str] = ["FlextInfraModelsCodegenPipelineModels"]
