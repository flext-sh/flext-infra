"""Real Git behavior for repository-local development worktrees."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService, c
from flext_tests import tm
from tests import u


class TestsFlextInfraWorktreeService:
    """The typed service owns the complete safe lane lifecycle."""

    @staticmethod
    def _lane(primary_root: Path, outermost_project: Path, branch: str) -> Path:
        """Derive the configured collision-safe test contract."""
        digest = u.Cli.sha256_content(str(primary_root.resolve()))[
            : c.Infra.WORKTREE_NAMESPACE_DIGEST_LENGTH
        ]
        namespace = f"{primary_root.resolve().name}-{digest}"
        return (
            outermost_project.resolve().parent
            / c.Infra.WORKTREES_DIRNAME
            / namespace
            / branch
        )

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = "A standard PEP 621 description string"\n',
            encoding="utf-8",
        )
        (repository / "Makefile").write_text(
            ".PHONY: setup\n"
            "setup:\n"
            '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
            '\t@grep -q "^\\[project\\]" "$(WORKSPACE)/pyproject.toml"\n'
            '\t@printf "setting up %s\\n" "$(WORKSPACE)"\n',
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(repository)
        return repository

    @staticmethod
    def _commit_fixture(repository: Path, message: str) -> None:
        """Commit one deliberate fixture mutation."""
        tm.ok(u.Infra.git_capture(repository, ("add", "Makefile", "pyproject.toml")))
        tm.ok(u.Infra.git_capture(repository, ("commit", "-m", message)))

    def test_list_reports_the_primary_worktree(self, tmp_path: Path) -> None:
        """List is read-only and reports Git's canonical registry."""
        repository = self._repository(tmp_path)

        listed = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository, operation=c.Infra.WorktreeOperation.LIST
            ).execute()
        )

        tm.that(listed, has=f"worktree {repository}")

    def test_add_and_remove_use_the_isolated_lane_path(self, tmp_path: Path) -> None:
        """A valid PEP 621 string survives typed setup in the isolated lane."""
        repository = self._repository(tmp_path)
        branch = "feature/example"
        lane = self._lane(repository, repository, branch)

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
        tm.that(not lane.is_relative_to(repository), where=bool)
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

    def test_add_reads_the_lane_instead_of_dirty_primary_metadata(
        self, tmp_path: Path
    ) -> None:
        """Setup never inherits the primary checkout as its workspace owner."""
        repository = self._repository(tmp_path)
        branch = "feature/isolated-metadata"
        lane = self._lane(repository, repository, branch)
        (repository / "pyproject.toml").write_text(
            '[dependency-groups]\ndescription = "dirty primary WIP"\n', encoding="utf-8"
        )

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
        tm.that(
            (repository / "pyproject.toml").read_text(encoding="utf-8"),
            eq='[dependency-groups]\ndescription = "dirty primary WIP"\n',
        )
        tm.that(
            (lane / "pyproject.toml").read_text(encoding="utf-8"),
            has='description = "A standard PEP 621 description string"',
        )

    def test_add_escapes_a_dirty_outer_project_ancestor(self, tmp_path: Path) -> None:
        """The lane container sits outside every project uv could discover."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / "pyproject.toml").write_text(
            '[dependency-groups]\ndescription = "dirty outer WIP"\n', encoding="utf-8"
        )
        nested = outer_project / "nested"
        nested.mkdir()
        repository = self._repository(nested)
        branch = "feature/outer-isolation"
        lane = self._lane(repository, outer_project, branch)

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
        tm.that(not lane.is_relative_to(outer_project), where=bool)
        tm.that(
            (outer_project / "pyproject.toml").read_text(encoding="utf-8"),
            eq='[dependency-groups]\ndescription = "dirty outer WIP"\n',
        )

    def test_same_named_repositories_use_distinct_lane_namespaces(
        self, tmp_path: Path
    ) -> None:
        """Repository names never collide inside one outer lane container."""
        outer_project = tmp_path / "outer"
        outer_project.mkdir()
        (outer_project / "pyproject.toml").write_text(
            '[project]\nname = "outer"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        first_parent = outer_project / "first"
        second_parent = outer_project / "second"
        first_parent.mkdir()
        second_parent.mkdir()
        first = self._repository(first_parent)
        second = self._repository(second_parent)
        branch = "feature/same-name"

        first_lane = self._lane(first, outer_project, branch)
        tm.that(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=first,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch=branch,
                    base="HEAD",
                    apply_changes=True,
                ).execute()
            ),
            eq=str(first_lane),
        )
        second_lane = self._lane(second, outer_project, branch)
        tm.that(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=second,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch=branch,
                    base="HEAD",
                    apply_changes=True,
                ).execute()
            ),
            eq=str(second_lane),
        )

        tm.that(first.name, eq=second.name)
        tm.that(first_lane != second_lane, where=bool)
        tm.that(first_lane.parent.parent != second_lane.parent.parent, where=bool)

    def test_invalid_lane_metadata_fails_precisely_and_rolls_back(
        self, tmp_path: Path
    ) -> None:
        """The typed lane ingress rejects a non-string PEP 621 description."""
        repository = self._repository(tmp_path)
        branch = "feature/invalid-metadata"
        lane = self._lane(repository, repository, branch)
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = ["not", "a", "string"]\n',
            encoding="utf-8",
        )
        self._commit_fixture(repository, "test: invalid project metadata")

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="description")
        tm.fail(result, has="clean lane rolled back")
        tm.that(not lane.exists(), where=bool)
        tm.that(
            tm.ok(
                u.Infra.git_run(
                    repository,
                    ("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"),
                )
            ).exit_code,
            eq=1,
        )

    def test_clean_setup_failure_rolls_back_only_the_new_lane(
        self, tmp_path: Path
    ) -> None:
        """A clean failed setup removes its new lane and exact created branch."""
        repository = self._repository(tmp_path)
        branch = "feature/clean-setup-failure"
        lane = self._lane(repository, repository, branch)
        (repository / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n\t@printf 'visible setup progress\\n'\n\t@exit 17\n",
            encoding="utf-8",
        )
        self._commit_fixture(repository, "test: clean setup failure")

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="failed (2)")
        tm.fail(result, has="clean lane rolled back")
        tm.that(not lane.exists(), where=bool)

    def test_setup_failure_preserves_new_lane_with_work(self, tmp_path: Path) -> None:
        """A failed setup never destroys work it created before returning."""
        repository = self._repository(tmp_path)
        branch = "feature/dirty-setup-failure"
        lane = self._lane(repository, repository, branch)
        (repository / "Makefile").write_text(
            ".PHONY: setup\n"
            "setup:\n"
            "\t@printf 'visible setup progress\\n'\n"
            "\t@printf 'preserve me\\n' > setup-wip.txt\n"
            "\t@exit 19\n",
            encoding="utf-8",
        )
        self._commit_fixture(repository, "test: dirty setup failure")

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has=f"preserving lane {lane}")
        tm.fail(result, has="setup left worktree changes")
        tm.that(
            (lane / "setup-wip.txt").read_text(encoding="utf-8"), eq="preserve me\n"
        )

    def test_update_fast_forwards_a_lane_to_the_requested_base(
        self, tmp_path: Path
    ) -> None:
        """Update advances an existing lane only through a fast-forward."""
        repository = self._repository(tmp_path)
        branch = "feature/update"
        lane = self._lane(repository, repository, branch)
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

    def test_add_fast_forwards_an_existing_local_branch_to_base(
        self, tmp_path: Path
    ) -> None:
        """A stale local branch is reconciled to BASE before setup runs."""
        repository = self._repository(tmp_path)
        branch = "feature/stale-local"
        tm.ok(u.Infra.git_capture(repository, ("branch", branch, "HEAD")))
        (repository / "base.txt").write_text("base\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(repository, ("add", "base.txt")))
        tm.ok(u.Infra.git_capture(repository, ("commit", "-m", "test: advance base")))
        base: str = tm.ok(
            u.Infra.git_capture(repository, ("rev-parse", "HEAD"))
        ).strip()

        lane: str = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=base,
                apply_changes=True,
            ).execute()
        )

        tm.that(
            tm.ok(u.Infra.git_capture(Path(lane), ("rev-parse", "HEAD"))).strip(),
            eq=base,
        )
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("rev-parse", branch))).strip(),
            eq=base,
        )

    def test_add_fast_forwards_a_remote_only_branch_to_base(
        self, tmp_path: Path
    ) -> None:
        """A remote-only branch is checked out then reconciled to BASE."""
        repository = self._repository(tmp_path)
        remote = tmp_path / "origin.git"
        branch = "feature/remote-only"
        tm.ok(u.Infra.git_capture(repository, ("init", "--bare", str(remote))))
        tm.ok(
            u.Infra.git_capture(
                repository, ("remote", "set-url", "origin", str(remote))
            )
        )
        tm.ok(
            u.Infra.git_capture(
                repository, ("push", "origin", f"HEAD:refs/heads/{branch}")
            )
        )
        tm.ok(
            u.Infra.git_capture(
                repository,
                (
                    "fetch",
                    "origin",
                    f"refs/heads/{branch}:refs/remotes/origin/{branch}",
                ),
            )
        )
        (repository / "base.txt").write_text("base\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(repository, ("add", "base.txt")))
        tm.ok(u.Infra.git_capture(repository, ("commit", "-m", "test: advance base")))
        base: str = tm.ok(
            u.Infra.git_capture(repository, ("rev-parse", "HEAD"))
        ).strip()

        lane: str = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=base,
                apply_changes=True,
            ).execute()
        )

        tm.that(
            tm.ok(u.Infra.git_capture(Path(lane), ("rev-parse", "HEAD"))).strip(),
            eq=base,
        )
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("rev-parse", branch))).strip(),
            eq=base,
        )

    def test_add_rejects_a_divergent_existing_branch_before_lane_mutation(
        self, tmp_path: Path
    ) -> None:
        """A divergent branch fails before it creates a lane or runs setup."""
        repository = self._repository(tmp_path)
        branch = "feature/divergent"
        tm.ok(u.Infra.git_capture(repository, ("branch", branch, "HEAD")))
        (repository / "base.txt").write_text("base\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(repository, ("add", "base.txt")))
        tm.ok(u.Infra.git_capture(repository, ("commit", "-m", "test: advance base")))
        base: str = tm.ok(
            u.Infra.git_capture(repository, ("rev-parse", "HEAD"))
        ).strip()
        diverged = tmp_path / "diverged"
        tm.ok(
            u.Infra.git_capture(repository, ("worktree", "add", str(diverged), branch))
        )
        (diverged / "branch.txt").write_text("branch\n", encoding="utf-8")
        tm.ok(u.Infra.git_capture(diverged, ("add", "branch.txt")))
        tm.ok(u.Infra.git_capture(diverged, ("commit", "-m", "test: diverge branch")))
        branch_head: str = tm.ok(
            u.Infra.git_capture(diverged, ("rev-parse", "HEAD"))
        ).strip()
        tm.ok(u.Infra.git_capture(repository, ("worktree", "remove", str(diverged))))
        lane = self._lane(repository, repository, branch)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch=branch,
            base=base,
            apply_changes=True,
        ).execute()

        tm.fail(result, has="cannot fast-forward")
        tm.that(not lane.exists(), where=bool)
        tm.that(
            tm.ok(u.Infra.git_capture(repository, ("rev-parse", branch))).strip(),
            eq=branch_head,
        )

    def test_attached_submodule_uses_one_primary_local_container(
        self, tmp_path: Path
    ) -> None:
        """Attached repositories use one container under the registry primary."""
        child_source = tmp_path / "child-source"
        child_source.mkdir()
        (child_source / "README.md").write_text("child\n", encoding="utf-8")
        (child_source / "pyproject.toml").write_text(
            '[project]\nname = "child"\nversion = "0.1.0"\n'
            'description = "Attached child fixture"\n',
            encoding="utf-8",
        )
        (child_source / "Makefile").write_text(
            ".PHONY: setup\n"
            "setup:\n"
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
            )
        )
        attached = superproject / "attached"
        tm.ok(u.Infra.git_capture(attached, ("config", "--unset", "core.worktree")))
        tm.that(
            tm.ok(u.Infra.git_primary_worktree_root(attached)), eq=attached.resolve()
        )
        linked = tmp_path / "attached-linked"
        tm.ok(
            u.Infra.git_capture(
                attached, ("worktree", "add", "--detach", str(linked), "HEAD")
            )
        )
        tm.that(tm.ok(u.Infra.git_primary_worktree_root(linked)), eq=linked.resolve())
        tm.ok(
            u.Infra.git_capture(linked, ("worktree", "remove", "--force", str(linked)))
        )
        branch = "feature/attached"
        primary = tm.ok(u.Infra.git_primary_worktree_root(attached))
        expected_lane = self._lane(primary, superproject, branch)

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
