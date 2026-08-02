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

    def _require_apply(self) -> p.Result[bool]:
        """Require the public mutation token for a worktree state change."""
        if not self.apply_changes:
            return r.fail(f"worktree {self.operation} requires --apply")
        return r.ok(True)

    @staticmethod
    def _ensure_new_lane(lane: Path) -> p.Result[Path]:
        """Create the parent for one lane only when its target is absent."""
        if lane.exists():
            return r.fail(f"worktree lane already exists: {lane}")
        return u.Cli.ensure_dir(lane.parent).map(lambda _: lane)

    def _remote_add_arguments(
        self, lane: Path, branch: str, base: str
    ) -> p.Result[tuple[str, ...]]:
        """Derive the add command for a branch absent from local refs."""
        return self._ref_exists(f"refs/remotes/origin/{branch}").map(
            lambda remote_exists: (
                (
                    "worktree",
                    "add",
                    "--track",
                    "-b",
                    branch,
                    str(lane),
                    f"origin/{branch}",
                )
                if remote_exists
                else ("worktree", "add", "-b", branch, str(lane), base)
            )
        )

    def _add_arguments(
        self, lane: Path, branch: str, base: str
    ) -> p.Result[tuple[str, ...]]:
        """Derive one Git worktree-add command from canonical refs."""
        return self._ref_exists(f"refs/heads/{branch}").flat_map(
            lambda local_exists: (
                r[tuple[str, ...]].ok(("worktree", "add", str(lane), branch))
                if local_exists
                else self._remote_add_arguments(lane, branch, base)
            )
        )

    def _create_lane(self, lane: Path, branch: str, base: str) -> p.Result[Path]:
        """Register one prepared lane through Git's canonical worktree command."""
        return self._add_arguments(lane, branch, base).flat_map(
            lambda arguments: u.Infra.git_capture(
                self.workspace_root, arguments
            ).map(lambda _: lane)
        )

    @staticmethod
    def _preserved_lane_error(lane: Path, setup_error: str) -> str:
        """Describe a setup failure without discarding its fix-forward lane."""
        return (
            f"worktree setup failed: {setup_error}; preserving lane {lane} "
            "and its branch for fix-forward recovery"
        )

    @classmethod
    def _run_lane_setup(cls, lane: Path) -> p.Result[str]:
        """Run canonical setup inside an already registered lane."""
        return u.Cli.run_live(
            (c.Infra.MAKE, "setup", "WHAT=", f"WORKSPACE={lane}"),
            cwd=lane,
            # Only this nested Make inherits the transaction marker: allowing
            # it to re-enter the outer lock would deadlock its owning process.
            env=u.Cli.process_env(overrides={c.Infra.WORKTREE_TRANSACTION_ENV: "1"}),
            remove_env_keys=(
                "MAKEFLAGS",
                "MAKELEVEL",
                "MAKEOVERRIDES",
                "MFLAGS",
                "UV_PROJECT",
                "UV_PROJECT_ENVIRONMENT",
                "VIRTUAL_ENV",
            ),
        ).map(lambda _: str(lane)).map_error(
            lambda error: cls._preserved_lane_error(lane, error)
        )

    @classmethod
    def _setup_lane(cls, lane: Path) -> p.Result[str]:
        """Validate lane metadata before running its canonical setup."""
        return u.read_project_metadata(lane).map_error(
            lambda error: cls._preserved_lane_error(lane, error)
        ).flat_map(lambda _: cls._run_lane_setup(lane))

    def _add(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Create and set up one branch worktree transactionally."""
        return self._require_apply().flat_map(
            lambda _: self._lane_path(primary_root, branch)
        ).flat_map(self._ensure_new_lane).flat_map(
            lambda lane: self._create_lane(lane, branch, base)
        ).flat_map(self._setup_lane)

    def _remove(self, primary_root: Path, branch: str) -> p.Result[str]:
        """Remove one clean canonical lane without deleting its branch."""
        return self._require_apply().flat_map(
            lambda _: self._registered_lane(primary_root, branch)
        ).flat_map(
            lambda lane: u.Infra.git_remove_clean_worktree(primary_root, lane).map(
                lambda _: str(lane)
            )
        )

    @staticmethod
    def _require_lane_branch(lane: Path, branch: str, current: str) -> p.Result[Path]:
        """Require an existing lane to own the requested branch."""
        current_branch = current.strip()
        if current_branch != branch:
            return r.fail(
                f"worktree lane branch mismatch: expected {branch}, "
                f"found {current_branch}"
            )
        return r.ok(lane)

    @staticmethod
    def _require_clean_lane(lane: Path, status: str) -> p.Result[Path]:
        """Reject merge-forward when the selected lane contains uncommitted work."""
        if status.strip():
            return r.fail(
                "worktree update requires a clean lane; commit the owned WIP "
                "before merge-forward"
            )
        return r.ok(lane)

    @classmethod
    def _validate_update_lane(cls, lane: Path, branch: str) -> p.Result[Path]:
        """Validate the physical lane, checked-out branch, and clean state."""
        if not lane.is_dir():
            return r.fail(f"worktree lane does not exist: {lane}")
        return u.Infra.git_capture(
            lane, ("symbolic-ref", "--quiet", "--short", "HEAD")
        ).flat_map(
            lambda current: cls._require_lane_branch(lane, branch, current)
        ).flat_map(
            lambda _: u.Infra.git_capture(
                lane, ("status", "--porcelain", "--untracked-files=all")
            )
        ).flat_map(lambda status: cls._require_clean_lane(lane, status))

    @staticmethod
    def _resolve_update_base(lane: Path, base: str) -> p.Result[tuple[Path, str]]:
        """Resolve the requested merge-forward base to one immutable commit."""
        return u.Infra.git_capture(
            lane, ("rev-parse", "--verify", f"{base}^{{commit}}")
        ).map(lambda base_oid: (lane, base_oid.strip()))

    @staticmethod
    def _merge_update_lane(lane: Path, base_oid: str) -> p.Result[str]:
        """Merge-forward only when the resolved base is not already integrated."""
        return u.Infra.git_run(
            lane, ("merge-base", "--is-ancestor", base_oid, "HEAD")
        ).flat_map(
            lambda ancestry: (
                r[str].ok(str(lane))
                if ancestry.exit_code == 0
                else u.Infra.git_capture(
                    lane, ("merge", "--no-edit", base_oid)
                ).map(lambda _: str(lane))
            )
        )

    def _update(self, primary_root: Path, branch: str, base: str) -> p.Result[str]:
        """Merge-forward one clean canonical lane to the requested base."""
        return self._require_apply().flat_map(
            lambda _: self._registered_lane(primary_root, branch)
        ).flat_map(
            lambda lane: self._validate_update_lane(lane, branch)
        ).flat_map(
            lambda lane: self._resolve_update_base(lane, base)
        ).flat_map(
            lambda resolved: self._merge_update_lane(resolved[0], resolved[1])
        )

    def _execute_branch_operation(
        self, primary_root: Path, branch: str
    ) -> p.Result[str]:
        """Validate shared branch inputs and dispatch one mutating operation."""
        if self.operation == c.Infra.WorktreeOperation.REMOVE:
            return self._remove(primary_root, branch)
        base = (self.base or "").strip()
        if not base:
            return r.fail(f"worktree {self.operation} requires --base")
        operation = (
            self._add
            if self.operation == c.Infra.WorktreeOperation.ADD
            else self._update
        )
        return operation(primary_root, branch, base)

    @override
    def execute(self) -> p.Result[str]:
        """Execute the selected worktree operation."""
        return self._primary_root().flat_map(
            lambda primary_root: (
                u.Infra.git_capture(
                    primary_root, ("worktree", "list", "--porcelain")
                )
                if self.operation == c.Infra.WorktreeOperation.LIST
                else self._validated_branch().flat_map(
                    lambda branch: self._execute_branch_operation(primary_root, branch)
                )
            )
        )


__all__: list[str] = ["FlextInfraWorktreeService"]
