"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_cli import p


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    @runtime_checkable
    class WorkspaceLoopOutcome(Protocol):
        """Public structural view of the workspace gate loop outcome."""

        results: tuple[p.Infra.ProjectResult, ...]
        failed: int
        skipped: int
        total_elapsed: float


__all__: list[str] = ["FlextInfraProtocolsCheck"]
