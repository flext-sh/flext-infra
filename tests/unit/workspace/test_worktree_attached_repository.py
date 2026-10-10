"""Attached-repository worktree topology behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorktreeService
from tests import c, m, u


class TestsFlextInfraAttachedRepositoryWorktree(u.Tests.WorktreeFixture):
    """Exercise Git's primary registry for an attached repository."""

    def test_attached_submodule_uses_one_primary_local_container(
        self,
        tmp_path: Path,
    ) -> None:
        """An attached member is its own primary and owns one lane container.

        ADD on a member whose ``.gitmodules`` entry declares no branch is
        refused by lane admission (no integration line to bind). The lane is
        therefore registered natively at the canonical path derived from the
        member's own primary root. REMOVE resolves that lane from the member's
        registry, then retirement admission, which inspects the registry from
        the lane itself, fails closed: from a linked lane Git lists the
        member's storage directory as the primary row and the primary checkout
        cannot be proven, so the lane stays on disk.
        """
        child_source = tmp_path / "child-source"
        child_source.mkdir()
        (child_source / "README.md").write_text("child\n", encoding="utf-8")
        (child_source / "pyproject.toml").write_text(
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
        branch = "feature/attached"
        # The member declares no ``.gitmodules`` branch, so lane admission has
        # no integration line for it and refuses before any lane effect.
        _ = self.refused_lane(
            attached,
            branch,
            reason="Git submodule branch is missing: attached",
        )
        expected_lane = self.native_lane(attached, branch)
        tm.that(
            f"{c.Infra.WORKTREES_DIRNAME}/{c.Infra.WORKTREES_DIRNAME}"
            not in expected_lane.as_posix(),
            eq=True,
        )
        tm.fail(
            FlextInfraWorktreeService(
                repository_root=attached,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch=branch,
                apply_changes=True,
            ).execute(),
            has="primary checkout is unproven for storage-only registry row",
        )
        tm.that(expected_lane.is_dir(), eq=True)
