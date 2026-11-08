"""Phase analysis and pipeline state models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import FlextInfraModelsBase, FlextInfraModelsMixins
from flext_infra._models._config import FlextInfraModelsConfig


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

    class CodegenRepositoryPlanOutcome(m.ArbitraryTypesModel):
        """One repository's planned files and environment."""

        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Planned repository name"),
        ]
        files: Annotated[
            tuple[
                Annotated[
                    p.Infra.CodegenFilePlan,
                    t.schema_for_model(lambda: FlextInfraModelsConfig.CodegenFilePlan),
                ],
                ...,
            ],
            m.Field(description="Governed and retired file plans"),
        ] = ()
        environment: Annotated[
            Annotated[
                p.Infra.UvEnvironmentPlan,
                t.schema_for_model(lambda: FlextInfraModelsConfig.UvEnvironmentPlan),
            ]
            | None,
            m.Field(description="uv environment plan of the repository"),
        ] = None
        elapsed: Annotated[
            float,
            m.Field(ge=0, description="Planning wall seconds"),
        ] = 0.0

    class CodegenPlan(m.ArbitraryTypesModel):
        """Candidate effects of one completely planned request."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True,
        )
        request: Annotated[
            t.Port[p.Infra.CodegenGenerateRequest],
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            tuple[
                Annotated[
                    p.Infra.RepositoryRef,
                    t.schema_for_model(lambda: FlextInfraModelsConfig.RepositoryRef),
                ],
                ...,
            ],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            Annotated[
                p.Infra.WorkspaceSpec,
                t.schema_for_model(lambda: FlextInfraModelsConfig.WorkspaceSpec),
            ],
            m.Field(description="Workspace governing the selection"),
        ]
        uv_environments: Annotated[
            tuple[
                Annotated[
                    p.Infra.UvEnvironmentPlan,
                    t.schema_for_model(
                        lambda: FlextInfraModelsConfig.UvEnvironmentPlan
                    ),
                ],
                ...,
            ],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            tuple[
                Annotated[
                    p.Infra.CodegenFilePlan,
                    t.schema_for_model(lambda: FlextInfraModelsConfig.CodegenFilePlan),
                ],
                ...,
            ],
            m.Field(description="All render results validated before application"),
        ]
        outcomes: tuple[
            Annotated[
                p.Infra.CodegenRepositoryPlanOutcome,
                t.schema_for_model(
                    lambda: FlextInfraModelsCodegenPipeline.CodegenRepositoryPlanOutcome
                ),
            ],
            ...,
        ] = m.Field(
            default=(),
            description="Original repository outcomes retained for coherent admission",
        )

    class CodegenResult(FlextInfraModelsBase.FrozenArbitrary):
        """The generation plan and the files its publication changed."""

        plan: Annotated[
            Annotated[
                p.Infra.CodegenPlan,
                t.schema_for_model(lambda: FlextInfraModelsCodegenPipeline.CodegenPlan),
            ],
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

        docs_planner: t.Port[p.Infra.DocsArtifactPlannerFactory] = m.Field(
            exclude=True, description="Builds the docs planner for one conform scope"
        )
        file_publisher: t.Port[p.Infra.CodegenFilePublisher] = m.Field(
            exclude=True,
            description="Shared guarded normalization and publication owner",
        )
        source_preview: t.Port[p.Infra.SourcePreview] = m.Field(
            exclude=True, description="Native staged source-view owner"
        )
        candidate_validator: t.Port[
            Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]
        ] = m.Field(
            exclude=True,
            description="Native cold-import admission in the source runtime",
        )
        component_planner: t.Port[p.Infra.SourceComponentPlanner] = m.Field(
            exclude=True, description="Shared recursive facade composition planner"
        )

    class CodegenConformState(m.ArbitraryTypesModel):
        """Mutable request-local data owned by one projection invocation."""

        source_inputs: t.Port[
            dict[
                Path,
                Annotated[
                    p.Cli.AtomicFileState,
                    t.schema_for_model(lambda: m.Cli.AtomicFileState),
                ],
            ]
        ] = m.Field(
            default_factory=dict,
            description="Original source witnesses retained after native planning",
        )
        source_imports: t.Port[dict[Path, tuple[frozenset[str], frozenset[str]]]] = (
            m.Field(
                default_factory=dict[Path, tuple[frozenset[str], frozenset[str]]],
                description=(
                    "Original runtime and typing import facts of captured sources"
                ),
            )
        )

        request: t.Port[p.Infra.CodegenGenerateRequest] | None = m.Field(
            default=None,
            description="Validated projection request retained by reference",
        )
        provider_plans: (
            tuple[
                Annotated[
                    p.Infra.CodegenFilePlan,
                    t.schema_for_model(lambda: FlextInfraModelsConfig.CodegenFilePlan),
                ],
                ...,
            ]
            | None
        ) = m.Field(
            default=None,
            exclude=True,
            description="Original cohort plans available to native source reads",
        )
        repository_root: Path = m.Field(
            default=Path(),
            description="Generation tool repository",
        )
        initial_workspace: (
            Annotated[
                p.Infra.WorkspaceSpec,
                t.schema_for_model(lambda: FlextInfraModelsConfig.WorkspaceSpec),
            ]
            | None
        ) = m.Field(
            default=None,
            description="Declared scaffold specification",
        )
        ports: t.Port[p.Infra.CodegenConformPorts] | None = m.Field(
            default=None,
            description="Facade-bound docs planning",
        )
        docs_planner: t.Port[p.Infra.DocsArtifactPlanner] | None = m.Field(
            default=None,
            description="Actual planner before effects",
        )
        snapshot: t.Port[p.Infra.WorkspaceSnapshot] | None = m.Field(
            default=None,
            description=(
                "The run's one workspace snapshot; present while repositories plan"
            ),
        )


__all__: list[str] = ["FlextInfraModelsCodegenPipeline"]
