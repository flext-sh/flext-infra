"""Worktree registry facts — filesystem discovery and staleness measurement."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesGitWorktreeFactsMixin:
    """Measure registered worktrees without shelling out to git.

    Discovery reads ``.git/worktrees/<id>/gitdir`` directly: the pointer file
    names the worktree's own ``.git`` entry, so the worktree root is its
    parent. Broken pointers and missing roots are skipped, never fatal.
    Consumers own retirement policy; this mixin only reports facts.
    """

    _DAY_SECONDS: float = 86400.0

    @classmethod
    def git_registered_worktrees(
        cls, repository_root: Path
    ) -> p.Result[t.VariadicTuple[t.Pair[Path, str]]]:
        """Return (root, branch) for every registered worktree, sorted by root."""
        registry = repository_root / ".git" / "worktrees"
        if not registry.is_dir():
            return r[tuple[tuple[t.Pair[Path, str], ...]]].ok(())
        resolved: list[t.Pair[Path, str]] = []
        seen: set[Path] = set()
        for entry in sorted(registry.iterdir()):
            gitdir = entry / "gitdir"
            try:
                pointer = Path(gitdir.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                continue
            worktree_root = pointer.parent
            if not worktree_root.is_dir() or worktree_root in seen:
                continue
            seen.add(worktree_root)
            branch = ""
            try:
                head = (entry / "HEAD").read_text(encoding="utf-8").strip()
            except OSError:
                head = ""
            if head.startswith("ref: refs/heads/"):
                branch = head.removeprefix("ref: refs/heads/")
            resolved.append((worktree_root, branch))
        return r[tuple[tuple[t.Pair[Path, str], ...]]].ok(tuple(resolved))

    @classmethod
    def git_collect_worktree_facts(
        cls,
        *,
        repository_root: Path,
        tool_internal: t.StrSequence,
        deps_dirs: t.StrSequence,
        activity_window_days: int,
        now: float,
        tree_stats: Callable[[Path], m.Infra.GitTreeStats],
    ) -> p.Result[m.Infra.WorktreesReport]:
        """Measure every registered worktree into one facts report.

        Classification marks a worktree ``tool_internal`` when its path sits
        under any ``tool_internal`` fragment; dependency bytes count only
        existing non-symlink ``deps_dirs`` children; staleness compares the
        newest mtime against ``now`` and the activity window. A fact is a
        retirement candidate purely when stale — executing retirement belongs
        to a consumer, never to this mixin.
        """
        registered = cls.git_registered_worktrees(repository_root)
        if registered.failure:
            return r[m.Infra.WorktreesReport].from_failure(registered)
        facts: list[m.Infra.WorktreeFact] = []
        for worktree_root, branch in registered.value:
            stats = tree_stats(worktree_root)
            deps_bytes = 0
            for deps_dir in deps_dirs:
                candidate = worktree_root / deps_dir
                if candidate.is_dir() and not candidate.is_symlink():
                    deps_bytes += tree_stats(candidate).total_bytes
            kind: str = (
                "tool_internal"
                if any(
                    str(worktree_root).endswith(internal)
                    or f"/{internal}/" in f"{worktree_root}/"
                    for internal in tool_internal
                )
                else "sibling"
            )
            stale_days = max(0.0, (now - stats.newest_mtime) / cls._DAY_SECONDS)
            stale = stale_days > activity_window_days
            facts.append(
                m.Infra.WorktreeFact(
                    name=worktree_root.name,
                    path=worktree_root,
                    repo=repository_root,
                    kind=kind,
                    bytes=stats.total_bytes,
                    deps_bytes=deps_bytes,
                    stale_days=stale_days,
                    exact=stats.exact,
                    branch=branch,
                    retire_candidate=stale,
                )
            )
        return r[m.Infra.WorktreesReport].ok(
            m.Infra.WorktreesReport(facts=tuple(facts))
        )


__all__: list[str] = ["FlextInfraUtilitiesGitWorktreeFactsMixin"]
