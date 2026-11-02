# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/static
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsConfigStatic:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SourceScanSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class MutationLockSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def wait_deadline_seconds(self) -> t.PositiveFloat: ...
        @property
        def poll_interval_seconds(self) -> t.PositiveFloat: ...
        @property
        def report_interval_seconds(self) -> t.PositiveFloat: ...

    @runtime_checkable
    class ConsolidationOutcome(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def found(self) -> int: ...
        @property
        def lines(self) -> tuple[str, ...]: ...
        @property
        def record(self) -> t.JsonMapping | None: ...
        @property
        def applied(self) -> int: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigStatic",
]
