"""Automatic Git topology and exceptional policy overlay resolution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override
from urllib.parse import urlsplit

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base import s
from packaging.utils import canonicalize_name

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(s[c.Infra.WorkspaceMode]):
    """Resolve physical Git topology independently from managed policy."""

    @staticmethod
    def resolve_repository_root(repository_root: Path) -> p.Result[Path]:
        """Resolve the current repository root without crossing a gitlink."""
        resolved_root = repository_root.expanduser().resolve()
        repository = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-toplevel"], cwd=resolved_root
        )
        if repository.failure:
            inside_work_tree = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=resolved_root
            )
            if inside_work_tree.failure or inside_work_tree.value.strip() != "true":
                return r[Path].ok(resolved_root)
            return r[Path].fail(
                repository.error or "unable to resolve current Git repository"
            )
        return r[Path].ok(Path(repository.value).resolve())

    @staticmethod
    def resolve_workspace_root(repository_root: Path) -> p.Result[Path]:
        """Resolve the physical superproject, or the current repository."""
        current = FlextInfraWorkspaceDetector.resolve_repository_root(repository_root)
        if current.failure:
            return r[Path].fail(current.error)
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=current.value,
        )
        if superproject.failure:
            inside_work_tree = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=current.value
            )
            if inside_work_tree.failure or inside_work_tree.value.strip() != "true":
                return r[Path].ok(current.value)
            return r[Path].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        if not superproject.value:
            return r[Path].ok(current.value)
        return r[Path].ok(Path(superproject.value).resolve())

    @staticmethod
    def _repository_url_parts(url: str) -> p.Result[tuple[str, str]]:
        """Derive normalized repository and provider slugs from one Git URL."""
        raw = url.strip().rstrip("/")
        if not raw:
            return r[tuple[str, str]].fail("repository URL is empty")
        if "://" in raw:
            path = urlsplit(raw).path
        elif "@" in raw and ":" in raw.partition("@")[2]:
            path = raw.partition("@")[2].partition(":")[2]
        else:
            path = raw
        parts = tuple(part for part in path.strip("/").split("/") if part)
        match parts:
            case [*_, provider_part, repository_part]:
                repository = str(
                    canonicalize_name(repository_part.removesuffix(".git"))
                )
                provider = str(canonicalize_name(provider_part))
            case _:
                return r[tuple[str, str]].fail(
                    f"repository URL has no provider/repository identity: {url}"
                )
        if not repository or not provider:
            return r[tuple[str, str]].fail(f"repository URL identity is invalid: {url}")
        return r[tuple[str, str]].ok((repository, provider))

    @staticmethod
    def _overlay_for(
        observed_identity: str,
    ) -> p.Result[m.Infra.RepositoryTopologyOverlaySpec | None]:
        """Select exactly one exceptional overlay for an observed repository."""
        overlays = config.Infra.topology.overlays
        duplicate_matches = tuple(
            sorted({
                overlay.match
                for overlay in overlays
                if sum(item.match == overlay.match for item in overlays) > 1
            })
        )
        if duplicate_matches:
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].fail(
                "duplicate topology overlays: " + ", ".join(duplicate_matches)
            )
        selected_overlays = tuple(
            overlay
            for overlay in overlays
            if observed_identity in {overlay.match, overlay.identity}
        )
        if len(selected_overlays) > 1:
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].fail(
                f"topology identity selects multiple overlays: {observed_identity}"
            )
        if not selected_overlays:
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].ok(None)
        selected = selected_overlays[0]
        if selected.beads.namespace is not None and not selected.beads.enabled:
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].fail(
                f"Beads namespace requires enabled=true: {observed_identity}"
            )
        external_paths = tuple(
            reference.path.as_posix() for reference in selected.external_refs
        )
        if any(
            path in {"", "."} or Path(path).is_absolute() or ".." in Path(path).parts
            for path in external_paths
        ):
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].fail(
                f"external reference paths must be safe workspace relatives: "
                f"{observed_identity}"
            )
        if len(external_paths) != len(set(external_paths)):
            return r[m.Infra.RepositoryTopologyOverlaySpec | None].fail(
                f"duplicate external reference paths: {observed_identity}"
            )
        return r[m.Infra.RepositoryTopologyOverlaySpec | None].ok(selected)

    @staticmethod
    def _git_repository_url(repository_root: Path) -> p.Result[str | None]:
        """Read an optional Git origin without treating its absence as an error."""
        output = u.Cli.run_raw(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"], cwd=repository_root
        )
        if output.failure:
            return r[str | None].fail(
                output.error or "unable to inspect repository origin"
            )
        if output.value.exit_code == 0:
            origin = output.value.stdout.strip()
            if not origin:
                return r[str | None].fail("Git origin URL is empty")
            return r[str | None].ok(origin)
        if output.value.exit_code == 1:
            return r[str | None].ok(None)
        return r[str | None].fail(
            output.value.stderr.strip() or "unable to inspect repository origin"
        )

    @staticmethod
    def _git_branch(repository_root: Path) -> p.Result[str]:
        """Read the current branch, retaining HEAD for detached checkouts."""
        output = u.Cli.run_raw(
            [c.Infra.GIT, "symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=repository_root,
        )
        if output.failure:
            return r[str].fail(output.error or "unable to inspect repository branch")
        if output.value.exit_code == 0 and output.value.stdout.strip():
            return r[str].ok(output.value.stdout.strip())
        if output.value.exit_code == 1:
            return r[str].ok("HEAD")
        return r[str].fail(
            output.value.stderr.strip() or "unable to inspect repository branch"
        )

    @classmethod
    def _local_identity(
        cls, repository_root: Path
    ) -> p.Result[tuple[str, str, str, str, str, bool]]:
        """Read canonical local identity from Git and optional PEP 621 metadata."""
        metadata_name: str | None = None
        metadata_url: str | None = None
        pyproject = repository_root / c.PYPROJECT_FILENAME
        if pyproject.is_file():
            metadata = u.read_project_metadata(repository_root)
            if metadata.failure:
                return r[tuple[str, str, str, str, str, bool]].fail(
                    metadata.error or f"invalid project metadata: {pyproject}"
                )
            metadata_name = metadata.value.project.name
            metadata_url = metadata.value.project.urls.repository or None
        origin = cls._git_repository_url(repository_root)
        if origin.failure:
            return r[tuple[str, str, str, str, str, bool]].fail(origin.error)
        repository_url = origin.value or metadata_url or repository_root.as_uri()
        url_parts = cls._repository_url_parts(repository_url)
        if url_parts.failure:
            return r[tuple[str, str, str, str, str, bool]].fail(url_parts.error)
        observed_identity, provider = url_parts.value
        overlay = cls._overlay_for(observed_identity)
        if overlay.failure:
            return r[tuple[str, str, str, str, str, bool]].fail(overlay.error)
        identity = (
            overlay.value.identity
            if overlay.value is not None and overlay.value.identity is not None
            else observed_identity
        )
        branch = cls._git_branch(repository_root)
        if branch.failure:
            inside = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=repository_root
            )
            if inside.success and inside.value.strip() == "true":
                return r[tuple[str, str, str, str, str, bool]].fail(branch.error)
            branch_name = "HEAD"
        else:
            branch_name = branch.value
        return r[tuple[str, str, str, str, str, bool]].ok((
            identity,
            metadata_name or identity,
            provider,
            repository_url,
            branch_name,
            pyproject.is_file(),
        ))

    @staticmethod
    def _indexed_gitlinks(repository_root: Path) -> p.Result[t.StrSequence]:
        """Return Git-indexed submodules after exact .gitmodules reconciliation."""
        indexed = u.Cli.capture(
            [c.Infra.GIT, "ls-files", "--stage"], cwd=repository_root
        )
        if indexed.failure:
            return r[t.StrSequence].fail(
                indexed.error or "unable to inspect repository gitlinks"
            )
        indexed_paths: set[str] = set()
        for line in indexed.value.splitlines():
            metadata, separator, path = line.partition("\t")
            match metadata.split():
                case [mode, _, _] if separator:
                    if mode == "160000":
                        indexed_paths.add(path)
                case _:
                    return r[t.StrSequence].fail("malformed Git index entry")
        gitmodules_path = repository_root / c.Infra.GITMODULES
        if not gitmodules_path.is_file():
            if indexed_paths:
                return r[t.StrSequence].fail(
                    f"indexed gitlinks require {c.Infra.GITMODULES}"
                )
            return r[t.StrSequence].ok(())
        declared = u.Cli.run_raw(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
            ],
            cwd=repository_root,
        )
        if declared.failure:
            return r[t.StrSequence].fail(
                declared.error or "unable to inspect declared Git submodules"
            )
        if declared.value.exit_code not in {0, 1}:
            return r[t.StrSequence].fail(
                declared.value.stderr.strip()
                or "unable to inspect declared Git submodules"
            )
        declared_paths: set[str] = set()
        for line in declared.value.stdout.splitlines():
            match line.split(maxsplit=1):
                case [_, path]:
                    declared_paths.add(path)
                case _:
                    return r[t.StrSequence].fail(
                        "malformed Git submodule path declaration"
                    )
        if declared_paths != indexed_paths:
            return r[t.StrSequence].fail(
                "declared Git submodules and indexed gitlinks differ"
            )
        return r[t.StrSequence].ok(tuple(sorted(indexed_paths)))

    @staticmethod
    def _gitmodule_contract(
        superproject_root: Path, member_path: str
    ) -> p.Result[tuple[str, str]]:
        """Read one Gitlink URL and optional branch from .gitmodules."""
        entries = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
            ],
            cwd=superproject_root,
        )
        if entries.failure:
            return r[tuple[str, str]].fail(
                entries.error or "unable to read Git submodule paths"
            )
        matching_keys: t.MutableSequenceOf[str] = []
        for line in entries.value.splitlines():
            match line.split(maxsplit=1):
                case [key, path] if path == member_path:
                    matching_keys.append(key)
                case [_, _]:
                    continue
                case _:
                    return r[tuple[str, str]].fail("malformed Git submodule path entry")
        if len(matching_keys) != 1:
            return r[tuple[str, str]].fail(
                f"Git submodule path must be declared exactly once: {member_path}"
            )
        section = matching_keys[0].removesuffix(".path")
        url = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get",
                f"{section}.url",
            ],
            cwd=superproject_root,
        )
        if url.failure or not url.value:
            return r[tuple[str, str]].fail(
                url.error or f"Git submodule URL is missing: {member_path}"
            )
        branch = u.Cli.run_raw(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get",
                f"{section}.branch",
            ],
            cwd=superproject_root,
        )
        if branch.failure:
            return r[tuple[str, str]].fail(
                branch.error or f"unable to inspect Git submodule branch: {member_path}"
            )
        if branch.value.exit_code == 0 and branch.value.stdout.strip():
            branch_name = branch.value.stdout.strip()
        elif branch.value.exit_code == 1:
            branch_name = "HEAD"
        else:
            return r[tuple[str, str]].fail(
                branch.value.stderr.strip()
                or f"unable to inspect Git submodule branch: {member_path}"
            )
        return r[tuple[str, str]].ok((url.value, branch_name))

    @classmethod
    def _derive_workspace_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive a complete generic spec from physical Git and typed overlays."""
        current = cls.resolve_repository_root(repository_root)
        if current.failure:
            return r[m.Infra.WorkspaceSpec].fail(current.error)
        identity = cls._local_identity(current.value)
        if identity.failure:
            return r[m.Infra.WorkspaceSpec].fail(identity.error)
        (project_identity, distribution, provider, repository_url, branch, package) = (
            identity.value
        )
        overlay = cls._overlay_for(cls._repository_url_parts(repository_url).value[0])
        if overlay.failure:
            return r[m.Infra.WorkspaceSpec].fail(overlay.error)
        gitlinks = cls._indexed_gitlinks(current.value)
        if gitlinks.failure:
            inside = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=current.value
            )
            if inside.success and inside.value.strip() == "true":
                return r[m.Infra.WorkspaceSpec].fail(gitlinks.error)
            gitlink_paths: t.StrSequence = ()
        else:
            gitlink_paths = gitlinks.value
        is_workspace = bool(gitlink_paths)
        root_repository = m.Infra.RepositoryRef(
            name=project_identity,
            distribution=distribution,
            provider=provider,
            url=repository_url,
            branch=branch,
            path=Path(),
            role=(
                c.Infra.RepositoryRole.WORKSPACE_ROOT
                if is_workspace
                else c.Infra.RepositoryRole.STANDALONE
            ),
            state=c.Infra.RepositoryState.ACTIVE,
            profile=(
                c.Infra.MakeProfile.WORKSPACE_ROOT
                if is_workspace
                else c.Infra.MakeProfile.STANDALONE
            ),
            checkout=(
                c.Infra.CheckoutKind.ROOT
                if is_workspace
                else c.Infra.CheckoutKind.INDEPENDENT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=package,
            editable=False,
            read_only=False,
        )
        explicit_external = {
            reference.path.as_posix(): reference
            for reference in (
                overlay.value.external_refs if overlay.value is not None else ()
            )
        }
        unknown_external = tuple(sorted(set(explicit_external) - set(gitlink_paths)))
        if unknown_external:
            return r[m.Infra.WorkspaceSpec].fail(
                "external reference overlays are not indexed gitlinks: "
                + ", ".join(unknown_external)
            )
        members: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        content_only: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        for member_path in gitlink_paths:
            contract = cls._gitmodule_contract(current.value, member_path)
            if contract.failure:
                return r[m.Infra.WorkspaceSpec].fail(contract.error)
            member_url, member_branch = contract.value
            member_parts = cls._repository_url_parts(member_url)
            if member_parts.failure:
                return r[m.Infra.WorkspaceSpec].fail(member_parts.error)
            member_identity, member_provider = member_parts.value
            external = member_path in explicit_external or member_provider != provider
            repository = m.Infra.RepositoryRef(
                name=member_identity,
                distribution=member_identity,
                provider=member_provider,
                url=member_url,
                branch=member_branch,
                path=Path(member_path),
                role=(
                    c.Infra.RepositoryRole.CONTENT_ONLY
                    if external
                    else c.Infra.RepositoryRole.WORKSPACE_MEMBER
                ),
                state=(
                    c.Infra.RepositoryState.CONTENT_ONLY
                    if external
                    else c.Infra.RepositoryState.ACTIVE
                ),
                profile=None if external else c.Infra.MakeProfile.WORKSPACE_MEMBER,
                checkout=c.Infra.CheckoutKind.SUBMODULE,
                codegen=(
                    c.Infra.CodegenKind.NONE
                    if external
                    else c.Infra.CodegenKind.CONFORM
                ),
                package=(
                    False
                    if external
                    else (current.value / member_path / c.PYPROJECT_FILENAME).is_file()
                ),
                editable=(
                    False
                    if external
                    else (current.value / member_path / c.PYPROJECT_FILENAME).is_file()
                ),
                read_only=external,
            )
            if external:
                content_only.append(repository)
            else:
                members.append(repository)
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_identity,
                repository=root_repository,
                members=tuple(members),
                content_only=tuple(content_only),
                exclusions=(),
            )
        )

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive topology from Git; generated manifests are projections only."""
        return cls._derive_workspace_spec(repository_root)

    @classmethod
    def _attached_repository(
        cls, repository_root: Path, superproject_root: Path
    ) -> p.Result[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]]:
        """Resolve one attached Gitlink through its parent-derived topology."""
        try:
            member_path = repository_root.relative_to(superproject_root).as_posix()
        except ValueError as exc:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].fail_op(
                "Workspace detection", exc
            )
        parent = cls.load_workspace_spec(superproject_root)
        if parent.failure:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].fail(
                parent.error
            )
        matches = tuple(
            repository
            for repository in (*parent.value.members, *parent.value.content_only)
            if repository.path.as_posix() == member_path
        )
        if len(matches) != 1:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].fail(
                f"Git submodule path has no single topology owner: {member_path}"
            )
        declared = matches[0]
        if declared.read_only:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].ok((
                declared,
                parent.value,
            ))
        origin = cls._git_repository_url(repository_root)
        if origin.failure:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].fail(
                origin.error
            )
        if origin.value is not None and origin.value != declared.url:
            return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].fail(
                f"managed Git submodule origin mismatch: {member_path}"
            )
        return r[tuple[m.Infra.RepositoryRef, m.Infra.WorkspaceSpec]].ok((
            declared,
            parent.value,
        ))

    @classmethod
    def inspect(
        cls, project_root: Path, declared: m.Infra.RepositoryRef | None = None
    ) -> p.Result[m.Infra.RepositoryTopology]:
        """Inspect Git once and derive conform, Make, and Beads independently."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[m.Infra.RepositoryTopology].fail_op("Workspace detection", exc)
        if not resolved_project_root.is_dir():
            return r[m.Infra.RepositoryTopology].fail(
                f"project root is not a directory: {resolved_project_root}"
            )
        repository_root = cls.resolve_repository_root(resolved_project_root)
        if repository_root.failure:
            return r[m.Infra.RepositoryTopology].fail(repository_root.error)
        superproject = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=repository_root.value,
        )
        if superproject.failure:
            return r[m.Infra.RepositoryTopology].fail(
                superproject.error or "unable to inspect Git superproject"
            )
        if superproject.value.exit_code == 0 and superproject.value.stdout.strip():
            workspace_root = Path(superproject.value.stdout.strip()).resolve()
            attached = cls._attached_repository(repository_root.value, workspace_root)
            if attached.failure:
                return r[m.Infra.RepositoryTopology].fail(attached.error)
            attached_repository, parent_spec = attached.value
            external = attached_repository.read_only
            effective = attached_repository.model_copy(
                update={
                    "path": Path(),
                    "role": (
                        c.Infra.RepositoryRole.CONTENT_ONLY
                        if external
                        else c.Infra.RepositoryRole.STANDALONE
                    ),
                    "profile": None if external else c.Infra.MakeProfile.STANDALONE,
                    "checkout": c.Infra.CheckoutKind.SUBMODULE,
                }
            )
            parent_overlay = cls._overlay_for(parent_spec.repository.name)
            if parent_overlay.failure:
                return r[m.Infra.RepositoryTopology].fail(parent_overlay.error)
            external_uses = ()
            if external and parent_overlay.value is not None:
                external_uses = tuple(
                    reference
                    for reference in parent_overlay.value.external_refs
                    if reference.path == attached_repository.path
                )
            return r[m.Infra.RepositoryTopology].ok(
                m.Infra.RepositoryTopology(
                    repository_root=repository_root.value,
                    workspace_root=workspace_root,
                    physical="attached",
                    mode=c.Infra.WorkspaceMode.STANDALONE,
                    conform="external" if external else "managed",
                    make_profile=None if external else c.Infra.MakeProfile.STANDALONE,
                    external_uses=external_uses,
                    beads_enabled=False,
                    repository=effective,
                )
            )
        if superproject.value.exit_code not in {0, 128}:
            return r[m.Infra.RepositoryTopology].fail(
                superproject.value.stderr.strip()
                or "unable to inspect Git superproject"
            )
        spec = cls.load_workspace_spec(repository_root.value)
        if spec.failure:
            return r[m.Infra.RepositoryTopology].fail(spec.error)
        repository = declared or spec.value.repository
        is_workspace = bool(spec.value.members or spec.value.content_only)
        overlay = cls._overlay_for(spec.value.name)
        if overlay.failure:
            return r[m.Infra.RepositoryTopology].fail(overlay.error)
        beads_overlay = (
            overlay.value.beads
            if overlay.value is not None
            else m.Infra.BeadsOverlaySpec()
        )
        if is_workspace and (
            beads_overlay.enabled or beads_overlay.namespace is not None
        ):
            return r[m.Infra.RepositoryTopology].fail(
                "Beads overlays are only valid for independent repositories"
            )
        effective = repository.model_copy(
            update={
                "path": Path(),
                "role": (
                    c.Infra.RepositoryRole.WORKSPACE_ROOT
                    if is_workspace
                    else c.Infra.RepositoryRole.STANDALONE
                ),
                "profile": (
                    c.Infra.MakeProfile.WORKSPACE_ROOT
                    if is_workspace
                    else c.Infra.MakeProfile.STANDALONE
                ),
                "checkout": (
                    c.Infra.CheckoutKind.ROOT
                    if is_workspace
                    else c.Infra.CheckoutKind.INDEPENDENT
                ),
            }
        )
        beads_enabled = is_workspace or beads_overlay.enabled
        return r[m.Infra.RepositoryTopology].ok(
            m.Infra.RepositoryTopology(
                repository_root=repository_root.value,
                workspace_root=repository_root.value,
                physical="workspace-root" if is_workspace else "independent",
                mode=(
                    c.Infra.WorkspaceMode.WORKSPACE
                    if is_workspace
                    else c.Infra.WorkspaceMode.STANDALONE
                ),
                conform="managed",
                make_profile=effective.profile,
                managed_gitlinks=tuple(
                    repository.path.as_posix() for repository in spec.value.members
                ),
                external_gitlinks=tuple(
                    repository.path.as_posix() for repository in spec.value.content_only
                ),
                external_uses=(
                    overlay.value.external_refs if overlay.value is not None else ()
                ),
                beads_enabled=beads_enabled,
                beads_namespace=(
                    beads_overlay.namespace or spec.value.name
                    if beads_enabled
                    else None
                ),
                repository=effective,
            )
        )

    @classmethod
    def effective_repository(
        cls, repository_root: Path, declared: m.Infra.RepositoryRef
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Project one repository contract through the observed topology."""
        topology = cls.inspect(repository_root, declared)
        if topology.failure:
            return r[m.Infra.RepositoryRef].fail(topology.error)
        return r[m.Infra.RepositoryRef].ok(topology.value.repository)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Project the public mode from canonical topology inspection."""
        inspected = self.inspect(project_root)
        if inspected.failure:
            return r[c.Infra.WorkspaceMode].fail(
                inspected.error or "unable to inspect repository topology"
            )
        return r[c.Infra.WorkspaceMode].ok(inspected.value.mode)

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute detection against the configured repository root."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
