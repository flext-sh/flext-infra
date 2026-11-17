"""Attached-repository worktree topology behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, tm, u


class TestsFlextInfraAttachedRepositoryWorktree(u.Tests.WorktreeFixture):
    """Exercise Git's primary registry for an attached repository."""

    def test_attached_submodule_lane_cannot_prove_a_storage_only_primary(
        self,
        tmp_path: Path,
    ) -> None:
        """A lane of an attached member derives from the member's own primary root.

        The lane is registered natively at the canonical path derived from the
        member's own primary root. Listing from this linked lane cannot prove
        the storage-only primary row without ``core.worktree``, and the lane
        stays in place.
        """
        child_source = tmp_path / "child-source"
        child_source.mkdir()
        (child_source / "README.md").write_text("child\n", encoding="utf-8")
        (child_source / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "child"\nversion = "0.1.0"\n'
            'description = "Attached child fixture"\n',
            encoding="utf-8",
        )
        (child_source / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n"
            '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
            '\t@printf "setting up %s\\n" "$(WORKSPACE)"\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(child_source)
        super_root = tmp_path / "super"
        super_root.mkdir()
        superproject = self._repository(super_root)
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(child_source),
                    "attached",
                ],
                cwd=superproject,
            ),
        )
        attached = superproject / "attached"
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "--unset", "core.worktree"],
                cwd=attached,
            ),
        )
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=attached),
                ),
            ).primary_root,
            eq=attached.resolve(),
        )
        linked = tmp_path / "attached-linked"
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", "--detach", str(linked), "HEAD"],
                cwd=attached,
            ),
        )
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=linked),
                ),
            ).primary_root,
            eq=linked.resolve(),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "remove", "--force", str(linked)],
                cwd=linked,
            ),
        )
        expected_lane = self.native_lane(attached, "feature/attached")
        tm.that(
            f"{c.Infra.WORKTREES_DIRNAME}/{c.Infra.WORKTREES_DIRNAME}"
            not in expected_lane.as_posix(),
            eq=True,
        )
        tm.fail(
            u.Infra.git_list_worktrees(
                m.Infra.GitRepoRequest(repo_root=expected_lane),
            ),
            has="primary checkout is unproven for storage-only registry row",
        )
        tm.ok(expected_lane.is_dir())
