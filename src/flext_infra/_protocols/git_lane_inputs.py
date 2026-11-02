# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsGitLaneInputs:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class GitLaneRef(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        oid: t.NonEmptyStr

    @runtime_checkable
    class GitLaneViolation(Protocol):
        """Structural data contract projected from the owning model."""

        kind: c.Infra.LaneViolationKind
        ref: t.NonEmptyStr
        detail: t.NonEmptyStr


__all__: list[str] = [
    "FlextInfraProtocolsGitLaneInputs",
]
