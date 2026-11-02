# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_git/worktree_facts
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class FlextInfraProtocolsGitWorktreeFacts:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitTreeStats(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def total_bytes(self) -> int: ...
        @property
        def newest_mtime(self) -> float: ...
        @property
        def exact(self) -> bool: ...


__all__: list[str] = [
    "FlextInfraProtocolsGitWorktreeFacts",
]
