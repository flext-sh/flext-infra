"""Source discovery specification models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config import FlextInfraModelsConfigContract


class FlextInfraModelsConfigStatic:
    """Source discovery specification models."""

    class RopePreferencesSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Native source-engine policy validated by the SDK's own vocabulary."""

        preferred_import_style: t.Infra.RopeNativeImportStyle = m.Field(
            description="Native import form used by identity-preserving refactors"
        )

    class SourceScanSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Canonical production roots and recursively ignored directories."""

        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Ordered production source directory names"),
        ]

    class MutationLockSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Concurrent-writer reconciliation for one mutation scope."""

        reconcile_attempts: Annotated[
            t.NonNegativeInt,
            m.Field(description="Replans after another writer changed a destination"),
        ]

    class RouteBudgetSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Wall-time budget one heavy route arms after it is admitted."""

        budget_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Wall time from admission to forced termination"),
        ]
        grace_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Graceful termination reserve inside the budget"),
        ]

        @m.model_validator(mode="after")
        def require_grace_inside_budget(self) -> Self:
            """Keep the termination reserve strictly inside the budget.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If the grace reserve does not fit in the budget.

            """
            if self.grace_seconds >= self.budget_seconds:
                msg = "grace_seconds must be less than budget_seconds"
                raise ValueError(msg)
            return self

    class GateAdmissionSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Host-wide FIFO admission for heavy gates (FLEXT ADR-032)."""

        capacity_normal: Annotated[
            t.PositiveInt,
            m.Field(description="Concurrent heavy gates admitted at normal pressure"),
        ]
        capacity_high: Annotated[
            t.PositiveInt,
            m.Field(description="Concurrent heavy gates admitted under host pressure"),
        ]
        heartbeat_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Interval at which a live ticket refreshes itself"),
        ]
        ttl_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Heartbeat age after which a held ticket is reclaimed"),
        ]
        poll_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Interval between admission decisions of a waiter"),
        ]
        generation: Annotated[
            FlextInfraModelsConfigStatic.RouteBudgetSpec,
            m.Field(description="Budget of codegen generate after admission"),
        ]
        modification: Annotated[
            FlextInfraModelsConfigStatic.RouteBudgetSpec,
            m.Field(description="Budget of refactor mod after admission"),
        ]

        @m.model_validator(mode="after")
        def require_bounded_admission(self) -> Self:
            """Keep pressure capacity and reclaim timing coherent.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If pressure capacity exceeds normal capacity or the
                    TTL does not exceed the heartbeat interval.

            """
            if self.capacity_high > self.capacity_normal:
                msg = "capacity_high must not exceed capacity_normal"
                raise ValueError(msg)
            if self.ttl_seconds <= self.heartbeat_seconds:
                msg = "ttl_seconds must exceed heartbeat_seconds"
                raise ValueError(msg)
            return self

    class ConsolidationOutcome(FlextInfraModelsConfigContract.ConfigContract):
        """Per-file constants consolidation outcome."""

        found: Annotated[
            int, m.Field(description="Canonical matches found in the file")
        ]
        lines: Annotated[
            tuple[str, ...], m.Field(description="Report lines for the file")
        ]
        record: Annotated[
            t.JsonMapping | None,
            m.Field(description="Applied-change record; none outside application"),
        ]
        applied: Annotated[int, m.Field(description="Replacements applied to the file")]


__all__: list[str] = ["FlextInfraModelsConfigStatic"]
