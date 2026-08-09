"""Shared helpers for the make work saga."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import FlextInfraWorktreeService, c, m, u

if TYPE_CHECKING:
    from flext_infra import p

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class FlextInfraWorkSagaCommon:
    """Resolve bases, branches, and primary-worktree safety."""

    workspace_root: Path
    base: str | None
    bead: str | None
    kind: c.Infra.WorkKind | None
    name: str | None
    branch: str | None

    def _primary_root(self) -> p.Result[Path]:
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=self.workspace_root)
        )
        if primary.failure:
            return r[Path].fail(primary.error or "failed to resolve primary worktree")
        return r[Path].ok(primary.value.primary_root)

    def _resolve_integration_base(self, primary_root: Path) -> p.Result[str]:
        explicit = (self.base or "").strip()
        if explicit:
            return r.ok(explicit)
        cursor = primary_root.resolve()
        for candidate in (cursor, *cursor.parents):
            manifest = candidate / "config" / "workspace.yaml"
            if not manifest.is_file():
                continue
            loaded = u.Cli.files_read_yaml(manifest)
            if loaded.failure:
                return r.fail(loaded.error or f"failed to read {manifest}")
            payload = loaded.value
            if not isinstance(payload, dict):
                continue
            integration = payload.get("integration")
            if isinstance(integration, dict):
                branch = integration.get("branch")
                if isinstance(branch, str) and branch.strip():
                    return r.ok(branch.strip())
        return r.ok("HEAD")

    @staticmethod
    def _git_integration_ref(primary_root: Path, base: str) -> str:
        """Map a logical integration name to the Git ref used for lane creation.

        Prefer origin/<branch> when the remote-tracking ref exists so a stale
        local integration branch cannot seed new lanes after `git fetch`.
        Metadata keeps the logical name; only Git operations use this ref.
        """
        cleaned = base.strip()
        if not cleaned or cleaned == "HEAD" or cleaned.startswith("origin/"):
            return cleaned
        remote = f"origin/{cleaned}"
        checked = u.Infra.git_ref_exists(
            m.Infra.GitRefRequest(
                repo_root=primary_root, reference=f"refs/remotes/{remote}"
            )
        )
        if checked.success and checked.value.value:
            return remote
        return cleaned

    def _validated_kind_slug(self) -> p.Result[tuple[c.Infra.WorkKind, str]]:
        if self.kind is None:
            return r.fail("work start requires --kind")
        # Why: mro-5bts the service model stores enum values, so re-enter the
        # enum here and keep every downstream saga step typed.
        kind = c.Infra.WorkKind(self.kind)
        slug = (self.name or "").strip().lower()
        if not slug:
            return r.fail("work start requires --name")
        if slug in c.Infra.WORK_FORBIDDEN_SLUGS:
            return r.fail(f"forbidden work slug: {slug}")
        if not _SLUG_RE.fullmatch(slug):
            return r.fail(f"invalid work slug (kebab-case required): {slug}")
        return r.ok((kind, slug))

    @staticmethod
    def _branch_name(kind: c.Infra.WorkKind, slug: str) -> str:
        return f"{kind.value}/{slug}"

    def _resolve_lane_branch(self) -> p.Result[str]:
        explicit = (self.branch or "").strip()
        if explicit:
            return r.ok(explicit)
        bead = (self.bead or "").strip()
        if bead:
            shown = u.Infra.beads_show_json(bead, root=self.workspace_root)
            if shown.success:
                metadata = shown.value.get("metadata")
                if isinstance(metadata, dict):
                    stored = metadata.get("branch")
                    if isinstance(stored, str) and stored.strip():
                        return r.ok(stored.strip())
        kind_slug = self._validated_kind_slug()
        if kind_slug.failure:
            return r.fail(kind_slug.error or "unable to resolve lane branch")
        kind, slug = kind_slug.value
        return r.ok(self._branch_name(kind, slug))

    @staticmethod
    def _is_primary_path(primary_root: Path, lane: Path) -> bool:
        return lane.resolve() == primary_root.resolve()

    @staticmethod
    def _git_head(root: Path) -> p.Result[str]:
        oid = u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=root))
        if oid.failure:
            return r.fail(oid.error or "failed to resolve HEAD")
        return r.ok(oid.value.oid)

    @staticmethod
    def _refuse_permanent_branch(branch: str, integration: str) -> p.Result[bool]:
        cleaned_branch = branch.strip()
        cleaned_integration = integration.strip()
        if cleaned_branch in {"main", "master"} or (
            cleaned_integration and cleaned_branch == cleaned_integration
        ):
            return r.fail(f"work refuses permanent branch {cleaned_branch}")
        return r.ok(True)

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
        """Return the validated topology role one lane records on its bead."""
        role = str(metadata.get("role") or "").strip()
        declared = tuple(item.value for item in c.Infra.WorkLaneRole)
        if role and role not in declared:
            return r.fail(f"unknown lane role on bead metadata: {role}")
        return r.ok(role)

    @staticmethod
    def _epic_binding(metadata: dict[str, object]) -> p.Result[m.Infra.EpicLaneBinding]:
        """Read the typed epic binding a child lane records on its bead."""
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
        """Prove one child lane still sits under its registered epic lane."""
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
        """Validate the recorded epic/child topology against Git's registry."""
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
        """Return one bead's metadata mapping with string keys."""
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            return {}
        return {str(key): value for key, value in metadata.items()}

    @staticmethod
    def _ensure_clean(lane: Path) -> p.Result[bool]:
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=lane))
        if status.failure:
            return r.fail(status.error or f"failed to inspect {lane}")
        if status.value.dirty:
            return r.fail("work land/finish requires a clean lane worktree")
        return r.ok(True)

    @staticmethod
    def _format_receipt(
        *,
        bead: str,
        operation: c.Infra.WorkOperation,
        primary: Path,
        worktree: str,
        branch: str,
        base: str,
        head_oid: str,
        pr: str,
    ) -> str:
        """Render the machine-readable lifecycle receipt of one saga step."""
        return "\n".join((
            f"receipt.bead={bead}",
            f"receipt.operation={operation.value}",
            f"receipt.primary={primary}",
            f"receipt.worktree={worktree}",
            f"receipt.branch={branch}",
            f"receipt.base={base}",
            f"receipt.head_oid={head_oid}",
            f"receipt.pr={pr}",
        ))

    @staticmethod
    def _push_rejection(lane: Path, branch: str, error: str) -> str:
        """Explain a rejected push with the local and remote SHAs that diverged."""
        local = u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=lane))
        remote = u.Infra.git_rev_parse(
            m.Infra.GitCommitishRequest(repo_root=lane, commitish=f"origin/{branch}")
        )
        local_oid = local.value.oid if local.success else "unresolved"
        remote_oid = remote.value.oid if remote.success else "unresolved"
        return f"{error} local={local_oid} remote={remote_oid}"


__all__: list[str] = ["FlextInfraWorkSagaCommon"]
