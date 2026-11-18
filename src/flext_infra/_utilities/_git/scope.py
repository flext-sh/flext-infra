"""Git-aware scope resolution mixin for the private git facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import configparser
import threading
from collections.abc import MutableMapping, Sequence
from pathlib import Path

from git import GitCommandError, Repo, Submodule

from flext_infra import c, m
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitRepo,
    FlextInfraUtilitiesGitSemanticIdentity,
)


class FlextInfraUtilitiesGitScope(FlextInfraUtilitiesGitRepo):
    """Static helpers for resolving tracked files and directories within Git scopes."""

    class ScopeFacts:
        """One invocation's Git scope facts, read from Git once and shared.

        The composition root of a read-only invocation builds one instance and
        injects it as ``p.Infra.GitScopeFacts``; every consumer then shares each
        repository's worktree root and tracked inventory. The instance holds no
        fact beyond the invocation that owns it.
        """

        def __init__(self) -> None:
            """Start with no fact read; each one is read on first request."""
            self._lock = threading.Lock()
            self._repo_roots: MutableMapping[str, str | None] = {}
            self._repo_paths: MutableMapping[str, Sequence[str]] = {}
            self._scopes: MutableMapping[str, Sequence[str] | None] = {}

        def tracked_scope_relative_paths(
            self,
            scope_root: Path,
        ) -> Sequence[str] | None:
            """Return tracked scope-relative paths, read once per scope.

            Returns:
                Tracked paths relative to ``scope_root`` or ``None`` outside Git.

            """
            scope = str(scope_root.resolve())
            mixin = FlextInfraUtilitiesGitScope
            with self._lock:
                if scope in self._scopes:
                    return self._scopes[scope]
                if scope not in self._repo_roots:
                    self._repo_roots[scope] = mixin.git_repo_root(scope)
                repo_root = self._repo_roots[scope]
                scoped: Sequence[str] | None = None
                if repo_root is not None:
                    if repo_root not in self._repo_paths:
                        self._repo_paths[repo_root] = (
                            mixin.git_tracked_repo_relative_paths(repo_root)
                        )
                    scoped = mixin.scope_relative_paths(
                        scope,
                        repo_root,
                        self._repo_paths[repo_root],
                    )
                self._scopes[scope] = scoped
                return scoped

    @classmethod
    def git_repo_root(cls, scope_root: str) -> str | None:
        """Return the enclosing Git worktree root, or ``None`` outside any worktree.

        Only the canonical three-way work-tree probe may classify a path as
        outside Git; a genuine probe or open failure raises instead of being
        reported as absence. Git is a required dependency of this scope probe;
        unavailable executables must fail rather than hide tracked-file scope.

        Returns:
            The enclosing Git worktree root, or ``None`` outside any worktree.

        Raises:
            OSError: If ``probed.failure``; or if ``opened.failure``.
            RuntimeError: If opened Git repository has no worktree.

        """
        resolved_scope = Path(scope_root).resolve()
        probe = FlextInfraUtilitiesGitSemanticIdentity.git_is_inside_work_tree
        probed = probe(m.Infra.GitRepoRequest(repo_root=resolved_scope))
        if probed.failure:
            raise OSError(probed.error or "failed to probe Git work tree")
        if not probed.value.value:
            return None
        opened = cls._open_repo(resolved_scope)
        if opened.failure:
            raise OSError(opened.error or "failed to open git repository")
        working_tree_dir = opened.value.working_tree_dir
        if working_tree_dir is None:
            msg = f"opened Git repository has no worktree: {scope_root}"
            raise RuntimeError(msg)
        return str(Path(working_tree_dir).resolve())

    @classmethod
    def git_binding_issues(cls, workspace_root: Path) -> tuple[m.Infra.Issue, ...]:
        """Report gitlink and member-head inconsistencies of a superproject.

        Returns:
            One issue per inconsistent or stale binding edge, in declaration order.

        Raises:
            OSError: The superproject repository cannot be opened.

        """
        descriptors = workspace_root / c.Infra.GITMODULES_FILENAME
        if not descriptors.is_file():
            return ()
        declared = configparser.ConfigParser()
        declared.read(descriptors, encoding="utf-8")
        members = tuple(
            path
            for section in declared.sections()
            if (path := declared.get(section, "path", fallback=""))
        )
        if not members:
            return ()
        opened = cls._open_repo(workspace_root)
        if opened.failure:
            raise OSError(opened.error or "failed to open the superproject")
        repository = opened.value
        if not repository.head.is_valid():
            return ()
        branch = None if repository.head.is_detached else repository.active_branch.name
        pinned_tree = repository.head.commit.tree
        issues: list[m.Infra.Issue] = []
        for member in members:
            entry = pinned_tree[member]
            if not isinstance(entry, Submodule):
                issues.append(
                    cls._binding_issue(
                        member,
                        "unresolved",
                        "the recorded gitlink is absent from HEAD",
                    )
                )
                continue
            member_open = cls._open_repo(workspace_root / member)
            if member_open.failure:
                issues.append(
                    cls._binding_issue(
                        member,
                        "unresolved",
                        "the member repository cannot be opened",
                    )
                )
                continue
            state, detail, severity = cls._binding_state(
                member_open.value, entry.hexsha, branch
            )
            if state == "consistent":
                continue
            issues.append(cls._binding_issue(member, state, detail, severity))
        return tuple(issues)

    @staticmethod
    def _binding_state(
        member: Repo,
        pinned: str,
        branch: str | None,
    ) -> tuple[str, str, str]:
        """Classify one binding edge into its repair state, detail and severity.

        Returns:
            The state name, the SHA detail and the severity owning its repair.

        """
        observed = member.head.commit.hexsha if member.head.is_valid() else ""
        name = f"origin/{branch}" if branch else ""
        tip = (
            member.refs[name].commit.hexsha
            if name and name in member.refs
            else "unavailable"
        )
        detail = f"gitlink {pinned} member {observed or 'unavailable'} tip {tip}"
        if observed and observed != pinned:
            try:
                member.git.merge_base("--is-ancestor", pinned, observed)
            except GitCommandError:
                return "member-behind", detail, c.Infra.GateSeverity.ERROR
            return "member-ahead", detail, c.Infra.GateSeverity.ERROR
        if tip not in {"unavailable", pinned}:
            return "pin-stale", detail, c.Infra.GateSeverity.WARNING
        if member.index.diff(None) or member.untracked_files:
            return "dirty-unpinned", detail, c.Infra.GateSeverity.WARNING
        return "consistent", detail, c.Infra.GateSeverity.WARNING

    @staticmethod
    def _binding_issue(
        member: str,
        state: str,
        detail: str,
        severity: str = c.Infra.GateSeverity.ERROR,
    ) -> m.Infra.Issue:
        """Build the issue that names one binding edge and its repair route.

        Returns:
            The typed issue carrying the exact SHAs.

        """
        return m.Infra.Issue(
            file=member,
            line=0,
            column=0,
            code=state,
            message=detail,
            severity=severity,
        )

    @classmethod
    def git_tracked_repo_relative_paths(cls, repo_root: str) -> Sequence[str]:
        """Return literal index and dirty paths, preserving every filename byte.

        Porcelain v1 with NUL termination disables filename quoting. Disabling
        rename detection yields one path per record, including both sides of
        a rename as independent deletion/addition entries. Native Git errors
        escape instead of returning an incomplete inventory.

        Returns:
            Literal index and dirty paths, preserving every filename byte.

        """
        resolved_root = Path(repo_root).resolve()
        repo = cls._repo(resolved_root)
        tracked_output = repo.git.ls_files("-z", strip_newline_in_stdout=False)
        status_output = repo.git.status(
            "--porcelain=v1",
            "-z",
            "--no-renames",
            "--untracked-files=no",
            strip_newline_in_stdout=False,
        )
        # Tracked authority = index plus dirty tracked paths. Porcelain `??`
        # records are untracked and never enter the inventory; a git-ignored
        # scope may still carry force-staged tracked files, so check_ignore
        # must never veto the union.
        scope_paths = {path for path in tracked_output.split("\0") if path}
        scope_paths.update(
            record[3:]
            for record in status_output.split("\0")
            if record and not record.startswith("??")
        )
        return tuple(sorted(scope_paths))

    @staticmethod
    def scope_relative_paths(
        scope_root: str,
        repo_root: str,
        repo_relative_paths: Sequence[str],
    ) -> Sequence[str]:
        """Project repository-relative tracked paths onto one scope.

        The Git index and porcelain status identify paths relative to the
        repository root. Callers join the result onto ``scope_root``, so this
        function strips the scope's path components. Returned paths remain
        literal and scope-relative.

        Returns:
            The tracked paths under ``scope_root``, relative to it.

        """
        scope_prefix = Path(scope_root).resolve().relative_to(Path(repo_root).resolve())
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
    def _git_tracked_scope_relative_paths(cls, scope_root: str) -> Sequence[str] | None:
        """Return tracked paths relative to ``scope_root``; ``None`` outside Git.

        The index and status union is the sole tracked authority: a git-ignored
        scope directory may still carry force-staged tracked files, so
        check_ignore must never veto the result.

        Returns:
            Current tracked paths relative to ``scope_root`` or ``None`` outside Git.

        """
        repo_root = cls.git_repo_root(scope_root)
        if repo_root is None:
            return None
        return cls.scope_relative_paths(
            scope_root,
            repo_root,
            cls.git_tracked_repo_relative_paths(repo_root),
        )

    @classmethod
    def git_source_scope_paths(cls, scope_root: Path) -> tuple[Path, ...] | None:
        """Inventory tracked and unpublished source paths without following links.

        Args:
            scope_root: The root path of the scope to inventory.

        Returns:
            A tuple of tracked and unpublished source paths under the scope, or ``None``
              if Git is inactive.

        """
        root = cls.git_repo_root(str(scope_root))
        if root is None:
            return None
        repository = Path(root)
        output = cls._repo(repository).git.ls_files(
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            strip_newline_in_stdout=False,
        )
        scope = scope_root.resolve()
        if not scope.is_relative_to(repository):
            return ()
        # The scope prefix is decided once on Git's literal repository-relative
        # text; only paths inside it are materialized and stat-ed.
        prefix = scope.relative_to(repository).as_posix()
        inside = "" if prefix == "." else prefix + "/"
        selected: set[Path] = set()
        for path in output.split("\0"):
            if not path or not (path.startswith(inside) or path == inside[:-1]):
                continue
            candidate = repository / path
            if candidate.is_file() or candidate.is_symlink():
                selected.add(candidate)
        return tuple(sorted(selected))

    @classmethod
    def git_tracked_scope_paths(cls, scope_root: Path) -> Sequence[Path] | None:
        """Return tracked files under one scope as absolute paths when Git is active.

        Returns:
            Tracked files under one scope as absolute paths when Git is active.

        """
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
        """Return tracked top-level directory names under one scope when Git is active.

        Returns:
            Tracked top-level directory names under one scope when Git is active.

        """
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(scope_root.resolve()),
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
        repository_root: Path,
        project_root: Path,
    ) -> bool:
        """Return whether one candidate project has a tracked descriptor file.

        Returns:
            Whether one candidate project has a tracked descriptor file.

        """
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(repository_root.resolve()),
        )
        if relative_paths is None:
            return True
        tracked_paths = frozenset(relative_paths)
        resolved_workspace = repository_root.resolve()
        resolved_project = project_root.resolve()
        relative_prefix = ""
        if resolved_project != resolved_workspace:
            relative_prefix = (
                resolved_project.relative_to(resolved_workspace).as_posix() + "/"
            )
        tracked_gitlink = relative_prefix.removesuffix("/")
        if tracked_gitlink and tracked_gitlink in tracked_paths:
            return True
        return f"{relative_prefix}{c.PYPROJECT_FILENAME}" in tracked_paths


__all__: list[str] = ["FlextInfraUtilitiesGitScope"]
