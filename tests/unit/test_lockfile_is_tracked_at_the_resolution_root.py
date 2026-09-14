"""Tests that only the fleet workspace root commits the uv lockfile.

``uv.lock`` pins the exact resolved dependency graph, and design B
(flext-62fbu) gives that truth to one owner: the fleet workspace root. A
member repository does not own a lock -- resolution happens once at the root,
and inside the workspace uv resolves the root's file no matter which member
directory the command runs from.

A member that committed one anyway carried a second, unowned copy that could
not be refreshed in place. uv keeps the revision a lock pins when it
re-resolves, so a member lock written before flext-core capped structlog kept
pinning 0.12.0rc0; CI then resolved ``structlog>=26.1.0`` against a project
declaring ``<26`` and setup failed as unsatisfiable. The ignore policy now
blocks the file for a member and keeps allowing it at the root.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c
from tests import u as test_u


class TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot:
    """The ignore policy splits the lockfile by profile, and only by profile."""

    @staticmethod
    def _is_tracked_for(profile: c.Infra.MakeProfile) -> bool:
        """Return whether git would track the lockfile under *profile*."""
        patterns = test_u.Tests.ignore_patterns_for_profile(profile)
        return test_u.Tests.is_tracked_under(
            "\n".join(patterns) + "\n", c.Infra.UV_LOCK_FILENAME
        )

    def test_workspace_root_still_commits_the_lockfile(self) -> None:
        """The one owner of dependency truth keeps its lockfile versionable."""
        tm.that(self._is_tracked_for(c.Infra.MakeProfile.WORKSPACE), eq=True)

    def test_member_repository_never_commits_a_lockfile(self) -> None:
        """A member resolves from declared metadata; a lock there is a second owner."""
        tm.that(self._is_tracked_for(c.Infra.MakeProfile.STANDALONE), eq=False)
