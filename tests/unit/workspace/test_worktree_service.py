"""Real Git behavior for repository-local development worktrees."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import FlextInfraWorktreeService, c
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorktreeService:
    """The typed service owns the complete safe lane lifecycle."""

    @staticmethod
    def _repository(tmp_path: Path, *, setup_succeeds: bool = True) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        setup_recipe = (
            "@git config --local fixture.setup-complete true"
            if setup_succeeds
            else '@echo "fixture setup failure" >&2; exit 23'
        )
        (repository / "Makefile").write_text(
            f".PHONY: setup\nsetup:\n\t{setup_recipe}\n", encoding="utf-8"
        )
        u.Tests.initialize_git_repo(repository)
        return repository

    @staticmethod
    def _branch_exists(repository: Path, branch: str) -> bool:
        checked = tm.ok(
            u.Infra.git_run(
                repository, ("show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
            )
        )
        return checked.exit_code == 0

    def test_list_reports_the_primary_worktree(self, tmp_path: Path) -> None:
        """List is read-only and reports Git's canonical registry."""
        repository = self._repository(tmp_path)

        listed = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository, operation=c.Infra.WorktreeOperation.LIST
            ).execute()
        )

        tm.that(listed, has=f"worktree {repository}")

    def test_add_and_remove_use_the_repository_local_lane_path(
        self, tmp_path: Path
    ) -> None:
        """Mutations require apply and converge under .worktrees/<branch>."""
        repository = self._repository(tmp_path)
        branch = "feature/example"
        lane = repository / c.Infra.WORKTREES_DIRNAME / branch

        added = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                apply_changes=True,
            ).execute()
        )

        tm.that(added, eq=str(lane))
        tm.that(lane.is_dir(), eq=True)
        tm.that(
            tm.ok(
                u.Infra.git_capture(lane, ("config", "--get", "fixture.setup-complete"))
            ),
            eq="true",
        )
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("worktree", "list", "--porcelain"))),
            has=f"worktree {lane}",
        )

        removed = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch=branch,
                apply_changes=True,
            ).execute()
        )

        tm.that(removed, eq=str(lane))
        tm.that(lane.exists(), eq=False)

    def test_mutation_without_apply_fails_closed(self, tmp_path: Path) -> None:
        """A branch alone never authorizes repository mutation."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/no-apply",
        ).execute()

        tm.fail(result, has="requires --apply")

    def test_setup_failure_removes_the_orphan_lane(self, tmp_path: Path) -> None:
        """A failed canonical setup leaves neither a lane nor registry entry."""
        repository = self._repository(tmp_path, setup_succeeds=False)
        branch = "feature/setup-fails"
        lane = repository / c.Infra.WORKTREES_DIRNAME / branch

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            apply_changes=True,
        ).execute()

        tm.fail(result, has="fixture setup failure")
        tm.that(lane.exists(), eq=False)
        tm.that(self._branch_exists(repository, branch), eq=False)
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("worktree", "list", "--porcelain"))),
            lacks=f"worktree {lane}",
        )

    def test_setup_failure_preserves_a_preexisting_branch(self, tmp_path: Path) -> None:
        """Rollback deletes only a branch created by the failed add operation."""
        repository = self._repository(tmp_path, setup_succeeds=False)
        branch = "feature/preexisting"
        tm.ok(u.Infra.git_capture(repository, ("branch", branch)))

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            apply_changes=True,
        ).execute()

        tm.fail(result, has="fixture setup failure")
        tm.that(self._branch_exists(repository, branch), eq=True)

    def test_remove_preserves_a_dirty_lane(self, tmp_path: Path) -> None:
        """Explicit removal fails closed when the selected lane contains WIP."""
        repository = self._repository(tmp_path)
        branch = "feature/dirty-lane"
        lane = repository / c.Infra.WORKTREES_DIRNAME / branch
        tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                apply_changes=True,
            ).execute()
        )
        dirty_file = lane / "uncommitted.txt"
        dirty_file.write_text("preserve me\n", encoding="utf-8")

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()

        tm.fail(result, has="contains modified or untracked files")
        tm.that(dirty_file.read_text(encoding="utf-8"), eq="preserve me\n")
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("worktree", "list", "--porcelain"))),
            has=f"worktree {lane}",
        )


__all__: tuple[str, ...] = ()
