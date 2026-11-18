# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/refactor_campaigns
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsConfigRefactorCampaigns:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class RenameCampaignSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable public selector for this CSV campaign."""
            ...

        @property
        def rename_definitions(self) -> bool:
            """Atomically rename owned declarations and references."""
            ...

        @property
        def csv(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Config-directory-relative path to the old,new rename-list CSV; the list
            ships with the declaring config.
            """
            ...

        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-root-relative scan directories; empty selects the whole
            repository root.
            """
            ...

        @property
        def bindings(self) -> Mapping[str, Sequence[str]]:
            """Structural member projected from the owning model.

            CSV expression prefixes mapped to current public Rope owner identities.
            """
            ...

        @property
        def text_globs(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Explicit root-relative non-Python documentation and configuration text
            surfaces.
            """
            ...

        @property
        def python_documentation(self) -> bool:
            """Structural member projected from the owning model.

            Rename comments and actual Python docstrings without changing executable
            strings.
            """
            ...

        @property
        def exclude_globs(self) -> Sequence[str]:
            """Generated projections excluded from campaign targets."""
            ...

    @runtime_checkable
    class ModOwnerSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Stable public selector for a non-catalog mod owner."""
            ...

        @property
        def kind(self) -> Literal["semantic", "callback"]:
            """Structural member projected from the owning model."""
            ...

        @property
        def phase(self) -> str | None:
            """Structural member projected from the owning model."""
            ...

        @property
        def callback(self) -> str | None:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class RefactorCsvCampaignsSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def rewire_directory(self) -> Path:
            """Repository-relative immutable native rewire artifacts."""
            ...

        @property
        def campaigns(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRefactorCampaigns.RenameCampaignSpec, ...]:
            """Ordered rename campaigns."""
            ...

        @property
        def owners(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRefactorCampaigns.ModOwnerSpec, ...]:
            """Explicit semantic and callback mod owners."""
            ...

        @property
        def semantic_plan(self) -> Path | None:
            """Explicit workspace-relative semantic rename artifact."""
            ...

        @property
        def semantic_decisions(self) -> Path | None:
            """Workspace-relative SemanticRenameSelections JSON input."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRefactorCampaigns",
]
