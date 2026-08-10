"""Shared helpers for the make work saga."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, u
from flext_infra._utilities._work import FlextInfraWorkTopology
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class FlextInfraWorkSagaCommon(FlextInfraWorkTopology):
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

    def _validated_kind_slug(
        self, issue_type: str | None = None
    ) -> p.Result[tuple[c.Infra.WorkKind, str]]:
        kind = self.kind
        if kind is None:
            workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
                self.workspace_root
            )
            if workspace.failure:
                return r.fail(workspace.error or "failed to load workspace lane policy")
            match (issue_type or "").strip().lower():
                case "epic":
                    kind = c.Infra.WorkKind.FEATURE
                case "bug":
                    kind = c.Infra.WorkKind.BUGFIX
                case "feature":
                    kind = c.Infra.WorkKind.FEATURE
                case "task":
                    kind = c.Infra.WorkKind(workspace.value.work.task_kind)
                case "chore":
                    kind = c.Infra.WorkKind(workspace.value.work.chore_kind)
                case "":
                    return r.fail("work start bead is missing issue_type; pass --kind")
                case invalid:
                    return r.fail(
                        f"work start cannot derive kind from issue_type {invalid}"
                    )
        # Why: mro-5bts the service model stores enum values, so re-enter the
        # enum here and keep every downstream saga step typed.
        kind = c.Infra.WorkKind(kind)
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
