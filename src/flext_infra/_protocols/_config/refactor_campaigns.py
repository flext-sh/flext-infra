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

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigRefactorCampaigns:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class RenameCampaignSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def rename_definitions(self) -> bool: ...
        @property
        def csv(self) -> t.NonEmptyStr: ...
        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def bindings(self) -> Mapping[str, Sequence[str]]: ...
        @property
        def text_globs(self) -> Sequence[str]: ...
        @property
        def python_documentation(self) -> bool: ...
        @property
        def exclude_globs(self) -> Sequence[str]: ...

    @runtime_checkable
    class ModOwnerSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr: ...
        @property
        def kind(self) -> Literal["semantic", "callback"]: ...
        @property
        def phase(self) -> str | None: ...
        @property
        def callback(self) -> str | None: ...

    @runtime_checkable
    class RefactorCsvCampaignsSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def campaigns(self) -> tuple[p.Infra.RenameCampaignSpec, ...]: ...
        @property
        def owners(self) -> tuple[p.Infra.ModOwnerSpec, ...]: ...
        @property
        def semantic_plan(self) -> Path | None: ...
        @property
        def semantic_decisions(self) -> Path | None: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRefactorCampaigns",
]
