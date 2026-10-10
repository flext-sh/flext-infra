"""Worktree child containment and removal behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorktreeService
from tests import c, p, u


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

        Epic and child are registered natively at their canonical paths
        because admission refuses every ADD (bead flext-itpd1.3.26); REMOVE
        reads the parent/child topology from Git's registry alone. Retiring the
        child itself then fails closed at the native retirement contract, so
        removing the child and then the epic is unreachable until retirement
        admission opens; both lanes stay registered on disk.
        """
        repository = self._repository(tmp_path)
        epic_branch = "feature/epic-beta"
        epic = self.native_lane(repository, epic_branch)
        child_branch = "feature/child-two"
        child = self.native_lane(repository, child_branch, epic_lane=epic)

        refused = self._remove(repository, epic_branch)

        tm.fail(refused, has="while children are registered")
        tm.fail(refused, has=str(child))
        tm.fail(self._remove(repository, child_branch), has="retirement refused")
        tm.that(child.is_dir(), eq=True)
        tm.that(epic.is_dir(), eq=True)

    def test_child_add_with_an_unregistered_epic_lane_is_refused(
        self,
        tmp_path: Path,
    ) -> None:
        """A child never materializes a container for an epic that does not exist.

        Admission refuses the ADD before the epic registry check runs (bead
        flext-itpd1.3.26), so the success path that reached that check is
        unreachable until admission opens; the fail-closed outcome is the same:
        no container, lane, ref, or registration.
        """
        repository = self._repository(tmp_path)
        missing = tmp_path / "no-such-epic"

        _ = self.refused_lane(repository, "feature/child-orphan", epic_lane=missing)

        tm.that(missing.exists(), eq=False)
