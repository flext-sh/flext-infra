from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import p


from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

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
    class DocsExportBinding(Protocol):
        """Public export binding fields."""

        @property
        def export_name(self) -> str: ...

        @property
        def module_name(self) -> str: ...

    @runtime_checkable
    class DocsPublicContract(Protocol):
        """Exact source objects and derived public documentation facts."""

        @property
        def metadata(self) -> p.ProjectMetadata: ...

        @property
        def repository(self) -> FlextInfraProtocolsDocs.DocsRepositoryRef | None: ...

        @property
        def package_name(self) -> str: ...

        @property
        def doc_summary(self) -> str: ...

        @property
        def site_title(self) -> str: ...

        @property
        def site_url(self) -> str: ...

        @property
        def repo_url(self) -> str: ...

        @property
        def exports(self) -> tuple[str, ...]: ...

        @property
        def aliases(self) -> tuple[str, ...]: ...

        @property
        def facades(self) -> tuple[str, ...]: ...

        @property
        def module_exports(self) -> tuple[str, ...]: ...

        @property
        def public_symbols(self) -> tuple[str, ...]: ...

        @property
        def export_bindings(
            self,
        ) -> tuple[FlextInfraProtocolsDocs.DocsExportBinding, ...]: ...

        @property
        def modules(self) -> tuple[str, ...]: ...

        @property
        def source_paths(self) -> tuple[str, ...]: ...

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
    class DocsTocToken(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def level(self) -> int: ...

        @property
        def id(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def html(self) -> str: ...

        @property
        def data_toc_label(self) -> str: ...

        @property
        def children(self) -> Sequence[p.Infra.DocsTocToken]: ...

    @runtime_checkable
    class DocsRenderedToc(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def toc_tokens(self) -> Sequence[p.Infra.DocsTocToken]: ...

    @runtime_checkable
    class DocsProjectIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str: ...

        @property
        def module_count(self) -> int: ...

    @runtime_checkable
    class DocsClassCount(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_class(self) -> str: ...

        @property
        def count(self) -> int: ...

    @runtime_checkable
    class DocsGovernanceLinks(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def agents(self) -> str: ...

        @property
        def governance(self) -> str: ...

        @property
        def skills(self) -> str: ...

        @property
        def onboarding(self) -> str: ...

    @runtime_checkable
    class DocsGuideEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_name(self) -> str: ...

        @property
        def title(self) -> str: ...

    @runtime_checkable
    class DocsModuleEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str: ...

        @property
        def path(self) -> str: ...

    @runtime_checkable
    class DocsPageContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

    @runtime_checkable
    class DocsDirectivePageContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def title(self) -> str: ...

        @property
        def dotted_path(self) -> str: ...

    @runtime_checkable
    class DocsProjectIndexContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def name(self) -> str: ...

        @property
        def project_class(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def description(self) -> str: ...

        @property
        def links(self) -> p.Infra.DocsGovernanceLinks: ...

    @runtime_checkable
    class DocsProjectReadmeContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def name(self) -> str: ...

        @property
        def project_class(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def description(self) -> str: ...

        @property
        def links(self) -> p.Infra.DocsGovernanceLinks: ...

        @property
        def facades(self) -> Sequence[str]: ...

    @runtime_checkable
    class DocsGuidesIndexContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def name(self) -> str: ...

        @property
        def guides(self) -> Sequence[p.Infra.DocsGuideEntry]: ...

    @runtime_checkable
    class DocsApiReadmeContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def name(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def facades(self) -> Sequence[str]: ...

        @property
        def module_count(self) -> int: ...

    @runtime_checkable
    class DocsOverviewContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def site_title(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def description(self) -> str: ...

        @property
        def doc_summary(self) -> str: ...

        @property
        def classifiers(self) -> Sequence[str]: ...

        @property
        def project_class(self) -> str: ...

        @property
        def keywords(self) -> Sequence[str]: ...

        @property
        def facades(self) -> Sequence[str]: ...

        @property
        def aliases(self) -> Sequence[str]: ...

        @property
        def public_symbols(self) -> Sequence[str]: ...

        @property
        def module_exports(self) -> Sequence[str]: ...

        @property
        def preview_limits(self) -> Mapping[str, int]: ...

        @property
        def module_count(self) -> int: ...

    @runtime_checkable
    class DocsModulesIndexContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def name(self) -> str: ...

        @property
        def modules(self) -> Sequence[p.Infra.DocsModuleEntry]: ...

    @runtime_checkable
    class DocsRootOverviewContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def site_title(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def description(self) -> str: ...

        @property
        def project_count(self) -> int: ...

        @property
        def class_counts(self) -> Sequence[p.Infra.DocsClassCount]: ...

    @runtime_checkable
    class DocsRootProjectsIndexContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def entries(self) -> Sequence[p.Infra.DocsProjectIndexEntry]: ...

    @runtime_checkable
    class DocsProjectCatalogContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def documentation_language(self) -> str: ...

        @property
        def line_width(self) -> int: ...

        @property
        def preview_limit(self) -> int: ...

        @property
        def entries(self) -> Sequence[p.Infra.DocsCatalogEntry]: ...

    @runtime_checkable
    class DocsCollectRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> bool: ...

        @property
        def repository_root(self) -> Path: ...

        @property
        def configuration(self) -> Path: ...

    @runtime_checkable
    class DocsGenerateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...

        @property
        def projects(self) -> Sequence[str] | None: ...

        @property
        def output_dir(self) -> Path | str | None: ...

        @property
        def include_root(self) -> bool: ...

    @runtime_checkable
    class DocstringCoverage(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checked(self) -> int: ...

        @property
        def documented(self) -> int: ...

        @property
        def percent(self) -> float: ...

    @runtime_checkable
    class AuditIssue(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> str: ...

        @property
        def issue_type(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def message(self) -> str: ...

    @runtime_checkable
    class GeneratedFile(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> str: ...

        @property
        def changed(self) -> bool: ...

        @property
        def written(self) -> bool: ...

    @runtime_checkable
    class AuditScopeParams(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> str: ...

        @property
        def docstring_min(self) -> float | None: ...

    @runtime_checkable
    class DocsPhaseReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phase(self) -> str: ...

        @property
        def scope(self) -> str: ...

        @property
        def result(self) -> str: ...

        @property
        def reason(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def site_dir(self) -> str: ...

        @property
        def checks(self) -> Sequence[str]: ...

        @property
        def strict(self) -> bool: ...

        @property
        def passed(self) -> bool: ...

        @property
        def changed_files(self) -> int: ...

        @property
        def applied(self) -> bool: ...

        @property
        def generated(self) -> int: ...

        @property
        def source(self) -> str: ...

        @property
        def missing_adr_skills(self) -> Sequence[str]: ...

        @property
        def todo_written(self) -> bool: ...

        @property
        def items(self) -> Sequence[p.Infra.DocsPhaseItemModel]: ...


__all__: list[str] = ["FlextInfraProtocolsDocs"]
