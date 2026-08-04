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
        if worktree == "removed":
            return r.fail(f"bead {bead} lane worktree already removed")
        if not integration:
            base = self._resolve_integration_base(primary_root)
            if base.failure:
                return r.fail(base.error or "missing integration base")
            integration = base.value
        lane_meta = Path(worktree)
        if self._is_primary_path(primary_root, lane_meta):
            return r.fail("work finish refuses the primary worktree")
        permanent = self._refuse_permanent_branch(branch, integration)
        if permanent.failure:
            return r.fail(
                permanent.error or f"work finish refuses permanent branch {branch}"
            )
        bound = self._bound_registered_lane(primary_root, branch, worktree)
        if bound.failure:
            return r.fail(bound.error or "work finish lane binding failed")
        lane = bound.value
        merged = self._require_merged_pr(primary_root, branch, pr_number)
        if merged.failure:
            return r.fail(merged.error or "work finish PR state check failed")
        if not lane.is_dir():
            return r.fail(f"lane worktree missing: {lane}")
        if not expected:
            return r.fail(f"bead {bead} missing metadata.head_oid for finish CAS")
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to resolve lane HEAD")
        if head.value != expected:
            return r.fail(
                f"CAS failed before finish: expected {expected} head={head.value}"
            )
        removed = FlextInfraWorktreeService(
            workspace_root=primary_root,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            apply_changes=True,
        ).execute()
        if removed.failure:
            return r.fail(removed.error or f"failed to remove lane {branch}")
        deleted = u.Infra.git_capture(
            primary_root, ("update-ref", "-d", f"refs/heads/{branch}", expected)
        )
        if deleted.failure:
            exists = u.Infra.git_run(
                primary_root,
                ("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"),
            )
            if exists.success and exists.value.exit_code == 0:
                return r.fail(deleted.error or f"failed to delete local ref {branch}")
        notes = (
            f"work finish: cmd=make work WHAT=finish cwd={primary_root} exit=0 "
            f"decisive=removed {worktree} branch={branch}"
        )
        updated = u.Infra.beads_update_lane(
            bead,
            metadata={"worktree": "removed", "head_oid": expected},
            notes=notes,
            root=self.workspace_root,
        )
        if updated.failure:
            return r.fail(updated.error or "failed to record finish on bead")
        receipt = self._format_receipt(
            bead=bead,
            operation=c.Infra.WorkOperation.FINISH,
            primary=primary_root,
            worktree=worktree,
            branch=branch,
            base=integration,
            head_oid=expected,
            pr=pr_number,
        )
        return r.ok(f"FINISHED BRANCH={branch} WORKTREE={worktree}\n{receipt}")

    @staticmethod
    def _require_merged_pr(
        primary_root: Path, branch: str, pr_number: str
    ) -> p.Result[bool]:
        """Refuse to retire a lane whose pull request is not merged."""
        if not pr_number:
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
            if open_prs.failure:
                return r.fail(open_prs.error or f"failed to list open PRs for {branch}")
            if (open_prs.value or "").strip() not in {"", "[]"}:
                return r.fail(f"work finish refuses open PR on {branch}")
            return r.ok(True)
        viewed = u.Cli.capture(
            ("gh", "pr", "view", pr_number, "--json", "state,mergedAt,headRefName"),
            cwd=primary_root,
        )
        if viewed.failure:
            return r.fail(viewed.error or "failed to inspect PR merge state")
        payload = json.loads(viewed.value or "{}")
        state = str(payload.get("state") or "")
        head_ref = str(payload.get("headRefName") or "").strip()
        if head_ref and head_ref != branch:
            return r.fail(
                f"work finish PR #{pr_number} head {head_ref} "
                f"does not match lane branch {branch}"
            )
        if state.upper() != "MERGED" and not payload.get("mergedAt"):
            return r.fail(f"work finish requires merged PR #{pr_number}; state={state}")
        return r.ok(True)


__all__: list[str] = ["FlextInfraWorkSagaFinish"]
