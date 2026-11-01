"""Canonical Git worktree composition for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitWorktreeCheckpoint,
    FlextInfraUtilitiesGitWorktreeDiscovery,
    FlextInfraUtilitiesGitWorktreeFacts,
    FlextInfraUtilitiesGitWorktreeMaterialization,
    FlextInfraUtilitiesGitWorktreePatch,
    FlextInfraUtilitiesGitWorktreeRemoval,
    FlextInfraUtilitiesGitWorktreeRoots,
)


class FlextInfraUtilitiesGitWorktree(
    FlextInfraUtilitiesGitWorktreeCheckpoint,
    FlextInfraUtilitiesGitWorktreeDiscovery,
    FlextInfraUtilitiesGitWorktreeFacts,
    FlextInfraUtilitiesGitWorktreeMaterialization,
    FlextInfraUtilitiesGitWorktreePatch,
    FlextInfraUtilitiesGitWorktreeRemoval,
    FlextInfraUtilitiesGitWorktreeRoots,
):
    """Compose worktree discovery, materialization, checkpoint, patch, and removal."""


__all__: list[str] = ["FlextInfraUtilitiesGitWorktree"]
