"""Structural documentation contracts for exact model transport.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p

if TYPE_CHECKING:
    from flext_infra import t


# NOTE (multi-agent, mro-wkii.17.23 / agent: uv_overlay_owner): protocols mirror
# source models structurally; no concrete m type crosses a public interface.
@runtime_checkable
class FlextInfraProtocolsDocs(Protocol):
    """Documentation model protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class DocstringCoverage(Protocol):
        """Docstring coverage metric for one documentation scope."""

        @property
        def checked(self) -> t.NonNegativeInt: ...

        @property
        def documented(self) -> t.NonNegativeInt: ...

        @property
        def percent(self) -> float: ...

    @runtime_checkable
    class AuditIssue(Protocol):
        """Single documentation audit finding."""

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
        """Record of a generated file operation."""

        @property
        def path(self) -> str: ...

        @property
        def written(self) -> bool: ...

    @runtime_checkable
    class AuditScopeParams(p.BaseModel, Protocol):
        """Bundled parameters for a single audit scope run."""

        @property
        def check(self) -> str: ...

        @property
        def strict(self) -> bool: ...

        @property
        def docstring_min(self) -> float | None: ...

        @property
        def budgets(self) -> tuple[int | None, t.IntMapping] | None: ...

    @runtime_checkable
    class DocsPhaseItemModel(p.BaseModel, Protocol):
        """Unified item payload for docs phase reports."""

        @property
        def phase(self) -> str: ...

        @property
        def file(self) -> str: ...

        @property
        def issue_type(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def links(self) -> t.NonNegativeInt: ...

        @property
        def toc(self) -> t.NonNegativeInt: ...

        @property
        def codeblocks(self) -> t.NonNegativeInt: ...

        @property
        def path(self) -> str: ...

        @property
        def written(self) -> bool: ...

    @runtime_checkable
    class DocsPhaseReport(p.BaseModel, Protocol):
        """Unified report payload for docs phases."""

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
        def passed(self) -> bool: ...

        @property
        def checks(self) -> t.StrSequence: ...

        @property
        def strict(self) -> bool: ...

        @property
        def changed_files(self) -> t.NonNegativeInt: ...

        @property
        def applied(self) -> bool: ...

        @property
        def generated(self) -> t.NonNegativeInt: ...

        @property
        def source(self) -> str: ...

        @property
        def missing_adr_skills(self) -> t.StrSequence: ...

        @property
        def todo_written(self) -> bool: ...

        @property
        def items(self) -> t.SequenceOf[FlextInfraProtocolsDocs.DocsPhaseItemModel]: ...

    @runtime_checkable
    class DocsRepositoryRef(p.BaseModel, Protocol):
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
    class DocsProviderSpec(p.BaseModel, Protocol):
        """Git provider fields consumed by documentation."""

        @property
        def name(self) -> str: ...

        @property
        def organization(self) -> str: ...

        @property
        def base_url(self) -> str: ...

        @property
        def branch(self) -> str: ...

    @runtime_checkable
    class DocsExportBinding(p.BaseModel, Protocol):
        """Public export binding fields."""

        @property
        def export_name(self) -> str: ...

        @property
        def module_name(self) -> str: ...

    @runtime_checkable
    class DocsPublicContract(p.BaseModel, Protocol):
        """Exact source objects and derived public documentation facts."""

        @property
        def metadata(self) -> p.ProjectMetadata: ...

        @property
        def repository(self) -> FlextInfraProtocolsDocs.DocsRepositoryRef | None: ...

        @property
        def provider(self) -> FlextInfraProtocolsDocs.DocsProviderSpec | None: ...

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


__all__: list[str] = ["FlextInfraProtocolsDocs"]
