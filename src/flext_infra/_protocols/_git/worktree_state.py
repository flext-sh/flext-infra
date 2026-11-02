# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_git/worktree_state
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsGitWorktreeState:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitMutationScope(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path: ...
        @property
        def git_dir(self) -> Path | None: ...

    @runtime_checkable
    class MutationLockHolder(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pid(self) -> int: ...
        @property
        def operation(self) -> str: ...
        @property
        def root(self) -> Path: ...
        @property
        def acquired_at(self) -> datetime: ...
        @property
        def released_at(self) -> datetime | None: ...

    @runtime_checkable
    class GitWorktreeCheckpointPublication(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def remote_name(self) -> str: ...
        @property
        def remote_url(self) -> str: ...
        @property
        def checkpoint_ref(self) -> str: ...
        @property
        def checkpoint_oid(self) -> str: ...

    @runtime_checkable
    class GitWorktreeStateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def retained_commits(self) -> tuple[str, ...]: ...
        @property
        def repo_root(self) -> Path: ...
        @property
        def paths(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class GitWorktreeIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def mode(self) -> str: ...
        @property
        def oid(self) -> str: ...

    @runtime_checkable
    class GitIndexFileState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entry(self) -> p.Infra.GitWorktreeIndexEntry | None: ...
        @property
        def content(self) -> bytes | None: ...

    @runtime_checkable
    class GitIndexRetirementRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def entry(self) -> p.Infra.GitWorktreeIndexEntry: ...

    @runtime_checkable
    class GitWorktreeObservedFile(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def content(self) -> bytes | None: ...
        @property
        def mode(self) -> str: ...
        @property
        def permissions(self) -> int: ...

    @runtime_checkable
    class GitWorktreeFileState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def mode(self) -> str: ...
        @property
        def permissions(self) -> int: ...
        @property
        def oid(self) -> str: ...

    @runtime_checkable
    class GitWorktreeObservedContent(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def content(self) -> bytes | None: ...
        @property
        def mode(self) -> str: ...
        @property
        def permissions(self) -> int: ...

    @runtime_checkable
    class GitWorktreeStateSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def retained_commits(self) -> tuple[str, ...]: ...
        @property
        def head_entries(self) -> tuple[p.Infra.GitWorktreeIndexEntry, ...]: ...
        @property
        def repo_root(self) -> Path: ...
        @property
        def common_dir(self) -> Path: ...
        @property
        def head(self) -> str: ...
        @property
        def branch(self) -> str | None: ...
        @property
        def paths(self) -> tuple[Path, ...]: ...
        @property
        def index_entries(self) -> tuple[p.Infra.GitWorktreeIndexEntry, ...]: ...
        @property
        def files(self) -> tuple[p.Infra.GitWorktreeFileState, ...]: ...

    @runtime_checkable
    class GitWorktreeStateCheckpoint(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def snapshot(self) -> p.Infra.GitWorktreeStateSnapshot: ...
        @property
        def checkpoint_ref(self) -> str: ...
        @property
        def index_commit(self) -> str: ...
        @property
        def worktree_commit(self) -> str: ...

    @runtime_checkable
    class GitLaneOwnershipReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checkpoint(self) -> p.Infra.GitWorktreeStateCheckpoint: ...
        @property
        def publication(self) -> p.Infra.GitWorktreeCheckpointPublication: ...


__all__: list[str] = [
    "FlextInfraProtocolsGitWorktreeState",
]
