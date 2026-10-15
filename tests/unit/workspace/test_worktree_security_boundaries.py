"""Security contracts for real Git worktree boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraWorktreeService
from tests import c, m, p, u


class TestsFlextInfraWorktreeSecurityBoundaries:
    """Security contracts for real Git worktree boundaries."""

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        (repository / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n\t@printf 'setup\\n'\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(repository)
        return repository

    @staticmethod
    def _add(
        repository: Path,
        branch: str,
        base: str = "HEAD",
        *,
        epic: Path | None = None,
    ) -> p.Result[str]:
        return FlextInfraWorktreeService(
            repository_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base=base,
            epic_lane=epic,
            apply_changes=True,
        ).execute()

    @pytest.mark.parametrize("base", ["--help", "-C", "--upload-pack=payload"])
    def test_option_like_base_fails_before_lane_mutation(
        self,
        tmp_path: Path,
        base: str,
    ) -> None:
        """Test option like base fails before lane mutation."""
        repository = self._repository(tmp_path)

        result = self._add(repository, "feature/option-base", base)

        tm.fail(result, has="invalid base commitish")
        tm.that(
            tm.ok(
                u.Infra.git_list_worktrees(
                    m.Infra.GitRepoRequest(repo_root=repository),
                ),
            ).porcelain.count("worktree "),
            eq=1,
        )

    def test_unresolved_base_fails_before_lane_mutation(self, tmp_path: Path) -> None:
        """An unresolvable base is refused by admission before any lane effect.

        Admission proves the requested base contains the live integration tip
        before the service resolves the base itself, so the refusal carries
        Git's own unresolved-ref diagnostic for the requested name.
        """
        repository = self._repository(tmp_path)

        _ = u.Tests.WorktreeFixture.refused_lane(
            repository,
            "feature/missing-base",
            base="missing/base",
            reason="Ref 'missing/base' did not resolve",
        )

    @pytest.mark.parametrize("entry", ["epic", "container"])
    def test_symlinked_epic_topology_fails_closed(
        self,
        tmp_path: Path,
        entry: str,
    ) -> None:
        """A child ADD under a symlinked epic topology never writes outside.

        Admission refuses the child ADD (bead flext-itpd1.3.26) before the
        symlink checks run; the success path is unreachable until admission
        opens and the symlink target stays empty either way.
        """
        repository = self._repository(tmp_path)
        epic = u.Tests.WorktreeFixture.native_lane(repository, "feature/secure-epic")
        outside = tmp_path / "outside"
        outside.mkdir()
        if entry == "container":
            (epic / c.Infra.WORKTREES_DIRNAME).symlink_to(
                outside,
                target_is_directory=True,
            )
        else:
            # Retirement admission is closed, so the epic is unregistered
            # natively before its path is replaced by a symlink.
            tm.ok(
                u.Cli.run_checked(
                    [c.Infra.GIT, "worktree", "remove", str(epic)],
                    cwd=repository,
                ),
            )
            epic.symlink_to(outside, target_is_directory=True)

        try:
            _ = u.Tests.WorktreeFixture.refused_lane(
                repository,
                f"feature/{entry}-child",
                epic_lane=epic,
            )

            tm.that(list(outside.iterdir()), eq=[])
        finally:
            if epic.is_symlink():
                epic.unlink()

    @pytest.mark.parametrize("epic", ["unregistered", "foreign"])
    def test_child_add_under_an_unowned_epic_is_refused(
        self,
        tmp_path: Path,
        epic: str,
    ) -> None:
        """A child ADD is refused under an unregistered or a foreign epic lane.

        ``unregistered`` names a real directory Git does not register;
        ``foreign`` names a registered epic while the child branch is already
        checked out under another epic. Admission refuses both (bead
        flext-itpd1.3.26) before the registry checks run, leaving no lane, ref,
        or registration behind.
        """
        repository = self._repository(tmp_path)
        native = u.Tests.WorktreeFixture.native_lane
        epic_lane = tmp_path / "unregistered-epic"
        child = "feature/registry-child"
        if epic == "foreign":
            first = native(repository, "feature/first-epic")
            epic_lane = native(repository, "feature/second-epic")
            _ = native(repository, child, epic_lane=first)
        else:
            epic_lane.mkdir()

        _ = u.Tests.WorktreeFixture.refused_lane(
            repository,
            child,
            epic_lane=epic_lane,
        )
