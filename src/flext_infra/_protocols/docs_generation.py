# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import t
from flext_infra._models._config import (
    FlextInfraModelsConfigArtifact,
    FlextInfraModelsConfigWorkspace,
)


class FlextInfraProtocolsDocsGeneration:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class DocsCatalogEntry(Protocol):
        """Structural data contract projected from the owning model."""

        name: str
        project_class: str
        package_name: str
        description: str
        api_page: str

    @runtime_checkable
    class DocScope(Protocol):
        """Structural data contract projected from the owning model."""

        declared_files: tuple[FlextInfraModelsConfigArtifact.CodegenFilePlan, ...] = ...
        name: t.NonEmptyStr
        path: Path
        report_dir: Path
        project_class: str = ...
        package_name: str = ...
        documentation_language: t.Infra.DocumentationLanguage = ...
        governance_source: (
            FlextInfraModelsConfigWorkspace.CodegenBootstrapSource | None
        ) = ...
        repository_root_override: Path | None = ...

    @runtime_checkable
    class DocsRenderedArtifact(Protocol):
        """Structural data contract projected from the owning model."""

        relative_path: Path
        desired_content: bytes | None
        desired_mode: Literal[420] | None

    @runtime_checkable
    class DocsScopeArtifacts(Protocol):
        """Structural data contract projected from the owning model."""

        scope: FlextInfraModelsDocsGeneration.DocScope
        artifacts: tuple[FlextInfraModelsDocsGeneration.DocsRenderedArtifact, ...]

    @runtime_checkable
    class DocsGenerationBundle(Protocol):
        """Structural data contract projected from the owning model."""

        scopes: tuple[FlextInfraModelsDocsGeneration.DocsScopeArtifacts, ...]
        metadata_files: tuple[FlextInfraModelsConfigArtifact.CodegenFilePlan, ...] = ...
        repository_root: Path


__all__: list[str] = [
    "FlextInfraProtocolsDocsGeneration",
]
