"""Real Git behavior for repository-local development worktrees."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService, c, m
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
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "add", "Makefile", "pyproject.toml"], cwd=repository
            )
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "commit", "-m", message], cwd=repository))

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
            tm.ok(
                u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=repository))
            ).text,
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

    def test_private_add_does_not_parse_project_metadata(self, tmp_path: Path) -> None:
        """Raw ADD creates the checkout; public work start owns provisioning."""
        repository = self._repository(tmp_path)
        branch = "feature/invalid-metadata"
        lane = self._lane(repository, repository, branch)
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = ["not", "a", "string"]\n',
            encoding="utf-8",
        )
        self._commit_fixture(repository, "test: invalid project metadata")

        result = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )

        tm.that(result, eq=str(lane))
        tm.that(lane.is_dir(), where=bool)
        tm.that(
            tm.ok(
                u.Infra.git_ref_exists(
                    m.Infra.GitRefRequest(
                        repo_root=repository, reference=f"refs/heads/{branch}"
                    )
                )
            ).value,
            eq=True,
        )

    def test_private_add_does_not_execute_clean_failing_setup(
        self, tmp_path: Path
    ) -> None:
        """Raw ADD leaves setup execution to the public work-start saga."""
        repository = self._repository(tmp_path)
        branch = "feature/clean-setup-failure"
        lane = self._lane(repository, repository, branch)
        (repository / "Makefile").write_text(
            ".PHONY: setup\nsetup:\n\t@printf 'visible setup progress\\n'\n\t@exit 17\n",
            encoding="utf-8",
        )
        self._commit_fixture(repository, "test: clean setup failure")

        result = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )

        tm.that(result, eq=str(lane))
        tm.that(lane.is_dir(), eq=True)

    def test_private_add_does_not_execute_dirty_failing_setup(
        self, tmp_path: Path
    ) -> None:
        """Raw ADD cannot create setup work before saga provisioning."""
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

        result = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                apply_changes=True,
            ).execute()
        )

        tm.that(result, eq=str(lane))
        tm.that(not (lane / "setup-wip.txt").exists(), where=bool)

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
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", "owner.txt"], cwd=repository))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-m", "test: advance update base"],
                cwd=repository,
            )
        )
        base = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=repository))
        ).oid
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=lane)
                )
            ).primary_root,
            eq=repository.resolve(),
        )

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
        updated_head = tm.ok(
            u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=lane))
        ).oid
        tm.that(updated_head, ne=base)
        parents = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "rev-list", "--parents", "-n", "1", updated_head],
                cwd=lane,
            )
        ).split()
        tm.that(len(parents), eq=3)

    def test_child_lane_nests_under_its_epic_container(self, tmp_path: Path) -> None:
        """A child lane is namespaced by the epic lane that owns it."""
        repository = self._repository(tmp_path)
        epic_branch = "feature/epic-alpha"
        epic = Path(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch=epic_branch,
                    base="HEAD",
                    apply_changes=True,
                ).execute()
            )
        )
        child_branch = "feature/child-one"

        child = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=child_branch,
                base=epic_branch,
                epic_lane=epic,
                apply_changes=True,
            ).execute()
        )

        container = epic / c.Infra.WORKTREES_DIRNAME
        tm.that(child, eq=str(container / "child-one"))
        tm.that(Path(child).is_relative_to(container), where=bool)
        tm.that(
            tm.ok(
                u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=repository))
            ).text,
            has=f"worktree {child}",
        )

    def test_remove_refuses_an_epic_lane_with_registered_children(
        self, tmp_path: Path
    ) -> None:
        """A registered child keeps its epic lane alive until the child is gone."""
        repository = self._repository(tmp_path)
        epic_branch = "feature/epic-beta"
        epic = Path(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch=epic_branch,
                    base="HEAD",
                    apply_changes=True,
                ).execute()
            )
        )
        child_branch = "feature/child-two"
        child = Path(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch=child_branch,
                    base=epic_branch,
                    epic_lane=epic,
                    apply_changes=True,
                ).execute()
            )
        )

        refused = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=epic_branch,
            apply_changes=True,
        ).execute()

        tm.fail(refused, has="while children are registered")
        tm.fail(refused, has=str(child))
        tm.that(epic.is_dir(), where=bool)

        tm.that(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.REMOVE,
                    branch=child_branch,
                    apply_changes=True,
                ).execute()
            ),
            eq=str(child),
        )
        tm.that(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.REMOVE,
                    branch=epic_branch,
                    apply_changes=True,
                ).execute()
            ),
            eq=str(epic),
        )
        tm.that(not epic.exists(), where=bool)

    def test_child_add_refuses_an_unregistered_epic_lane(self, tmp_path: Path) -> None:
        """A child never materializes a container for an epic that does not exist."""
        repository = self._repository(tmp_path)
        missing = tmp_path / "no-such-epic"

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/child-orphan",
            base="HEAD",
            epic_lane=missing,
            apply_changes=True,
        ).execute()

        tm.fail(result, has=f"epic lane worktree does not exist: {missing}")
        tm.that(not missing.exists(), where=bool)

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
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "--unset", "core.worktree"], cwd=attached
            )
        )
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=attached)
                )
            ).primary_root,
            eq=attached.resolve(),
        )
        linked = tmp_path / "attached-linked"
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", "--detach", str(linked), "HEAD"],
                cwd=attached,
            )
        )
        tm.that(
            tm.ok(
                u.Infra.git_primary_worktree_root(
                    m.Infra.GitRepoRequest(repo_root=linked)
                )
            ).primary_root,
            eq=linked.resolve(),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "remove", "--force", str(linked)], cwd=linked
            )
        )
        branch = "feature/attached"
        primary = tm.ok(
            u.Infra.git_primary_worktree_root(
                m.Infra.GitRepoRequest(repo_root=attached)
            )
        ).primary_root
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
