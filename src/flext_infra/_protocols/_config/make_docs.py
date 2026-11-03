# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/make_docs
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import t
from flext_infra._protocols._config import FlextInfraProtocolsConfigContract


class FlextInfraProtocolsConfigMakeDocs:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DocsOverviewPreviewLimitsSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def aliases(self) -> int:
            """Alias preview limit."""
            ...

        @property
        def public_symbols(self) -> int:
            """Public symbol preview limit."""
            ...

        @property
        def facades(self) -> int:
            """Facade preview limit."""
            ...

        @property
        def module_exports(self) -> int:
            """Module export preview limit."""
            ...

        @property
        def keywords(self) -> int:
            """Keyword preview limit."""
            ...

    @runtime_checkable
    class DocsGithubRepoSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def organization(self) -> t.NonEmptyStr:
            """GitHub organization."""
            ...

        @property
        def repository(self) -> t.NonEmptyStr:
            """GitHub repository."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr:
            """Working-line branch for doc links."""
            ...

        @property
        def local_checkout(self) -> str:
            """Optional local checkout path (~ expanded) for existence checks."""
            ...

    @runtime_checkable
    class MakeDocsSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def contract_guide(self) -> Path | None:
            """Canonical guide with the generated Make contract section."""
            ...

        @property
        def actions(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Docs verb lifecycle actions in execution order; every entry must be a
            registered docs CLI action.
            """
            ...

        @property
        def mutable_actions(self) -> tuple[t.NonEmptyStr, ...]:
            """Docs actions that mutate."""
            ...

        @property
        def reports_dir(self) -> Path:
            """Repository-relative docs reports directory."""
            ...

        @property
        def overview_preview_limits(
            self,
        ) -> FlextInfraProtocolsConfigMakeDocs.DocsOverviewPreviewLimitsSpec:
            """Maximum preview sizes for generated API overviews."""
            ...

        @property
        def cross_project_relative_link_pattern(self) -> t.NonEmptyStr:
            """Regex rejecting cross-project relative Markdown links."""
            ...

        @property
        def stale_github_organizations(self) -> tuple[t.NonEmptyStr, ...]:
            """Placeholder GitHub orgs that must be rewritten."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigMakeDocs",
]
