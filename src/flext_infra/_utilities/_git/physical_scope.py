"""Physical Git ownership shared by cold bootstrap and typed mutation APIs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from git import Repo
from git.repo.fun import is_git_dir

from flext_infra import c


class FlextInfraUtilitiesGitPhysicalScope:
    """Elect one physical worktree or marker-free file scope without model imports."""

    @staticmethod
    def scope_paths(root: Path) -> tuple[Path, Path | None]:
        """Authenticate the declared scope and its nearest Git storage directory.

        Returns:
            The physical scope root and its Git directory when one is declared.

        Raises:
            ValueError: A marker is invalid or the root belongs to Git storage.

        """
        resolved = root.resolve(strict=True)
        if not resolved.is_dir():
            message = f"mutation scope is not a physical directory: {root}"
            raise ValueError(message)
        for candidate in (resolved, *resolved.parents):
            marker = candidate / c.Infra.GIT_DIR
            if marker.exists() or marker.is_symlink():
                with Repo(candidate, search_parent_directories=False) as repo:
                    if (
                        repo.bare
                        or repo.working_tree_dir is None
                        or Path(repo.working_tree_dir).resolve() != candidate
                    ):
                        message = (
                            "declared Git marker does not own this worktree: "
                            f"{candidate}"
                        )
                        raise ValueError(message)
                    return resolved, Path(repo.git_dir).resolve()
            if is_git_dir(candidate):
                message = (
                    "mutation scope belongs to Git storage rather than a "
                    f"worktree: {root}"
                )
                raise ValueError(message)
        return resolved, None

    @classmethod
    def lock_path(cls, root: Path) -> Path:
        """Derive the canonical lock from the same authenticated physical scope.

        Returns:
            The shared mutation lock inside Git storage or the scope state owner.

        """
        scope_root, git_dir = cls.scope_paths(root)
        directory = (
            git_dir
            if git_dir is not None
            else scope_root / c.Infra.TRANSACTION_STATE_DIRNAME
        )
        return directory / c.Infra.MUTATION_LOCK_NAME


__all__: list[str] = ["FlextInfraUtilitiesGitPhysicalScope"]
