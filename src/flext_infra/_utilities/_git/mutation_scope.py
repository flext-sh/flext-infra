"""Strict worktree versus physical file-scope classification for writers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from git import GitError

from flext_infra import m, p, r
from flext_infra._utilities._git.physical_scope import (
    FlextInfraUtilitiesGitPhysicalScope,
)


class FlextInfraUtilitiesGitMutationScope:
    """Classify absent Git ownership before opening any declared Git marker."""

    @classmethod
    def git_mutation_scope(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitMutationScope]:
        """Reject malformed declared Git roots; marker-free roots remain file scopes.

        Returns:
            The resulting ``p.Result[p.Infra.GitMutationScope]``.

        """
        try:
            root, git_dir = FlextInfraUtilitiesGitPhysicalScope.scope_paths(
                request.repo_root
            )
        except (GitError, OSError, ValueError) as exc:
            return r.fail(str(exc), exception=exc)
        return r.ok(m.Infra.GitMutationScope(root=root, git_dir=git_dir))

    @classmethod
    def mutation_lock_path(cls, root: Path) -> p.Result[Path]:
        """Locate the file-change lease shared by short writers of ``root``.

        The lease lives in Git storage, or in the state directory outside Git,
        so it never dirties the working tree. It covers one atomic file effect,
        never a whole operation: concurrent sessions plan and run gates freely.

        Returns:
            The lease path, or the scope classification failure.

        """
        try:
            lock_path = FlextInfraUtilitiesGitPhysicalScope.lock_path(root)
        except (GitError, OSError, ValueError) as exc:
            return r.fail(str(exc), exception=exc)
        return r.ok(lock_path)


__all__: list[str] = ["FlextInfraUtilitiesGitMutationScope"]
