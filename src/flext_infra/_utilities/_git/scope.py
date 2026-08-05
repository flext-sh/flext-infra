"""Git-aware scope resolution mixin for the private git facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra._utilities._git.repo import git_repo
from flext_infra._utilities._git.semantic import FlextInfraUtilitiesGitSemanticMixin
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesGitScopeMixin(FlextInfraUtilitiesGitSemanticMixin):
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
            repo = git_repo(resolved_root)
            tracked_output = repo.git.ls_files(with_exceptions=False)
            status_output = repo.git.status(
                "--porcelain", "--untracked-files=all", with_exceptions=False
            )
        except (OSError, ValueError):
            return None
        scope_paths: set[str] = set()
        for raw_line in tracked_output.splitlines():
            normalized = raw_line.strip()
            if normalized:
                scope_paths.add(normalized)
        # Preserve prior Cli-era behavior: status failure yields empty porcelain.
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
        repo_root_text = FlextInfraUtilitiesGitScopeMixin._git_repo_root(scope_root)
        if repo_root_text is None:
            return None
        repo_relative_paths = (
            FlextInfraUtilitiesGitScopeMixin._git_tracked_repo_relative_paths(
                repo_root_text
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
    def git_tracked_top_level_dir_names(cls, scope_root: Path) -> frozenset[str] | None:
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
        cls, workspace_root: Path, project_root: Path
    ) -> bool:
        """Return whether one candidate project has a tracked descriptor file."""
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(workspace_root.resolve())
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
        return f"{relative_prefix}{c.Infra.PYPROJECT_FILENAME}" in tracked_paths


__all__: list[str] = ["FlextInfraUtilitiesGitScopeMixin"]
