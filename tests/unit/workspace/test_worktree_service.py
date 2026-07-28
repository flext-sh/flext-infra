"""Real Git behavior for repository-local development worktrees."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.workspace.worktree import FlextInfraWorktreeService
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorktreeService:
    """The typed service owns the complete safe lane lifecycle."""

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        u.Tests.initialize_git_repo(repository)
        return repository

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


__all__: tuple[str, ...] = ()
