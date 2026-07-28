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
    """List, add, and remove development lanes under the owning repository."""

    operation: Annotated[
        c.Infra.WorktreeOperation, m.Field(description="Worktree lifecycle operation")
    ]
    branch: Annotated[
        str | None, m.Field(description="Git branch identifying the development lane")
    ] = None
    base: Annotated[
        str, m.Field(description="Commit-ish used only when creating a new branch")
    ] = "HEAD"

    def _primary_root(self) -> p.Result[Path]:
        """Resolve the primary worktree from Git's canonical registry."""
        listed = u.Infra.git_capture(
            self.workspace_root, ("worktree", "list", "--porcelain")
        )
        if listed.failure:
            return r.fail(listed.error or "failed to list Git worktrees")
        first = next(
            (
                line.removeprefix("worktree ").strip()
                for line in listed.value.splitlines()
                if line.startswith("worktree ")
            ),
            "",
        )
        if not first:
            return r.fail("Git worktree registry contains no primary worktree")
        return r.ok(Path(first).resolve())

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
    def _lane_path(primary_root: Path, branch: str) -> p.Result[Path]:
        """Derive a repository-local lane path and reject traversal."""
        lanes_root = (primary_root / c.Infra.WORKTREES_DIRNAME).resolve()
        lane_path = (lanes_root / branch).resolve()
        if not lane_path.is_relative_to(lanes_root):
            return r.fail(f"branch resolves outside {c.Infra.WORKTREES_DIRNAME}")
        return r.ok(lane_path)

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

    def _add(self, primary_root: Path, branch: str) -> p.Result[str]:
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
        if local.value:
            arguments = ("worktree", "add", str(lane), branch)
        else:
            remote = self._ref_exists(f"refs/remotes/origin/{branch}")
            if remote.failure:
                return r.fail(remote.error or "failed to inspect remote branch")
            arguments = (
                (
                    "worktree",
                    "add",
                    "--track",
                    "-b",
                    branch,
                    str(lane),
                    f"origin/{branch}",
                )
                if remote.value
                else ("worktree", "add", "-b", branch, str(lane), self.base)
            )
        added = u.Infra.git_capture(self.workspace_root, arguments)
        if added.failure:
            return r.fail(added.error or f"failed to add worktree for {branch}")
        setup = u.Cli.run_raw((c.Infra.MAKE, "setup"), cwd=lane)
        setup_error = ""
        if setup.failure:
            setup_error = setup.error or "make setup execution failed"
        elif setup.value.exit_code != 0:
            setup_error = (setup.value.stderr or setup.value.stdout).strip()
            if not setup_error:
                setup_error = f"make setup exited {setup.value.exit_code}"
        if setup_error:
            cleanup = u.Infra.git_remove_worktree(primary_root, lane)
            if cleanup.failure:
                return r.fail(
                    f"worktree setup failed: {setup_error}; "
                    f"cleanup failed: {cleanup.error or 'unknown cleanup failure'}"
                )
            if not local.value:
                branch_cleanup = u.Infra.git_capture(
                    primary_root, ("branch", "-D", branch)
                )
                if branch_cleanup.failure:
                    return r.fail(
                        f"worktree setup failed: {setup_error}; "
                        "created branch cleanup failed: "
                        f"{branch_cleanup.error or 'unknown branch cleanup failure'}"
                    )
            return r.fail(f"worktree setup failed: {setup_error}")
        return r.ok(str(lane))

    def _remove(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Remove one clean canonical lane without deleting its branch."""
        if not self.apply_changes:
            return r.fail("worktree remove requires --apply")
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "invalid worktree lane path")
        lane = lane_result.value
        removed = u.Infra.git_remove_clean_worktree(primary_root, lane)
        if removed.failure:
            return r.fail(removed.error or f"failed to remove worktree for {branch}")
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
        if self.operation == c.Infra.WorktreeOperation.ADD:
            return self._add(primary.value, branch.value)
        return self._remove(primary.value, branch.value)


__all__: list[str] = ["FlextInfraWorktreeService"]
