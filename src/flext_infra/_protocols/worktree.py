# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsWorktree:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class LintSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        tool: t.NonEmptyStr
        exit_code: int
        errors: t.NonNegativeInt = ...
        warnings: t.NonNegativeInt = ...
        output: str = ...

    @runtime_checkable
    class RepositoryDelta(Protocol):
        """Structural data contract projected from the owning model."""

        relative_path: t.NonEmptyStr
        source_root: Path
        worktree_root: Path
        checkpoint_sha: t.NonEmptyStr
        changed_files: Sequence[str] = ...
        patch: bytes = ...

    @runtime_checkable
    class RepositoryWorktree(Protocol):
        """Structural data contract projected from the owning model."""

        relative_path: t.NonEmptyStr
        source_root: Path
        worktree_root: Path
        checkpoint_sha: t.NonEmptyStr

    @runtime_checkable
    class WorktreeFactsPolicy(Protocol):
        """Structural data contract projected from the owning model."""

        tool_internal: Sequence[str] = ...
        deps_dirs: Sequence[str] = ...

    @runtime_checkable
    class WorktreeFactsQuery(Protocol):
        """Structural data contract projected from the owning model."""

        repo_roots: tuple[Path, ...]
        policy: FlextInfraProtocolsWorktree.WorktreeFactsPolicy
        now: float
        activity_window_days: int
        bead_rows: tuple[t.JsonMapping, ...] = ...
        actor_evidence: Mapping[str, tuple[str, str]] | None = ...

    @runtime_checkable
    class WorktreeCandidate(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        repo: Path
        branch: str = ...

    @runtime_checkable
    class WorktreeFact(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        path: Path
        repo: Path
        kind: Literal["sibling", "tool_internal"]
        bytes: t.NonNegativeInt = ...
        deps_bytes: t.NonNegativeInt = ...
        stale_days: float = ...
        exact: bool = ...
        branch: str = ...
        bead: str = ...
        pr_number: int | None = ...
        actor: str = ...
        session_id: str = ...
        retire_candidate: bool = ...

    @runtime_checkable
    class PruneAction(Protocol):
        """Structural data contract projected from the owning model."""

        kind: Literal[
            "cache-expire",
            "cache-lru",
            "log-truncate",
            "tmp-expire",
            "trash-empty",
            "quarantine-expire",
            "junk-remove",
            "dir-move",
            "file-move",
            "dir-remove",
            "contents-remove",
        ]
        path: Path
        reason: t.NonEmptyStr
        owner: t.NonEmptyStr
        reclaim_bytes: t.NonNegativeInt = ...

    @runtime_checkable
    class PrunePlan(Protocol):
        """Structural data contract projected from the owning model."""

        generated_at: datetime
        mode: str
        apply: bool
        actions: tuple[FlextInfraProtocolsWorktree.PruneAction, ...] = ...
        total_reclaim_bytes: t.NonNegativeInt = ...

    @runtime_checkable
    class WorktreesReport(Protocol):
        """Structural data contract projected from the owning model."""

        facts: tuple[FlextInfraProtocolsWorktree.WorktreeFact, ...] = ...
        plan: FlextInfraProtocolsWorktree.PrunePlan | None = ...


__all__: list[str] = [
    "FlextInfraProtocolsWorktree",
]
