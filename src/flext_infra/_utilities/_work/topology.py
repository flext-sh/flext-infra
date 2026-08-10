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

    @staticmethod
    def _lane_role(metadata: dict[str, object]) -> p.Result[str]:
        role = str(metadata.get("role") or "").strip()
        declared = tuple(item.value for item in c.Infra.WorkLaneRole)
        if role and role not in declared:
            return r.fail(f"unknown lane role on bead metadata: {role}")
        return r.ok(role)

    @staticmethod
    def _epic_binding(metadata: dict[str, object]) -> p.Result[m.Infra.EpicLaneBinding]:
        fields = {
            key: str(metadata.get(key) or "").strip()
            for key in ("epic_bead", "epic_branch", "epic_worktree", "child_slug")
        }
        missing = sorted(key for key, value in fields.items() if not value)
        if missing:
            return r.fail(f"child lane metadata missing {', '.join(missing)}")
        return r.ok(
            m.Infra.EpicLaneBinding(
                epic_bead=fields["epic_bead"],
                epic_branch=fields["epic_branch"],
                epic_worktree=Path(fields["epic_worktree"]),
                child_slug=fields["child_slug"],
            )
        )

    @classmethod
    def _bound_child_topology(
        cls, primary_root: Path, metadata: dict[str, object], lane: Path
    ) -> p.Result[Path]:
        binding = cls._epic_binding(metadata)
        if binding.failure:
            return r.fail(binding.error or "invalid child lane metadata")
        epic = cls._bound_registered_lane(
            primary_root, binding.value.epic_branch, str(binding.value.epic_worktree)
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
        cls, primary_root: Path, metadata: dict[str, object], lane: Path
    ) -> p.Result[str]:
        role = cls._lane_role(metadata)
        if role.failure:
            return r.fail(role.error or "invalid lane role")
        if role.value != c.Infra.WorkLaneRole.CHILD:
            return r.ok(role.value)
        checked = cls._bound_child_topology(primary_root, metadata, lane)
        if checked.failure:
            return r.fail(checked.error or "child lane topology validation failed")
        return r.ok(role.value)

    @staticmethod
    def _typed_metadata(payload: dict[str, object]) -> dict[str, object]:
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            return {}
        return {str(key): value for key, value in metadata.items()}
