"""make work WHAT=start and WHAT=status saga steps."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, u
from flext_infra._utilities.work_saga_common import FlextInfraWorkSagaCommon

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkSagaStart(FlextInfraWorkSagaCommon):
    """Start and status steps for the public work saga."""

    apply_changes: bool

    @staticmethod
    def _reusable_lane(primary_root: Path, branch: str) -> Path | None:
        """Return the lane Git already owns for the branch, when it is usable.

        Git's worktree registry is the only authority on lane existence. A
        start interrupted after `worktree add` leaves a registered lane whose
        bead carries no metadata, so re-running start adopts that lane instead
        of failing on "worktree lane already exists".
        """
        registered = FlextInfraWorktreeService.registered_lane(primary_root, branch)
        if registered.failure:
            return None
        lane = registered.value
        return lane if lane.is_dir() else None

    @staticmethod
    def _rollback_started_lane(
        primary_root: Path, branch: str, reused: Path | None, error: str | None
    ) -> str:
        """Undo a lane this start created when its bead registration failed."""
        reason = error or "failed to register lane on bead"
        if reused is not None:
            return reason
        removed = FlextInfraWorktreeService(
            workspace_root=primary_root,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()
        if removed.failure:
            return (
                f"{reason}; lane {branch} rollback failed: "
                f"{removed.error or 'unknown worktree removal failure'}"
            )
        return f"{reason}; lane {branch} rolled back"

    def _start(self, primary_root: Path) -> p.Result[str]:
        if not self.apply_changes:
            return r.fail("work start requires --apply")
        bead = (self.bead or "").strip()
        if not bead:
            return r.fail("work start requires --bead")
        kind_slug = self._validated_kind_slug()
        if kind_slug.failure:
            return r.fail(kind_slug.error or "invalid kind/name")
        kind, slug = kind_slug.value
        branch = self._branch_name(kind, slug)
        shown = u.Infra.beads_show_json(bead, root=self.workspace_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        metadata = shown.value.get("metadata")
        if isinstance(metadata, dict):
            existing_br = str(metadata.get("branch") or "").strip()
            existing_wt = str(metadata.get("worktree") or "").strip()
            bound = bool(existing_br and existing_wt and Path(existing_wt).exists())
            if bound and existing_br != branch:
                return r.fail(
                    f"bead {bead} already bound to branch {existing_br} "
                    f"at {existing_wt}"
                )
        base = self._resolve_integration_base(primary_root)
        if base.failure:
            return r.fail(base.error or "failed to resolve integration base")
        reused = self._reusable_lane(primary_root, branch)
        if reused is None:
            fetched = u.Infra.git_capture(primary_root, ("fetch", "origin"))
            if fetched.failure:
                return r.fail(fetched.error or "work start failed to fetch origin")
            created = FlextInfraWorktreeService(
                workspace_root=primary_root,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=base.value,
                apply_changes=True,
            ).execute()
            if created.failure:
                return r.fail(created.error or f"failed to start lane {branch}")
            lane = Path(created.value)
        else:
            lane = reused
        if self._is_primary_path(primary_root, lane):
            return r.fail("work start refused to use the primary worktree as a lane")
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to read lane HEAD")
        decisive = "lane-reused" if reused is not None else "lane-ready"
        notes = (
            f"work start: cmd=make work WHAT=start cwd={lane} "
            f"branch={branch} base={base.value} exit=0 decisive={decisive} "
            f"head={head.value}"
        )
        updated = u.Infra.beads_update_lane(
            bead,
            metadata={
                "branch": branch,
                "worktree": str(lane),
                "kind": kind.value,
                "slug": slug,
                "integration_base": base.value,
                "head_oid": head.value,
            },
            labels=(f"branch:{branch}",),
            notes=notes,
            root=self.workspace_root,
        )
        if updated.failure:
            return r.fail(
                self._rollback_started_lane(primary_root, branch, reused, updated.error)
            )
        receipt = self._format_receipt(
            bead=bead,
            operation=c.Infra.WorkOperation.START,
            primary=primary_root,
            worktree=str(lane),
            branch=branch,
            base=base.value,
            head_oid=head.value,
            pr="",
        )
        return r.ok(
            f"LANE_ID={bead} BRANCH={branch} WORKTREE={lane} "
            f"BASE={base.value} HEAD={head.value}\n{receipt}"
        )

    def _status(self, primary_root: Path) -> p.Result[str]:
        bead = (self.bead or "").strip()
        branch_result = self._resolve_lane_branch()
        branch = branch_result.value if branch_result.success else (self.branch or "")
        lines: list[str] = ["work status"]
        if bead:
            shown = u.Infra.beads_show_json(bead, root=self.workspace_root)
            if shown.failure:
                lines.append(f"bead: error={shown.error}")
            else:
                meta = shown.value.get("metadata")
                meta_obj = meta if isinstance(meta, dict) else dict[str, object]()
                lines.extend((
                    f"bead: {bead}",
                    f"bead_status: {shown.value.get('status')}",
                    f"assignee: {shown.value.get('assignee')}",
                ))
                for key in c.Infra.WORK_BEADS_METADATA_KEYS:
                    value = meta_obj.get(key)
                    if value is not None:
                        lines.append(f"metadata.{key}: {value}")
                stored_branch = meta_obj.get("branch")
                if not branch and isinstance(stored_branch, str):
                    branch = stored_branch
        listed = FlextInfraWorktreeService(
            workspace_root=primary_root, operation=c.Infra.WorktreeOperation.LIST
        ).execute()
        if listed.failure:
            lines.append(f"worktrees: error={listed.error}")
        else:
            lines.extend(("worktrees:", listed.value.rstrip()))
        if branch:
            lines.append(f"branch: {branch}")
            pr_list = u.Cli.capture(
                (
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch,
                    "--state",
                    "open",
                    "--json",
                    "number,url,state,baseRefName",
                ),
                cwd=primary_root,
            )
            if pr_list.failure:
                lines.append(f"pr: error={pr_list.error}")
            else:
                lines.append(f"pr_open: {pr_list.value or '[]'}")
        primary_flag = self.workspace_root.resolve() == primary_root.resolve()
        lines.append(f"primary_checkout: {primary_flag}")
        return r.ok("\n".join(lines))


__all__: list[str] = ["FlextInfraWorkSagaStart"]
