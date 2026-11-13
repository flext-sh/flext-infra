# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols. Git package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols._git.identity import FlextInfraProtocolsGitIdentity
    from flext_infra._protocols._git.worktree_facts import (
        FlextInfraProtocolsGitWorktreeFacts,
    )
    from flext_infra._protocols._git.worktree_state import (
        FlextInfraProtocolsGitWorktreeState,
    )


__all__: tuple[str, ...] = (
    "FlextInfraProtocolsGitIdentity",
    "FlextInfraProtocolsGitWorktreeFacts",
    "FlextInfraProtocolsGitWorktreeState",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraProtocolsGitIdentity": ".identity",
        "FlextInfraProtocolsGitWorktreeFacts": ".worktree_facts",
        "FlextInfraProtocolsGitWorktreeState": ".worktree_state",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraProtocolsGitIdentity": ("GitIdentityReport",),
        "FlextInfraProtocolsGitWorktreeFacts": ("GitTreeStats",),
        "FlextInfraProtocolsGitWorktreeState": (
            "GitMutationScope",
            "GitWorktreeCheckpointPublication",
            "GitWorktreeStateRequest",
            "GitWorktreeIndexEntry",
            "GitIndexFileState",
            "GitIndexRetirementRequest",
            "GitWorktreeObservedFile",
            "GitWorktreeFileState",
            "GitWorktreeObservedContent",
            "GitWorktreeStateSnapshot",
            "GitWorktreeStateCheckpoint",
            "GitLaneOwnershipReceipt",
        ),
    },
)
