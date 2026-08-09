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
        shown = u.Infra.beads_show_json(bead, root=primary_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        meta = shown.value.get("metadata")
        if not isinstance(meta, dict):
            return r.fail(f"bead {bead} has no lane metadata; run work start first")
        bound_matrix = self._bound_root_matrix(primary_root, bead, meta)
        if bound_matrix.failure:
            return r.fail(bound_matrix.error or "work land root lane binding failed")
        identity = bound_matrix.value.identity
        lane = bound_matrix.value.lane
        matrix = bound_matrix.value.matrix
        root_entry = next(entry for entry in matrix.entries if entry.project == ".")
        branch = root_entry.branch
        recorded_integration = str(meta.get("integration_base") or "").strip()
        # Why: a lane always integrates into the branch its role names — the
        # repository integration branch for a top-level epic, the parent epic
        # branch for every nested lane.
        integration = identity.base_branch
        if (
            recorded_integration
            and recorded_integration not in {"HEAD", integration}
            and recorded_integration != integration
        ):
            return r.fail(
                "work land refuses metadata.integration_base drift: "
                f"metadata={recorded_integration} ssot={integration}"
            )
        permanent = self._refuse_permanent_branch(branch, integration)
        if permanent.failure:
            return r.fail(
                permanent.error or f"work land refuses permanent branch {branch}"
            )
        if self._is_primary_path(primary_root, lane):
            return r.fail("work land refuses the primary worktree")
        for entry in matrix.entries:
            project_root = self._matrix_project_root(lane, entry.project)
            if project_root.failure:
                return r.fail(project_root.error or "matrix project is invalid")
            clean = self._ensure_clean(project_root.value)
            if clean.failure:
                return r.fail(
                    clean.error or f"matrix project is dirty: {entry.project}"
                )
            current = self._git_head(project_root.value)
            if current.failure:
                return r.fail(
                    current.error or f"failed to resolve matrix HEAD: {entry.project}"
                )
            if current.value != entry.head_oid:
                contains = u.Infra.git_is_ancestor(
                    m.Infra.GitCommitishRequest(
                        repo_root=project_root.value, commitish=entry.head_oid
                    )
                )
                if contains.failure or not contains.value.value:
                    return r.fail(
                        f"CAS failed for {entry.project}: expected={entry.head_oid} "
                        f"head={current.value}"
                    )
        synced = FlextInfraWorktreeService(
            workspace_root=primary_root,
            operation=c.Infra.WorktreeOperation.UPDATE,
            branch=branch,
            base=self._git_integration_ref(primary_root, integration),
            lane_dir=identity.lane_dir,
            parent_lane=identity.parent_lane,
            apply_changes=True,
        ).execute()
        if synced.failure:
            return r.fail(synced.error or "work land sync failed")
        pushed = u.Infra.git_push_upstream(
            m.Infra.GitPushRequest(repo_root=lane, branch=branch)
        )
        if pushed.failure:
            return r.fail(
                self._push_rejection(
                    lane, branch, pushed.error or f"failed to push {branch}"
                )
            )
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to resolve pushed HEAD")
        pr_base = integration
        if pr_base == "HEAD":
            resolved_base = u.Infra.git_abbrev_ref_head(
                m.Infra.GitRepoRequest(repo_root=primary_root)
            )
            if resolved_base.failure:
                return r.fail(
                    resolved_base.error or "failed to resolve HEAD for PR base"
                )
            pr_base = resolved_base.value.text
            if not pr_base or pr_base == "HEAD":
                return r.fail(
                    "work land cannot open a PR with unresolved integration base HEAD"
                )
        pr = u.Infra.run_github_pull_request(
            m.Infra.GithubPullRequestRequest(
                repo_root=str(primary_root),
                action=c.Infra.PullRequestAction.CREATE,
                base=pr_base,
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
        landed_entries: list[m.Infra.WorkLaneEntry] = [
            root_entry.model_copy(
                update={
                    "head_oid": head.value,
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                    "state": "landed",
                }
            )
        ]
        for entry in matrix.entries:
            if entry.project == ".":
                continue
            project_root = self._matrix_project_root(lane, entry.project)
            if project_root.failure:
                return r.fail(project_root.error or "matrix project is invalid")
            pushed_entry = u.Infra.git_push_upstream(
                m.Infra.GitPushRequest(
                    repo_root=project_root.value, branch=entry.branch
                )
            )
            if pushed_entry.failure:
                return r.fail(
                    self._push_rejection(
                        project_root.value,
                        entry.branch,
                        pushed_entry.error or f"failed to push {entry.project}",
                    )
                )
            entry_head = self._git_head(project_root.value)
            if entry_head.failure:
                return r.fail(
                    entry_head.error
                    or f"failed to resolve matrix HEAD: {entry.project}"
                )
            entry_pr = u.Infra.run_github_pull_request(
                m.Infra.GithubPullRequestRequest(
                    repo_root=str(project_root.value),
                    action=c.Infra.PullRequestAction.CREATE,
                    base=pr_base,
                    head=entry.branch,
                    title=f"{entry.branch}: lane land",
                    body=f"Automated land for bead {bead} ({entry.branch}).",
                    draft=False,
                )
            )
            entry_observed = self._observe_open_pr(project_root.value, entry.branch)
            if entry_pr.failure and entry_observed.failure:
                return r.fail(
                    entry_pr.error or entry_observed.error or "work land PR failed"
                )
            entry_pr_number, entry_pr_url = (
                entry_observed.value if entry_observed.success else ("", "")
            )
            landed_entries.append(
                entry.model_copy(
                    update={
                        "head_oid": entry_head.value,
                        "pr_number": entry_pr_number,
                        "pr_url": entry_pr_url,
                        "state": "landed",
                    }
                )
            )
        landed_matrix = m.Infra.WorkLaneMatrix(entries=tuple(landed_entries))
        meta_update = {
            "integration_base": pr_base,
            c.Infra.WORK_BEADS_MATRIX_KEY: landed_matrix.model_dump_json(),
        }
        labels: tuple[str, ...] = (f"pr:{pr_number}",) if pr_number else ()
        notes = (
            f"work land: cmd=make work WHAT=land cwd={lane} exit=0 "
            f"decisive=PR {pr_url or pr_number or 'pending'} sha={head.value}"
        )
        updated = u.Infra.beads_update_lane(
            bead, metadata=meta_update, labels=labels, notes=notes, root=primary_root
        )
        if updated.failure:
            return r.fail(updated.error or "failed to record land on bead")
        receipt = self._format_receipt(
            bead=bead,
            operation=c.Infra.WorkOperation.LAND,
            primary=primary_root,
            worktree=str(lane),
            branch=branch,
            base=pr_base,
            head_oid=head.value,
            pr=pr_number,
        )
        return r.ok(
            f"BRANCH={branch} HEAD={head.value} PR_NUMBER={pr_number} "
            f"PR_URL={pr_url}\n{receipt}"
        )


__all__: list[str] = ["FlextInfraWorkSagaPublish"]
