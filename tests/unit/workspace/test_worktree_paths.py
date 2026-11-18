"""Worktree path and namespace behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService
from tests import c, m, tm, u


class TestsFlextInfraWorktreePaths(u.Tests.WorktreeFixture):
    """Group cohesive worktree behavior."""

    def test_list_reports_the_primary_worktree(self, tmp_path: Path) -> None:
        """List is read-only and reports Git's canonical registry."""
        repository = self._repository(tmp_path)

        listed = tm.ok(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.LIST,
            ).execute(),
        )

        tm.that(listed, has=f"worktree {repository}")

    def test_remove_retires_the_isolated_lane(
        self,
        tmp_path: Path,
    ) -> None:
        """REMOVE resolves the isolated lane and removes its clean checkout.

        REMOVE resolves the lane from Git's registry, removes the clean
        worktree and keeps its branch; without ``apply`` it changes nothing.
        """
        repository = self._repository(tmp_path)
        branch = "feature/example"
        lane = self.native_lane(repository, branch)

        tm.fail(lane.is_relative_to(repository))
        tm.that(
            tm.ok(
                u.Infra.git_list_worktrees(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            ).porcelain,
            has=f"worktree {lane}",
        )
        tm.fail(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch=branch,
            ).execute(),
            has="worktree remove requires --apply",
        )
        tm.ok(lane.is_dir())

        removed = FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()

        tm.that(tm.ok(removed), eq=str(lane))
        tm.fail(lane.exists())
        tm.that(u.Tests.git_ref_exists(repository, f"refs/heads/{branch}"), eq=True)

    def test_add_creates_the_canonical_lane_and_refuses_a_second_one(
        self,
        tmp_path: Path,
    ) -> None:
        """ADD registers the branch at its canonical path, once, only on apply."""
        repository = self._repository(tmp_path)
        branch = "feature/added"
        lane = tm.ok(FlextInfraWorktreeService.canonical_lane_path(repository, branch))

        tm.fail(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=c.Infra.GIT_HEAD,
            ).execute(),
            has="worktree add requires --apply",
        )
        tm.fail(lane.exists())

        added = FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base=c.Infra.GIT_HEAD,
            apply_changes=True,
        ).execute()

        tm.that(tm.ok(added), eq=str(lane))
        tm.that(
            tm.ok(FlextInfraWorktreeService.registered_lane(repository, branch)),
            eq=lane,
        )
        tm.that(
            tm.ok(
                u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=lane)),
            ).oid,
            eq=tm.ok(
                u.Infra.git_repository_head(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            ).oid,
        )
        tm.fail(
            FlextInfraWorktreeService(
                repository_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=c.Infra.GIT_HEAD,
                apply_changes=True,
            ).execute(),
            has=f"worktree branch is already registered: {branch}",
        )

    def test_lane_path_escapes_a_dirty_outer_project_ancestor(
        self,
        tmp_path: Path,
    ) -> None:
        """The reserved lane container sits outside every project uv could discover."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / c.PYPROJECT_FILENAME).write_text(
            '[dependency-groups]\ndescription = "dirty outer WIP"\n',
            encoding="utf-8",
        )
        nested = outer_project / "nested"
        nested.mkdir()
        repository = self._repository(nested)

        lane = self.native_lane(repository, "feature/outer-isolation")

        tm.ok(lane.is_dir())
        tm.fail(lane.is_relative_to(outer_project))
        tm.that(
            (outer_project / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            eq='[dependency-groups]\ndescription = "dirty outer WIP"\n',
        )

    def test_same_named_repositories_use_distinct_lane_namespaces(
        self,
        tmp_path: Path,
    ) -> None:
        """Repository names never collide inside one outer lane container."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "outer"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        first_parent = outer_project / "first"
        second_parent = outer_project / "second"
        first_parent.mkdir()
        second_parent.mkdir()
        first = self._repository(first_parent)
        second = self._repository(second_parent)
        branch = "feature/same-name"

        first_lane = self.native_lane(first, branch)
        second_lane = self.native_lane(second, branch)

        tm.that(first.name, eq=second.name)
        tm.ok(first_lane != second_lane)
        tm.ok(first_lane.parent.parent != second_lane.parent.parent)
