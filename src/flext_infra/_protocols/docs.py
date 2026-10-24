"""Structural documentation contracts for exact model transport.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from flext_infra import p, t


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
        def exports(self) -> t.VariadicTuple[str]: ...

        @property
        def aliases(self) -> t.VariadicTuple[str]: ...

        @property
        def facades(self) -> t.VariadicTuple[str]: ...

        @property
        def module_exports(self) -> t.VariadicTuple[str]: ...

        @property
        def public_symbols(self) -> t.VariadicTuple[str]: ...

        @property
        def export_bindings(
            self,
        ) -> tuple[FlextInfraProtocolsDocs.DocsExportBinding, ...]: ...

        @property
        def modules(self) -> t.VariadicTuple[str]: ...

        @property
        def source_paths(self) -> t.VariadicTuple[str]: ...

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


__all__: list[str] = ["FlextInfraProtocolsDocs"]
