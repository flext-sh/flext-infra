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

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDocsGeneration:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DocsCatalogEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str: ...
        @property
        def project_class(self) -> str: ...
        @property
        def package_name(self) -> str: ...
        @property
        def description(self) -> str: ...
        @property
        def api_page(self) -> str: ...

    @runtime_checkable
    class DocsDependencyReference(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def documentation_url(self) -> t.NonEmptyStr: ...
        @property
        def installed_version(self) -> str | None: ...
        @property
        def locked_versions(self) -> tuple[str, ...]: ...
        @property
        def source(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class DocsLlmsContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def title(self) -> t.NonEmptyStr: ...
        @property
        def projects(self) -> tuple[p.Infra.DocsCatalogEntry, ...]: ...
        @property
        def dependencies(self) -> tuple[p.Infra.DocsDependencyReference, ...]: ...

    @runtime_checkable
    class DocsRootInputs(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_contract(self) -> t.JsonMapping: ...
        @property
        def markdown_width(self) -> int: ...
        @property
        def exclude_docs(self) -> Sequence[str]: ...

    @runtime_checkable
    class DocScope(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def declared_files(self) -> tuple[p.Infra.CodegenFilePlan, ...]: ...
        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> Path: ...
        @property
        def report_dir(self) -> Path: ...
        @property
        def project_class(self) -> str: ...
        @property
        def package_name(self) -> str: ...
        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage: ...
        @property
        def governance_source(self) -> p.Infra.CodegenBootstrapSource | None: ...
        @property
        def repository_root_override(self) -> Path | None: ...
        @property
        def repository_root(self) -> Path: ...

    @runtime_checkable
    class DocsRenderedArtifact(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> Path: ...
        @property
        def desired_content(self) -> bytes | None: ...
        @property
        def desired_mode(self) -> Literal[420] | None: ...

    @runtime_checkable
    class DocsScopeArtifacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope(self) -> p.Infra.DocScope: ...
        @property
        def artifacts(self) -> tuple[p.Infra.DocsRenderedArtifact, ...]: ...

    @runtime_checkable
    class DocsGenerationBundle(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scopes(self) -> tuple[p.Infra.DocsScopeArtifacts, ...]: ...
        @property
        def metadata_files(self) -> tuple[p.Infra.CodegenFilePlan, ...]: ...
        @property
        def repository_root(self) -> Path: ...


__all__: list[str] = [
    "FlextInfraProtocolsDocsGeneration",
]
