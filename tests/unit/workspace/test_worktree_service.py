"""Real Git behavior for recursive in-workspace development worktrees."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraWorktreeService, c, m
from flext_tests import tm
from tests import u


class TestsFlextInfraWorktreeService:
    """The typed service owns the complete safe lane lifecycle."""

    @staticmethod
    def _lane(parent_lane: Path, lane_dir: str) -> Path:
        """Derive the canonical recursive lane contract under a parent lane."""
        return parent_lane.resolve() / c.Infra.WORKTREES_DIRNAME / lane_dir

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / ".gitignore").write_text(
            f"{c.Infra.WORKTREES_DIRNAME}/\n", encoding="utf-8"
        )
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

    def test_add_and_remove_use_the_in_workspace_lane_path(
        self, tmp_path: Path
    ) -> None:
        """A lane lives inside the workspace, one level under `.worktrees`."""
        repository = self._repository(tmp_path)
        branch = "feature/mro-1-example"
        lane = self._lane(repository, "mro-1-example")

        added = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                lane_dir="mro-1-example",
                apply_changes=True,
            ).execute()
        )

        tm.that(added, eq=str(lane))
        tm.that(lane.is_dir(), where=bool)
        tm.that(lane.is_relative_to(repository), where=bool)
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
                lane_dir="mro-1-example",
                apply_changes=True,
            ).execute()
        )

        tm.that(removed, eq=str(lane))
        tm.that(not lane.exists(), where=bool)

    def test_lane_directory_never_nests_by_branch_shape(self, tmp_path: Path) -> None:
        """The branch never contributes a directory level to the lane path."""
        repository = self._repository(tmp_path)

        added = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="feature/mro-2-flat",
                base="HEAD",
                lane_dir="mro-2-flat",
                apply_changes=True,
            ).execute()
        )

        tm.that(added, eq=str(self._lane(repository, "mro-2-flat")))
        tm.that("feature" not in added.removeprefix(str(repository)), where=bool)

    def test_child_lane_nests_under_its_parent_lane(self, tmp_path: Path) -> None:
        """A child lane is derived under the parent lane's own container."""
        repository = self._repository(tmp_path)
        epic_lane = self._lane(repository, "mro-3-epic")
        tm.that(
            tm.ok(
                FlextInfraWorktreeService(
                    workspace_root=repository,
                    operation=c.Infra.WorktreeOperation.ADD,
                    branch="epic/mro-3-epic",
                    base="HEAD",
                    lane_dir="mro-3-epic",
                    apply_changes=True,
                ).execute()
            ),
            eq=str(epic_lane),
        )

        child = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="feature/mro-3.1-child",
                base="HEAD",
                lane_dir="mro-3.1-child",
                parent_lane=epic_lane,
                apply_changes=True,
            ).execute()
        )

        tm.that(child, eq=str(self._lane(epic_lane, "mro-3.1-child")))
        tm.that(Path(child).is_relative_to(epic_lane), where=bool)
        tm.that(
            tm.ok(FlextInfraWorktreeService.child_lanes(repository, epic_lane)),
            eq=(Path(child).resolve(),),
        )

    def test_add_without_lane_dir_fails_closed(self, tmp_path: Path) -> None:
        """A lane path is derived from its Bead, never from the branch."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/mro-4-no-dir",
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="requires --lane-dir")

    def test_registered_lane_refuses_a_non_canonical_registration(
        self, tmp_path: Path
    ) -> None:
        """A branch registered outside its derived path is never reused."""
        repository = self._repository(tmp_path)
        rogue = tmp_path / "rogue-lane"
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "worktree",
                    "add",
                    "-b",
                    "feature/mro-5-rogue",
                    str(rogue),
                    "HEAD",
                ],
                cwd=repository,
            )
        )

        result = FlextInfraWorktreeService.registered_lane(
            repository, "feature/mro-5-rogue", self._lane(repository, "mro-5-rogue")
        )

        tm.fail(result, has="registered outside its canonical lane")

    def test_add_reads_the_lane_instead_of_dirty_primary_metadata(
        self, tmp_path: Path
    ) -> None:
        """Setup never inherits the primary checkout as its workspace owner."""
        repository = self._repository(tmp_path)
        lane = self._lane(repository, "mro-6-isolated")
        (repository / "pyproject.toml").write_text(
            '[dependency-groups]\ndescription = "dirty primary WIP"\n', encoding="utf-8"
        )

        added = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="feature/mro-6-isolated",
                base="HEAD",
                lane_dir="mro-6-isolated",
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

    def test_invalid_lane_metadata_fails_precisely_and_rolls_back(
        self, tmp_path: Path
    ) -> None:
        """The typed lane ingress rejects a non-string PEP 621 description."""
        repository = self._repository(tmp_path)
        branch = "feature/mro-7-invalid"
        lane = self._lane(repository, "mro-7-invalid")
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
            lane_dir="mro-7-invalid",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="description")
        tm.fail(result, has="clean lane rolled back")
        tm.that(not lane.exists(), where=bool)
        tm.that(
            tm.ok(
                u.Infra.git_ref_exists(
                    m.Infra.GitRefRequest(
                        repo_root=repository, reference=f"refs/heads/{branch}"
                    )
                )
            ).value,
            eq=False,
        )

    def test_clean_setup_failure_preserves_the_new_lane_for_resume(
        self, tmp_path: Path
    ) -> None:
        """Even a clean failed setup keeps its lane so the next start resumes it.

        Provisioning clones every governed submodule, so discarding a clean but
        unprovisioned lane threw that away and forced a manual re-clone. The
        checkout is valid; only its environment is missing.
        """
        repository = self._repository(tmp_path)
        branch = "feature/mro-8-clean-failure"
        lane = self._lane(repository, "mro-8-clean-failure")
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
            lane_dir="mro-8-clean-failure",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="failed (2)")
        tm.fail(result, has=f"lane {branch} preserved at {lane}")
        tm.that(lane.is_dir(), eq=True)

    def test_setup_failure_preserves_new_lane_with_work(self, tmp_path: Path) -> None:
        """A failed setup never destroys work it created before returning."""
        repository = self._repository(tmp_path)
        branch = "feature/mro-9-dirty-failure"
        lane = self._lane(repository, "mro-9-dirty-failure")
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
            lane_dir="mro-9-dirty-failure",
            apply_changes=True,
        ).execute()

        tm.fail(result, has=f"lane {branch} preserved at {lane}")
        tm.that(
            (lane / "setup-wip.txt").read_text(encoding="utf-8"), eq="preserve me\n"
        )

    def test_update_fast_forwards_a_lane_to_the_requested_base(
        self, tmp_path: Path
    ) -> None:
        """Update advances an existing lane only through a fast-forward."""
        repository = self._repository(tmp_path)
        branch = "feature/mro-10-update"
        lane = self._lane(repository, "mro-10-update")
        tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                lane_dir="mro-10-update",
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
                lane_dir="mro-10-update",
                apply_changes=True,
            ).execute()
        )

        tm.that(updated, eq=str(lane))
        tm.that(
            tm.ok(
                u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=lane))
            ).oid,
            eq=base,
        )

    def test_mutation_without_apply_fails_closed(self, tmp_path: Path) -> None:
        """A branch alone never authorizes repository mutation."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/mro-11-no-apply",
            base="HEAD",
            lane_dir="mro-11-no-apply",
        ).execute()

        tm.fail(result, has="requires --apply")

    def test_add_without_base_fails_loud(self, tmp_path: Path) -> None:
        """A mutating caller must explicitly select its integration base."""
        repository = self._repository(tmp_path)

        result = FlextInfraWorktreeService(
            workspace_root=repository,
            operation=c.Infra.WorktreeOperation.ADD,
            branch="feature/mro-12-no-base",
            lane_dir="mro-12-no-base",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="requires --base")

    def test_member_checkout_never_owns_its_own_lane(self, tmp_path: Path) -> None:
        """A member repository yields the workspace root as the lane owner."""
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
        member = superproject / "attached"

        tm.that(
            tm.ok(FlextInfraWorktreeService.workspace_primary_root(member)),
            eq=superproject.resolve(),
        )

        lane = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=superproject,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="feature/mro-13-member",
                base="HEAD",
                lane_dir="mro-13-member",
                apply_changes=True,
            ).execute()
        )

        expected_lane = self._lane(superproject, "mro-13-member")
        tm.that(lane, eq=str(expected_lane))
        # Why: Git spells a submodule's own checkout through its gitdir under
        # .git/modules, so the invariant under test is that the member gained no
        # lane of its own — never how Git renders its single main worktree.
        member_worktrees = tm.ok(
            u.Infra.git_list_worktrees(m.Infra.GitRepoRequest(repo_root=member))
        ).text
        tm.that(member_worktrees, lacks=str(expected_lane))
        tm.that(
            len([
                line
                for line in member_worktrees.splitlines()
                if line.startswith("worktree ")
            ]),
            eq=1,
        )

        removed = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=superproject,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch="feature/mro-13-member",
                lane_dir="mro-13-member",
                apply_changes=True,
            ).execute()
        )
        tm.that(removed, eq=str(expected_lane))


__all__: tuple[str, ...] = ()
