"""Host-wide heavy-gate admission records (FLEXT ADR-032).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal

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

    class GateRunRecord(m.ContractModel):
        """Latest recorded run of one gate and selection.

        ``status`` defaults to ``success`` so existing repeat-ledger entries
        (which only ever recorded successes) stay valid.
        """

        gate: Annotated[t.NonEmptyStr, m.Field(description="Gate that was run")]
        status: Annotated[
            Literal["success", "failure"],
            m.Field(description="Outcome of the run"),
        ] = "success"
        selection: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="LAWS/RULES selection; empty when unselected"),
        ] = ()
        repository: Annotated[
            t.NonEmptyStr, m.Field(description="Checkout root the run acted on")
        ]
        admitted_at: Annotated[
            t.AwareDatetime, m.Field(description="Admission time of the run")
        ]
        finished_at: Annotated[
            t.AwareDatetime, m.Field(description="Time the run finished")
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
