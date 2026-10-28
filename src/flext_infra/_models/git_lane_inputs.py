"""Git lane leaf declarations for strict, acyclic Pydantic schema composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import Annotated

from flext_cli import m

from flext_infra import c, t


class FlextInfraModelsGitLaneInputs:
    """Leaf declarations available before dependent Pydantic schemas are built."""

    class GitLaneRef(m.ContractModel):
        """One native reference identity, without a hygiene verdict."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Full Git reference name")]
        oid: Annotated[t.NonEmptyStr, m.Field(description="Observed reference commit")]

    class GitLaneViolation(m.ContractModel):
        """One lane accumulation offence with its preservation-first instruction."""

        kind: Annotated[
            c.Infra.LaneViolationKind,
            m.Field(description="Violation class"),
        ]
        ref: Annotated[
            t.NonEmptyStr,
            m.Field(description="Offending stash, branch, or worktree"),
        ]
        detail: Annotated[
            t.NonEmptyStr,
            m.Field(description="Preservation-first adjudication"),
        ]

    class GitLanePullRequest(m.ExternalContractModel):
        """Selected public GitHub PR fields, parsed once at ingress."""

        number: Annotated[int, m.Field(description="Open pull request number")]
        head_ref_name: Annotated[
            str,
            m.Field(alias="headRefName", description="PR source branch"),
        ]
        updated_at: Annotated[
            t.AwareDatetime,
            m.Field(alias="updatedAt", description="Latest PR activity"),
        ]

    class GitLaneBeadMetadata(m.ExternalContractModel):
        """Canonical tracker ownership fields used by worktree correlation."""

        branch: Annotated[str, m.Field(description="Declared Bead branch")] = ""
        work_branch: Annotated[
            str,
            m.Field(alias="gc.work_branch", description="Gas City branch"),
        ] = ""
        work_dir: Annotated[str, m.Field(description="Declared Bead worktree")] = ""
        gc_work_dir: Annotated[
            str,
            m.Field(alias="gc.work_dir", description="Gas City worktree"),
        ] = ""

    class GitLaneCoordinationPolicy(m.ExternalContractModel):
        """Read the abandonment threshold from global governance, not a copy."""

        abandonment_threshold_minutes: Annotated[
            float,
            m.Field(gt=0, description="Global maximum inactive lane age"),
        ]


__all__: list[str] = ["FlextInfraModelsGitLaneInputs"]
