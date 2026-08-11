"""Canonical Git responsibility mixin for ``u.Infra``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from git import GitCommandError

from flext_core import r
from flext_infra._utilities._git.worktree_patch import (
    FlextInfraUtilitiesGitWorktreePatchMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesGitWorktreeRemovalMixin(
    FlextInfraUtilitiesGitWorktreePatchMixin
):
    """Own worktree removal operations."""

    @classmethod
    def git_remove_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove one explicitly selected temporary worktree and prune metadata."""
        try:
            repo = cls._repo(source_root)
            repo.git.worktree("remove", "--force", str(worktree_root))
            repo.git.worktree("prune")
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to remove worktree: {exc}")
        return r[bool].ok(True)

    @classmethod
    def git_remove_clean_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove an explicitly selected clean worktree and prune metadata."""
        try:
            repo = cls._repo(source_root)
            repo.git.worktree("remove", str(worktree_root))
            repo.git.worktree("prune")
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to remove clean worktree: {exc}")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesGitWorktreeRemovalMixin"]
