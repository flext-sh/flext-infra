"""Worktree path and namespace behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorktreeService
from tests import c, m, u


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

    def test_remove_keeps_the_isolated_lane_while_retirement_is_closed(
        self,
        tmp_path: Path,
    ) -> None:
        """REMOVE resolves the isolated lane and fails closed at retirement.

        The lane is registered natively because admission refuses every ADD
        (bead flext-itpd1.3.26). REMOVE resolves it from Git's registry and
        proves integration ancestry, then the native retirement contract
        refuses: ancestry alone never authorizes removal, so actually removing
        the checkout is unreachable until retirement admission opens.
        """
        repository = self._repository(tmp_path)
        branch = "feature/example"
        lane = self.native_lane(repository, branch)

        tm.that(lane.is_relative_to(repository), eq=False)
        tm.that(
            tm.ok(
                u.Infra.git_list_worktrees(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            ).porcelain,
            has=f"worktree {lane}",
        )

        refused = FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()

        tm.fail(refused, has="retirement refused")
        tm.that(lane.is_dir(), eq=True)

    def test_lane_path_escapes_a_dirty_outer_project_ancestor(
        self,
        tmp_path: Path,
    ) -> None:
        """The reserved lane container sits outside every project uv could discover."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / "pyproject.toml").write_text(
            '[dependency-groups]\ndescription = "dirty outer WIP"\n',
            encoding="utf-8",
        )
        nested = outer_project / "nested"
        nested.mkdir()
        repository = self._repository(nested)

        lane = self.native_lane(repository, "feature/outer-isolation")

        tm.that(lane.is_dir(), eq=True)
        tm.that(lane.is_relative_to(outer_project), eq=False)
        tm.that(
            (outer_project / "pyproject.toml").read_text(encoding="utf-8"),
            eq='[dependency-groups]\ndescription = "dirty outer WIP"\n',
        )

    def test_same_named_repositories_use_distinct_lane_namespaces(
        self,
        tmp_path: Path,
    ) -> None:
        """Repository names never collide inside one outer lane container."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / "pyproject.toml").write_text(
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
        tm.that(first_lane != second_lane, eq=True)
        tm.that(first_lane.parent.parent != second_lane.parent.parent, eq=True)
