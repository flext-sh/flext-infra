# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import p, t


class FlextInfraProtocolsCodegenPipeline:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class CodegenCommand(Protocol):
        """Structural data contract projected from the owning model."""

        check_only: bool = ...
        output_format: str = ...

    @runtime_checkable
    class CodegenAutoFixCommand(Protocol):
        """Structural data contract projected from the owning model."""

        check_only: bool = ...
        output_format: str = ...
        rules_only: bool = ...

    @runtime_checkable
    class CandidateBootstrapCommand(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        dry_run: bool = ...
        check_only: bool = ...
        apply_changes: bool = ...

    @runtime_checkable
    class CodegenResult(Protocol):
        """Structural data contract projected from the owning model."""

        plan: FlextInfraProtocolsCodegenPipeline.CodegenPlan
        written_files: tuple[Path, ...] = ...
        errors: tuple[str, ...] = ...

    @runtime_checkable
    class CodegenConformPorts(Protocol):
        """Structural data contract projected from the owning model."""

        docs_planner: t.Port[p.Infra.DocsArtifactPlannerFactory]
        file_publisher: t.Port[p.Infra.CodegenFilePublisher]
        source_preview: t.Port[p.Infra.SourcePreview]
        candidate_validator: t.Port[
            Callable[[Path, Path, tuple[Path, ...]], p.Result[bool]]
        ]
        component_planner: t.Port[p.Infra.SourceComponentPlanner]


__all__: list[str] = [
    "FlextInfraProtocolsCodegenPipeline",
]
