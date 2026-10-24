"""Git lane ownership declarations composed from completed leaf schemas.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsGitLaneInputs


class FlextInfraModelsGitLaneOwnership(FlextInfraModelsGitLaneInputs):
    """Ownership schemas resolve strictly from the preceding leaf declarations."""

    class GitLaneBead(m.ExternalContractModel):
        """Selected Bead fields; no age-only abandonment classification."""

        id: Annotated[str, m.Field(description="Canonical Bead identifier")]
        status: Annotated[str, m.Field(description="Current Bead lifecycle status")]
        assignee: Annotated[
            str | None,
            m.Field(description="Claimed execution owner"),
        ] = None
        updated_at: Annotated[
            t.AwareDatetime,
            m.Field(description="Latest Bead activity"),
        ]
        metadata: Annotated[
            FlextInfraModelsGitLaneInputs.GitLaneBeadMetadata | None,
            m.Field(description="Explicit branch/worktree ownership correlation"),
        ] = None

    class GitLaneGovernance(m.ExternalContractModel):
        """Minimal typed view of the global governance SSOT."""

        coordination: Annotated[
            FlextInfraModelsGitLaneInputs.GitLaneCoordinationPolicy,
            m.Field(description="Global coordination policy"),
        ]


__all__: list[str] = ["FlextInfraModelsGitLaneOwnership"]
