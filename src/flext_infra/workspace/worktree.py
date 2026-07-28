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
        str, m.Field(description="Commit-ish used only when creating a new branch")
    ] = "HEAD"

    def _primary_root(self) -> p.Result[Path]:
        """Resolve the primary worktree from Git's canonical registry."""
        return u.Infra.git_primary_worktree_root(self.root)

    def _validated_branch(self) -> p.Result[str]:
        """Validate and return the branch required by mutating operations."""
        branch = (self.branch or "").strip()
        if not branch:
            return r.fail(f"worktree {self.operation} requires --branch")
        checked = u.Infra.git_capture(
            self.root, ("check-ref-format", "--branch", branch)
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
            self.root, ("show-ref", "--verify", "--quiet", reference)
        )
        if checked.failure:
            return r.fail(checked.error or f"failed to inspect Git ref: {reference}")
        if checked.value.exit_code not in {0, 1}:
            detail = (checked.value.stderr or checked.value.stdout).strip()
            return r.fail(detail or f"failed to inspect Git ref: {reference}")
        return r.ok(checked.value.exit_code == 0)

    def _add(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Create one branch worktree at its canonical repository-local path."""
        if not self.apply_changes:
            return r.fail("worktree add requires --apply")
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "failed to resolve worktree lane")
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
        added = u.Infra.git_capture(self.root, arguments)
        if added.failure:
            return r.fail(added.error or f"failed to add worktree for {branch}")
        return r.ok(str(lane))

    def _remove(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Remove one clean canonical lane without deleting its branch."""
        if not self.apply_changes:
            return r.fail("worktree remove requires --apply")
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "failed to resolve worktree lane")
        lane = lane_result.value
        removed = u.Infra.git_capture(self.root, ("worktree", "remove", str(lane)))
        if removed.failure:
            return r.fail(removed.error or f"failed to remove worktree for {branch}")
        pruned = u.Infra.git_capture(self.root, ("worktree", "prune"))
        if pruned.failure:
            return r.fail(pruned.error or "failed to prune worktree registry")
        return r.ok(str(lane))

    def _update(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Fast-forward one clean canonical lane to the requested base."""
        if not self.apply_changes:
            return r.fail("worktree update requires --apply")
        lane_result = self._lane_path(primary_root, branch)
        if lane_result.failure:
            return r.fail(lane_result.error or "failed to resolve worktree lane")
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
        updated = u.Infra.git_capture(lane, ("merge", "--ff-only", self.base))
        if updated.failure:
            return r.fail(
                updated.error
                or f"worktree update cannot fast-forward {branch} to {self.base}"
            )
        return r.ok(str(lane))

    @override
    def execute(self) -> p.Result[str]:
        """Execute the selected worktree operation."""
        primary = self._primary_root()
        if primary.failure:
            return r.fail(primary.error or "failed to resolve primary worktree")
        operation = str(self.operation)
        if operation == c.Infra.WorktreeOperation.LIST:
            return u.Infra.git_capture(
                primary.value, ("worktree", "list", "--porcelain")
            )
        branch = self._validated_branch()
        if branch.failure:
            return r.fail(branch.error or "invalid worktree branch")
        if operation == c.Infra.WorktreeOperation.ADD:
            return self._add(primary.value, branch.value)
        if operation == c.Infra.WorktreeOperation.UPDATE:
            return self._update(primary.value, branch.value)
        return self._remove(primary.value, branch.value)


__all__: list[str] = ["FlextInfraWorktreeService"]
