"""Transaction and session models for the codegen pipeline.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Literal

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import FlextInfraModelsBase, FlextInfraModelsRope
from flext_infra._models._config import FlextInfraConfigModels


class FlextInfraModelsCodegenTransactionModels:
    """Transaction and session models for the codegen pipeline."""

    class CodegenSourcePreviewOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Authenticated inputs and runtime boundaries for one source preview."""

        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(), description="Pinned source states authenticated by the preview"
        )
        runtime_root: Path | None = m.Field(
            default=None, description="Explicit physical runtime owner when supplied"
        )
        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        runtime_check: bool = m.Field(
            default=True,
            description="Validate the candidate through its native runtime",
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None,
            description="Declared file modes for the staged source updates",
        )

    class CodegenSourceRuntime(FlextInfraModelsBase.FrozenArbitrary):
        """Source ownership and its explicitly elected execution environment."""

        workspace: Path = m.Field(description="Canonical source workspace root")
        runtime_root: Path | None = m.Field(
            default=None, description="Explicit physical runtime owner when supplied"
        )

    class StageSourceOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Authenticated inputs, topology and declarations for a source candidate."""

        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(), description="Pinned source states of the staging invocation"
        )
        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None, description="Declared source modes preserved during staging"
        )
        declared_files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            default=(), description="Authenticated candidate file declarations"
        )
        source_directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = m.Field(
            default=(), description="Original native source election receipts"
        )
        source_query_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(), description="Original native source query ancestry"
        )
        original_project: p.Infra.RopeProject | None = m.Field(
            default=None,
            description="Original Rope read owner a derived candidate view extends",
        )

    class StagePackagePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Pinned package/dependency inputs and the declared public facade contract."""

        package: str = m.Field(description="Selected canonical package namespace")
        module: str = m.Field(description="Selected public facade module")
        classname: str = m.Field(description="Published class preserved by projection")
        owner_module: str = m.Field(description="Canonical complete private owner")
        upstream: t.VariadicTuple[t.Pair[str, str]] = m.Field(
            description="Declared upstream base imports"
        )
        members: t.StrSequence = m.Field(
            description="Owner declarations inherited by the public facade"
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Pinned package layouts"
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            description="Pinned source/resource/metadata states"
        )
        workspace_packages: t.StrSequence = m.Field(
            description="Workspace namespaces requiring sealed origins"
        )

    class StageSourcePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Pinned project closure and desired bytes for effect-free validation."""

        version: Literal[1] = m.Field(default=1, description="Source receipt version")
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
        source_directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = m.Field(
            default=(), description="Native directory elections of this source epoch"
        )
        source_query_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(), description="Native root and source query identities"
        )
        prepared_hashes: t.VariadicTuple[t.Pair[Path, str | None]] = m.Field(
            default=(), description="Exact prepared update digests; None retires a file"
        )
        directory_publications: tuple[m.Cli.AtomicDirectoryState, ...] = m.Field(
            default=(), description="Journal-proven own directory births for admission"
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
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            default=(),
            description="Original physical binding and consumption epoch",
        )
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryInventory] = m.Field(
            default=(),
            description="Original native directory-election receipts",
        )
        source_query_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = (
            m.Field(
                default=(),
                description="Original native path-election topology receipts",
            )
        )

    class StagePackageView(FlextInfraModelsBase.FrozenArbitrary):
        """Journal-owned materialized package view, never another source of truth."""

        plan: FlextInfraModelsCodegenTransactionModels.StagePackagePlan = m.Field(
            description="Pinned input and public-feature contract"
        )
        root: Path = m.Field(
            description="Runtime artifact inside a registered transaction root"
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Actual materialized package origins"
        )
        manifest: m.Cli.AtomicPhysicalTreeManifest = m.Field(
            description="Descriptor-authenticated candidate tree"
        )
        target: m.Cli.AtomicPhysicalTreeEntry = m.Field(
            description="Exact desired facade bytes and physical identity"
        )


__all__: list[str] = ["FlextInfraModelsCodegenTransactionModels"]
