"""Worktree registry facts: filesystem discovery and staleness measurement."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import m, u

if TYPE_CHECKING:
    from pathlib import Path

_TOOL_INTERNAL = (".claude/worktrees",)
_DEPS_DIRS = (".venv", "node_modules")
_WINDOW_DAYS = 90


def _stats(path: Path) -> m.Infra.GitTreeStats:
    total = 0
    newest = 0.0
    for candidate in path.rglob("*"):
        if candidate.is_file():
            stat = candidate.stat()
            total += stat.st_size
            newest = max(newest, stat.st_mtime)
    return m.Infra.GitTreeStats(total_bytes=total, newest_mtime=newest, exact=True)


def _collect(tmp_path: Path, now: float) -> m.Infra.WorktreesReport:
    result = u.Infra.git_collect_worktree_facts(
        repository_root=tmp_path,
        tool_internal=_TOOL_INTERNAL,
        deps_dirs=_DEPS_DIRS,
        activity_window_days=_WINDOW_DAYS,
        now=now,
        tree_stats=_stats,
    )
    tm.ok(result)
    return result.value


def _register(repository_root: Path, name: str, worktree_root: Path) -> None:
    registry = repository_root / ".git" / "worktrees" / name
    registry.mkdir(parents=True, exist_ok=True)
    (worktree_root / ".git").write_text(
        f"gitdir: {registry}/gitdir\n", encoding="utf-8"
    )
    (registry / "gitdir").write_text(f"{worktree_root / '.git'}\n", encoding="utf-8")
    (registry / "HEAD").write_text("ref: refs/heads/0.12.0-dev\n", encoding="utf-8")


class TestsGitWorktreeFacts:
    """Registry facts mirror the governed consumer's measurement contract."""

    def test_no_registry_reports_empty(self, tmp_path: Path) -> None:
        """A repository without registered worktrees yields an empty report."""
        report = _collect(tmp_path, now=1_800_000_000.0)
        tm.that(report.facts, eq=())

    def test_sibling_and_tool_internal_classified(self, tmp_path: Path) -> None:
        """Paths under tool-internal fragments classify as tool_internal."""
        sibling = tmp_path.parent / f"{tmp_path.name}-worktrees" / "lane"
        internal = tmp_path / ".claude" / "worktrees" / "agent-x"
        sibling.mkdir(parents=True)
        internal.mkdir(parents=True)
        _register(tmp_path, "lane", sibling)
        _register(tmp_path, "agent-x", internal)

        report = _collect(tmp_path, now=1_800_000_000.0)
        kinds = {fact.name: fact.kind for fact in report.facts}
        tm.that(kinds["lane"], eq="sibling")
        tm.that(kinds["agent-x"], eq="tool_internal")

    def test_stale_worktree_flags_retire_candidate_and_deps_bytes(
        self, tmp_path: Path
    ) -> None:
        """Staleness beyond the window flags retirement; deps bytes measured."""
        stale = tmp_path / ".claude" / "worktrees" / "stale"
        (stale / ".venv" / "lib").mkdir(parents=True)
        (stale / ".venv" / "lib" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (stale / "keep.py").write_text("y = 2\n", encoding="utf-8")
        _register(tmp_path, "stale", stale)
        old = 1_800_000_000.0 - 120 * 86400
        for candidate in stale.rglob("*"):
            os.utime(candidate, (old, old))

        report = _collect(tmp_path, now=1_800_000_000.0)
        fact = report.facts[0]
        tm.that(fact.retire_candidate, eq=True)
        tm.that(fact.stale_days > _WINDOW_DAYS, eq=True)
        tm.that(fact.deps_bytes > 0, eq=True)

    def test_fresh_worktree_is_not_retire_candidate(self, tmp_path: Path) -> None:
        """A recently-touched worktree never flags retirement."""
        fresh = tmp_path / ".claude" / "worktrees" / "fresh"
        fresh.mkdir(parents=True)
        _register(tmp_path, "fresh", fresh)
        recent = 1_800_000_000.0 - 86400
        for candidate in fresh.rglob("*"):
            os.utime(candidate, (recent, recent))

        report = _collect(tmp_path, now=1_800_000_000.0)
        tm.that(report.facts[0].retire_candidate, eq=False)

    def test_same_worktree_registered_twice_is_deduped(self, tmp_path: Path) -> None:
        """Duplicate registry entries for one root yield a single fact."""
        worktree = tmp_path / ".claude" / "worktrees" / "twin"
        worktree.mkdir(parents=True)
        _register(tmp_path, "twin-a", worktree)
        _register(tmp_path, "twin-b", worktree)

        report = _collect(tmp_path, now=1_800_000_000.0)
        tm.that(len(report.facts), eq=1)

    def test_broken_gitdir_is_skipped(self, tmp_path: Path) -> None:
        """A registry pointer at a nonexistent root is skipped, never fatal."""
        broken = tmp_path / ".git" / "worktrees" / "broken"
        broken.mkdir(parents=True)
        (broken / "gitdir").write_text("/nonexistent/wt/.git\n", encoding="utf-8")

        report = _collect(tmp_path, now=1_800_000_000.0)
        tm.that(report.facts, eq=())


__all__: list[str] = ["TestsGitWorktreeFacts"]
