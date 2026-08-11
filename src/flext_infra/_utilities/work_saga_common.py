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
        return FlextInfraWorktreeService.workspace_primary_root(self.workspace_root)

    @staticmethod
    def _tracker_parent(payload: dict[str, object]) -> str:
        """Return the parent bead id the tracker records for one bead."""
        parent = payload.get("parent")
        if isinstance(parent, str) and parent.strip():
            return parent.strip()
        dependencies = payload.get("dependencies")
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if (
                    isinstance(dependency, dict)
                    and dependency.get("dependency_type") == "parent-child"
                ):
                    dependency_id = dependency.get("id")
                    if isinstance(dependency_id, str) and dependency_id.strip():
                        return dependency_id.strip()
        return ""

    @staticmethod
    def _has_lane_metadata(primary_root: Path, bead: str) -> bool:
        """Report whether a bead already carries lane coordinates of its own."""
        shown = u.Infra.beads_show_json(bead, root=primary_root)
        if shown.failure:
            return False
        meta = shown.value.get("metadata")
        if not isinstance(meta, dict):
            return False
        return bool(
            str(meta.get("kind") or "").strip() and str(meta.get("slug") or "").strip()
        )

    def _parent_context(
        self,
        primary_root: Path,
        payload: dict[str, object],
        bead: str,
        kind: c.Infra.WorkKind,
        seen: frozenset[str],
    ) -> p.Result[m.Infra.WorkLaneParentContext]:
        """Resolve the parent lane a bead's own lane must be nested under.

        An epic anchors at the workspace root when it has no tracker parent, or
        when that parent carries no lane of its own: the tracker tree is a
        planning tree, and only the beads that own execution carry lanes. Every
        other lane hangs off its immediate parent epic lane, which must already
        exist and be registered exactly at its canonical path.
        """
        parent_bead = self._tracker_parent(payload)
        if not parent_bead:
            if kind is not c.Infra.WorkKind.EPIC:
                return r.fail(
                    f"bead {bead} has no tracker parent, so lane kind "
                    f"{kind.value} has no epic lane to nest under; give it a "
                    "parent epic or start it as KIND=epic"
                )
            base = self._resolve_integration_base(primary_root)
            if base.failure:
                return r.fail(base.error or "failed to resolve integration base")
            return r.ok(
                m.Infra.WorkLaneParentContext(
                    parent_lane=primary_root.resolve(), base_branch=base.value
                )
            )
        ancestor = self._stored_identity(primary_root, parent_bead, seen | {bead})
        if ancestor.failure:
            # Why: the tracker tree is a PLANNING tree and only the beads that
            # own execution carry lanes. An epic whose parent carries no lane is
            # therefore the root of its own lane chain and anchors at the
            # workspace root, so a planning container never has to materialize a
            # worktree. A non-epic keeps failing here: a leaf always needs its
            # immediate epic lane.
            if kind is c.Infra.WorkKind.EPIC and not self._has_lane_metadata(
                primary_root, parent_bead
            ):
                base = self._resolve_integration_base(primary_root)
                if base.failure:
                    return r.fail(base.error or "failed to resolve integration base")
                return r.ok(
                    m.Infra.WorkLaneParentContext(
                        parent_lane=primary_root.resolve(), base_branch=base.value
                    )
                )
            return r.fail(ancestor.error or f"unusable parent epic {parent_bead}")
        if not ancestor.value.is_epic:
            return r.fail(
                f"lane parent {parent_bead} is not an epic lane "
                f"(kind={ancestor.value.kind}); only epic lanes own child lanes"
            )
        registered = FlextInfraWorktreeService.registered_lane(
            primary_root, ancestor.value.branch, ancestor.value.lane_path
        )
        if registered.failure:
            return r.fail(
                f"parent epic lane {parent_bead} is not usable: "
                f"{registered.error or 'lane is not registered'}"
            )
        return r.ok(
            m.Infra.WorkLaneParentContext(
                parent_lane=ancestor.value.lane_path,
                parent_bead=parent_bead,
                parent_branch=ancestor.value.branch,
                base_branch=ancestor.value.branch,
            )
        )

    def _lane_identity(
        self,
        primary_root: Path,
        payload: dict[str, object],
        bead: str,
        kind: c.Infra.WorkKind,
        slug: str,
        seen: frozenset[str] = frozenset(),
    ) -> p.Result[m.Infra.WorkLaneIdentity]:
        """Derive the one canonical identity of a lane from its Bead."""
        context = self._parent_context(primary_root, payload, bead, kind, seen)
        if context.failure:
            return r.fail(context.error or "failed to resolve parent lane")
        lane_dir = f"{bead}-{slug}"
        lane_path = FlextInfraWorktreeService.derive_lane_path(
            context.value.parent_lane, lane_dir
        )
        if lane_path.failure:
            return r.fail(lane_path.error or "failed to derive lane path")
        return r.ok(
            m.Infra.WorkLaneIdentity(
                bead=bead,
                slug=slug,
                kind=kind,
                branch=f"{kind.value}/{lane_dir}",
                lane_dir=lane_dir,
                lane_path=lane_path.value,
                parent_lane=context.value.parent_lane,
                parent_bead=context.value.parent_bead,
                parent_branch=context.value.parent_branch,
                base_branch=context.value.base_branch,
            )
        )

    def _stored_identity(
        self, primary_root: Path, bead: str, seen: frozenset[str] = frozenset()
    ) -> p.Result[m.Infra.WorkLaneIdentity]:
        """Re-derive one already-started lane identity from its Bead metadata."""
        if bead in seen:
            return r.fail(f"lane parent chain is cyclic at bead {bead}")
        if len(seen) >= c.Infra.WORK_LANE_MAX_DEPTH:
            return r.fail(f"lane parent chain is too deep at bead {bead}")
        shown = u.Infra.beads_show_json(bead, root=primary_root)
        if shown.failure:
            return r.fail(shown.error or f"unknown bead {bead}")
        meta = shown.value.get("metadata")
        stored_kind = (
            str(meta.get("kind") or "").strip() if isinstance(meta, dict) else ""
        )
        stored_slug = (
            str(meta.get("slug") or "").strip() if isinstance(meta, dict) else ""
        )
        if not stored_kind or not stored_slug:
            return r.fail(
                f"bead {bead} has no lane metadata (kind/slug); start its lane "
                f"first: make work WHAT=start BEAD={bead} KIND=epic NAME=<slug> "
                "APPLY=Y"
            )
        if stored_kind not in {kind.value for kind in c.Infra.WorkKind}:
            return r.fail(f"bead {bead} records an unknown lane kind: {stored_kind}")
        return self._lane_identity(
            primary_root,
            shown.value,
            bead,
            c.Infra.WorkKind(stored_kind),
            stored_slug,
            seen,
        )

    @staticmethod
    def _matrix_from_metadata(
        meta: dict[str, object],
    ) -> p.Result[m.Infra.WorkLaneMatrix]:
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
        project_paths = (
            primary_root,
            *(project.path.resolve() for project in projects.value),
        )
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
                return r.fail(
                    head.error or f"failed to resolve matrix head: {project_name}"
                )
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
        self, primary_root: Path, bead: str, meta: dict[str, object]
    ) -> p.Result[m.Infra.WorkLaneBinding]:
        """Bind bead metadata to the one canonical, registered workspace lane."""
        worktree = str(meta.get("worktree") or "").strip()
        if not worktree:
            return r.fail("bead lane metadata is missing root worktree")
        matrix = self._matrix_from_metadata(meta)
        if matrix.failure:
            return r.fail(matrix.error or "invalid root lane matrix")
        root_entries = [entry for entry in matrix.value.entries if entry.project == "."]
        if len(root_entries) != 1:
            return r.fail("workspace lane matrix requires exactly one root entry")
        identity = self._stored_identity(primary_root, bead)
        if identity.failure:
            return r.fail(identity.error or f"bead {bead} has no canonical lane")
        if root_entries[0].branch != identity.value.branch:
            return r.fail(
                "work metadata branch does not match the derived lane branch: "
                f"metadata={root_entries[0].branch} derived={identity.value.branch}"
            )
        lane = self._bound_registered_lane(
            primary_root, identity.value.branch, worktree, identity.value.lane_path
        )
        if lane.failure:
            return r.fail(lane.error or "root lane binding failed")
        return r.ok(
            m.Infra.WorkLaneBinding(
                identity=identity.value, lane=lane.value, matrix=matrix.value
            )
        )

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
        primary_root: Path, branch: str, worktree: str, canonical: Path
    ) -> p.Result[Path]:
        """Accept a lane only when metadata, registry, and derivation agree."""
        canonical_lane = canonical.expanduser().resolve()
        meta_lane = Path(worktree).expanduser().resolve()
        if meta_lane != canonical_lane:
            return r.fail(
                "work metadata worktree is not the derived lane path: "
                f"metadata={meta_lane} derived={canonical_lane}"
            )
        registered = FlextInfraWorktreeService.registered_lane(
            primary_root, branch, canonical_lane
        )
        if registered.failure:
            return r.fail(
                registered.error or f"worktree branch is not registered: {branch}"
            )
        return r.ok(registered.value.resolve())

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
