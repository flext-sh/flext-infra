"""Worktree child containment and removal behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService
from tests import c, p, tm, u


class TestsFlextInfraWorktreeRemoval(u.Tests.WorktreeFixture):
    """Group cohesive worktree behavior."""

    @staticmethod
    def _remove(repository: Path, branch: str) -> p.Result[str]:
        return FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()

    def test_remove_refuses_an_epic_lane_with_registered_children(
        self,
        tmp_path: Path,
    ) -> None:
        """A registered child keeps its epic lane alive until the child is gone.

        REMOVE reads the parent/child topology from Git's registry alone. Once
        the child is removed, the epic lane is removable too.
        """
        repository = self._repository(tmp_path)
        epic_branch = "feature/epic-beta"
        epic = self.native_lane(repository, epic_branch)
        child_branch = "feature/child-two"
        child = self.native_lane(repository, child_branch, epic_lane=epic)

        refused = self._remove(repository, epic_branch)

        tm.fail(refused, has="while children are registered")
        tm.fail(refused, has=str(child))
        tm.ok(self._remove(repository, child_branch))
        tm.fail(child.exists())
        tm.ok(self._remove(repository, epic_branch))
        tm.fail(epic.exists())

    def test_child_add_with_an_unregistered_epic_lane_is_refused(
        self,
        tmp_path: Path,
    ) -> None:
        """A child never materializes a container for an epic that does not exist.

        The refusal leaves no container, lane, ref, or registration.
        """
        repository = self._repository(tmp_path)
        missing = tmp_path / "no-such-epic"

        _ = self.refused_lane(
            repository,
            "feature/child-orphan",
            epic_lane=missing,
            reason="epic lane worktree does not exist",
        )

        tm.fail(missing.exists())

    def test_remove_refuses_a_dirty_lane_and_an_unregistered_branch(
        self,
        tmp_path: Path,
    ) -> None:
        """REMOVE keeps a lane that holds uncommitted bytes and needs a real lane."""
        repository = self._repository(tmp_path)
        branch = "feature/dirty"
        lane = self.native_lane(repository, branch)
        retained = lane / "retained.txt"
        retained.write_text("retained WIP\n", encoding="utf-8")

        tm.fail(self._remove(repository, branch), has="dirty worktree")
        tm.that(retained.read_text(encoding="utf-8"), eq="retained WIP\n")
        tm.fail(
            self._remove(repository, "feature/absent"),
            has="worktree branch is not registered: feature/absent",
        )
