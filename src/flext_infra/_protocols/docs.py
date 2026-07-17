"""Structural documentation contracts for exact model transport."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_cli import p


# NOTE (multi-agent, mro-wkii.17.23 / agent: uv_overlay_owner): protocols mirror
# source models structurally; no concrete m type crosses a public interface.
@runtime_checkable
class FlextInfraProtocolsDocs(Protocol):
    """Documentation model protocols exposed through ``p.Infra``."""

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
