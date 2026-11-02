# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/root
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigRoot:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class Infra(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def initial_project_version(self) -> t.NonEmptyStr: ...
        @property
        def codegen(self) -> p.Infra.CodegenConfigSpec: ...
        @property
        def tooling(self) -> p.Infra.ToolConfigDocument: ...
        @property
        def source_scan(self) -> p.Infra.SourceScanSpec: ...
        @property
        def mutation_lock(self) -> p.Infra.MutationLockSpec: ...
        @property
        def release(self) -> p.Infra.ReleasePolicySpec: ...
        @property
        def refactor_csv_campaigns(self) -> p.Infra.RefactorCsvCampaignsSpec: ...

    @runtime_checkable
    class Root(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def Infra(self) -> p.Infra.Infra: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRoot",
]
