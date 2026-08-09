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
        """Resolve the workspace-root primary, never a member checkout lane."""
        superproject = u.Infra.git_superproject_working_tree(
            m.Infra.GitRepoRequest(repo_root=self.workspace_root)
        )
        if superproject.failure:
            return r[Path].fail(
                superproject.error or "failed to resolve workspace superproject"
            )
        workspace_root = (
            Path(superproject.value.text).resolve()
            if superproject.value.text.strip()
            else self.workspace_root.resolve()
        )
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=workspace_root)
        )
        if primary.failure:
            return r[Path].fail(primary.error or "failed to resolve primary worktree")
        return r[Path].ok(primary.value.primary_root)

    @staticmethod
    def _matrix_from_metadata(meta: dict[str, object]) -> p.Result[m.Infra.WorkLaneMatrix]:
        """Parse the only accepted serialized workspace lane matrix."""
        raw = meta.get(c.Infra.WORK_BEADS_MATRIX_KEY)
        if not isinstance(raw, str) or not raw.strip():
            return r.fail("bead lane metadata is missing serialized matrix")
        try:
            return r.ok(m.Infra.WorkLaneMatrix.model_validate_json(raw))
        except c.ValidationError as exc:
            return r.fail(f"invalid serialized workspace lane matrix: {exc}")

    @staticmethod
    def _matrix_project_root(lane: Path, project: str) -> p.Result[Path]:
        """Resolve one matrix project strictly within the root worktree."""
        candidate = (lane / project).resolve()
        if not candidate.is_relative_to(lane.resolve()):
            return r.fail(f"matrix project resolves outside root worktree: {project}")
        if not candidate.is_dir():
            return r.fail(f"matrix project checkout is missing: {project}")
        return r.ok(candidate)

    def _matrix_for_started_lane(
        self, primary_root: Path, lane: Path, branch: str
    ) -> p.Result[m.Infra.WorkLaneMatrix]:
        """Attach every governed project at its lane branch and capture CAS heads."""
        projects = u.Infra.resolve_projects(primary_root, ())
        if projects.failure:
            return r.fail(projects.error or "failed to resolve workspace projects")
        entries: list[m.Infra.WorkLaneEntry] = []
        project_paths = (primary_root, *(project.path.resolve() for project in projects.value))
        for project_path in dict.fromkeys(project_paths):
            try:
                relative = project_path.relative_to(primary_root.resolve())
            except ValueError:
                return r.fail(f"workspace project is outside root: {project_path}")
            project_name = relative.as_posix() or "."
            lane_project = self._matrix_project_root(lane, project_name)
            if lane_project.failure:
                return r.fail(lane_project.error or "invalid matrix project")
            if project_name != ".":
                attached = u.Infra.git_attach_branch_at_head(
                    m.Infra.GitBranchRequest(
                        repo_root=lane_project.value, branch=branch
                    )
                )
                if attached.failure:
                    return r.fail(
                        attached.error
                        or f"failed to attach workspace project branch: {project_name}"
                    )
            head = self._git_head(lane_project.value)
            if head.failure:
                return r.fail(head.error or f"failed to resolve matrix head: {project_name}")
            entries.append(
                m.Infra.WorkLaneEntry(
                    project=project_name,
                    branch=branch,
                    head_oid=head.value,
                    state="started",
                )
            )
        if not entries:
            return r.fail("workspace lane matrix has no projects")
        return r.ok(m.Infra.WorkLaneMatrix(entries=tuple(entries)))

    def _bound_root_matrix(
        self, primary_root: Path, meta: dict[str, object]
    ) -> p.Result[tuple[Path, m.Infra.WorkLaneMatrix]]:
        """Validate metadata against the one registered root worktree and matrix."""
        worktree = str(meta.get("worktree") or "").strip()
        if not worktree:
            return r.fail("bead lane metadata is missing root worktree")
        matrix = self._matrix_from_metadata(meta)
        if matrix.failure:
            return r.fail(matrix.error or "invalid root lane matrix")
        root_entries = [entry for entry in matrix.value.entries if entry.project == "."]
        if len(root_entries) != 1:
            return r.fail("workspace lane matrix requires exactly one root entry")
        lane = self._bound_registered_lane(primary_root, root_entries[0].branch, worktree)
        if lane.failure:
            return r.fail(lane.error or "root lane binding failed")
        return r.ok((lane.value, matrix.value))

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
