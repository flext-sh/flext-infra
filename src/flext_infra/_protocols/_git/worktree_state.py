# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_git/worktree_state
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols


class FlextInfraProtocolsGitWorktreeState:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitMutationScope(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Physical requested mutation root."""
            ...

        @property
        def git_dir(self) -> Path | None:
            """Validated worktree Git directory, absent only for file scopes."""
            ...

    @runtime_checkable
    class MutationLockHolder(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pid(self) -> int:
            """Process that holds the lock."""
            ...

        @property
        def operation(self) -> str:
            """Operation the holder runs under the lock."""
            ...

        @property
        def root(self) -> Path:
            """Mutation root the holder writes."""
            ...

        @property
        def acquired_at(self) -> datetime:
            """UTC instant the lock was acquired."""
            ...

        @property
        def released_at(self) -> datetime | None:
            """UTC instant the holder released; none while held."""
            ...

    @runtime_checkable
    class GitWorktreeCheckpointPublication(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def remote_name(self) -> str:
            """Configured remote used for publication."""
            ...

        @property
        def remote_url(self) -> str:
            """Exact verified credential-free fetch and push URL."""
            ...

        @property
        def checkpoint_ref(self) -> str:
            """Published dedicated checkpoint reference."""
            ...

        @property
        def checkpoint_oid(self) -> str:
            """Exact advertised checkpoint commit."""
            ...

    @runtime_checkable
    class GitWorktreeStateRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def retained_commits(self) -> tuple[str, ...]:
            """Additional child commits referenced by owning gitlinks."""
            ...

        @property
        def repo_root(self) -> Path:
            """Source repository worktree root."""
            ...

        @property
        def paths(self) -> tuple[Path, ...]:
            """Literal owned relative paths; empty selects nothing."""
            ...

    @runtime_checkable
    class GitWorktreeIndexEntry(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Repository-relative index path."""
            ...

        @property
        def mode(self) -> str:
            """Git octal index entry mode."""
            ...

        @property
        def oid(self) -> str:
            """Index blob or gitlink object identifier."""
            ...

    @runtime_checkable
    class GitIndexFileState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entry(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeIndexEntry | None:
            """Stage-zero entry, absent for an untracked file."""
            ...

        @property
        def content(self) -> bytes | None:
            """Bytes of the captured index blob."""
            ...

    @runtime_checkable
    class GitIndexRetirementRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Exact owning repository."""
            ...

        @property
        def entry(self) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeIndexEntry:
            """Required immutable preimage of the index entry."""
            ...

    @runtime_checkable
    class GitWorktreeObservedFile(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def content(self) -> bytes | None:
            """Raw working bytes; link text for symlinks, None when absent."""
            ...

        @property
        def mode(self) -> str:
            """Git mode for raw bytes or symlink."""
            ...

        @property
        def permissions(self) -> int:
            """Exact filesystem permission bits."""
            ...

    @runtime_checkable
    class GitWorktreeFileState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Repository-relative working path."""
            ...

        @property
        def mode(self) -> str:
            """Git mode for raw bytes, symlink or gitlink."""
            ...

        @property
        def permissions(self) -> int:
            """Exact filesystem permission bits; zero for gitlinks."""
            ...

        @property
        def oid(self) -> str:
            """Object identifier for raw bytes or current gitlink HEAD."""
            ...

    @runtime_checkable
    class GitWorktreeObservedContent(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Repository-relative working path."""
            ...

        @property
        def content(self) -> bytes | None:
            """Observed working bytes; absent means no file."""
            ...

        @property
        def mode(self) -> str:
            """Git mode the observed bytes classify as."""
            ...

        @property
        def permissions(self) -> int:
            """Exact filesystem permission bits of the observation."""
            ...

    @runtime_checkable
    class GitWorktreeStateSnapshot(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def retained_commits(self) -> tuple[str, ...]:
            """Additional resolved commits retained by checkpoint ancestry."""
            ...

        @property
        def head_entries(
            self,
        ) -> tuple[FlextInfraProtocolsGitWorktreeState.GitWorktreeIndexEntry, ...]:
            """Original HEAD entries including deleted gitlink preimages."""
            ...

        @property
        def repo_root(self) -> Path:
            """Original source worktree root."""
            ...

        @property
        def common_dir(self) -> Path:
            """Shared Git object storage identity."""
            ...

        @property
        def head(self) -> str:
            """Original HEAD commit object identifier."""
            ...

        @property
        def branch(self) -> str | None:
            """Original native branch; absent for detached HEAD."""
            ...

        @property
        def paths(self) -> tuple[Path, ...]:
            """Exact literal ownership scope."""
            ...

        @property
        def index_entries(
            self,
        ) -> tuple[FlextInfraProtocolsGitWorktreeState.GitWorktreeIndexEntry, ...]:
            """Captured stage-zero index entries."""
            ...

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsGitWorktreeState.GitWorktreeFileState, ...]:
            """Captured raw working files and gitlink heads."""
            ...

    @runtime_checkable
    class GitWorktreeStateCheckpoint(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def snapshot(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeStateSnapshot:
            """Original immutable ownership and state evidence."""
            ...

        @property
        def checkpoint_ref(self) -> str:
            """Durable dedicated Git reference."""
            ...

        @property
        def index_commit(self) -> str:
            """Reachable commit retaining the original index tree."""
            ...

        @property
        def worktree_commit(self) -> str:
            """Structural member projected from the owning model.

            Reachable commit retaining raw working bytes and snapshot metadata.
            """
            ...

    @runtime_checkable
    class GitLaneOwnershipReceipt(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checkpoint(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeStateCheckpoint:
            """Full-repository capture identifying the prior owned branch."""
            ...

        @property
        def publication(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeCheckpointPublication:
            """Live independently retained checkpoint publication."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGitWorktreeState",
]
