# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/pipeline
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase, FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot
    from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenTransaction
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigArtifact,
        FlextInfraProtocolsConfigRelease,
        FlextInfraProtocolsConfigRepository,
        FlextInfraProtocolsConfigWorkspace,
    )


class FlextInfraProtocolsCodegenPipeline:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenCommand(FlextInfraProtocolsMixins.WriteMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check_only(self) -> bool:
            """Validate without writing."""
            ...

        @property
        def output_format(self) -> str:
            """Output format (json|text)."""
            ...

    @runtime_checkable
    class CodegenAutoFixCommand(CodegenCommand, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rules_only(self) -> bool:
            """Run only deterministic namespace rules."""
            ...

    @runtime_checkable
    class CandidateBootstrapCommand(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository with the candidate declarations."""
            ...

        @property
        def dry_run(self) -> bool:
            """Validate without writing."""
            ...

        @property
        def check_only(self) -> bool:
            """Validate without writing."""
            ...

        @property
        def apply_changes(self) -> bool:
            """Apply the complete candidate campaign."""
            ...

    @runtime_checkable
    class CodegenRepositoryPlanOutcome(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr:
            """Planned repository name."""
            ...

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Governed and retired file plans."""
            ...

        @property
        def environment(
            self,
        ) -> FlextInfraProtocolsConfigRelease.UvEnvironmentPlan | None:
            """Uv environment plan of the repository."""
            ...

        @property
        def elapsed(self) -> float:
            """Planning wall seconds."""
            ...

    @runtime_checkable
    class CodegenPlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def request(self) -> FlextInfraProtocolsConfigArtifact.CodegenGenerateRequest:
            """Validated public request."""
            ...

        @property
        def repositories(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.RepositoryRef, ...]:
            """Selected repositories in deterministic order."""
            ...

        @property
        def workspace(self) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec:
            """Workspace governing the selection."""
            ...

        @property
        def uv_environments(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRelease.UvEnvironmentPlan, ...]:
            """Uv plans paired with selected repositories."""
            ...

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """All render results validated before application."""
            ...

        @property
        def outcomes(
            self,
        ) -> tuple[
            FlextInfraProtocolsCodegenPipeline.CodegenRepositoryPlanOutcome, ...
        ]:
            """Original repository outcomes retained for coherent admission."""
            ...

    @runtime_checkable
    class CodegenResult(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def plan(self) -> FlextInfraProtocolsCodegenPipeline.CodegenPlan:
            """The plan actually used by the producer."""
            ...

        @property
        def written_files(self) -> tuple[Path, ...]:
            """Files atomically replaced by apply."""
            ...

        @property
        def errors(self) -> tuple[str, ...]:
            """Fail-closed validation or write errors."""
            ...

    @runtime_checkable
    class CodegenConformPorts(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def docs_planner(self) -> FlextInfraProtocolsBase.DocsArtifactPlannerFactory:
            """Builds the docs planner for one conform scope."""
            ...

        @property
        def file_publisher(self) -> FlextInfraProtocolsBase.CodegenFilePublisher:
            """Shared guarded normalization and publication owner."""
            ...

        @property
        def source_preview(self) -> FlextInfraProtocolsBase.SourcePreview:
            """Native staged source-view owner."""
            ...

        @property
        def candidate_validator(
            self,
        ) -> Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]:
            """Native cold-import admission in the source runtime."""
            ...

        @property
        def component_planner(self) -> FlextInfraProtocolsBase.SourceComponentPlanner:
            """Shared recursive facade composition planner."""
            ...

    @runtime_checkable
    class CodegenConformState(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_inputs(self) -> Mapping[Path, p.Cli.AtomicFileState]:
            """Original source witnesses retained after native planning."""
            ...

        @property
        def source_imports(self) -> dict[Path, tuple[frozenset[str], frozenset[str]]]:
            """Original runtime and typing import facts of captured sources."""
            ...

        @property
        def request(
            self,
        ) -> FlextInfraProtocolsConfigArtifact.CodegenGenerateRequest | None:
            """Validated projection request retained by reference."""
            ...

        @property
        def provider_plans(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...] | None:
            """Original cohort plans available to native source reads."""
            ...

        repository_root: Path

        @property
        def initial_workspace(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec | None:
            """Declared scaffold specification."""
            ...

        @property
        def ports(
            self,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenConformPorts | None:
            """Facade-bound docs planning."""
            ...

        @property
        def docs_planner(self) -> FlextInfraProtocolsBase.DocsArtifactPlanner | None:
            """Actual planner before effects."""
            ...

        @property
        def snapshot(
            self,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot | None:
            """The run's one workspace snapshot; present while repositories plan."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenPipeline",
]
