# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/git_lane_inputs
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsGitLaneInputs:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitLaneRef(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Full Git reference name."""
            ...

        @property
        def oid(self) -> t.NonEmptyStr:
            """Observed reference commit."""
            ...

    @runtime_checkable
    class GitLaneViolation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> c.Infra.LaneViolationKind:
            """Violation class."""
            ...

        @property
        def ref(self) -> t.NonEmptyStr:
            """Offending stash, branch, or worktree."""
            ...

        @property
        def detail(self) -> t.NonEmptyStr:
            """Preservation-first adjudication."""
            ...

    @runtime_checkable
    class GitLanePullRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def number(self) -> int:
            """Open pull request number."""
            ...

        @property
        def head_ref_name(self) -> str:
            """PR source branch."""
            ...

        @property
        def updated_at(self) -> t.AwareDatetime:
            """Latest PR activity."""
            ...

    @runtime_checkable
    class GitLaneBeadMetadata(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> str:
            """Declared Bead branch."""
            ...

        @property
        def work_branch(self) -> str:
            """Gas City branch."""
            ...

        @property
        def work_dir(self) -> str:
            """Declared Bead worktree."""
            ...

        @property
        def gc_work_dir(self) -> str:
            """Gas City worktree."""
            ...

    @runtime_checkable
    class GitLaneCoordinationPolicy(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def abandonment_threshold_minutes(self) -> float:
            """Global maximum inactive lane age."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGitLaneInputs",
]
