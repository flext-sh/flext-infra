# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable


class FlextInfraProtocolsGitWorktreeState:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class GitMutationScope(Protocol):
        """Structural data contract projected from the owning model."""

        root: Path
        git_dir: Path | None

    @runtime_checkable
    class MutationLockHolder(Protocol):
        """Structural data contract projected from the owning model."""

        pid: int
        operation: str
        root: Path
        acquired_at: datetime
        released_at: datetime | None

    @runtime_checkable
    class GitWorktreeCheckpointPublication(Protocol):
        """Structural data contract projected from the owning model."""

        remote_name: str
        remote_url: str
        checkpoint_ref: str
        checkpoint_oid: str

    @runtime_checkable
    class GitWorktreeStateRequest(Protocol):
        """Structural data contract projected from the owning model."""

        retained_commits: tuple[str, ...] = ...
        repo_root: Path
        paths: tuple[Path, ...]

    @runtime_checkable
    class GitWorktreeIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        mode: str
        oid: str

    @runtime_checkable
    class GitIndexFileState(Protocol):
        """Structural data contract projected from the owning model."""

        entry: FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry | None
        content: bytes | None

    @runtime_checkable
    class GitIndexRetirementRequest(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        entry: FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry

    @runtime_checkable
    class GitWorktreeObservedFile(Protocol):
        """Structural data contract projected from the owning model."""

        content: bytes | None
        mode: str
        permissions: int

    @runtime_checkable
    class GitWorktreeFileState(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        mode: str
        permissions: int
        oid: str

    @runtime_checkable
    class GitWorktreeObservedContent(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        content: bytes | None
        mode: str
        permissions: int

    @runtime_checkable
    class GitWorktreeStateSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        retained_commits: tuple[str, ...] = ...
        head_entries: tuple[FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry, ...]
        repo_root: Path
        common_dir: Path
        head: str
        branch: str | None
        paths: tuple[Path, ...]
        index_entries: tuple[
            FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry, ...
        ]
        files: tuple[FlextInfraModelsGitWorktreeState.GitWorktreeFileState, ...]

    @runtime_checkable
    class GitWorktreeStateCheckpoint(Protocol):
        """Structural data contract projected from the owning model."""

        snapshot: FlextInfraModelsGitWorktreeState.GitWorktreeStateSnapshot
        checkpoint_ref: str
        index_commit: str
        worktree_commit: str

    @runtime_checkable
    class GitLaneOwnershipReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        checkpoint: FlextInfraModelsGitWorktreeState.GitWorktreeStateCheckpoint
        publication: FlextInfraModelsGitWorktreeState.GitWorktreeCheckpointPublication


__all__: list[str] = [
    "FlextInfraProtocolsGitWorktreeState",
]
