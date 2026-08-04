"""make work WHAT=finish saga step."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, u
from flext_infra._utilities.work_saga_common import FlextInfraWorkSagaCommon

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkSagaFinish(FlextInfraWorkSagaCommon):
    """Finish step for the public work saga."""

    apply_changes: bool

    def _finish(self, primary_root: Path) -> p.Result[str]:
        if not self.apply_changes:
            return r.fail("work finish requires --apply")
        bead = (self.bead or "").strip()
        if not bead:
            return r.fail("work finish requires --bead")
        shown = u.Infra.beads_show_json(bead, root=self.workspace_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        meta = shown.value.get("metadata")
        if not isinstance(meta, dict):
            return r.fail(f"bead {bead} has no lane metadata")
        branch = str(meta.get("branch") or "").strip()
        worktree = str(meta.get("worktree") or "").strip()
        expected = str(meta.get("head_oid") or "").strip()
        pr_number = str(meta.get("pr_number") or "").strip()
        integration = str(meta.get("integration_base") or "").strip()
        if not branch or not worktree:
            return r.fail(f"bead {bead} missing branch/worktree metadata")
        lane = Path(worktree)
        if self._is_primary_path(primary_root, lane):
            return r.fail("work finish refuses the primary worktree")
        if branch in {"main", "master"} or branch == integration:
            return r.fail(f"work finish refuses permanent branch {branch}")
        if pr_number:
            viewed = u.Cli.capture(
                ("gh", "pr", "view", pr_number, "--json", "state,mergedAt"),
                cwd=primary_root,
            )
            if viewed.failure:
                return r.fail(viewed.error or "failed to inspect PR merge state")
            payload = json.loads(viewed.value or "{}")
            state = str(payload.get("state") or "")
            if state.upper() != "MERGED" and not payload.get("mergedAt"):
                return r.fail(
                    f"work finish requires merged PR #{pr_number}; state={state}"
                )
        else:
            open_prs = u.Cli.capture(
                (
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch,
                    "--state",
                    "open",
                    "--json",
                    "number",
                ),
                cwd=primary_root,
            )
            if open_prs.success and (open_prs.value or "") not in {"", "[]"}:
                return r.fail(f"work finish refuses open PR on {branch}")
        if lane.is_dir():
            if expected:
                head = self._git_head(lane)
                if head.success and head.value != expected:
                    return r.fail(
                        "CAS failed before finish: "
                        f"expected {expected} head={head.value}"
                    )
            removed = FlextInfraWorktreeService(
                workspace_root=primary_root,
                operation=c.Infra.WorktreeOperation.REMOVE,
                branch=branch,
                apply_changes=True,
            ).execute()
            if removed.failure:
                return r.fail(removed.error or f"failed to remove lane {branch}")
        if expected:
            deleted = u.Infra.git_capture(
                primary_root, ("update-ref", "-d", f"refs/heads/{branch}", expected)
            )
            if deleted.failure:
                exists = u.Infra.git_run(
                    primary_root,
                    ("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"),
                )
                if exists.success and exists.value.exit_code == 0:
                    return r.fail(
                        deleted.error or f"failed to delete local ref {branch}"
                    )
        notes = (
            f"work finish: cmd=make work WHAT=finish cwd={primary_root} exit=0 "
            f"decisive=removed {worktree} branch={branch}"
        )
        updated = u.Infra.beads_update_lane(
            bead,
            metadata={"worktree": "removed", "head_oid": expected or ""},
            notes=notes,
            root=self.workspace_root,
        )
        if updated.failure:
            return r.fail(updated.error or "failed to record finish on bead")
        return r.ok(f"FINISHED BRANCH={branch} WORKTREE={worktree}")


__all__: list[str] = ["FlextInfraWorkSagaFinish"]
