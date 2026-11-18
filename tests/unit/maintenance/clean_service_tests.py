"""Public behavior tests for disposable-artifact cleanup.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.maintenance import FlextInfraMaintenanceClean
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCleanService:
    """Validate cleanup through its public service contract."""

    @staticmethod
    def test_apply_removes_broken_managed_worktree_links(tmp_path: Path) -> None:
        """A failed test lane cannot leave a dangling workspace entry."""
        worktrees = tmp_path / c.Infra.WORKTREES_DIRNAME
        worktrees.mkdir()
        broken = worktrees / "broken-lane"
        broken.symlink_to(tmp_path / "missing-lane", target_is_directory=True)

        result = FlextInfraMaintenanceClean(
            repository_root=tmp_path,
            apply_changes=True,
        ).execute()

        tm.ok(result.success)
        tm.fail(broken.is_symlink())

    @staticmethod
    def test_apply_removes_member_disposables(tmp_path: Path) -> None:
        """The selector-free verb covers every declared member, not only the root."""
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(tmp_path)
        cache = config.Infra.codegen.make.clean.cache_dirs[0]
        (tmp_path / cache).mkdir()
        (member / cache).mkdir()

        result = FlextInfraMaintenanceClean(
            repository_root=tmp_path,
            apply_changes=True,
        ).execute()

        tm.ok(result.success)
        tm.fail((tmp_path / cache).exists())
        tm.fail((member / cache).exists())
