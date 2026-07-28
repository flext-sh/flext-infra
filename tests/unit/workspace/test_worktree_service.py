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
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n\t@:\n", encoding="utf-8"
        )
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
        """Mutations converge in the primary repository's canonical container."""
        repository = self._repository(tmp_path)
        branch = "feature/example"
        lane = repository / c.Infra.WORKTREES_DIRNAME / branch

        added = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )

        tm.that(added, eq=str(lane))
        tm.that(lane.is_dir(), where=bool)
        tm.that(lane.is_relative_to(repository), where=bool)
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
        tm.that(not lane.exists(), where=bool)

    def test_update_fast_forwards_a_lane_to_the_requested_base(
        self, tmp_path: Path
    ) -> None:
        """Update advances an existing lane only through a fast-forward."""
        repository = self._repository(tmp_path)
        branch = "feature/update"
        lane = repository / c.Infra.WORKTREES_DIRNAME / branch
        tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        (repository / "owner.txt").write_text("owner\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(repository, ("add", "owner.txt")))
        tm.ok(
            u.Infra.git_capture(
                repository, ("commit", "-m", "test: advance update base")
            )
        )
        base = tm.ok(u.Infra.git_capture(repository, ("rev-parse", "HEAD"))).strip()
        tm.that(tm.ok(u.Infra.git_primary_worktree_root(lane)), eq=repository.resolve())

        updated = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=lane,
                operation=c.Infra.WorktreeOperation.UPDATE,
                branch=branch,
                base=base,
                apply_changes=True,
            ).execute()
        )

        tm.that(updated, eq=str(lane))
        tm.that(
            tm.ok(u.Infra.git_capture(lane, ("rev-parse", "HEAD"))).strip(), eq=base
        )

    def test_mutation_without_apply_fails_closed(self, tmp_path: Path) -> None:
        """A branch alone never authorizes repository mutation."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/no-apply",
            base="HEAD",
        ).execute()

        tm.fail(result, has="requires --apply")

    def test_add_without_base_fails_loud(self, tmp_path: Path) -> None:
        """A mutating caller must explicitly select its integration base."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/no-base",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="requires --base")

    def test_attached_submodule_uses_one_primary_local_container(
        self, tmp_path: Path
    ) -> None:
        """Attached repositories use one container under the registry primary."""
        child_source = tmp_path / "child-source"
        child_source.mkdir()
        (child_source / "README.md").write_text("child\n", encoding="utf-8")
        (child_source / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n\t@:\n", encoding="utf-8"
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
            )
        )
        attached = superproject / "attached"
        tm.that(
            tm.ok(u.Infra.git_primary_worktree_root(attached)), eq=attached.resolve()
        )
        branch = "feature/attached"
        primary = tm.ok(u.Infra.git_primary_worktree_root(attached))
        expected_lane = primary / c.Infra.WORKTREES_DIRNAME / branch

        lane = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=attached,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(lane, eq=str(expected_lane))
        tm.that(
            f"{c.Infra.WORKTREES_DIRNAME}/{c.Infra.WORKTREES_DIRNAME}"
            not in expected_lane.as_posix(),
            where=bool,
        )

        removed = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=attached,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch=branch,
                apply_changes=True,
            ).execute()
        )
        tm.that(removed, eq=str(expected_lane))


__all__: tuple[str, ...] = ()
