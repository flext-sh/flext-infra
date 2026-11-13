# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/docs_generation
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_infra import c, t
    from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenTransaction
    from flext_infra._protocols._config import FlextInfraProtocolsConfigWorkspace


class FlextInfraProtocolsDocsGeneration:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DocsCatalogEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Project name."""
            ...

        @property
        def project_class(self) -> str:
            """Project class."""
            ...

        @property
        def package_name(self) -> str:
            """Import package name."""
            ...

        @property
        def description(self) -> str:
            """Project description."""
            ...

        @property
        def api_page(self) -> str:
            """Generated API page."""
            ...

    @runtime_checkable
    class DocsDependencyReference(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Normalized distribution name."""
            ...

        @property
        def documentation_url(self) -> t.NonEmptyStr:
            """Official publisher-declared or verified documentation URL."""
            ...

        @property
        def installed_version(self) -> str | None:
            """Observed installed distribution version."""
            ...

        @property
        def locked_versions(self) -> tuple[str, ...]:
            """Distinct versions declared by governed locks."""
            ...

        @property
        def source(self) -> t.NonEmptyStr:
            """Metadata or configured source establishing URL ownership."""
            ...

    @runtime_checkable
    class DocsLlmsContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def title(self) -> t.NonEmptyStr:
            """Owning workspace title."""
            ...

        @property
        def projects(
            self,
        ) -> tuple[FlextInfraProtocolsDocsGeneration.DocsCatalogEntry, ...]:
            """Generated first-party project references."""
            ...

        @property
        def dependencies(
            self,
        ) -> tuple[FlextInfraProtocolsDocsGeneration.DocsDependencyReference, ...]:
            """Official external documentation references."""
            ...

    @runtime_checkable
    class DocsRootInputs(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_contract(self) -> t.JsonMapping:
            """Validated workspace contract of the repository."""
            ...

        @property
        def markdown_width(self) -> int:
            """Prose width elected once for the destination repository."""
            ...

        @property
        def exclude_docs(self) -> Sequence[str]:
            """Repository-relative publication exclusion globs from codegen."""
            ...

    @runtime_checkable
    class DocScope(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declared_files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Captured presentation candidates."""
            ...

        @property
        def metadata_projection(
            self,
        ) -> FlextInfraProtocolsCodegenTransaction.CodegenFilePlan | None:
            """Planned pyproject.toml the run publishes for this scope."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Scope name."""
            ...

        @property
        def path(self) -> Path:
            """Absolute lexical scope root."""
            ...

        @property
        def report_dir(self) -> Path:
            """Absolute lexical report output directory."""
            ...

        @property
        def project_class(self) -> str:
            """Docs scope classification."""
            ...

        @property
        def package_name(self) -> str:
            """Primary package name for scope."""
            ...

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Project-local generated documentation language."""
            ...

        @property
        def governance_source(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.CodegenBootstrapSource | None:
            """Captured source and ref owning governance links."""
            ...

        @property
        def repository_root_override(self) -> Path | None:
            """Structural member projected from the owning model.

            Physical repository root when it differs from `path` (a member project
            scope inside a declared workspace); absent for a scope that owns its own
            docs policy.
            """
            ...

        @property
        def repository_root(self) -> Path:
            """The physical repository root owning this scope's docs policy."""
            ...

        def documentation_text(self, message: c.Infra.DocumentationText) -> str:
            """Structural member projected from the owning model.

            Resolve one finite presentation message without changing source prose.
            """
            ...

    @runtime_checkable
    class DocsRenderedArtifact(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> Path:
            """Normalized scope-relative destination."""
            ...

        @property
        def desired_content(self) -> bytes | None:
            """Exact desired bytes, or absence."""
            ...

        @property
        def desired_mode(self) -> Literal[420] | None:
            """Exact desired mode, or absence."""
            ...

    @runtime_checkable
    class DocsScopeArtifacts(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope(self) -> FlextInfraProtocolsDocsGeneration.DocScope:
            """Exact scope that owns every relative artifact."""
            ...

        @property
        def artifacts(
            self,
        ) -> tuple[FlextInfraProtocolsDocsGeneration.DocsRenderedArtifact, ...]:
            """Complete ordered desired artifact inventory."""
            ...

    @runtime_checkable
    class DocsGenerationBundle(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scopes(
            self,
        ) -> tuple[FlextInfraProtocolsDocsGeneration.DocsScopeArtifacts, ...]:
            """Ordered selected scope inventories."""
            ...

        @property
        def metadata_files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Owned metadata published with this render."""
            ...

        @property
        def repository_root(self) -> Path:
            """Absolute lexical physical workspace root."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDocsGeneration",
]
