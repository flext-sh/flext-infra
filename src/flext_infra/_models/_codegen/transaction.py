"""Source candidate models for the codegen pipeline.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsBase, FlextInfraModelsRope
from flext_infra._models._config import FlextInfraConfigModels


class FlextInfraModelsCodegenTransactionModels:
    """Source candidate models for the codegen pipeline."""

    class CodegenSourcePreviewOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Composition scopes and file modes of one source preview."""

        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None,
            description="Declared file modes for the staged source updates",
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(),
            description="Original source observations materialized in the view",
        )

    class StageSourceOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Composition scopes, file modes and declared effects of a source candidate."""

        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None, description="Declared source modes preserved during staging"
        )
        declared_files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            default=(), description="Authenticated candidate file declarations"
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(),
            description="Original source observations whose layouts join the closure",
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
        updates: t.MappingKV[Path, str | None] = m.Field(
            description=(
                "Desired sources keyed by live destination; None retires an artifact"
            ),
        )
        modes: t.MappingKV[Path, int] = m.Field(
            default_factory=lambda: MappingProxyType[Path, int]({}),
            description="Desired file-effect modes derived from original move sources",
        )
        declared_files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            default=(),
            description=(
                "Original file/absence witnesses with the current desired effects"
            ),
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Original project layouts in the desired import closure",
        )
        workspace_packages: tuple[str, ...] = m.Field(
            description="Original elected workspace namespaces",
        )
        candidate_layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Prospective import closure of the authenticated declarations",
        )
        candidate_workspace_packages: tuple[str, ...] = m.Field(
            description="Prospective namespaces requiring sealed candidate origins",
        )

    class SemanticSourcePlan(m.ImmutableValueModel):
        """Authenticated source campaign independent of explicit rename intent."""

        candidate: FlextInfraModelsCodegenTransactionModels.StageSourcePlan = m.Field(
            description="Authenticated complete source and runtime candidate closure",
        )
        consumer_roots: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="External scopes elected before producer publication",
        )


__all__: list[str] = ["FlextInfraModelsCodegenTransactionModels"]
