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
    epic: str | None

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

    def _registered_epic(
        self, primary_root: Path, epic_bead: str
    ) -> p.Result[tuple[str, Path]]:
        """Resolve the registered epic lane a child lane must be derived from."""
        shown = u.Infra.beads_show_json(epic_bead, root=self.workspace_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown epic bead {epic_bead}")
        metadata = self._typed_metadata(shown.value)
        role = self._lane_role(metadata)
        if role.failure:
            return r.fail(role.error or "invalid epic lane role")
        if role.value == c.Infra.WorkLaneRole.CHILD:
            return r.fail(f"bead {epic_bead} is a child lane and owns no children")
        epic_branch = str(metadata.get("branch") or "").strip()
        epic_worktree = str(metadata.get("worktree") or "").strip()
        if not epic_branch or not epic_worktree or epic_worktree == "removed":
            return r.fail(
                f"epic bead {epic_bead} is not a registered lane; "
                "run work start for the epic first"
            )
        bound = self._bound_registered_lane(primary_root, epic_branch, epic_worktree)
        if bound.failure:
            return r.fail(
                bound.error or f"epic lane {epic_branch} is not registered in Git"
            )
        if not bound.value.is_dir():
            return r.fail(f"epic lane worktree missing: {bound.value}")
        return r.ok((epic_branch, bound.value))

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
        epic_bead = (self.epic or "").strip()
        epic_lane: Path | None = None
        base = ""
        if epic_bead:
            if epic_bead == bead:
                return r.fail("work start refuses a bead that is its own epic")
            if (self.base or "").strip():
                return r.fail(
                    "work start derives a child base from its epic lane; drop --base"
                )
            resolved_epic = self._registered_epic(primary_root, epic_bead)
            if resolved_epic.failure:
                return r.fail(resolved_epic.error or "unresolved epic lane")
            # Why: the child base is the epic branch Git already has checked
            # out in the epic lane, never a literal the caller supplies.
            base, epic_lane = resolved_epic.value
            marked = u.Infra.beads_update_lane(
                epic_bead,
                metadata={"role": c.Infra.WorkLaneRole.EPIC.value},
                notes=(
                    f"work start: cmd=make work WHAT=start EPIC={epic_bead} "
                    f"decisive=epic-role-registered child={bead} branch={branch}"
                ),
                root=self.workspace_root,
            )
            if marked.failure:
                return r.fail(
                    marked.error or f"failed to register epic role on {epic_bead}"
                )
        else:
            resolved_base = self._resolve_integration_base(primary_root)
            if resolved_base.failure:
                return r.fail(
                    resolved_base.error or "failed to resolve integration base"
                )
            base = resolved_base.value
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
                base=(
                    base
                    if epic_lane is not None
                    else self._git_integration_ref(primary_root, base)
                ),
                epic_lane=epic_lane,
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
        head = self._git_head(lane)
        if head.failure:
            return r.fail(head.error or "failed to read lane HEAD")
        decisive = "lane-reused" if reused is not None else "lane-ready"
        notes = (
            f"work start: cmd=make work WHAT=start cwd={lane} "
            f"branch={branch} base={base} exit=0 decisive={decisive} "
            f"head={head.value}"
        )
        # Why: mro-dipb.1 kind may arrive as str; coerce like _branch_name.
        kind_value = kind.value
        lane_metadata: dict[str, str] = {
            "branch": branch,
            "worktree": str(lane),
            "kind": kind_value,
            "slug": slug,
            "integration_base": base,
            "head_oid": head.value,
        }
        labels: tuple[str, ...] = (f"branch:{branch}",)
        if epic_lane is not None:
            binding = m.Infra.EpicLaneBinding(
                epic_bead=epic_bead,
                epic_branch=base,
                epic_worktree=epic_lane,
                child_slug=slug,
            )
            lane_metadata |= {
                "role": c.Infra.WorkLaneRole.CHILD.value,
                "epic_bead": binding.epic_bead,
                "epic_branch": binding.epic_branch,
                "epic_worktree": str(binding.epic_worktree),
                "child_slug": binding.child_slug,
            }
            labels = (*labels, f"epic:{epic_bead}")
        updated = u.Infra.beads_update_lane(
            bead,
            metadata=lane_metadata,
            labels=labels,
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
            base=base,
            head_oid=head.value,
            pr="",
        )
        epic_selector = f" EPIC={epic_bead}" if epic_bead else ""
        return r.ok(
            f"LANE_ID={bead} BRANCH={branch} WORKTREE={lane} "
            f"BASE={base} HEAD={head.value}{epic_selector}\n{receipt}"
        )

    @classmethod
    def _reported_topology(
        cls, primary_root: Path, metadata: dict[str, object]
    ) -> list[str]:
        """Report the epic topology one bead claims against Git's registry.

        Silent for a lane that declares no role, so a plain lane keeps the
        exact status output it had before nested lanes existed.
        """
        role = cls._lane_role(metadata)
        if role.failure:
            return [f"epic_topology: error={role.error}"]
        if not role.value:
            return []
        worktree = str(metadata.get("worktree") or "").strip()
        if not worktree or worktree == "removed":
            return [f"epic_topology: role={role.value} lane=absent"]
        lane = Path(worktree)
        if role.value == c.Infra.WorkLaneRole.CHILD:
            checked = cls._bound_child_topology(primary_root, metadata, lane)
            if checked.failure:
                return [f"epic_topology: error={checked.error}"]
            return [f"epic_topology: child of {checked.value}"]
        children = FlextInfraWorktreeService.registered_children(primary_root, lane)
        if children.failure:
            return [f"epic_topology: error={children.error}"]
        rendered = " ".join(str(child) for child in children.value)
        return [
            f"epic_topology: epic children={len(children.value)} {rendered}".rstrip()
        ]

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
                lines.extend(self._reported_topology(primary_root, meta_obj))
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
