"""Repository-local development worktree lifecycle service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorktreeService(s[str]):
    """List, add, update, and remove development lanes under the repository."""

    operation: Annotated[
        c.Infra.WorktreeOperation, m.Field(description="Worktree lifecycle operation")
    ]
    branch: Annotated[
        str | None, m.Field(description="Git branch identifying the development lane")
    ] = None
    base: Annotated[
        str | None,
        m.Field(description="Commit-ish used to create or fast-forward a branch"),
    ] = None

    def _primary_root(self) -> p.Result[Path]:
        """Resolve the primary worktree from Git's canonical registry."""
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=self.workspace_root)
        )
        if primary.failure:
            return r[Path].fail(primary.error or "failed to resolve primary worktree")
        return r[Path].ok(primary.value.primary_root)

    def _validated_branch(self) -> p.Result[str]:
        """Validate and return the branch required by mutating operations."""
        branch = (self.branch or "").strip()
        if not branch:
            return r.fail(f"worktree {self.operation} requires --branch")
        checked = u.Infra.git_check_branch_format(
            m.Infra.GitBranchRequest(repo_root=self.workspace_root, branch=branch)
        )
        if checked.failure:
            return r.fail(checked.error or f"invalid branch name: {branch}")
        return r.ok(branch)

    @staticmethod
    def _lanes_root(primary_root: Path) -> p.Result[Path]:
        """Place new lanes outside every ancestor project discovery boundary."""
        resolved_primary = primary_root.resolve()
        outermost_project = resolved_primary
        for candidate in resolved_primary.parents:
            if (candidate / c.Infra.PYPROJECT_FILENAME).is_file():
                outermost_project = candidate
        namespace_digest = u.Cli.sha256_content(str(resolved_primary))[
            : c.Infra.WORKTREE_NAMESPACE_DIGEST_LENGTH
        ]
        namespace = f"{resolved_primary.name}-{namespace_digest}"
        return r.ok(
            (outermost_project.parent / c.Infra.WORKTREES_DIRNAME / namespace).resolve()
        )

    @classmethod
    def _lane_path(cls, primary_root: Path, branch: str) -> p.Result[Path]:
        """Derive an isolated lane path and reject branch traversal."""
        root_result = cls._lanes_root(primary_root)
        if root_result.failure:
            return r.fail(root_result.error or "failed to resolve worktree lanes root")
        lanes_root = root_result.value
        lane_path = (lanes_root / branch).resolve()
        if not lane_path.is_relative_to(lanes_root):
            return r.fail(f"branch resolves outside {c.Infra.WORKTREES_DIRNAME}")
        return r.ok(lane_path)

    @staticmethod
    def registered_lane(primary_root: Path, branch: str) -> p.Result[Path]:
        """Resolve an existing branch lane from Git's canonical registry."""
        listed = u.Infra.git_list_worktrees(
            m.Infra.GitRepoRequest(repo_root=primary_root)
        )
        if listed.failure:
            return r.fail(listed.error or "failed to list Git worktrees")
        current: Path | None = None
        for line in (*listed.value.text.splitlines(), ""):
            if line.startswith("worktree "):
                current = Path(line.removeprefix("worktree ").strip()).resolve()
            elif line == f"branch refs/heads/{branch}" and current is not None:
                return r.ok(current)
            elif not line:
                current = None
        return r.fail(f"worktree branch is not registered: {branch}")

    def _ref_exists(self, reference: str) -> p.Result[bool]:
        """Return whether an exact Git ref exists, preserving command failures."""
        checked = u.Infra.git_ref_exists(
            m.Infra.GitRefRequest(repo_root=self.workspace_root, reference=reference)
        )
        if checked.failure:
            return r.fail(checked.error or f"failed to inspect Git ref: {reference}")
        return r.ok(checked.value.value)

    @classmethod
    def setup_lane(cls, primary_root: Path, lane: Path) -> p.Result[bool]:
        """Provision primary dependencies and bind the lane to its environment."""
        beads_dir = lane / ".beads"
        if beads_dir.is_dir():
            beads_dir.chmod(0o700)
        declared = u.Infra.git_declared_submodule_paths(primary_root)
        if declared.failure:
            return r.fail(declared.error or "failed to read primary Git declarations")
        for relative in declared.value:
            child = primary_root / relative
            if (child / ".git").exists():
                continue
            initialized = u.Infra.git_submodule_init(
                m.Infra.GitRefRequest(
                    repo_root=primary_root, reference=relative.as_posix()
                )
            )
            if initialized.failure:
                return r.fail(
                    initialized.error
                    or f"failed to initialize primary gitlink {relative}"
                )
        venv_name = config.Infra.tooling.tools.pyright.path_rules.venv_name
        primary_venv = primary_root / venv_name
        lane_venv = lane / venv_name
        if lane_venv.is_symlink():
            if lane_venv.resolve() != primary_venv.resolve():
                return r.fail(
                    f"lane environment points outside the primary environment: {lane_venv}"
                )
        elif lane_venv.exists():
            return r.fail(f"refusing to replace existing lane environment: {lane_venv}")
        setup = u.Cli.run_live(
            (c.Infra.MAKE, "setup", "WHAT=", f"WORKSPACE={primary_root}"),
            cwd=primary_root,
            remove_env_keys=(
                "MAKEFLAGS",
                "MAKELEVEL",
                "MAKEOVERRIDES",
                "MFLAGS",
                "UV_PROJECT",
                "UV_PROJECT_ENVIRONMENT",
                "VIRTUAL_ENV",
            ),
        )
        if setup.failure:
            return r.fail(setup.error or "make setup execution failed")
        interpreter = primary_venv / "bin" / "python"
        if not interpreter.is_file():
            return r.fail(f"primary setup did not create an interpreter: {interpreter}")
        if not lane_venv.is_symlink():
            try:
                lane_venv.symlink_to(primary_venv, target_is_directory=True)
            except OSError as exc:
                return r.fail(f"failed to bind lane environment {lane_venv}: {exc}")
        return r.ok(True)

    @staticmethod
    def _rollback_new_lane(
        primary_root: Path,
        lane: Path,
        branch: str,
        created_branch_oid: str | None,
        setup_error: str,
    ) -> p.Result[str]:
        """Roll back only a clean lane created by the current add operation."""
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=lane))
        if status.failure:
            return r.fail(
                f"worktree setup failed: {setup_error}; preserving lane {lane}: "
                f"{status.error or 'cannot prove the new lane is clean'}"
            )
        if status.value.dirty:
            return r.fail(
                f"worktree setup failed: {setup_error}; preserving lane {lane} "
                "because setup left worktree changes"
            )
        cleanup = u.Infra.git_remove_clean_worktree(primary_root, lane)
        if cleanup.failure:
            return r.fail(
                f"worktree setup failed: {setup_error}; preserving lane {lane}: "
                f"{cleanup.error or 'clean lane rollback failed'}"
            )
        if created_branch_oid is not None:
            branch_cleanup = u.Infra.git_delete_ref(
                m.Infra.GitDeleteRefRequest(
                    repo_root=primary_root,
                    reference=f"refs/heads/{branch}",
                    expected_oid=created_branch_oid,
                )
            )
            if branch_cleanup.failure:
                return r.fail(
                    f"worktree setup failed: {setup_error}; "
                    "created branch cleanup failed: "
                    f"{branch_cleanup.error or 'unknown branch cleanup failure'}"
                )
        return r.fail(f"worktree setup failed: {setup_error}; clean lane rolled back")

    def _add(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Create and set up one branch worktree transactionally."""
        if not self.apply_changes:
            return r.fail("worktree add requires --apply")
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        if lane.exists():
            return r.fail(f"worktree lane already exists: {lane}")
        ensured = u.Cli.ensure_dir(lane.parent)
        if ensured.failure:
            return r.fail(ensured.error or f"failed to create {lane.parent}")
        local = self._ref_exists(f"refs/heads/{branch}")
        if local.failure:
            return r.fail(local.error or "failed to inspect local branch")
        remote = self._ref_exists(f"refs/remotes/origin/{branch}")
        if remote.failure:
            return r.fail(remote.error or "failed to inspect remote branch")
        added = u.Infra.git_add_lane_worktree(
            m.Infra.GitWorktreeAddRequest(
                repo_root=self.workspace_root,
                lane=lane,
                branch=branch,
                base=base,
                local_branch_exists=local.value,
                track_remote=not local.value and remote.value,
            )
        )
        if added.failure:
            return r.fail(added.error or f"failed to add worktree for {branch}")
        created_branch_oid: str | None = None
        if not local.value:
            created_oid = u.Infra.git_repository_head(
                m.Infra.GitRepoRequest(repo_root=lane)
            )
            if created_oid.failure:
                return self._rollback_new_lane(
                    primary_root,
                    lane,
                    branch,
                    None,
                    created_oid.error or "failed to retain created branch identity",
                )
            created_branch_oid = created_oid.value.oid
        metadata = u.read_project_metadata(lane)
        if metadata.failure:
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                created_branch_oid,
                metadata.error or "invalid lane project metadata",
            )
        return r.ok(str(lane))

    def _remove(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Remove one clean canonical lane without deleting its branch."""
        if not self.apply_changes:
            return r.fail("worktree remove requires --apply")
        lane_result = self.registered_lane(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        removed = u.Infra.git_remove_clean_worktree(primary_root, lane)
        if removed.failure:
            return r.fail(removed.error or f"failed to remove worktree for {branch}")
        return r.ok(str(lane))

    def _update(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Merge-forward one clean canonical lane to the requested base."""
        if not self.apply_changes:
            return r.fail("worktree update requires --apply")
        lane_result = self.registered_lane(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        if not lane.is_dir():
            return r.fail(f"worktree lane does not exist: {lane}")
        current_branch = u.Infra.git_symbolic_ref_short(
            m.Infra.GitRepoRequest(repo_root=lane)
        )
        if current_branch.failure:
            return r.fail(current_branch.error or f"failed to inspect lane {lane}")
        if current_branch.value.text != branch:
            return r.fail(
                f"worktree lane branch mismatch: expected {branch}, "
                f"found {current_branch.value.text}"
            )
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=lane))
        if status.failure:
            return r.fail(status.error or f"failed to inspect lane state: {lane}")
        if status.value.dirty:
            return r.fail(
                "worktree update requires a clean lane; commit the owned WIP "
                "before merge-forward"
            )
        resolved_base = u.Infra.git_resolve_commit(
            m.Infra.GitCommitishRequest(repo_root=lane, commitish=base)
        )
        if resolved_base.failure:
            return r.fail(resolved_base.error or f"cannot resolve update base: {base}")
        base_oid = resolved_base.value.oid
        contains_base = u.Infra.git_is_ancestor(
            m.Infra.GitCommitishRequest(repo_root=lane, commitish=base_oid)
        )
        if contains_base.failure:
            return r.fail(contains_base.error or "failed to inspect update ancestry")
        if contains_base.value.value:
            return r.ok(str(lane))
        updated = u.Infra.git_merge_no_edit(
            m.Infra.GitCommitishRequest(repo_root=lane, commitish=base_oid)
        )
        if updated.failure:
            return r.fail(
                updated.error
                or f"worktree update cannot merge-forward {branch} to {base_oid}"
            )
        return r.ok(str(lane))

    @override
    def execute(self) -> p.Result[str]:
        """Execute the selected worktree operation."""
        primary = self._primary_root()
        if primary.failure:
            return r.fail(primary.error or "failed to resolve primary worktree")
        if self.operation == c.Infra.WorktreeOperation.LIST:
            listed = u.Infra.git_list_worktrees(
                m.Infra.GitRepoRequest(repo_root=primary.value)
            )
            if listed.failure:
                return r.fail(listed.error or "failed to list Git worktrees")
            return r.ok(listed.value.text)
        branch = self._validated_branch()
        if branch.failure:
            return r.fail(branch.error or "invalid worktree branch")
        base = (self.base or "").strip()
        if (
            self.operation
            in {c.Infra.WorktreeOperation.ADD, c.Infra.WorktreeOperation.UPDATE}
            and not base
        ):
            return r.fail(f"worktree {self.operation} requires --base")
        if self.operation == c.Infra.WorktreeOperation.ADD:
            return self._add(primary.value, branch.value, base)
        if self.operation == c.Infra.WorktreeOperation.UPDATE:
            return self._update(primary.value, branch.value, base)
        return self._remove(primary.value, branch.value)


__all__: list[str] = ["FlextInfraWorktreeService"]
