"""Source candidate models for the codegen pipeline.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Self

from flext_cli import m, t

from flext_infra import p
from flext_infra._models import FlextInfraModelsBase
from flext_infra._models._codegen import FlextInfraModelsCodegenLazyInit
from flext_infra._models._git import FlextInfraModelsGitWorktreeState
from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot


class FlextInfraModelsCodegenTransaction:
    """Source candidate models for the codegen pipeline."""

    class CodegenFilePlan(m.Cli.FileChange):
        """One managed file change plus its governed ownership metadata."""

        inputs: Annotated[
            tuple[
                Annotated[
                    p.Cli.AtomicFileState,
                    t.schema_for_model(lambda: m.Cli.AtomicFileState),
                ],
                ...,
            ],
            m.Field(
                description="Original read-only observations consumed by this effect",
            ),
        ] = ()
        project: Annotated[Path, m.Field(description="Physical owning project root")]
        move_source: Annotated[
            Path | None,
            m.Field(description="Original source retired by this native resource move"),
        ] = None
        owner: Annotated[
            str,
            m.Field(description="Canonical artifact owner, empty for scaffold files"),
        ] = ""
        policy: Annotated[
            Literal["full", "merge"] | None,
            m.Field(description="Governed root artifact policy"),
        ] = None
        tracking: Annotated[
            Literal["versioned", "runtime-local"],
            m.Field(description="Declared persistence policy of this artifact"),
        ] = "versioned"
        index_before: Annotated[
            Annotated[
                p.Infra.GitWorktreeIndexEntry,
                t.schema_for_model(
                    lambda: FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry
                ),
            ]
            | None,
            m.Field(description="Captured index entry scheduled for retirement"),
        ] = None
        tracking_dependencies: Annotated[
            tuple[Path, ...],
            m.Field(
                description=(
                    "Portable declaration destinations required before retirement"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def validate_publication_identity(self) -> Self:
            """Keep every plan inside its project and its retirement consistent.

            Returns:
                The validated plan.

            Raises:
                ValueError: If the plan escapes its project, publishes a
                    first-party stub, or declares an inconsistent retirement.

            """
            if not self.project.is_absolute() or not self.path.is_relative_to(
                self.project
            ):
                msg = f"codegen path escapes owning project: {self.path}"
                raise ValueError(msg)
            if self.path.suffix == ".pyi" and self.desired_content is not None:
                msg = f"first-party .pyi publication is forbidden: {self.path}"
                raise ValueError(msg)
            move_source = self.move_source
            move_escapes = move_source is not None and (
                not move_source.is_absolute()
                or not move_source.is_relative_to(self.project)
            )
            if move_source is not None and (
                move_escapes
                or move_source == self.path
                or self.before.content is not None
                or self.desired_content is None
            ):
                msg = "native move provenance requires a distinct absent destination"
                raise ValueError(msg)
            if self.index_before is not None and (
                self.tracking != "runtime-local"
                or self.index_before.path.is_absolute()
                or self.project / self.index_before.path != self.path
            ):
                msg = "index retirement must match its runtime-local artifact"
                raise ValueError(msg)
            if any(
                not path.is_relative_to(self.project)
                for path in self.tracking_dependencies
            ):
                msg = "tracking declaration escapes the owning project"
                raise ValueError(msg)
            return self

    class StageSourceOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Composition scopes, file modes and declared effects of a source candidate."""

        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: Mapping[Path, int] | None = m.Field(
            default=None, description="Declared source modes preserved during staging"
        )
        declared_files: tuple[
            Annotated[
                p.Infra.CodegenFilePlan,
                t.schema_for_model(
                    lambda: FlextInfraModelsCodegenTransaction.CodegenFilePlan
                ),
            ],
            ...,
        ] = m.Field(default=(), description="Authenticated candidate file declarations")
        inputs: tuple[
            Annotated[
                p.Cli.AtomicFileState, t.schema_for_model(lambda: m.Cli.AtomicFileState)
            ],
            ...,
        ] = m.Field(
            default=(),
            description="Original source observations whose layouts join the closure",
        )
        import_edges: t.Port[Mapping[Path, tuple[frozenset[str], frozenset[str]]]] = (
            m.Field(
                default_factory=lambda: MappingProxyType[
                    Path, tuple[frozenset[str], frozenset[str]]
                ]({}),
                description=(
                    "Captured runtime and typing import facts retained by reference"
                ),
            )
        )
        snapshot: (
            t.Port[FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot] | None
        ) = m.Field(
            default=None,
            description=(
                "Run snapshot whose authenticated reads and import edges elect "
                "the closure instead of a second read and parse"
            ),
        )

        @m.model_validator(mode="after")
        def observed_import_inputs(self) -> Self:
            """Require original witnesses for every retained source import fact.

            Returns:
                This validated source-admission request.

            Raises:
                ValueError: If original witnesses conflict or an import fact
                    has no original source witness.

            """
            observed: dict[Path, m.Cli.AtomicFileState] = {}
            for state in self.inputs:
                previous = observed.setdefault(state.path, state)
                if previous != state:
                    message = f"conflicting original source witnesses: {state.path}"
                    raise ValueError(message)
            if self.import_edges.keys() - observed.keys():
                message = "captured import facts require original source witnesses"
                raise ValueError(message)
            return self

    class StageSourcePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Pinned project closure and desired bytes for effect-free validation."""

        workspace: Path = m.Field(description="Canonical source workspace root")
        workspaces: tuple[Path, ...] = m.Field(
            default=(),
            description="Explicit composition scopes, never a parent-directory scan",
        )
        roots: tuple[Path, ...] = m.Field(
            description="Discovered project roots covering the pinned source closure"
        )
        inputs: tuple[
            Annotated[
                p.Cli.AtomicFileState, t.schema_for_model(lambda: m.Cli.AtomicFileState)
            ],
            ...,
        ] = m.Field(description="Exact source and configuration observations")
        updates: Mapping[Path, str | None] = m.Field(
            description=(
                "Desired sources keyed by live destination; None retires an artifact"
            ),
        )
        modes: Mapping[Path, int] = m.Field(
            default_factory=lambda: MappingProxyType[Path, int]({}),
            description="Desired file-effect modes derived from original move sources",
        )
        declared_files: tuple[
            Annotated[
                p.Infra.CodegenFilePlan,
                t.schema_for_model(
                    lambda: FlextInfraModelsCodegenTransaction.CodegenFilePlan
                ),
            ],
            ...,
        ] = m.Field(
            default=(),
            description=(
                "Original file/absence witnesses with the current desired effects"
            ),
        )
        layouts: tuple[
            Annotated[
                p.Infra.RopeProjectLayout,
                t.schema_for_model(
                    lambda: FlextInfraModelsCodegenLazyInit.RopeProjectLayout
                ),
            ],
            ...,
        ] = m.Field(
            description="Original project layouts in the desired import closure",
        )
        workspace_packages: tuple[str, ...] = m.Field(
            description="Original elected workspace namespaces",
        )
        candidate_layouts: tuple[
            Annotated[
                p.Infra.RopeProjectLayout,
                t.schema_for_model(
                    lambda: FlextInfraModelsCodegenLazyInit.RopeProjectLayout
                ),
            ],
            ...,
        ] = m.Field(
            description="Prospective import closure of the authenticated declarations",
        )
        candidate_workspace_packages: tuple[str, ...] = m.Field(
            description="Prospective namespaces requiring sealed candidate origins",
        )

    class SemanticSourcePlan(m.ImmutableValueModel):
        """Authenticated source campaign independent of explicit rename intent."""

        candidate: Annotated[
            p.Infra.StageSourcePlan,
            t.schema_for_model(
                lambda: FlextInfraModelsCodegenTransaction.StageSourcePlan
            ),
        ] = m.Field(
            description="Authenticated complete source and runtime candidate closure",
        )
        consumer_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="External scopes elected before producer publication",
        )


__all__: list[str] = ["FlextInfraModelsCodegenTransaction"]
