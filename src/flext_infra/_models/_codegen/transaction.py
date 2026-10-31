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

from flext_infra._models import FlextInfraModelsBase
from flext_infra._models._codegen import FlextInfraModelsCodegenLazyInit
from flext_infra._models._git import FlextInfraModelsGitWorktreeState
from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot


class FlextInfraModelsCodegenTransaction:
    """Source candidate models for the codegen pipeline."""

    class CodegenFilePlan(m.Cli.FileChange):
        """One managed file change plus its governed ownership metadata."""

        inputs: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Original read-only observations consumed by this effect",
            ),
        ] = ()
        project: Annotated[Path, m.Field(description="Physical owning project root")]
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
            FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry | None,
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

    class CodegenSourcePreviewOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Composition scopes, observed file plans and modes of one source preview.

        Generation admission retains the original declarations so the staged
        candidate and publication describe the same updates and retirements.
        """

        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: Mapping[Path, int] | None = m.Field(
            default=None,
            description="Declared file modes for the staged source updates",
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(),
            description="Original source observations materialized in the view",
        )
        declared_files: tuple[
            FlextInfraModelsCodegenTransaction.CodegenFilePlan, ...
        ] = m.Field(
            default=(), description="Original declarations of the candidate effects"
        )

    class StageSourceOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Composition scopes, file modes and declared effects of a source candidate."""

        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: Mapping[Path, int] | None = m.Field(
            default=None, description="Declared source modes preserved during staging"
        )
        declared_files: tuple[
            FlextInfraModelsCodegenTransaction.CodegenFilePlan, ...
        ] = m.Field(default=(), description="Authenticated candidate file declarations")
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(),
            description="Original source observations whose layouts join the closure",
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
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            description="Exact source and configuration observations"
        )
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
            FlextInfraModelsCodegenTransaction.CodegenFilePlan, ...
        ] = m.Field(
            default=(),
            description=(
                "Original file/absence witnesses with the current desired effects"
            ),
        )
        layouts: tuple[FlextInfraModelsCodegenLazyInit.RopeProjectLayout, ...] = (
            m.Field(
                description="Original project layouts in the desired import closure",
            )
        )
        workspace_packages: tuple[str, ...] = m.Field(
            description="Original elected workspace namespaces",
        )
        candidate_layouts: tuple[
            FlextInfraModelsCodegenLazyInit.RopeProjectLayout, ...
        ] = m.Field(
            description="Prospective import closure of the authenticated declarations",
        )
        candidate_workspace_packages: tuple[str, ...] = m.Field(
            description="Prospective namespaces requiring sealed candidate origins",
        )

    class SemanticSourcePlan(m.ImmutableValueModel):
        """Authenticated source campaign independent of explicit rename intent."""

        candidate: FlextInfraModelsCodegenTransaction.StageSourcePlan = m.Field(
            description="Authenticated complete source and runtime candidate closure",
        )
        consumer_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="External scopes elected before producer publication",
        )


__all__: list[str] = ["FlextInfraModelsCodegenTransaction"]
