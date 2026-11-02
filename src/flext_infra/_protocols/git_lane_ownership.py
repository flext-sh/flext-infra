# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/git_lane_ownership
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsGitLaneOwnership:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitLaneBead(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str: ...
        @property
        def status(self) -> str: ...
        @property
        def assignee(self) -> str | None: ...
        @property
        def updated_at(self) -> t.AwareDatetime: ...
        @property
        def metadata(self) -> p.Infra.GitLaneBeadMetadata | None: ...

    @runtime_checkable
    class GitLaneGovernance(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def coordination(self) -> p.Infra.GitLaneCoordinationPolicy: ...


__all__: list[str] = [
    "FlextInfraProtocolsGitLaneOwnership",
]
