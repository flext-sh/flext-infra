"""Public u.Infra Git facet — status, ancestry, and worktree removal behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

from flext_infra import FlextInfraGitService, m
from tests import c, tm, u


class TestsFlextInfraGitFacetWorktreeStatus:
    """Exercise status, ancestry, and worktree removal on real repositories."""

    @staticmethod
    def _add_submodule(repository: Path, source: Path, name: str) -> None:
        """Add and commit ``source`` as a file-protocol submodule named ``name``."""
        _ = u.Tests.git_run(
            repository,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(source),
            name,
        )
        _ = u.Tests.git_run(repository, "commit", "-am", name)

    @staticmethod
    def _update_submodules(lane: Path) -> None:
        """Initialize every declared submodule inside the lane checkout."""
        _ = u.Tests.git_run(
            lane,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            c.MergeStrategy.UPDATE,
            "--init",
            "--recursive",
        )

    @staticmethod
    def test_repository_head_and_status_and_service(real_git_repo: Path) -> None:
        """Head, porcelain status, and FlextInfraGitService share one typed path."""
        head = u.Infra.git_repository_head(
            m.Infra.GitRepoRequest(repo_root=real_git_repo),
        )
        tm.that(head.success, truth=True)
        tm.that(head.value.oid, length=c.Infra.GIT_OID_HEX_LENGTH_SHA1)
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=real_git_repo))
        tm.that(status.success, truth=True)
        tm.that(status.value.porcelain, is_=str)
        tm.that(status.value.dirty, eq=False)
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=real_git_repo),
        )
        tm.that(primary.success, truth=True)
        tm.that(primary.value.primary_root == real_git_repo.resolve(), truth=True)
        report = FlextInfraGitService(repository_root=real_git_repo).execute()
        tm.that(report.success, truth=True)
        tm.that(report.value, is_=m.Infra.GitStatusReport)
        tm.that(report.value.repo_root == real_git_repo.resolve(), truth=True)
        tm.that(report.value.dirty, eq=False)

    @staticmethod
    def test_git_init_bare_on_non_repo_cwd(tmp_path: Path) -> None:
        """cwd-bound execute must allow git init --bare outside a worktree."""
        bare_root = tmp_path / "bare"
        bare_root.mkdir()
        init_result = u.Cli.run_checked([c.Infra.GIT, "init", "--bare"], cwd=bare_root)
        tm.that(init_result.success, truth=True)
        tm.that((bare_root / "HEAD").is_file(), truth=True)
        captured = u.Cli.capture([c.Infra.GIT, "rev-parse", "--git-dir"], cwd=bare_root)
        tm.that(captured.success, truth=True)
        tm.that(captured.value.strip() in {".", str(bare_root.resolve())}, truth=True)

    @staticmethod
    def test_service_status_reports_dirty_tree(real_git_repo: Path) -> None:
        """The status-only service flips dirty when the worktree changes."""
        clean = tm.ok(FlextInfraGitService(repository_root=real_git_repo).execute())
        tm.that(clean.dirty, eq=False)
        (real_git_repo / "dirty.txt").write_text("x", encoding="utf-8")
        dirty = tm.ok(FlextInfraGitService(repository_root=real_git_repo).execute())
        tm.that(dirty.dirty, eq=True)
        tm.that(dirty.porcelain, has="dirty.txt")

    @staticmethod
    def test_git_changed_paths_reports_tracked_and_untracked_files(
        real_git_repo: Path,
    ) -> None:
        """The public Git facade returns the complete existing worktree delta."""
        readme = real_git_repo / "README.md"
        readme.write_text("changed\n", encoding="utf-8")
        created = real_git_repo / "created.py"
        created.write_text("VALUE = 1\n", encoding="utf-8")

        changed = tm.ok(
            u.Infra.git_changed_paths(m.Infra.GitRepoRequest(repo_root=real_git_repo)),
        )

        tm.that(set(changed), eq={readme.resolve(), created.resolve()})

    @staticmethod
    def test_status_classifies_registered_nested_worktrees_as_administrative(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        container = repository / ".worktrees"
        first = container / "first"
        second = container / "second"
        container.mkdir()
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "branch", "first"], cwd=repository))
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "branch", "second"], cwd=repository))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", str(first), "first"],
                cwd=repository,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", str(second), "second"],
                cwd=repository,
            ),
        )
        clean = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        tm.that(clean.dirty, eq=False)
        (repository / "rogue.txt").write_text("rogue", encoding="utf-8")
        rogue = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        tm.that(rogue.dirty, eq=True)
        (repository / "rogue.txt").unlink()
        (container / "rogue.txt").write_text("rogue", encoding="utf-8")
        nested_rogue = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        tm.that(nested_rogue.dirty, eq=True)
        (container / "rogue.txt").unlink()
        (repository / "README.md").write_text("changed", encoding="utf-8")
        tracked = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        tm.that(tracked.dirty, eq=True)
        (repository / "README.md").write_text("# Test Repository\n", encoding="utf-8")
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "remove", str(second)],
                cwd=repository,
            ),
        )
        second.mkdir(parents=True)
        (second / "stale.txt").write_text("stale", encoding="utf-8")
        stale = tm.ok(
            u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=repository)),
        )
        tm.that(stale.dirty, eq=True)

    @staticmethod
    def test_missing_git_binary_fails_closed(tmp_path: Path) -> None:
        """Missing git on PATH must Result.fail without raising."""
        empty_path = tmp_path / "empty-path"
        empty_path.mkdir()
        with tm.scope(env={"PATH": str(empty_path)}):
            result = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=tmp_path))
        tm.that(result.failure, truth=True)
        tm.that(tm.not_none(result.error), has="git executable not found")

    @staticmethod
    def test_refresh_binary_reports_the_resolved_executable() -> None:
        """The public facet refreshes the Git binary it will then use."""
        refreshed = u.Infra.refresh_binary()
        tm.ok(refreshed)
        tm.ok(refreshed.value)

    def test_remove_clean_worktree_refuses_missing_lifecycle_proof(
        self,
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        source = u.Tests.git_repository(tmp_path, "member-source")
        self._add_submodule(repository, source, "member")
        lane = u.Tests.git_linked_lane(tmp_path, repository, "fixture-lane")
        self._update_submodules(lane)
        gitmodules = (repository / ".gitmodules").read_text(encoding="utf-8")
        gitlink = tm.ok(
            u.Cli.capture(
                (c.Infra.GIT, "ls-files", "--stage", "member"),
                cwd=repository,
            ),
        )
        configured = tm.ok(
            u.Cli.capture(
                (c.Infra.GIT, "config", "--get", "submodule.member.url"),
                cwd=repository,
            ),
        )

        u.Tests.git_run(repository, "fetch", "--quiet", "origin")

        tm.fail(
            u.Infra.git_remove_clean_worktree(repository, lane),
            has="retirement refused",
        )

        tm.that(lane.is_dir(), truth=True)
        tm.that((repository / "member").is_dir(), truth=True)
        tm.that(
            (repository / ".gitmodules").read_text(encoding="utf-8") == gitmodules,
            truth=True,
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    (c.Infra.GIT, "ls-files", "--stage", "member"), cwd=repository
                )
            ),
            eq=gitlink,
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    (c.Infra.GIT, "config", "--get", "submodule.member.url"),
                    cwd=repository,
                )
            ),
            eq=configured,
        )

    def test_remove_clean_worktree_refuses_dirty_nested_submodule(
        self,
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        nested_source = u.Tests.git_repository(tmp_path, "nested-source")
        member_source = u.Tests.git_repository(tmp_path, "member-source")
        self._add_submodule(member_source, nested_source, "nested")
        self._add_submodule(repository, member_source, "member")
        lane = u.Tests.git_linked_lane(tmp_path, repository, "dirty-lane")
        self._update_submodules(lane)
        (lane / "member" / "nested" / "dirty.txt").write_text(
            "dirty\n",
            encoding="utf-8",
        )

        result = u.Infra.git_remove_clean_worktree(repository, lane)

        tm.fail(result, has="dirty nested submodule")
        tm.that(lane.is_dir(), truth=True)

    @staticmethod
    def test_remove_clean_worktree_refuses_locked_worktree(
        tmp_path: Path,
    ) -> None:
        repository = u.Tests.git_repository(tmp_path)
        lane = u.Tests.git_linked_lane(tmp_path, repository, "locked-lane")
        _ = u.Tests.git_run(repository, "worktree", "lock", str(lane))

        result = u.Infra.git_remove_clean_worktree(repository, lane)

        tm.fail(result, has="locked worktree")
        tm.that(lane.is_dir(), truth=True)

    @staticmethod
    def test_is_ancestor_proves_any_pair_and_defaults_to_head(
        tmp_path: Path,
    ) -> None:
        """One owner proves ancestry for a pair and for the HEAD-bound case."""
        repository = u.Tests.git_repository(tmp_path)
        base = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=repository)),
        ).oid
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "switch", "-c", "topic"],
                cwd=repository,
            ),
        )
        (repository / "topic.txt").write_text("topic\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", "topic.txt"], cwd=repository))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "topic"],
                cwd=repository,
            ),
        )
        topic = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=repository)),
        ).oid

        ancestor = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(
                    repo_root=repository,
                    ancestor=base,
                    descendant=topic,
                ),
            ),
        )
        reverse = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(
                    repo_root=repository,
                    ancestor=topic,
                    descendant=base,
                ),
            ),
        )
        defaulted = tm.ok(
            u.Infra.git_is_ancestor(
                m.Infra.GitAncestryRequest(repo_root=repository, ancestor=base),
            ),
        )

        tm.ok(ancestor.value)
        tm.fail(reverse.value)
        tm.ok(defaulted.value)

    @staticmethod
    def test_is_ancestor_fails_on_unknown_commitish(tmp_path: Path) -> None:
        """An unresolvable side is a failure, never a silent negative."""
        repository = u.Tests.git_repository(tmp_path)

        result = u.Infra.git_is_ancestor(
            m.Infra.GitAncestryRequest(
                repo_root=repository,
                ancestor="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            ),
        )

        tm.that(result.failure, truth=True)
        tm.that(result.error, none=False)

    @staticmethod
    def test_has_staged_changes_tracks_the_index(tmp_path: Path) -> None:
        """The staged probe distinguishes a staged delta from a clean index."""
        repository = u.Tests.git_repository(tmp_path)
        request = m.Infra.GitRepoRequest(repo_root=repository)

        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        (repository / "staged.txt").write_text("staged\n", encoding="utf-8")
        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        tm.ok(
            u.Cli.run_checked([c.Infra.GIT, "add", "staged.txt"], cwd=repository),
        )
        tm.ok(tm.ok(u.Infra.git_has_staged_changes(request)).value)

        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "staged"],
                cwd=repository,
            ),
        )
        tm.fail(tm.ok(u.Infra.git_has_staged_changes(request)).value)
