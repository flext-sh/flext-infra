"""Registered epic and child topology proofs for the work saga."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, m, u
from flext_infra._utilities._work.ownership import FlextInfraWorkOwnership

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkTopology(FlextInfraWorkOwnership):
    """Prove recorded lane topology against Git's worktree registry."""

    workspace_root: Path

    def _live_child_topology(
        self,
        primary_root: Path,
        child_issue: m.Infra.BeadIssue,
        child: m.Infra.ChildLaneTopology,
    ) -> p.Result[Path]:
        if child_issue.parent != child.epic_bead:
            return r.fail(
                f"child bead {child_issue.id} parent mismatch: "
                f"live={child_issue.parent or 'none'} expected={child.epic_bead}"
            )
        shown = u.Infra.beads_show(child.epic_bead, root=self.workspace_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown epic bead {child.epic_bead}")
        epic = shown.value
        if epic.issue_type != "epic":
            return r.fail(f"bead {epic.id} must have issue_type=epic")
        if epic.status not in c.Infra.WORK_ACTIVE_ISSUE_STATUSES:
            return r.fail(f"epic bead {epic.id} is not active: {epic.status}")
        metadata = epic.metadata
        if not isinstance(metadata, m.Infra.ReadyLaneMetadata):
            return r.fail(f"epic bead {epic.id} lane is not ready")
        if not isinstance(metadata.topology, m.Infra.EpicLaneTopology):
            return r.fail(f"epic bead {epic.id} lane role is not epic")
        if metadata.topology.epic_bead != epic.id:
            return r.fail(f"epic bead {epic.id} topology owner mismatch")
        if metadata.branch != child.epic_branch:
            return r.fail(f"epic bead {epic.id} branch binding mismatch")
        if metadata.worktree.resolve() != child.epic_worktree.resolve():
            return r.fail(f"epic bead {epic.id} worktree binding mismatch")
        ownership = self._owned_reservation(epic.id, metadata.branch, metadata.worktree)
        if ownership.failure:
            return r.fail(ownership.error or "epic reservation ownership failed")
        bound = self._bound_registered_lane(
            primary_root, metadata.branch, str(metadata.worktree)
        )
        if bound.failure:
            return r.fail(bound.error or "epic registry binding failed")
        head = u.Cli.capture(("git", "rev-parse", "HEAD"), cwd=bound.value)
        if head.failure or head.value != metadata.head_oid:
            return r.fail(f"epic bead {epic.id} HEAD binding mismatch")
        return r.ok(bound.value)

    @staticmethod
    def _bound_registered_lane(
        primary_root: Path, branch: str, worktree: str
    ) -> p.Result[Path]:
        registered = FlextInfraWorktreeService.registered_lane(primary_root, branch)
        if registered.failure:
            return r.fail(
                registered.error or f"worktree branch is not registered: {branch}"
            )
        meta_lane = Path(worktree).expanduser().resolve()
        registry_lane = registered.value.resolve()
        if meta_lane != registry_lane:
            return r.fail(
                "work metadata worktree does not match registered lane: "
                f"metadata={meta_lane} registered={registry_lane}"
            )
        return r.ok(registry_lane)

    @classmethod
    def _bound_child_topology(
        cls, primary_root: Path, topology: m.Infra.ChildLaneTopology, lane: Path
    ) -> p.Result[Path]:
        epic = cls._bound_registered_lane(
            primary_root, topology.epic_branch, str(topology.epic_worktree)
        )
        if epic.failure:
            return r.fail(
                "child lane epic binding failed: "
                f"{epic.error or 'epic lane is not registered'}"
            )
        container = epic.value / c.Infra.WORKTREES_DIRNAME
        if not lane.resolve().is_relative_to(container):
            return r.fail(
                f"child lane {lane} is not nested under epic lane {epic.value}"
            )
        return r.ok(epic.value)

    @classmethod
    def _validated_lane_topology(
        cls,
        primary_root: Path,
        metadata: (
            m.Infra.PendingLaneReservation
            | m.Infra.ReadyLaneMetadata
            | m.Infra.FailedLaneMetadata
        ),
        lane: Path,
    ) -> p.Result[c.Infra.WorkLaneRole]:
        match metadata.topology:
            case m.Infra.ChildLaneTopology() as child:
                checked = cls._bound_child_topology(primary_root, child, lane)
                if checked.failure:
                    return r.fail(
                        checked.error or "child lane topology validation failed"
                    )
                return r.ok(c.Infra.WorkLaneRole.CHILD)
            case m.Infra.EpicLaneTopology():
                return r.ok(c.Infra.WorkLaneRole.EPIC)
            case m.Infra.PlainLaneTopology():
                return r.ok(c.Infra.WorkLaneRole.PLAIN)
