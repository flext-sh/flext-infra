"""Host-wide heavy-gate admission records (FLEXT ADR-032).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import c, t


class FlextInfraModelsGateAdmission:
    """Records exchanged through the per-host heavy-gate queue."""

    class GateTicket(m.ContractModel):
        """One queued or admitted heavy gate; content is diagnostic and decisive."""

        sequence: Annotated[
            t.PositiveInt, m.Field(description="Monotonic FIFO position")
        ]
        pid: Annotated[t.PositiveInt, m.Field(description="Ticket owner process")]
        gate: Annotated[t.NonEmptyStr, m.Field(description="Admitted gate name")]
        repository: Annotated[
            t.NonEmptyStr, m.Field(description="Repository the gate acts on")
        ]
        enqueued_at: Annotated[
            t.AwareDatetime, m.Field(description="Time the ticket joined the queue")
        ]
        admitted_at: Annotated[
            t.AwareDatetime | None,
            m.Field(description="Admission time; none while waiting"),
        ] = None
        heartbeat_at: Annotated[
            t.AwareDatetime, m.Field(description="Last liveness refresh by the owner")
        ]

    class HostPressureSnapshot(m.ExternalContractModel):
        """Host-pressure level published by the host-budget owner."""

        level: Annotated[
            c.Infra.HostPressureLevel,
            m.Field(description="Measured host memory-pressure level"),
        ]
        observed_at: Annotated[t.AwareDatetime, m.Field(description="Measurement time")]
        valid_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Seconds after observed_at the level stays valid"),
        ]


__all__: list[str] = ["FlextInfraModelsGateAdmission"]
