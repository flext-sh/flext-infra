"""GitPython repository helpers for the private git facet.

Only ``FlextInfraUtilitiesGitRepo`` lives here. Semantic operations use
GitPython's object-oriented API (``Repo``, ``IndexFile``, ``Remote``,
``BaseIndexEntry``) or the ``repo.git.<cmd>(args)`` proxy directly;
``Git(path).execute(tuple)`` with manual cast/protocol is eliminated.
"""

from __future__ import annotations

import shutil
from functools import lru_cache
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
    """Point GitPython at the absolute path of the canonical git binary.

    Module-level entry point for semantic mixins that operate outside the
    ``FlextInfraUtilitiesGitRepo`` class (semantic.py, semantic_identity.py);
    the classmethod delegates here so both surfaces share one implementation.
    """
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
    """Open one non-bare worktree repository at ``repo_root`` (module facade)."""
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
    if repo.bare or repo.working_tree_dir is None:
        return r[Repo].fail(f"bare or worktree-less repository at {resolved}")
    return r[Repo].ok(repo)


def git_repo(repo_root: Path) -> Repo:
    """Open a repository and unwrap, raising on failure (module facade)."""
    opened = git_open_repo(repo_root)
    if opened.failure:
        raise OSError(opened.error or "failed to open git repository")
    return opened.value


class FlextInfraUtilitiesGitRepo:
    """Git repository opener with GitPython native OO API."""

    @classmethod
    @lru_cache(maxsize=1)
    def _refresh_binary(cls) -> p.Result[bool]:
        """Point GitPython at the absolute path of the canonical git binary."""
        return git_refresh_binary()

    @classmethod
    def _open_repo(cls, repo_root: Path) -> p.Result[Repo]:
        """Open one non-bare worktree repository at ``repo_root``."""
        return git_open_repo(repo_root)

    @classmethod
    def _repo(cls, repo_root: Path) -> Repo:
        """Open a repo and unwrap, raising on failure.

        This is the canonical helper for semantic methods that prefer
        try/except → ``r[...].fail()`` over ``Result`` chaining.
        """
        return git_repo(repo_root)


__all__: list[str] = [
    "FlextInfraUtilitiesGitRepo",
    "git_open_repo",
    "git_refresh_binary",
    "git_repo",
]
