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
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsWorktree:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class LintSnapshot(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool(self) -> t.NonEmptyStr: ...
        @property
        def exit_code(self) -> int: ...
        @property
        def errors(self) -> t.NonNegativeInt: ...
        @property
        def warnings(self) -> t.NonNegativeInt: ...
        @property
        def output(self) -> str: ...

    @runtime_checkable
    class RepositoryDelta(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> t.NonEmptyStr: ...
        @property
        def source_root(self) -> Path: ...
        @property
        def worktree_root(self) -> Path: ...
        @property
        def checkpoint_sha(self) -> t.NonEmptyStr: ...
        @property
        def changed_files(self) -> Sequence[str]: ...
        @property
        def patch(self) -> bytes: ...

    @runtime_checkable
    class RepositoryWorktree(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> t.NonEmptyStr: ...
        @property
        def source_root(self) -> Path: ...
        @property
        def worktree_root(self) -> Path: ...
        @property
        def checkpoint_sha(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class WorktreeFactsPolicy(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool_internal(self) -> Sequence[str]: ...
        @property
        def deps_dirs(self) -> Sequence[str]: ...

    @runtime_checkable
    class WorktreeFactsQuery(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_roots(self) -> tuple[Path, ...]: ...
        @property
        def policy(self) -> p.Infra.WorktreeFactsPolicy: ...
        @property
        def now(self) -> float: ...
        @property
        def activity_window_days(self) -> int: ...
        @property
        def bead_rows(self) -> tuple[t.JsonMapping, ...]: ...
        @property
        def actor_evidence(self) -> Mapping[str, tuple[str, str]] | None: ...

    @runtime_checkable
    class WorktreeCandidate(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def repo(self) -> Path: ...
        @property
        def branch(self) -> str: ...

    @runtime_checkable
    class WorktreeFact(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> Path: ...
        @property
        def repo(self) -> Path: ...
        @property
        def kind(self) -> Literal["sibling", "tool_internal"]: ...
        @property
        def bytes(self) -> t.NonNegativeInt: ...
        @property
        def deps_bytes(self) -> t.NonNegativeInt: ...
        @property
        def stale_days(self) -> float: ...
        @property
        def exact(self) -> bool: ...
        @property
        def branch(self) -> str: ...
        @property
        def bead(self) -> str: ...
        @property
        def pr_number(self) -> int | None: ...
        @property
        def actor(self) -> str: ...
        @property
        def session_id(self) -> str: ...
        @property
        def retire_candidate(self) -> bool: ...

    @runtime_checkable
    class PruneAction(Protocol):
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
        ]: ...
        @property
        def path(self) -> Path: ...
        @property
        def reason(self) -> t.NonEmptyStr: ...
        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def reclaim_bytes(self) -> t.NonNegativeInt: ...

    @runtime_checkable
    class PrunePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def generated_at(self) -> datetime: ...
        @property
        def mode(self) -> str: ...
        @property
        def apply(self) -> bool: ...
        @property
        def actions(self) -> tuple[p.Infra.PruneAction, ...]: ...
        @property
        def total_reclaim_bytes(self) -> t.NonNegativeInt: ...

    @runtime_checkable
    class WorktreesReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def facts(self) -> tuple[p.Infra.WorktreeFact, ...]: ...
        @property
        def plan(self) -> p.Infra.PrunePlan | None: ...


__all__: list[str] = [
    "FlextInfraProtocolsWorktree",
]
