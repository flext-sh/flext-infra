"""GitPython repository helpers for the private git facet.

Only ``git_refresh_binary``, ``git_open_repo``, and ``git_repo`` live here.
Semantic operations use GitPython's object-oriented API (``Repo``, ``IndexFile``,
``Remote``, ``BaseIndexEntry``) or the ``repo.git.<cmd>(args)`` proxy directly;
``Git(path).execute(tuple)`` with manual cast/protocol is eliminated.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from git import (
    Git,
    GitCommandNotFound,
    InvalidGitRepositoryError,
    NoSuchPathError,
    Repo,
)

from flext_core import r
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra import p


def git_refresh_binary() -> p.Result[bool]:
    """Point GitPython at the absolute path of the canonical git binary."""
    # Git.refresh resolves relative names against cwd; always pass an absolute path.
    resolved = shutil.which(c.Infra.GIT)
    if resolved is None:
        return r[bool].fail(f"git executable not found on PATH: {c.Infra.GIT}")
    try:
        Git.refresh(resolved)
    except (FileNotFoundError, OSError) as exc:
        return r[bool].fail(f"git binary refresh failed: {exc}")
    return r[bool].ok(True)


def git_open_repo(repo_root: Path) -> p.Result[Repo]:
    """Open one non-bare worktree repository at ``repo_root``."""
    resolved = repo_root.expanduser().resolve()
    try:
        refreshed = git_refresh_binary()
        if refreshed.failure:
            return r[Repo].fail(refreshed.error or "git binary unavailable")
        repo = Repo(resolved)
    except (
        GitCommandNotFound,
        ImportError,
        InvalidGitRepositoryError,
        NoSuchPathError,
        OSError,
        ValueError,
    ) as exc:
        return r[Repo].fail(f"cannot open git repository at {resolved}: {exc}")
    # A submodule checkout stores its gitdir under the superproject
    # (.git/modules/<name>) and declares the worktree through core.worktree.
    # GitPython reads that config but does not apply it, so Repo() reports the
    # submodule as bare with working_tree_dir=None. Resolve the declared
    # worktree before rejecting the repository.
    if repo.bare or repo.working_tree_dir is None:
        declared_worktree = repo.config_reader().get_value("core", "worktree", "")
        if not declared_worktree:
            return r[Repo].fail(f"bare or worktree-less repository at {resolved}")
        worktree_path = Path(str(declared_worktree))
        if not worktree_path.is_absolute():
            worktree_path = (Path(repo.common_dir) / worktree_path).resolve()
        if not worktree_path.is_dir():
            return r[Repo].fail(f"bare or worktree-less repository at {resolved}")
    return r[Repo].ok(repo)


def git_repo(repo_root: Path) -> Repo:
    """Open a repo and unwrap, raising on failure.

    This is the canonical helper for semantic methods that prefer
    try/except → ``r[...].fail()`` over ``Result`` chaining.
    """
    opened = git_open_repo(repo_root)
    if opened.failure:
        raise OSError(opened.error or "failed to open git repository")
    return opened.value


class FlextInfraUtilitiesGitRepo:
    """Base for the typed Git owner mixins: shared GitPython open helpers."""

    @classmethod
    def _repo(cls, repo_root: Path) -> Repo:
        """Open one non-bare worktree repository, raising on failure."""
        return git_repo(repo_root)

    @classmethod
    def _open_repo(cls, repo_root: Path) -> p.Result[Repo]:
        """Open one non-bare worktree repository as a ``Result``."""
        return git_open_repo(repo_root)


__all__: list[str] = [
    "FlextInfraUtilitiesGitRepo",
    "git_open_repo",
    "git_refresh_binary",
    "git_repo",
]
