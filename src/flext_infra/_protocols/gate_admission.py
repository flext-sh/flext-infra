# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/gate_admission
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsGateAdmission:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GateTicket(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def sequence(self) -> t.PositiveInt:
            """Monotonic FIFO position."""
            ...

        @property
        def pid(self) -> t.PositiveInt:
            """Ticket owner process."""
            ...

        @property
        def gate(self) -> t.NonEmptyStr:
            """Admitted gate name."""
            ...

        @property
        def repository(self) -> t.NonEmptyStr:
            """Repository the gate acts on."""
            ...

        @property
        def enqueued_at(self) -> t.AwareDatetime:
            """Time the ticket joined the queue."""
            ...

        @property
        def admitted_at(self) -> t.AwareDatetime | None:
            """Admission time; none while waiting."""
            ...

        @property
        def heartbeat_at(self) -> t.AwareDatetime:
            """Last liveness refresh by the owner."""
            ...

    @runtime_checkable
    class HostPressureSnapshot(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def level(self) -> c.Infra.HostPressureLevel:
            """Measured host memory-pressure level."""
            ...

        @property
        def observed_at(self) -> t.AwareDatetime:
            """Measurement time."""
            ...

        @property
        def valid_seconds(self) -> t.PositiveInt:
            """Seconds after observed_at the level stays valid."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGateAdmission",
]
