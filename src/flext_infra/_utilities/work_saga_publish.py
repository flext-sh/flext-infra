"""make work WHAT=land saga step."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, m, u
from flext_infra._utilities.work_saga_common import FlextInfraWorkSagaCommon

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkSagaPublish(FlextInfraWorkSagaCommon):
    """Land step for the public work saga."""

    apply_changes: bool

    def _observe_open_pr(
        self, primary_root: Path, branch: str
    ) -> p.Result[tuple[str, str]]:
        listed = u.Cli.capture(
            (
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "number,url",
            ),
            cwd=primary_root,
        )
        if listed.failure:
            return r.fail(listed.error or "failed to list open PRs")
        rows = json.loads(listed.value or "[]")
        if not rows:
            return r.fail(f"no open PR for head {branch}")
        return r.ok((str(rows[0].get("number", "")), str(rows[0].get("url", ""))))

    def _land(self, primary_root: Path) -> p.Result[str]:
        if not self.apply_changes:
            return r.fail("work land requires --apply")
        bead = (self.bead or "").strip()
        if not bead:
            return r.fail("work land requires --bead")
        shown = u.Infra.beads_show_json(bead, root=self.workspace_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        meta = shown.value.get("metadata")
        if not isinstance(meta, dict):
            return r.fail(f"bead {bead} has no lane metadata; run work start first")
        branch = str(meta.get("branch") or "").strip()
        worktree = str(meta.get("worktree") or "").strip()
        integration = str(meta.get("integration_base") or "").strip()
        expected = str(meta.get("head_oid") or "").strip()
        if not branch or not worktree:
            return r.fail(f"bead {bead} missing branch/worktree metadata")
        lane = Path(worktree)
        if self._is_primary_path(primary_root, lane):
            return r.fail("work land refuses the primary worktree")
        if not lane.is_dir():
            return r.fail(f"lane worktree missing: {lane}")
        clean = self._ensure_clean(lane)
        if clean.failure:
            return r.fail(clean.error or "lane is dirty")
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to resolve lane HEAD")
        if expected and head.value != expected:
            contains = u.Infra.git_run(
                lane, ("merge-base", "--is-ancestor", expected, "HEAD")
            )
            if contains.failure or contains.value.exit_code != 0:
                return r.fail(
                    f"CAS failed: metadata.head_oid={expected} head={head.value}"
                )
        if not integration:
            base = self._resolve_integration_base(primary_root)
            if base.failure:
                return r.fail(base.error or "missing integration base")
            integration = base.value
        synced = FlextInfraWorktreeService(
            workspace_root=primary_root,
            operation=c.Infra.WorktreeOperation.UPDATE,
            branch=branch,
            base=integration,
            apply_changes=True,
        ).execute()
        if synced.failure:
            return r.fail(synced.error or "work land sync failed")
        pushed = u.Infra.git_capture(
            lane, ("push", "-u", "origin", f"HEAD:refs/heads/{branch}")
        )
        if pushed.failure:
            return r.fail(pushed.error or f"failed to push {branch}")
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to resolve pushed HEAD")
        pr = u.Infra.run_github_pull_request(
            m.Infra.GithubPullRequestRequest(
                repo_root=str(primary_root),
                action=c.Infra.PullRequestAction.CREATE,
                base=integration if integration != "HEAD" else None,
                head=branch,
                title=f"{branch}: lane land",
                body=f"Automated land for bead {bead} ({branch}).",
                draft=False,
            )
        )
        observed = self._observe_open_pr(primary_root, branch)
        if pr.failure and observed.failure:
            return r.fail(pr.error or observed.error or "work land PR failed")
        pr_number, pr_url = observed.value if observed.success else ("", "")
        meta_update = {"head_oid": head.value, "integration_base": integration}
        labels: tuple[str, ...] = ()
        if pr_number:
            meta_update["pr_number"] = pr_number
            labels = (f"pr:{pr_number}",)
        if pr_url:
            meta_update["pr_url"] = pr_url
        notes = (
            f"work land: cmd=make work WHAT=land cwd={lane} exit=0 "
            f"decisive=PR {pr_url or pr_number or 'pending'} sha={head.value}"
        )
        updated = u.Infra.beads_update_lane(
            bead,
            metadata=meta_update,
            labels=labels,
            notes=notes,
            root=self.workspace_root,
        )
        if updated.failure:
            return r.fail(updated.error or "failed to record land on bead")
        return r.ok(
            f"BRANCH={branch} HEAD={head.value} PR_NUMBER={pr_number} PR_URL={pr_url}"
        )


__all__: list[str] = ["FlextInfraWorkSagaPublish"]
