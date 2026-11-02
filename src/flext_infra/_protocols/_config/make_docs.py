# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/make_docs
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigMakeDocs:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DocsOverviewPreviewLimitsSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def aliases(self) -> int: ...
        @property
        def public_symbols(self) -> int: ...
        @property
        def facades(self) -> int: ...
        @property
        def module_exports(self) -> int: ...
        @property
        def keywords(self) -> int: ...

    @runtime_checkable
    class DocsGithubRepoSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def organization(self) -> t.NonEmptyStr: ...
        @property
        def repository(self) -> t.NonEmptyStr: ...
        @property
        def branch(self) -> t.NonEmptyStr: ...
        @property
        def local_checkout(self) -> str: ...

    @runtime_checkable
    class MakeDocsSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def contract_guide(self) -> Path | None: ...
        @property
        def actions(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def mutable_actions(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def reports_dir(self) -> Path: ...
        @property
        def overview_preview_limits(self) -> p.Infra.DocsOverviewPreviewLimitsSpec: ...
        @property
        def cross_project_relative_link_pattern(self) -> t.NonEmptyStr: ...
        @property
        def stale_github_organizations(self) -> tuple[t.NonEmptyStr, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigMakeDocs",
]
