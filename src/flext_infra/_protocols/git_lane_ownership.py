# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/git_lane_ownership
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsGitLaneInputs


class FlextInfraProtocolsGitLaneOwnership:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitLaneBead(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str:
            """Canonical Bead identifier."""
            ...

        @property
        def status(self) -> str:
            """Current Bead lifecycle status."""
            ...

        @property
        def assignee(self) -> str | None:
            """Claimed execution owner."""
            ...

        @property
        def updated_at(self) -> t.AwareDatetime:
            """Latest Bead activity."""
            ...

        @property
        def metadata(
            self,
        ) -> FlextInfraProtocolsGitLaneInputs.GitLaneBeadMetadata | None:
            """Explicit branch/worktree ownership correlation."""
            ...

    @runtime_checkable
    class GitLaneGovernance(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def coordination(
            self,
        ) -> FlextInfraProtocolsGitLaneInputs.GitLaneCoordinationPolicy:
            """Global coordination policy."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGitLaneOwnership",
]
