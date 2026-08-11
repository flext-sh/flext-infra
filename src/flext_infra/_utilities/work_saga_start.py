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
    def _reusable_lane(
        primary_root: Path, branch: str, canonical: Path
    ) -> p.Result[m.Infra.WorkLaneReuse]:
        """Report whether Git already owns a usable canonical lane.

        Git's worktree registry is the only authority on lane existence. A
        start interrupted after `worktree add` leaves a registered lane whose
        bead carries no metadata, so re-running start adopts that lane instead
        of failing on "worktree lane already exists". A branch registered at
        any other path is a defect and stops the start.
        """
        registered = FlextInfraWorktreeService.registered_lane(
            primary_root, branch, canonical
        )
        if registered.failure:
            error = registered.error or ""
            if error.startswith("worktree branch is not registered"):
                return r.ok(m.Infra.WorkLaneReuse(reused=False, lane_path=canonical))
            return r.fail(error or f"lane {branch} is not usable")
        lane = registered.value
        return r.ok(
            m.Infra.WorkLaneReuse(reused=lane.is_dir(), lane_path=lane)
            if lane.is_dir()
            else m.Infra.WorkLaneReuse(reused=False, lane_path=canonical)
        )

    @staticmethod
    def _rollback_started_lane(
        primary_root: Path,
        identity: m.Infra.WorkLaneIdentity,
        *,
        reused: bool,
        error: str | None,
    ) -> str:
        """Undo a lane this start created when its bead registration failed."""
        branch = identity.branch
        reason = error or "failed to register lane on bead"
        if reused:
            return reason
        removed = FlextInfraWorktreeService(
            workspace_root=primary_root,
            operation=c.Infra.WorktreeOperation.REMOVE,
            branch=branch,
            lane_dir=identity.lane_dir,
            parent_lane=identity.parent_lane,
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
        shown = u.Infra.beads_show_json(bead, root=primary_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        derived = self._lane_identity(primary_root, shown.value, bead, kind, slug)
        if derived.failure:
            return r.fail(derived.error or "failed to derive the lane path")
        identity = derived.value
        branch = identity.branch
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
                    return r.fail(
                        "workspace lane matrix requires exactly one root entry"
                    )
                if root_entries[0].branch != branch:
                    return r.fail(
                        f"bead {bead} already bound to branch {root_entries[0].branch} "
                        f"at {existing_wt}"
                    )
            elif existing_wt:
                # Why: a lane registered by an earlier engine carries no matrix.
                # Adopting it is safe ONLY when it is the very lane this bead
                # derives, so start upgrades that metadata in place; a record
                # pointing anywhere else is a real double-binding and stops here.
                existing_branch = str(metadata.get("branch") or "").strip()
                if Path(existing_wt).resolve() != identity.lane_path.resolve() or (
                    existing_branch and existing_branch != branch
                ):
                    return r.fail(
                        f"bead {bead} already bound to branch "
                        f"{existing_branch or 'unknown'} at {existing_wt}"
                    )
        # Why: a child lane lives inside its parent epic lane checkout, so an
        # unclean parent would fold uncommitted parent work into the child.
        candidate_reuse = self._reusable_lane(primary_root, branch, identity.lane_path)
        if (
            identity.parent_bead
            and candidate_reuse.success
            and not candidate_reuse.value.reused
        ):
            parent_status = u.Infra.git_status(
                m.Infra.GitStatusRequest(repo_root=identity.parent_lane)
            )
            if parent_status.failure:
                return r.fail(
                    parent_status.error
                    or f"failed to inspect parent epic lane {identity.parent_lane}"
                )
            if parent_status.value.dirty:
                return r.fail(
                    f"parent epic lane {identity.parent_bead} is dirty at "
                    f"{identity.parent_lane}; commit or clean it before starting "
                    f"the child lane {branch}"
                )
        base = identity.base_branch
        reusable = candidate_reuse
        if reusable.failure:
            return r.fail(reusable.error or f"lane {branch} is not usable")
        reused = reusable.value.reused
        if not reused:
            fetched = u.Infra.git_fetch_origin(
                m.Infra.GitRepoRequest(repo_root=primary_root)
            )
            if fetched.failure:
                return r.fail(fetched.error or "work start failed to fetch origin")
            created = FlextInfraWorktreeService(
                workspace_root=primary_root,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base=self._git_integration_ref(primary_root, base),
                lane_dir=identity.lane_dir,
                parent_lane=identity.parent_lane,
                apply_changes=True,
            ).execute()
            if created.failure:
                return r.fail(created.error or f"failed to start lane {branch}")
            lane = Path(created.value)
        else:
            lane = reusable.value.lane_path
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
        root_entry = next(
            entry for entry in matrix.value.entries if entry.project == "."
        )
        decisive = "lane-reused" if reused else "lane-ready"
        notes = (
            f"work start: cmd=make work WHAT=start cwd={lane} "
            f"branch={branch} base={base} exit=0 decisive={decisive} "
            f"head={root_entry.head_oid}"
        )
        updated = u.Infra.beads_update_lane(
            bead,
            metadata={
                "worktree": str(lane),
                # Why: mro-dipb.1 kind may arrive as str; the enum value is the
                # only shape the parent-chain re-derivation accepts.
                "kind": str(identity.kind),
                "slug": slug,
                "integration_base": base,
                c.Infra.WORK_BEADS_MATRIX_KEY: matrix.value.model_dump_json(),
            },
            labels=(f"branch:{branch}",),
            notes=notes,
            root=primary_root,
        )
        if updated.failure:
            return r.fail(
                self._rollback_started_lane(
                    primary_root, identity, reused=reused, error=updated.error
                )
            )
        receipt = self._format_receipt(
            bead=bead,
            operation=c.Infra.WorkOperation.START,
            primary=primary_root,
            worktree=str(lane),
            branch=branch,
            base=base,
            head_oid=root_entry.head_oid,
            pr="",
        )
        return r.ok(
            f"LANE_ID={bead} BRANCH={branch} WORKTREE={lane} "
            f"BASE={base} HEAD={root_entry.head_oid}\n{receipt}"
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
            bound = self._bound_root_matrix(primary_root, bead, meta)
            if bound.failure:
                return r.fail(bound.error or "work status root lane binding failed")
            identity = bound.value.identity
            lane = bound.value.lane
            matrix = bound.value.matrix
            children = FlextInfraWorktreeService.child_lanes(primary_root, lane)
            if children.failure:
                return r.fail(children.error or "failed to list child lanes")
            lines.extend((
                f"bead: {bead}",
                f"bead_status: {shown.value.get('status')}",
                f"assignee: {shown.value.get('assignee')}",
                f"metadata.branch: {identity.branch}",
                f"metadata.worktree: {lane}",
                f"branch: {identity.branch}",
                f"lane_kind: {identity.kind}",
                f"lane_parent_bead: {identity.parent_bead}",
                f"lane_parent_branch: {identity.parent_branch}",
                f"lane_parent: {identity.parent_lane}",
                f"lane_base: {identity.base_branch}",
            ))
            lines.extend(f"child_lane: {child}" for child in children.value)
            lines.extend(
                "matrix: "
                f"project={entry.project} branch={entry.branch} "
                f"head_oid={entry.head_oid} pr_number={entry.pr_number} "
                f"pr_url={entry.pr_url} state={entry.state}"
                for entry in matrix.entries
            )
        listed = FlextInfraWorktreeService(
            workspace_root=primary_root, operation=c.Infra.WorktreeOperation.LIST
        ).execute()
        if listed.failure:
            return r.fail(listed.error or "failed to list root worktrees")
        lines.extend(("worktrees:", listed.value.rstrip()))
        lines.append(
            f"primary_checkout: {self.workspace_root.resolve() == primary_root.resolve()}"
        )
        return r.ok("\n".join(lines))


__all__: list[str] = ["FlextInfraWorkSagaStart"]
