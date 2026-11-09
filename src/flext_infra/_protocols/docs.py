from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsDocsGeneration
    from flext_infra._protocols._config import FlextInfraProtocolsConfigRepository


from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import FlextCliProtocols

from flext_infra._protocols.base import FlextInfraProtocolsBase

"""Structural documentation contracts for exact model transport.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


# NOTE (multi-agent, flext-wkii.17.23 / agent: uv_overlay_owner): protocols mirror
# source models structurally; no concrete m type crosses a public interface.
@runtime_checkable
class FlextInfraProtocolsDocs(Protocol):
    """Documentation model protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class DocsRepositoryRef(Protocol):
        """Repository catalog fields consumed by documentation."""

        @property
        def name(self) -> str: ...

        @property
        def distribution(self) -> str: ...

        @property
        def url(self) -> str: ...

        @property
        def provider(self) -> str: ...

    @runtime_checkable
    class DocsExportBinding(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def export_name(self) -> str:
            """Public export name."""
            ...

        @property
        def module_name(self) -> str:
            """Defining module name."""
            ...

    @runtime_checkable
    class DocsPublicContract(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def metadata(self) -> p.ProjectMetadata:
            """Exact canonical project metadata model."""
            ...

        @property
        def repository(
            self,
        ) -> FlextInfraProtocolsConfigRepository.RepositoryRef | None:
            """Exact repository catalog model."""
            ...

        @property
        def package_name(self) -> str:
            """Documented package name."""
            ...

        @property
        def doc_summary(self) -> str:
            """Package docstring summary."""
            ...

        @property
        def site_title(self) -> str:
            """Resolved site title."""
            ...

        @property
        def site_url(self) -> str:
            """Resolved site URL."""
            ...

        @property
        def repo_url(self) -> str:
            """Resolved repository URL."""
            ...

        @property
        def exports(self) -> t.StrTuple:
            """Exports."""
            ...

        @property
        def aliases(self) -> t.StrTuple:
            """One-letter alias exports."""
            ...

        @property
        def facades(self) -> t.StrTuple:
            """Public facade exports."""
            ...

        @property
        def module_exports(self) -> t.StrTuple:
            """Exported module shortcuts."""
            ...

        @property
        def public_symbols(self) -> t.StrTuple:
            """Rope-resolved public symbols."""
            ...

        @property
        def export_bindings(
            self,
        ) -> tuple[FlextInfraProtocolsDocs.DocsExportBinding, ...]:
            """Export-to-module bindings."""
            ...

        @property
        def modules(self) -> t.StrTuple:
            """Generated public module pages."""
            ...

        @property
        def source_paths(self) -> t.StrTuple:
            """Mkdocstrings source roots."""
            ...

    @runtime_checkable
    class MkDocsConfigLoader(Protocol):
        """Native configuration callable required by strict builds."""

        def __call__(
            self, *, config_file: str, site_dir: str, strict: bool
        ) -> MkDocsConfig: ...

    @runtime_checkable
    class MkDocsServer(Protocol):
        """Native server callable required by documentation composition."""

        def __call__(
            self,
            *,
            config_file: str,
            livereload: bool,
            dev_addr: str,
            strict: bool,
        ) -> None: ...

    @runtime_checkable
    class MkDocsConfigModule(Protocol):
        """Read-only native module configuration operation."""

        @property
        def load_config(self) -> FlextInfraProtocolsDocs.MkDocsConfigLoader: ...

    @runtime_checkable
    class MkDocsServeModule(Protocol):
        """Read-only native module server operation."""

        @property
        def serve(self) -> FlextInfraProtocolsDocs.MkDocsServer: ...

    @runtime_checkable
    class DocsTocToken(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def level(self) -> int:
            """Rendered heading level."""
            ...

        @property
        def id(self) -> str:
            """Actual rendered heading ID."""
            ...

        @property
        def name(self) -> str:
            """Sanitized heading label."""
            ...

        @property
        def html(self) -> str:
            """Rendered inline heading HTML."""
            ...

        @property
        def data_toc_label(self) -> str:
            """Explicit TOC label."""
            ...

        @property
        def children(self) -> Sequence[FlextInfraProtocolsDocs.DocsTocToken]:
            """Nested heading tokens."""
            ...

    @runtime_checkable
    class DocsRenderedToc(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def toc_tokens(self) -> Sequence[FlextInfraProtocolsDocs.DocsTocToken]:
            """Rendered table of contents tokens."""
            ...

    @runtime_checkable
    class DocsProjectIndexEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Project name."""
            ...

        @property
        def module_count(self) -> t.NonNegativeInt:
            """Generated module page count."""
            ...

    @runtime_checkable
    class DocsClassCount(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_class(self) -> str:
            """Project class."""
            ...

        @property
        def count(self) -> t.NonNegativeInt:
            """Project count."""
            ...

    @runtime_checkable
    class DocsGovernanceLinks(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def agents(self) -> str:
            """AGENTS.md pointer."""
            ...

        @property
        def governance(self) -> str:
            """GOVERNANCE.md pointer."""
            ...

        @property
        def skills(self) -> str:
            """Skills directory pointer."""
            ...

        @property
        def onboarding(self) -> str:
            """Onboarding guide pointer."""
            ...

    @runtime_checkable
    class DocsGuideEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_name(self) -> str:
            """Guide file name."""
            ...

        @property
        def title(self) -> str:
            """Guide link title."""
            ...

    @runtime_checkable
    class DocsModuleEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Dotted module name."""
            ...

        @property
        def path(self) -> str:
            """Module page relative path."""
            ...

    @runtime_checkable
    class DocsPageContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Generated documentation language."""
            ...

        @property
        def line_width(self) -> t.PositiveInt:
            """Prose width of the Markdown line contract."""
            ...

        @property
        def preview_limit(self) -> t.PositiveInt:
            """Entries shown by a compact preview list."""
            ...

        @property
        def generated_header(self) -> str:
            """The canonical generated-file marker."""
            ...

        @property
        def text(self) -> Mapping[str, str]:
            """Every localized presentation message keyed by its member name."""
            ...

    @runtime_checkable
    class DocsDirectivePageContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def title(self) -> str:
            """Page title."""
            ...

        @property
        def dotted_path(self) -> str:
            """Documented dotted path."""
            ...

    @runtime_checkable
    class DocsProjectIndexContext(DocsPageContext, Protocol):
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
        def version(self) -> str:
            """Declared version."""
            ...

        @property
        def description(self) -> str:
            """Declared description."""
            ...

        @property
        def links(self) -> FlextInfraProtocolsDocs.DocsGovernanceLinks:
            """Governance pointers."""
            ...

    @runtime_checkable
    class DocsProjectReadmeContext(DocsProjectIndexContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def facades(self) -> Sequence[str]:
            """Primary public facades."""
            ...

    @runtime_checkable
    class DocsGuidesIndexContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Project name."""
            ...

        @property
        def guides(self) -> Sequence[FlextInfraProtocolsDocs.DocsGuideEntry]:
            """Ordered guide rows."""
            ...

    @runtime_checkable
    class DocsApiReadmeContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Project name."""
            ...

        @property
        def package_name(self) -> str:
            """Import package name."""
            ...

        @property
        def facades(self) -> Sequence[str]:
            """Primary public facades."""
            ...

        @property
        def module_count(self) -> t.NonNegativeInt:
            """Rendered module page count."""
            ...

    @runtime_checkable
    class DocsOverviewContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def site_title(self) -> str:
            """Overview site title."""
            ...

        @property
        def package_name(self) -> str:
            """Import package name."""
            ...

        @property
        def version(self) -> str:
            """Declared version."""
            ...

        @property
        def description(self) -> str:
            """Declared description."""
            ...

        @property
        def doc_summary(self) -> str:
            """Declared documentation summary."""
            ...

        @property
        def classifiers(self) -> Sequence[str]:
            """Trove classifiers."""
            ...

        @property
        def project_class(self) -> str:
            """Project class."""
            ...

        @property
        def keywords(self) -> Sequence[str]:
            """Project keywords."""
            ...

        @property
        def facades(self) -> Sequence[str]:
            """Primary facades."""
            ...

        @property
        def aliases(self) -> Sequence[str]:
            """Alias exports."""
            ...

        @property
        def public_symbols(self) -> Sequence[str]:
            """Public symbol exports."""
            ...

        @property
        def module_exports(self) -> Sequence[str]:
            """Module shortcut exports."""
            ...

        @property
        def preview_limits(self) -> Mapping[str, int]:
            """Preview length per exported field."""
            ...

        @property
        def module_count(self) -> t.NonNegativeInt:
            """Rendered module page count."""
            ...

    @runtime_checkable
    class DocsModulesIndexContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Project name."""
            ...

        @property
        def modules(self) -> Sequence[FlextInfraProtocolsDocs.DocsModuleEntry]:
            """Ordered module page rows."""
            ...

    @runtime_checkable
    class DocsRootOverviewContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def site_title(self) -> str:
            """Workspace site title."""
            ...

        @property
        def version(self) -> str:
            """Declared version."""
            ...

        @property
        def description(self) -> str:
            """Declared description."""
            ...

        @property
        def project_count(self) -> t.NonNegativeInt:
            """Governed project count."""
            ...

        @property
        def class_counts(self) -> Sequence[FlextInfraProtocolsDocs.DocsClassCount,]:
            """Projects per documentation class."""
            ...

    @runtime_checkable
    class DocsRootProjectsIndexContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(self) -> Sequence[FlextInfraProtocolsDocs.DocsProjectIndexEntry,]:
            """Per-project module page counts."""
            ...

    @runtime_checkable
    class DocsProjectCatalogContext(DocsPageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(
            self,
        ) -> Sequence[FlextInfraProtocolsDocsGeneration.DocsCatalogEntry,]:
            """Catalog rows that survive the exclusions."""
            ...

    @runtime_checkable
    class DocsCollectRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> bool:
            """Verify canonical published evidence without provider access."""
            ...

        @property
        def repository_root(self) -> Path:
            """Repository owning the plans."""
            ...

        @property
        def configuration(self) -> Path:
            """Versioned collection source associations."""
            ...

    @runtime_checkable
    class DocsGenerateRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root for docs generation."""
            ...

        @property
        def projects(self) -> Sequence[str] | None:
            """Optional selected project names."""
            ...

        @property
        def output_dir(self) -> Path | str | None:
            """Optional docs output directory override."""
            ...

        @property
        def include_root(self) -> bool:
            """Structural member projected from the owning model.

            Render the workspace root as a docs output scope (root guides remain
            readable sources regardless of this flag).
            """
            ...

    @runtime_checkable
    class DocstringCoverage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checked(self) -> t.NonNegativeInt:
            """Public docstring targets evaluated."""
            ...

        @property
        def documented(self) -> t.NonNegativeInt:
            """Targets carrying a docstring."""
            ...

        @property
        def percent(self) -> float:
            """Coverage percentage (100.0 when nothing checked)."""
            ...

    @runtime_checkable
    class AuditIssue(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str:
            """File path relative to scope."""
            ...

        @property
        def issue_type(self) -> str:
            """Issue category."""
            ...

        @property
        def severity(self) -> str:
            """Issue severity."""
            ...

        @property
        def message(self) -> str:
            """Issue description."""
            ...

    @runtime_checkable
    class GeneratedFile(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> str:
            """File path."""
            ...

        @property
        def changed(self) -> bool:
            """Whether generated content differs on disk."""
            ...

        @property
        def written(self) -> bool:
            """Whether file was written."""
            ...

    @runtime_checkable
    class AuditScopeParams(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> str:
            """Comma-separated checks."""
            ...

        @property
        def docstring_min(self) -> float | None:
            """Minimum docstring coverage percent; breach fails the scope."""
            ...

    @runtime_checkable
    class DocsPhaseReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> str:
            """Docs phase: audit, fix, build, generate, validate."""
            ...

        @property
        def scope(self) -> str:
            """Scope name."""
            ...

        @property
        def result(self) -> str:
            """Result status."""
            ...

        @property
        def reason(self) -> str:
            """Result reason."""
            ...

        @property
        def message(self) -> str:
            """Human-readable summary message."""
            ...

        @property
        def site_dir(self) -> str:
            """Built site directory path."""
            ...

        @property
        def checks(self) -> Sequence[str]:
            """Executed checks."""
            ...

        @property
        def strict(self) -> bool:
            """Strict-mode flag."""
            ...

        @property
        def passed(self) -> bool:
            """Whether phase passed."""
            ...

        @property
        def changed_files(self) -> t.NonNegativeInt:
            """Changed files count."""
            ...

        @property
        def applied(self) -> bool:
            """Apply mode flag."""
            ...

        @property
        def generated(self) -> t.NonNegativeInt:
            """Generated files count."""
            ...

        @property
        def source(self) -> str:
            """Source marker for generated content."""
            ...

        @property
        def missing_adr_skills(self) -> Sequence[str]:
            """Missing ADR skill references."""
            ...

        @property
        def todo_written(self) -> bool:
            """Whether TODOS.md was written."""
            ...

        @property
        def items(self) -> Sequence[FlextInfraProtocolsDocs.DocsPhaseItemModel]:
            """Phase-specific item payloads."""
            ...

    @runtime_checkable
    class DocsPhaseItemModel(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> str:
            """Docs phase: audit, fix, build, generate, validate."""
            ...

        @property
        def file(self) -> str:
            """Relative file path."""
            ...

        @property
        def issue_type(self) -> str:
            """Audit issue type."""
            ...

        @property
        def severity(self) -> str:
            """Audit issue severity."""
            ...

        @property
        def message(self) -> str:
            """Item detail message."""
            ...

        @property
        def links(self) -> t.NonNegativeInt:
            """Applied link fixes."""
            ...

        @property
        def toc(self) -> t.NonNegativeInt:
            """Applied TOC updates."""
            ...

        @property
        def codeblocks(self) -> t.NonNegativeInt:
            """Applied python codeblock fixes."""
            ...

        @property
        def path(self) -> str:
            """Generated file path."""
            ...

        @property
        def written(self) -> bool:
            """Generated file write flag."""
            ...

    @runtime_checkable
    class DocsPhaseReports(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> tuple[FlextInfraProtocolsDocs.DocsPhaseReport, ...]:
            """Structural member projected from the owning model."""
            ...


__all__: list[str] = ["FlextInfraProtocolsDocs"]
