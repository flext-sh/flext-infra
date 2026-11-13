# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/root
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsDepsToolConfig
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigArtifact,
        FlextInfraProtocolsConfigRefactorCampaigns,
        FlextInfraProtocolsConfigRelease,
        FlextInfraProtocolsConfigStatic,
    )


class FlextInfraProtocolsConfigRoot:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class Infra(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Project distribution name."""
            ...

        @property
        def initial_project_version(self) -> t.NonEmptyStr:
            """Version seeded into a newly scaffolded project."""
            ...

        @property
        def codegen(self) -> FlextInfraProtocolsConfigArtifact.CodegenConfigSpec:
            """Unified project and workspace codegen contract."""
            ...

        @property
        def tooling(self) -> FlextInfraProtocolsDepsToolConfig.ToolConfigDocument:
            """Validated lint, typecheck, and scaffold policy."""
            ...

        @property
        def source_scan(self) -> FlextInfraProtocolsConfigStatic.SourceScanSpec:
            """Production-only source discovery contract."""
            ...

        @property
        def rope(self) -> FlextInfraProtocolsConfigStatic.RopePreferencesSpec:
            """Native source-engine preference policy."""
            ...

        @property
        def gate_admission(self) -> FlextInfraProtocolsConfigStatic.GateAdmissionSpec:
            """Host-wide FIFO admission for heavy gates."""
            ...

        @property
        def release(self) -> FlextInfraProtocolsConfigRelease.ReleasePolicySpec:
            """Release protocol policy."""
            ...

        @property
        def refactor_csv_campaigns(
            self,
        ) -> FlextInfraProtocolsConfigRefactorCampaigns.RefactorCsvCampaignsSpec:
            """Declared CSV-driven rename campaigns for the mod verb."""
            ...

    @runtime_checkable
    class Root(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def Infra(self) -> FlextInfraProtocolsConfigRoot.Infra:
            """Validated flext-infra namespace."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRoot",
]
