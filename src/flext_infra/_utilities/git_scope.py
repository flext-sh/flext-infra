"""Git-aware scope resolution helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

from flext_infra import c, t


class FlextInfraUtilitiesGitScope:
    """Static helpers for resolving tracked files and directories within Git scopes."""

    @staticmethod
    @cache
    def _git_repo_root(scope_root: str) -> str | None:
        """Return the nearest enclosing Git worktree root for ``scope_root``."""
        current = Path(scope_root).resolve()
        while True:
            if (current / ".git").exists():
                return str(current)
            parent = current.parent
            if parent == current:
                return None
            current = parent

    @staticmethod
    @cache
    def _git_tracked_repo_relative_paths(repo_root: str) -> t.StrSequence | None:
        """Return tracked and dirty paths relative to one Git repo root."""
        resolved_root = Path(repo_root).resolve()
        try:
            repo = Repo(resolved_root)
        except (InvalidGitRepositoryError, NoSuchPathError, OSError, ValueError):
            return None
        if repo.bare or repo.working_tree_dir is None:
            return None
        scope_paths: set[str] = set()
        try:
            tracked_output = repo.git.ls_files()
        except GitCommandError:
            return None
        for raw_line in tracked_output.splitlines():
            normalized = raw_line.strip()
            if normalized:
                scope_paths.add(normalized)
        try:
            status_output = repo.git.status(
                "--porcelain",
                "--untracked-files=all",
            )
        except GitCommandError:
            status_output = ""
        for raw_line in status_output.splitlines():
            if not raw_line:
                continue
            file_path = raw_line[3:]
            if " -> " in file_path:
                file_path = file_path.split(" -> ", 1)[1]
            normalized = file_path.strip()
            if normalized:
                scope_paths.add(normalized)
        return tuple(sorted(scope_paths))

    @staticmethod
    @cache
    def _git_tracked_scope_relative_paths(scope_root: str) -> t.StrSequence | None:
        """Return tracked file paths relative to ``scope_root`` or ``None`` outside Git.

        ``git ls-files <scope_prefix>`` emits paths relative to the **repo root**.
        Callers join the result back onto ``scope_root``, so this function
        strips ``scope_prefix`` from each line to keep the contract honest:
        returned paths are scope-relative, never repo-relative.
        """
        resolved_root = Path(scope_root)
        repo_root_text = FlextInfraUtilitiesGitScope._git_repo_root(scope_root)
        if repo_root_text is None:
            return None
        repo_relative_paths = (
            FlextInfraUtilitiesGitScope._git_tracked_repo_relative_paths(
                repo_root_text,
            )
        )
        if repo_relative_paths is None:
            return None
        repo_root = Path(repo_root_text).resolve()
        try:
            scope_prefix = resolved_root.resolve().relative_to(repo_root)
        except ValueError:
            return None
        prefix_parts = scope_prefix.parts
        scope_paths: set[str] = set()
        for repo_relative_text in repo_relative_paths:
            repo_relative = Path(repo_relative_text)
            if prefix_parts:
                if repo_relative.parts[: len(prefix_parts)] != prefix_parts:
                    continue
                scope_relative = Path(*repo_relative.parts[len(prefix_parts) :])
            else:
                scope_relative = repo_relative
            scope_paths.add(scope_relative.as_posix())
        return tuple(sorted(scope_paths))

    @classmethod
    def git_tracked_scope_paths(cls, scope_root: Path) -> t.SequenceOf[Path] | None:
        """Return tracked files under one scope as absolute paths when Git is active."""
        resolved_root = scope_root.resolve()
        relative_paths = cls._git_tracked_scope_relative_paths(str(resolved_root))
        if relative_paths is None:
            return None
        return [
            resolved_root / Path(relative_path)
            for relative_path in relative_paths
            if (resolved_root / Path(relative_path)).is_file()
        ]

    @classmethod
    def git_tracked_top_level_dir_names(
        cls,
        scope_root: Path,
    ) -> frozenset[str] | None:
        """Return tracked top-level directory names under one scope when Git is active."""
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(scope_root.resolve())
        )
        if relative_paths is None:
            return None
        return frozenset(
            relative.parts[0]
            for relative_path in relative_paths
            if (relative := Path(relative_path)).parts
        )

    @classmethod
    def project_descriptor_is_tracked(
        cls,
        workspace_root: Path,
        project_root: Path,
    ) -> bool:
        """Return whether one candidate project has a tracked descriptor file."""
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(workspace_root.resolve()),
        )
        if relative_paths is None:
            return True
        tracked_paths = frozenset(relative_paths)
        resolved_workspace = workspace_root.resolve()
        resolved_project = project_root.resolve()
        relative_prefix = ""
        if resolved_project != resolved_workspace:
            relative_prefix = (
                resolved_project.relative_to(resolved_workspace).as_posix() + "/"
            )
        tracked_gitlink = relative_prefix.removesuffix("/")
        if tracked_gitlink and tracked_gitlink in tracked_paths:
            return True
        return any(
            f"{relative_prefix}{filename}" in tracked_paths
            for filename in (c.Infra.PYPROJECT_FILENAME, c.Infra.GO_MOD)
        )


__all__: list[str] = ["FlextInfraUtilitiesGitScope"]
