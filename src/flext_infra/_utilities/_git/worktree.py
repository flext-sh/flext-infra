"""Canonical Git worktree composition for ``u.Infra``.

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

from flext_infra._utilities._git import FlextInfraUtilitiesGitWorktreeRemoval


class FlextInfraUtilitiesGitWorktree(FlextInfraUtilitiesGitWorktreeRemoval):
    """Compose worktree discovery, materialization, checkpoint, patch, and removal."""


__all__: list[str] = ["FlextInfraUtilitiesGitWorktree"]
