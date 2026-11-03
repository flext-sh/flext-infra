# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/worktree
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t


class FlextInfraProtocolsWorktree:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class LintSnapshot(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool(self) -> t.NonEmptyStr:
            """Canonical tool name."""
            ...

        @property
        def exit_code(self) -> int:
            """Tool process exit code."""
            ...

        @property
        def errors(self) -> t.NonNegativeInt:
            """Detected error count."""
            ...

        @property
        def warnings(self) -> t.NonNegativeInt:
            """Detected warning count."""
            ...

        @property
        def output(self) -> str:
            """Combined captured tool output."""
            ...

    @runtime_checkable
    class RepositoryDelta(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> t.NonEmptyStr:
            """Repository path relative to the repository root."""
            ...

        @property
        def source_root(self) -> Path:
            """Original repository worktree root."""
            ...

        @property
        def worktree_root(self) -> Path:
            """Temporary repository worktree root."""
            ...

        @property
        def checkpoint_sha(self) -> t.NonEmptyStr:
            """Synthetic dirty-state checkpoint SHA."""
            ...

        @property
        def changed_files(self) -> Sequence[str]:
            """Files changed by the isolated command."""
            ...

        @property
        def patch(self) -> bytes:
            """Binary Git patch relative to the checkpoint."""
            ...

    @runtime_checkable
    class RepositoryWorktree(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> t.NonEmptyStr:
            """Repository path relative to the repository root."""
            ...

        @property
        def source_root(self) -> Path:
            """Original repository worktree root."""
            ...

        @property
        def worktree_root(self) -> Path:
            """Temporary detached repository worktree root."""
            ...

        @property
        def checkpoint_sha(self) -> t.NonEmptyStr:
            """Current isolated checkpoint SHA."""
            ...

    @runtime_checkable
    class WorktreeFactsPolicy(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool_internal(self) -> Sequence[str]:
            """Path fragments classifying tool-internal worktrees."""
            ...

        @property
        def deps_dirs(self) -> Sequence[str]:
            """Rebuildable dependency directories inside a worktree."""
            ...

    @runtime_checkable
    class WorktreeFactsQuery(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_roots(self) -> tuple[Path, ...]:
            """Repository roots whose registry is scanned."""
            ...

        @property
        def policy(self) -> FlextInfraProtocolsWorktree.WorktreeFactsPolicy:
            """Layout and dependency vocabulary to apply."""
            ...

        @property
        def now(self) -> float:
            """Current epoch seconds."""
            ...

        @property
        def activity_window_days(self) -> int:
            """Staleness window in days."""
            ...

        @property
        def bead_rows(self) -> tuple[t.JsonMapping, ...]:
            """Optional bead rows for correlation."""
            ...

        @property
        def actor_evidence(self) -> Mapping[str, tuple[str, str]] | None:
            """Optional worktree-path to (actor, session) evidence."""
            ...

    @runtime_checkable
    class WorktreeCandidate(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Worktree checkout root."""
            ...

        @property
        def repo(self) -> Path:
            """Owning repository root."""
            ...

        @property
        def branch(self) -> str:
            """HEAD-derived branch."""
            ...

    @runtime_checkable
    class WorktreeFact(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Worktree directory name."""
            ...

        @property
        def path(self) -> Path:
            """Worktree checkout root."""
            ...

        @property
        def repo(self) -> Path:
            """Owning repository root."""
            ...

        @property
        def kind(self) -> Literal["sibling", "tool_internal"]:
            """Layout kind of the registered worktree."""
            ...

        @property
        def bytes(self) -> t.NonNegativeInt:
            """Total tree bytes."""
            ...

        @property
        def deps_bytes(self) -> t.NonNegativeInt:
            """Rebuildable deps bytes."""
            ...

        @property
        def stale_days(self) -> float:
            """Days since the newest mtime."""
            ...

        @property
        def exact(self) -> bool:
            """Whether the measurement hit no bound."""
            ...

        @property
        def branch(self) -> str:
            """HEAD-derived branch."""
            ...

        @property
        def bead(self) -> str:
            """Correlated bead id."""
            ...

        @property
        def pr_number(self) -> int | None:
            """Correlated pull request number."""
            ...

        @property
        def actor(self) -> str:
            """Last known actor."""
            ...

        @property
        def session_id(self) -> str:
            """Attributed session id."""
            ...

        @property
        def retire_candidate(self) -> bool:
            """Retirement candidate; execution never happens here."""
            ...

    @runtime_checkable
    class PruneAction(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(
            self,
        ) -> Literal[
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
        ]:
            """Mutation strategy for the subject path."""
            ...

        @property
        def path(self) -> Path:
            """Mutation subject."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Why the action is planned."""
            ...

        @property
        def owner(self) -> t.NonEmptyStr:
            """Owning surface."""
            ...

        @property
        def reclaim_bytes(self) -> t.NonNegativeInt:
            """Bytes the action reclaims."""
            ...

    @runtime_checkable
    class PrunePlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def generated_at(self) -> datetime:
            """UTC plan instant."""
            ...

        @property
        def mode(self) -> str:
            """Detected execution mode."""
            ...

        @property
        def apply(self) -> bool:
            """Whether this plan will execute."""
            ...

        @property
        def actions(self) -> tuple[FlextInfraProtocolsWorktree.PruneAction, ...]:
            """Planned actions in stable order."""
            ...

        @property
        def total_reclaim_bytes(self) -> t.NonNegativeInt:
            """Total bytes the plan reclaims."""
            ...

    @runtime_checkable
    class WorktreesReport(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def facts(self) -> tuple[FlextInfraProtocolsWorktree.WorktreeFact, ...]:
            """Every measured registered worktree."""
            ...

        @property
        def plan(self) -> FlextInfraProtocolsWorktree.PrunePlan | None:
            """Planned stale-deps pruning, when any."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsWorktree",
]
