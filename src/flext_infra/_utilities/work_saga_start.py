"""make work WHAT=start and WHAT=status saga steps."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, m, u
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
        shown = u.Infra.beads_show_json(bead, root=primary_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        metadata = shown.value.get("metadata")
        if isinstance(metadata, dict):
            existing_wt = str(metadata.get("worktree") or "").strip()
            existing_matrix = self._matrix_from_metadata(metadata)
            if existing_wt and existing_matrix.success:
                root_entries = [
                    entry
                    for entry in existing_matrix.value.entries
                    if entry.project == "."
                ]
                if len(root_entries) != 1:
                    return r.fail("workspace lane matrix requires exactly one root entry")
                if root_entries[0].branch != branch:
                    return r.fail(
                        f"bead {bead} already bound to branch {root_entries[0].branch} "
                        f"at {existing_wt}"
                    )
            elif existing_wt:
                return r.fail(
                    existing_matrix.error
                    or "bead lane metadata is missing serialized matrix"
                )
        base = self._resolve_integration_base(primary_root)
        if base.failure:
            return r.fail(base.error or "failed to resolve integration base")
        reused = self._reusable_lane(primary_root, branch)
        if reused is None:
            fetched = u.Infra.git_fetch_origin(
                m.Infra.GitRepoRequest(repo_root=primary_root)
            )
            if fetched.failure:
                return r.fail(fetched.error or "work start failed to fetch origin")
            created = FlextInfraWorktreeService(
                workspace_root=primary_root,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=self._git_integration_ref(primary_root, base.value),
                apply_changes=True,
            ).execute()
            if created.failure:
                return r.fail(created.error or f"failed to start lane {branch}")
            lane = Path(created.value)
        else:
            lane = reused
        if self._is_primary_path(primary_root, lane):
            return r.fail("work start refused to use the primary worktree as a lane")
        # Why: mro-c6di — every maintained worktree runs `make setup`, so start
        # owns that guarantee for the lane it hands back. An adopted lane used to
        # skip provisioning entirely and was handed over with whatever
        # environment an interrupted start had left behind.
        prepared = FlextInfraWorktreeService.setup_lane(primary_root, lane)
        if prepared.failure:
            # Why: provisioning is RESUMABLE, so a failed `make setup` must not
            # destroy the checkout it already produced. Rolling back here forced
            # a manual repair and re-clone after any transient setup failure (a
            # stale submodule checkout, a network blip). The lane and its branch
            # are kept exactly as they are and start stays idempotent: fix the
            # cause, run the same command again, and it resumes from the
            # existing checkout instead of starting over.
            return r.fail(
                f"{prepared.error or 'failed to provision lane'}; "
                f"lane {branch} preserved at {lane} - resolve the cause and "
                f"re-run the same work start to resume provisioning"
            )
        matrix = self._matrix_for_started_lane(primary_root, lane, branch)
        if matrix.failure:
            return r.fail(matrix.error or "failed to build workspace lane matrix")
        root_entry = next(entry for entry in matrix.value.entries if entry.project == ".")
        decisive = "lane-reused" if reused is not None else "lane-ready"
        notes = (
            f"work start: cmd=make work WHAT=start cwd={lane} "
            f"branch={branch} base={base.value} exit=0 decisive={decisive} "
            f"head={root_entry.head_oid}"
        )
        # Why: mro-dipb.1 kind may arrive as str; coerce like _branch_name.
        kind_value = kind.value
        updated = u.Infra.beads_update_lane(
            bead,
            metadata={
                "worktree": str(lane),
                "kind": kind_value,
                "slug": slug,
                "integration_base": base.value,
                c.Infra.WORK_BEADS_MATRIX_KEY: matrix.value.model_dump_json(),
            },
            labels=(f"branch:{branch}",),
            notes=notes,
            root=primary_root,
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
            head_oid=root_entry.head_oid,
            pr="",
        )
        return r.ok(
            f"LANE_ID={bead} BRANCH={branch} WORKTREE={lane} "
            f"BASE={base.value} HEAD={root_entry.head_oid}\n{receipt}"
        )

    def _status(self, primary_root: Path) -> p.Result[str]:
        bead = (self.bead or "").strip()
        lines: list[str] = ["work status"]
        if bead:
            shown = u.Infra.beads_show_json(bead, root=primary_root)
            if shown.failure:
                return r.fail(shown.error or f"unknown bead {bead}")
            meta = shown.value.get("metadata")
            if not isinstance(meta, dict):
                return r.fail(f"bead {bead} has no root lane metadata")
            bound = self._bound_root_matrix(primary_root, meta)
            if bound.failure:
                return r.fail(bound.error or "work status root lane binding failed")
            lane, matrix = bound.value
            lines.extend((
                f"bead: {bead}",
                f"bead_status: {shown.value.get('status')}",
                f"assignee: {shown.value.get('assignee')}",
                f"metadata.branch: {matrix.entries[0].branch}",
                f"metadata.worktree: {lane}",
                f"branch: {matrix.entries[0].branch}",
            ))
            for entry in matrix.entries:
                lines.append(
                    "matrix: "
                    f"project={entry.project} branch={entry.branch} "
                    f"head_oid={entry.head_oid} pr_number={entry.pr_number} "
                    f"pr_url={entry.pr_url} state={entry.state}"
                )
        listed = FlextInfraWorktreeService(
            workspace_root=primary_root, operation=c.Infra.WorktreeOperation.LIST
        ).execute()
        if listed.failure:
            return r.fail(listed.error or "failed to list root worktrees")
        lines.extend(("worktrees:", listed.value.rstrip()))
        lines.append(f"primary_checkout: {self.workspace_root.resolve() == primary_root.resolve()}")
        return r.ok("\n".join(lines))


__all__: list[str] = ["FlextInfraWorkSagaStart"]
