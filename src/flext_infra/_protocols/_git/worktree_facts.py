# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class FlextInfraProtocolsGitWorktreeFacts:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class GitTreeStats(Protocol):
        """Structural data contract projected from the owning model."""

        total_bytes: int
        newest_mtime: float
        exact: bool


__all__: list[str] = [
    "FlextInfraProtocolsGitWorktreeFacts",
]
