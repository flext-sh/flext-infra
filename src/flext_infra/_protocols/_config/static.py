# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/static
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsConfigStatic:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class RopePreferencesSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def preferred_import_style(self) -> c.Infra.RopeImportStyle:
            """Native import form used by identity-preserving refactors."""
            ...

    @runtime_checkable
    class SourceScanSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Ordered production source directory names."""
            ...

    @runtime_checkable
    class RouteBudgetSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def budget_seconds(self) -> t.PositiveInt:
            """Wall time from admission to forced termination."""
            ...

        @property
        def grace_seconds(self) -> t.PositiveInt:
            """Graceful termination reserve inside the budget."""
            ...

    @runtime_checkable
    class GateRepeatWindow(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def window_seconds(self) -> t.PositiveInt:
            """Time after a success during which the form is refused."""
            ...

        @property
        def lighter(self) -> t.NonEmptyStr:
            """Lighter command a refusal names."""
            ...

    @runtime_checkable
    class GateRepeatSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def check(self) -> FlextInfraProtocolsConfigStatic.GateRepeatWindow:
            """Window of a complete make check."""
            ...

        @property
        def tests_full(self) -> FlextInfraProtocolsConfigStatic.GateRepeatWindow:
            """Window of make tests-full."""
            ...

        @property
        def mod_full(self) -> FlextInfraProtocolsConfigStatic.GateRepeatWindow:
            """Window of make mod without LAWS or RULES."""
            ...

        @property
        def mod_selection(self) -> FlextInfraProtocolsConfigStatic.GateRepeatWindow:
            """Window of make mod repeating one LAWS/RULES selection."""
            ...

    @runtime_checkable
    class ModEvidenceSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_artifact_retention_seconds(self) -> t.PositiveInt:
            """Structural member projected from the owning model.

            Age after which an artifact no published evidence references is removed;
            longer than any route that can still publish it.
            """
            ...

    @runtime_checkable
    class GateAdmissionSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def capacity_normal(self) -> t.PositiveInt:
            """Concurrent heavy gates admitted at normal pressure."""
            ...

        @property
        def capacity_high(self) -> t.PositiveInt:
            """Concurrent heavy gates admitted under host pressure."""
            ...

        @property
        def heartbeat_seconds(self) -> t.PositiveInt:
            """Interval at which a live ticket refreshes itself."""
            ...

        @property
        def ttl_seconds(self) -> t.PositiveInt:
            """Heartbeat age after which a held ticket is reclaimed."""
            ...

        @property
        def poll_seconds(self) -> t.PositiveInt:
            """Interval between admission decisions of a waiter."""
            ...

        @property
        def generation(self) -> FlextInfraProtocolsConfigStatic.RouteBudgetSpec:
            """Budget of codegen generate after admission."""
            ...

        @property
        def modification(self) -> FlextInfraProtocolsConfigStatic.RouteBudgetSpec:
            """Budget of refactor mod after admission."""
            ...

        @property
        def repeat(self) -> FlextInfraProtocolsConfigStatic.GateRepeatSpec:
            """Repeat limit of the full-weight forms."""
            ...

    @runtime_checkable
    class ConsolidationOutcome(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def found(self) -> int:
            """Canonical matches found in the file."""
            ...

        @property
        def lines(self) -> tuple[str, ...]:
            """Report lines for the file."""
            ...

        @property
        def record(self) -> t.JsonMapping | None:
            """Applied-change record; none outside application."""
            ...

        @property
        def applied(self) -> int:
            """Replacements applied to the file."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigStatic",
]
