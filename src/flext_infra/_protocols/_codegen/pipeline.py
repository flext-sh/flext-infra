# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/pipeline
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsCodegenPipeline:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def projects(self) -> Sequence[str] | None: ...
        @property
        def verbose(self) -> bool: ...
        @property
        def apply(self) -> bool: ...
        @property
        def gates(self) -> Sequence[str]: ...
        @property
        def dry_run(self) -> bool: ...
        @property
        def check_only(self) -> bool: ...
        @property
        def output_format(self) -> str: ...

    @runtime_checkable
    class CodegenAutoFixCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def projects(self) -> Sequence[str] | None: ...
        @property
        def verbose(self) -> bool: ...
        @property
        def apply(self) -> bool: ...
        @property
        def gates(self) -> Sequence[str]: ...
        @property
        def dry_run(self) -> bool: ...
        @property
        def check_only(self) -> bool: ...
        @property
        def output_format(self) -> str: ...
        @property
        def rules_only(self) -> bool: ...

    @runtime_checkable
    class CandidateBootstrapCommand(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def dry_run(self) -> bool: ...
        @property
        def check_only(self) -> bool: ...
        @property
        def apply_changes(self) -> bool: ...

    @runtime_checkable
    class CodegenRepositoryPlanOutcome(Protocol):
        """Structural data contract projected from the owning model."""

        repository: t.NonEmptyStr
        files: tuple[p.Infra.CodegenFilePlan, ...]
        environment: p.Infra.UvEnvironmentPlan | None
        elapsed: float

    @runtime_checkable
    class CodegenPlan(Protocol):
        """Structural data contract projected from the owning model."""

        request: p.Infra.CodegenGenerateRequest
        repositories: tuple[p.Infra.RepositoryRef, ...]
        workspace: p.Infra.WorkspaceSpec
        uv_environments: tuple[p.Infra.UvEnvironmentPlan, ...]
        files: tuple[p.Infra.CodegenFilePlan, ...]
        outcomes: tuple[p.Infra.CodegenRepositoryPlanOutcome, ...]

    @runtime_checkable
    class CodegenResult(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def plan(self) -> p.Infra.CodegenPlan: ...
        @property
        def written_files(self) -> tuple[Path, ...]: ...
        @property
        def errors(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class CodegenConformPorts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def docs_planner(self) -> p.Infra.DocsArtifactPlannerFactory: ...
        @property
        def file_publisher(self) -> p.Infra.CodegenFilePublisher: ...
        @property
        def source_preview(self) -> p.Infra.SourcePreview: ...
        @property
        def candidate_validator(
            self,
        ) -> Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]: ...
        @property
        def component_planner(self) -> p.Infra.SourceComponentPlanner: ...

    @runtime_checkable
    class CodegenConformState(Protocol):
        """Structural data contract projected from the owning model."""

        source_inputs: dict[Path, p.Cli.AtomicFileState]
        source_imports: dict[Path, tuple[frozenset[str], frozenset[str]]]
        request: p.Infra.CodegenGenerateRequest | None
        provider_plans: tuple[p.Infra.CodegenFilePlan, ...] | None
        repository_root: Path
        initial_workspace: p.Infra.WorkspaceSpec | None
        ports: p.Infra.CodegenConformPorts | None
        docs_planner: p.Infra.DocsArtifactPlanner | None
        snapshot: p.Infra.WorkspaceSnapshot | None


__all__: list[str] = [
    "FlextInfraProtocolsCodegenPipeline",
]
