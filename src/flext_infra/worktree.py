"""Repository-local development worktree lifecycle service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, m, u
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
        return u.Infra.git_primary_worktree_root(self.workspace_root)

    def _validated_branch(self) -> p.Result[str]:
        """Validate and return the branch required by mutating operations."""
        branch = (self.branch or "").strip()
        if not branch:
            return r.fail(f"worktree {self.operation} requires --branch")
        checked = u.Infra.git_capture(
            self.workspace_root, ("check-ref-format", "--branch", branch)
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
    def _registered_lane(primary_root: Path, branch: str) -> p.Result[Path]:
        """Resolve an existing branch lane from Git's canonical registry."""
        listed = u.Infra.git_capture(primary_root, ("worktree", "list", "--porcelain"))
        if listed.failure:
            return r.fail(listed.error or "failed to list Git worktrees")
        current: Path | None = None
        for line in (*listed.value.splitlines(), ""):
            if line.startswith("worktree "):
                current = Path(line.removeprefix("worktree ").strip()).resolve()
            elif line == f"branch refs/heads/{branch}" and current is not None:
                return r.ok(current)
            elif not line:
                current = None
        return r.fail(f"worktree branch is not registered: {branch}")

    def _ref_exists(self, reference: str) -> p.Result[bool]:
        """Return whether an exact Git ref exists, preserving command failures."""
        checked = u.Infra.git_run(
            self.workspace_root, ("show-ref", "--verify", "--quiet", reference)
        )
        if checked.failure:
            return r.fail(checked.error or f"failed to inspect Git ref: {reference}")
        if checked.value.exit_code not in {0, 1}:
            detail = (checked.value.stderr or checked.value.stdout).strip()
            return r.fail(detail or f"failed to inspect Git ref: {reference}")
        return r.ok(checked.value.exit_code == 0)

    @staticmethod
    def _rollback_new_lane(
        primary_root: Path,
        lane: Path,
        branch: str,
        owned_branch_oid: str | None,
        restore_branch_oid: str | None,
        failure_detail: str,
    ) -> p.Result[str]:
        """Roll back a clean lane and only the exact branch mutation we own."""
        status = u.Infra.git_capture(
            lane, ("status", "--porcelain", "--untracked-files=all")
        )
        if status.failure:
            return r.fail(
                f"worktree add failed: {failure_detail}; preserving lane {lane}: "
                f"{status.error or 'cannot prove the new lane is clean'}"
            )
        if status.value.strip():
            return r.fail(
                f"worktree add failed: {failure_detail}; preserving lane {lane} "
                "because setup left worktree changes"
            )
        cleanup = u.Infra.git_remove_clean_worktree(primary_root, lane)
        if cleanup.failure:
            return r.fail(
                f"worktree add failed: {failure_detail}; preserving lane {lane}: "
                f"{cleanup.error or 'clean lane rollback failed'}"
            )
        if owned_branch_oid is not None:
            branch_ref = f"refs/heads/{branch}"
            branch_arguments = (
                ("update-ref", "-d", branch_ref, owned_branch_oid)
                if restore_branch_oid is None
                else ("update-ref", branch_ref, restore_branch_oid, owned_branch_oid)
            )
            branch_rollback = u.Infra.git_capture(primary_root, branch_arguments)
            if branch_rollback.failure:
                return r.fail(
                    f"worktree add failed: {failure_detail}; branch rollback failed: "
                    f"{branch_rollback.error or 'unknown branch rollback failure'}"
                )
        return r.fail(f"worktree add failed: {failure_detail}; clean lane rolled back")

    def _add(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Create and set up one branch worktree transactionally."""
        if not self.apply_changes:
            return r.fail("worktree add requires --apply")
        resolved_base = u.Infra.git_capture(
            primary_root, ("rev-parse", "--verify", f"{base}^{{commit}}")
        )
        if resolved_base.failure:
            return r.fail(
                resolved_base.error or f"worktree add cannot resolve base: {base}"
            )
        base_oid = resolved_base.value.strip()
        local_ref = f"refs/heads/{branch}"
        local = self._ref_exists(local_ref)
        if local.failure:
            return r.fail(local.error or "failed to inspect local branch")
        remote_ref = f"refs/remotes/origin/{branch}"
        remote_exists = False
        source_ref: str | None = local_ref if local.value else None
        if not local.value:
            remote = self._ref_exists(remote_ref)
            if remote.failure:
                return r.fail(remote.error or "failed to inspect remote branch")
            remote_exists = remote.value
            if remote_exists:
                source_ref = remote_ref
        source_oid: str | None = None
        if source_ref is not None:
            resolved_source = u.Infra.git_capture(
                primary_root, ("rev-parse", "--verify", f"{source_ref}^{{commit}}")
            )
            if resolved_source.failure:
                return r.fail(
                    resolved_source.error
                    or f"worktree add cannot resolve branch: {source_ref}"
                )
            source_oid = resolved_source.value.strip()
            ancestry = u.Infra.git_run(
                primary_root, ("merge-base", "--is-ancestor", source_oid, base_oid)
            )
            if ancestry.failure:
                return r.fail(ancestry.error or "failed to validate worktree base")
            if ancestry.value.exit_code != 0:
                detail = (ancestry.value.stderr or ancestry.value.stdout).strip()
                if ancestry.value.exit_code == 1:
                    detail = (
                        f"worktree add cannot fast-forward {source_ref} "
                        f"from {source_oid} to {base} ({base_oid})"
                    )
                return r.fail(
                    detail or f"failed to validate ancestry from {source_ref} to {base}"
                )
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        if lane.exists():
            return r.fail(f"worktree lane already exists: {lane}")
        ensured = u.Cli.ensure_dir(lane.parent)
        if ensured.failure:
            return r.fail(ensured.error or f"failed to create {lane.parent}")
        if local.value:
            arguments = ("worktree", "add", str(lane), branch)
        elif remote_exists:
            arguments = (
                "worktree",
                "add",
                "--track",
                "-b",
                branch,
                str(lane),
                f"origin/{branch}",
            )
        else:
            arguments = ("worktree", "add", "-b", branch, str(lane), base_oid)
        added = u.Infra.git_capture(primary_root, arguments)
        if added.failure:
            return r.fail(added.error or f"failed to add worktree for {branch}")
        expected_start_oid = source_oid or base_oid
        created_branch = not local.value
        checked_out = u.Infra.git_capture(
            lane, ("rev-parse", "--verify", "HEAD^{commit}")
        )
        if checked_out.failure:
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                expected_start_oid if created_branch else None,
                None,
                checked_out.error or "failed to retain branch identity",
            )
        checked_out_oid = checked_out.value.strip()
        if checked_out_oid != expected_start_oid:
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                checked_out_oid if created_branch else None,
                None,
                f"branch moved during preflight: expected {expected_start_oid}, "
                f"found {checked_out_oid}",
            )
        if checked_out_oid != base_oid:
            reconciled = u.Infra.git_capture(lane, ("merge", "--ff-only", base_oid))
            if reconciled.failure:
                return self._rollback_new_lane(
                    primary_root,
                    lane,
                    branch,
                    checked_out_oid if created_branch else None,
                    None,
                    reconciled.error
                    or f"failed to fast-forward {branch} to {base_oid}",
                )
        final_head = u.Infra.git_capture(
            lane, ("rev-parse", "--verify", "HEAD^{commit}")
        )
        restore_branch_oid = (
            source_oid if local.value and source_oid != base_oid else None
        )
        owned_branch_oid = (
            base_oid if created_branch or restore_branch_oid is not None else None
        )
        if final_head.failure or final_head.value.strip() != base_oid:
            found = final_head.value.strip() if final_head.success else "unresolved"
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                owned_branch_oid,
                restore_branch_oid,
                final_head.error
                or f"branch reconciliation expected {base_oid}, found {found}",
            )
        metadata = u.read_project_metadata(lane)
        if metadata.failure:
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                owned_branch_oid,
                restore_branch_oid,
                metadata.error or "invalid lane project metadata",
            )
        setup = u.Cli.run_live(
            (c.Infra.MAKE, "setup", "WHAT=", f"WORKSPACE={lane}"),
            cwd=lane,
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
            return self._rollback_new_lane(
                primary_root,
                lane,
                branch,
                owned_branch_oid,
                restore_branch_oid,
                setup.error or "make setup execution failed",
            )
        return r.ok(str(lane))

    def _remove(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Remove one clean canonical lane without deleting its branch."""
        if not self.apply_changes:
            return r.fail("worktree remove requires --apply")
        lane_result = self._registered_lane(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        removed = u.Infra.git_remove_clean_worktree(primary_root, lane)
        if removed.failure:
            return r.fail(removed.error or f"failed to remove worktree for {branch}")
        return r.ok(str(lane))

    def _update(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Fast-forward one canonical lane to the explicitly requested base."""
        if not self.apply_changes:
            return r.fail("worktree update requires --apply")
        lane_result = self._registered_lane(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        if not lane.is_dir():
            return r.fail(f"worktree lane does not exist: {lane}")
        current_branch = u.Infra.git_capture(
            lane, ("symbolic-ref", "--quiet", "--short", "HEAD")
        )
        if current_branch.failure:
            return r.fail(current_branch.error or f"failed to inspect lane {lane}")
        if current_branch.value.strip() != branch:
            return r.fail(
                f"worktree lane branch mismatch: expected {branch}, "
                f"found {current_branch.value.strip()}"
            )
        updated = u.Infra.git_capture(lane, ("merge", "--ff-only", base))
        if updated.failure:
            return r.fail(
                updated.error
                or f"worktree update cannot fast-forward {branch} to {base}"
            )
        return r.ok(str(lane))

    @override
    def execute(self) -> p.Result[str]:
        """Execute the selected worktree operation."""
        primary = self._primary_root()
        if primary.failure:
            return r.fail(primary.error or "failed to resolve primary worktree")
        if self.operation == c.Infra.WorktreeOperation.LIST:
            return u.Infra.git_capture(
                primary.value, ("worktree", "list", "--porcelain")
            )
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
