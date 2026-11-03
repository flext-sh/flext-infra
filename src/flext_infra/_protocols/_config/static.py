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
    from flext_infra import t


class FlextInfraProtocolsConfigStatic:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SourceScanSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Ordered production source directory names."""
            ...

    @runtime_checkable
    class MutationLockSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def wait_deadline_seconds(self) -> t.PositiveFloat:
            """Longest wait before failing with the last holder."""
            ...

        @property
        def poll_interval_seconds(self) -> t.PositiveFloat:
            """Interval between read-only lock availability polls."""
            ...

        @property
        def report_interval_seconds(self) -> t.PositiveFloat:
            """Interval between progress lines naming the holder."""
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
