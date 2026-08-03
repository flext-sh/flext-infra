"""Shared helpers for the make work saga."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, u

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
        return u.Infra.git_primary_worktree_root(self.workspace_root)

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

    def _validated_kind_slug(self) -> p.Result[tuple[c.Infra.WorkKind, str]]:
        if self.kind is None:
            return r.fail("work start requires --kind")
        try:
            kind = (
                self.kind
                if isinstance(self.kind, c.Infra.WorkKind)
                else c.Infra.WorkKind(str(self.kind))
            )
        except ValueError:
            return r.fail(f"invalid work kind: {self.kind}")
        slug = (self.name or "").strip().lower()
        if not slug:
            return r.fail("work start requires --name")
        if slug in c.Infra.WORK_FORBIDDEN_SLUGS:
            return r.fail(f"forbidden work slug: {slug}")
        if not _SLUG_RE.fullmatch(slug):
            return r.fail(f"invalid work slug (kebab-case required): {slug}")
        return r.ok((kind, slug))

    @staticmethod
    def _branch_name(kind: c.Infra.WorkKind | str, slug: str) -> str:
        kind_value = kind.value if isinstance(kind, c.Infra.WorkKind) else str(kind)
        return f"{kind_value}/{slug}"

    def _resolve_lane_branch(self) -> p.Result[str]:
        explicit = (self.branch or "").strip()
        if explicit:
            return r.ok(explicit)
        bead = (self.bead or "").strip()
        if bead:
            shown = u.Infra.beads_show_json(bead)
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
        oid = u.Infra.git_capture(root, ("rev-parse", "HEAD"))
        if oid.failure:
            return r.fail(oid.error or "failed to resolve HEAD")
        return r.ok(oid.value.strip())

    @staticmethod
    def _ensure_clean(lane: Path) -> p.Result[None]:
        status = u.Infra.git_capture(
            lane, ("status", "--porcelain", "--untracked-files=all")
        )
        if status.failure:
            return r.fail(status.error or f"failed to inspect {lane}")
        if status.value.strip():
            return r.fail("work land/finish requires a clean lane worktree")
        return r.ok(None)


__all__: list[str] = ["FlextInfraWorkSagaCommon"]
