"""Registered epic and child topology proofs for the work saga."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, m

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkTopology:
    """Prove recorded lane topology against Git's worktree registry."""

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
