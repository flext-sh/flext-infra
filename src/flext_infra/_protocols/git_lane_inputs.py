# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/git_lane_inputs
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsGitLaneInputs:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitLaneRef(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def oid(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitLaneViolation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> c.Infra.LaneViolationKind: ...
        @property
        def ref(self) -> t.NonEmptyStr: ...
        @property
        def detail(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GitLanePullRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def number(self) -> int: ...
        @property
        def head_ref_name(self) -> str: ...
        @property
        def updated_at(self) -> t.AwareDatetime: ...

    @runtime_checkable
    class GitLaneBeadMetadata(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def branch(self) -> str: ...
        @property
        def work_branch(self) -> str: ...
        @property
        def work_dir(self) -> str: ...
        @property
        def gc_work_dir(self) -> str: ...

    @runtime_checkable
    class GitLaneCoordinationPolicy(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def abandonment_threshold_minutes(self) -> float: ...


__all__: list[str] = [
    "FlextInfraProtocolsGitLaneInputs",
]
