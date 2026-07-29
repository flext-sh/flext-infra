"""Strict manifest-backed workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(s[c.Infra.WorkspaceMode]):
    """Classify only declared roots and real, declared Git submodules."""

    # NOTE (multi-agent, mro-wkii.17.10 / agent: implement_topology_detector):
    # workspace membership is proven from the manifest SSOT plus Git's own
    # superproject metadata; ancestor and sibling discovery is intentionally absent.

    @staticmethod
    def _manifest_path(repository_root: Path) -> Path:
        """Return the repository-local topology manifest path."""
        config_dir: Path = t.Infra.PATH_ADAPTER.validate_python(c.CONFIG_DIR_NAME)
        manifest_name: Path = t.Infra.PATH_ADAPTER.validate_python(
            c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        return repository_root / config_dir / manifest_name

    @staticmethod
    def _schema_path() -> Path:
        """Return the packaged schema consumed by the public config facade."""
        schemas_dir: Path = t.Infra.PATH_ADAPTER.validate_python(
            c.CONFIG_SCHEMAS_DIR_NAME
        )
        schema_name: Path = t.Infra.PATH_ADAPTER.validate_python(
            c.Infra.WORKSPACE_SCHEMA_FILENAME
        )
        return Path(__file__).resolve().parents[1] / schemas_dir / schema_name

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the repository-local manifest, or derive it from the SSOT catalog."""
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file():
            return cls._derive_workspace_spec(repository_root)
        loaded = u.Cli.config_load(
            manifest_path, schema_path=cls._schema_path(), expand_env=False
        )
        if loaded.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                loaded.error or f"invalid workspace manifest: {manifest_path}"
            )
        try:
            # mro-i6nq.10: Validate the pure config model at its loading boundary.
            validated = m.Infra.WorkspaceSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.WorkspaceSpec].fail_op(
                f"workspace manifest model validation ({manifest_path})", exc
            )
        return r[m.Infra.WorkspaceSpec].ok(validated)

    @classmethod
    def _derive_workspace_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive a generic minimal spec from the codegen catalog SSOT.

        Standalone projects (and their transaction worktrees) ship no
        ``config/workspace.yaml``. Their topology is nonetheless declared in the
        canonical ``config.Infra.codegen`` catalog. The project's own name is
        read from its ``pyproject.toml`` via the flext-core project-metadata
        SSOT, then matched against the catalog to retain the exact declared
        repository contract. Nothing is fabricated; a project absent from both
        the manifest and the catalog fails closed.
        """
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                metadata.error
                or f"cannot derive workspace spec without metadata: {repository_root}"
            )
        project_name = metadata.value.project.name
        repository = next(
            (
                declared
                for declared in config.Infra.codegen.repositories
                if declared.name == project_name
            ),
            None,
        )
        if repository is None:
            return r[m.Infra.WorkspaceSpec].fail(
                f"project is absent from the codegen catalog: {project_name}"
            )
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_name,
                repository=repository,
            )
        )

    @staticmethod
    def resolve_repository_root(repository_root: Path) -> p.Result[Path]:
        """Resolve the current repository root without crossing a gitlink."""
        resolved_root = repository_root.expanduser().resolve()
        repository = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-toplevel"],
            cwd=resolved_root,
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
    def _validate_local_repository(repository: m.Infra.RepositoryRef) -> p.Result[bool]:
        """Validate the role/profile invariants for a local manifest owner."""
        if repository.path.as_posix() != ".":
            return r[bool].fail("local repository manifest path must be '.'")
        if repository.state != c.Infra.RepositoryState.ACTIVE:
            return r[bool].fail("local repository must have active state")
        expected_profile = {
            c.Infra.RepositoryRole.WORKSPACE_ROOT: c.Infra.MakeProfile.WORKSPACE_ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER: (
                c.Infra.MakeProfile.WORKSPACE_MEMBER
            ),
            c.Infra.RepositoryRole.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }.get(repository.role)
        if expected_profile is None:
            return r[bool].fail(
                f"unsupported local repository role: {repository.role.value}"
            )
        if repository.profile != expected_profile:
            return r[bool].fail(
                "local repository role/profile mismatch: "
                f"{repository.role.value}/{repository.profile}"
            )
        expected_checkout = {
            c.Infra.RepositoryRole.WORKSPACE_ROOT: c.Infra.CheckoutKind.ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER: c.Infra.CheckoutKind.SUBMODULE,
        }.get(repository.role)
        standalone_checkout = (
            repository.role is c.Infra.RepositoryRole.STANDALONE
            and repository.checkout
            in {
                c.Infra.CheckoutKind.INDEPENDENT,
                c.Infra.CheckoutKind.SUBMODULE,
            }
        )
        if repository.checkout is not expected_checkout and not standalone_checkout:
            return r[bool].fail(
                "local repository role/checkout mismatch: "
                f"{repository.role.value}/{repository.checkout.value}"
            )
        if repository.read_only:
            return r[bool].fail("local repository cannot be read-only")
        return r[bool].ok(True)

    @staticmethod
    def _declared_submodule_paths(repository_root: Path) -> p.Result[t.StrSequence]:
        """Return Git-indexed submodules declared by this repository."""
        gitmodules_path = repository_root / c.Infra.GITMODULES
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
        if not gitmodules_path.is_file():
            if indexed_paths:
                return r[t.StrSequence].fail(
                    f"indexed gitlinks require {c.Infra.GITMODULES}"
                )
            return r[t.StrSequence].ok(())
        declared = u.Cli.capture(
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
            if not indexed_paths:
                return r[t.StrSequence].ok(())
            return r[t.StrSequence].fail(
                declared.error or "unable to read declared Git submodules"
            )
        declared_paths: set[str] = set()
        for line in declared.value.splitlines():
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
    def _classify_gitlinks(
        workspace_spec: m.Infra.WorkspaceSpec | None,
        indexed_gitlinks: t.StrSequence,
    ) -> p.Result[tuple[t.StrSequence, t.StrSequence]]:
        """Classify Git links through the typed workspace ownership manifest."""
        if not indexed_gitlinks:
            return r[tuple[t.StrSequence, t.StrSequence]].ok(((), ()))
        if workspace_spec is None:
            return r[tuple[t.StrSequence, t.StrSequence]].fail(
                "Git submodules require a typed workspace ownership manifest"
            )
        invalid_members = tuple(
            repository.name
            for repository in workspace_spec.members
            if repository.state is not c.Infra.RepositoryState.ACTIVE
            or repository.role is not c.Infra.RepositoryRole.WORKSPACE_MEMBER
            or repository.profile is not c.Infra.MakeProfile.WORKSPACE_MEMBER
            or repository.checkout is not c.Infra.CheckoutKind.SUBMODULE
            or repository.codegen is c.Infra.CodegenKind.NONE
            or repository.read_only
        )
        if invalid_members:
            return r[tuple[t.StrSequence, t.StrSequence]].fail(
                "managed workspace member contracts are invalid: "
                + ", ".join(sorted(invalid_members))
            )
        invalid_external = tuple(
            repository.name
            for repository in workspace_spec.content_only
            if repository.role is not c.Infra.RepositoryRole.CONTENT_ONLY
            or repository.codegen is not c.Infra.CodegenKind.NONE
            or not repository.read_only
        )
        if invalid_external:
            return r[tuple[t.StrSequence, t.StrSequence]].fail(
                "external workspace repository contracts are invalid: "
                + ", ".join(sorted(invalid_external))
            )
        managed_paths = {
            repository.path.as_posix() for repository in workspace_spec.members
        }
        external_paths = {
            repository.path.as_posix()
            for repository in workspace_spec.content_only
            if repository.checkout is c.Infra.CheckoutKind.SUBMODULE
        }
        overlap = managed_paths & external_paths
        if overlap:
            return r[tuple[t.StrSequence, t.StrSequence]].fail(
                "workspace gitlinks have conflicting ownership: "
                + ", ".join(sorted(overlap))
            )
        indexed_paths = set(indexed_gitlinks)
        classified_paths = managed_paths | external_paths
        if indexed_paths != classified_paths:
            return r[tuple[t.StrSequence, t.StrSequence]].fail(
                "Git submodules and typed workspace ownership differ"
            )
        return r[tuple[t.StrSequence, t.StrSequence]].ok(
            (tuple(sorted(managed_paths)), tuple(sorted(external_paths)))
        )

    @classmethod
    def analysis_exclusion_paths(
        cls, repository_root: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Derive analyzer exclusions from immutable repositories and path overlays."""
        if not cls._manifest_path(repository_root).is_file():
            # Without the config owner there is no declared external tree.
            return r[tuple[Path, ...]].ok(())
        workspace_result = cls.load_workspace_spec(repository_root)
        if workspace_result.failure:
            return r[tuple[Path, ...]].fail(
                workspace_result.error or "workspace analysis scope is unavailable"
            )
        return r[tuple[Path, ...]].ok(
            cls.workspace_analysis_exclusion_paths(workspace_result.value)
        )

    @staticmethod
    def workspace_analysis_exclusion_paths(
        workspace: m.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Project one analysis scope from a validated workspace contract."""
        paths = dict.fromkeys((
            *(repository.path for repository in workspace.content_only),
            *(exclusion.path for exclusion in workspace.exclusions),
        ))
        return tuple(paths)

    @staticmethod
    def _gitmodule_contract(
        superproject_root: Path, member_path: str
    ) -> p.Result[tuple[str, str]]:
        """Read the exact URL and branch for one declared Git submodule path."""
        gitmodules_path = superproject_root / c.Infra.GITMODULES
        if not gitmodules_path.is_file():
            return r[tuple[str, str]].fail(
                f"Git superproject has no {c.Infra.GITMODULES}: {superproject_root}"
            )
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
            if not line.strip():
                continue
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
        branch = u.Cli.capture(
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
        if branch.failure or not branch.value:
            return r[tuple[str, str]].fail(
                branch.error or f"Git submodule branch is missing: {member_path}"
            )
        return r[tuple[str, str]].ok((url.value, branch.value))

    @classmethod
    def _detect_attached(
        cls,
        project_root: Path,
        superproject_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None,
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Validate a real submodule against the parent and local manifests."""
        member_root_result = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-toplevel"], cwd=project_root
        )
        if member_root_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                member_root_result.error or "unable to resolve Git repository root"
            )
        member_root = Path(member_root_result.value).resolve()
        try:
            member_path = member_root.relative_to(superproject_root).as_posix()
        except ValueError as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)

        parent_manifest = cls._manifest_path(superproject_root)
        if not parent_manifest.is_file():
            return r[c.Infra.WorkspaceMode].fail(
                f"Git superproject has no workspace manifest: {parent_manifest}"
            )
        parent_result = cls.load_workspace_spec(superproject_root)
        if parent_result.failure:
            return r[c.Infra.WorkspaceMode].fail(parent_result.error)
        parent_spec = parent_result.value
        parent_contract = cls._validate_local_repository(parent_spec.repository)
        if parent_contract.failure:
            return r[c.Infra.WorkspaceMode].fail(parent_contract.error)
        if parent_spec.repository.role != c.Infra.RepositoryRole.WORKSPACE_ROOT:
            return r[c.Infra.WorkspaceMode].fail(
                "Git superproject manifest role must be workspace-root"
            )

        declared_members = tuple(
            repository
            for repository in parent_spec.members
            if repository.path.as_posix() == member_path
        )
        if len(declared_members) != 1:
            return r[c.Infra.WorkspaceMode].fail(
                f"Git submodule path is not one active workspace member: {member_path}"
            )
        declared = declared_members[0]
        if (
            declared.state != c.Infra.RepositoryState.ACTIVE
            or declared.role != c.Infra.RepositoryRole.WORKSPACE_MEMBER
            or declared.profile != c.Infra.MakeProfile.WORKSPACE_MEMBER
            or declared.checkout != c.Infra.CheckoutKind.SUBMODULE
            or declared.read_only
        ):
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member role/state/profile/checkout mismatch: {member_path}"
            )

        local_spec = workspace_spec
        local_manifest = cls._manifest_path(member_root)
        if local_spec is None and local_manifest.is_file():
            local_result = cls.load_workspace_spec(member_root)
            if local_result.failure:
                return r[c.Infra.WorkspaceMode].fail(local_result.error)
            local_spec = local_result.value
        if local_spec is not None:
            local_repository = local_spec.repository
            comparable_local = (
                local_repository.name,
                local_repository.distribution,
                local_repository.provider,
                local_repository.url,
                local_repository.branch,
                local_repository.state,
                local_repository.codegen,
                local_repository.package,
                local_repository.editable,
                local_repository.read_only,
                local_repository.beads,
            )
            comparable_declared = (
                declared.name,
                declared.distribution,
                declared.provider,
                declared.url,
                declared.branch,
                declared.state,
                declared.codegen,
                declared.package,
                declared.editable,
                declared.read_only,
                declared.beads,
            )
            if comparable_local != comparable_declared:
                return r[c.Infra.WorkspaceMode].fail(
                    f"local and parent workspace member contracts differ: {member_path}"
                )

        gitmodule_result = cls._gitmodule_contract(superproject_root, member_path)
        if gitmodule_result.failure:
            return r[c.Infra.WorkspaceMode].fail(gitmodule_result.error)
        gitmodule_url, gitmodule_branch = gitmodule_result.value
        origin = u.Cli.capture(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"], cwd=member_root
        )
        if origin.failure or not origin.value:
            return r[c.Infra.WorkspaceMode].fail(
                origin.error or f"workspace member origin is missing: {member_path}"
            )
        gitlink = u.Cli.capture(
            [c.Infra.GIT, "ls-files", "--stage", "--", member_path],
            cwd=superproject_root,
        )
        if gitlink.failure or not gitlink.value:
            return r[c.Infra.WorkspaceMode].fail(
                gitlink.error or f"workspace member gitlink is missing: {member_path}"
            )
        match gitlink.value.split():
            case ["160000", gitlink_head, "0", indexed_path] if (
                indexed_path == member_path
            ):
                pass
            case _:
                return r[c.Infra.WorkspaceMode].fail(
                    f"workspace member gitlink is malformed: {member_path}"
                )
        member_head = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", "HEAD^{commit}"], cwd=member_root
        )
        if member_head.failure or not member_head.value:
            return r[c.Infra.WorkspaceMode].fail(
                member_head.error or f"workspace member HEAD is missing: {member_path}"
            )
        if gitmodule_url != declared.url or origin.value != declared.url:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member URL mismatch: {member_path}"
            )
        if gitmodule_branch != declared.branch:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member branch mismatch: {member_path}"
            )
        if member_head.value != gitlink_head:
            return r[c.Infra.WorkspaceMode].fail(
                "workspace member gitlink mismatch: "
                f"{member_path} expected {gitlink_head} got {member_head.value}"
            )
        return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.WORKSPACE)

    @classmethod
    def inspect(
        cls,
        project_root: Path,
        declared: m.Infra.RepositoryRef | None = None,
    ) -> p.Result[m.Infra.RepositoryTopology]:
        """Inspect Git topology once and derive every runtime policy."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[m.Infra.RepositoryTopology].fail_op(
                "Workspace detection", exc
            )
        if not resolved_project_root.is_dir():
            return r[m.Infra.RepositoryTopology].fail(
                f"project root is not a directory: {resolved_project_root}"
            )

        workspace_spec: m.Infra.WorkspaceSpec | None = None
        local_manifest = cls._manifest_path(resolved_project_root)
        if local_manifest.is_file():
            local_result = cls.load_workspace_spec(resolved_project_root)
            if local_result.failure:
                return r[m.Infra.RepositoryTopology].fail(local_result.error)
            # mro-i6nq.10: Unwrap only after the fail-closed result branch.
            local_spec = local_result.unwrap()
            local_contract = cls._validate_local_repository(local_spec.repository)
            if local_contract.failure:
                return r[m.Infra.RepositoryTopology].fail(local_contract.error)
            workspace_spec = local_spec
            declared = declared or local_spec.repository
        git_probe = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=resolved_project_root,
        )
        if git_probe.failure:
            return r[m.Infra.RepositoryTopology].fail(
                git_probe.error or "unable to execute Git workspace probe"
            )
        if git_probe.value.exit_code != 0:
            if (resolved_project_root / c.Infra.GIT_DIR).exists():
                return r[m.Infra.RepositoryTopology].fail(
                    git_probe.value.stderr.strip() or "invalid Git repository metadata"
                )
            return cls._topology_result(
                resolved_project_root,
                declared=declared,
                mode=c.Infra.WorkspaceMode.STANDALONE,
                attached=False,
                managed_gitlinks=(),
                external_gitlinks=(),
            )
        repository_root = cls.resolve_repository_root(resolved_project_root)
        if repository_root.failure:
            return r[m.Infra.RepositoryTopology].fail(
                repository_root.error or "unable to resolve current Git repository"
            )
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=repository_root.value,
        )
        if superproject.failure:
            return r[m.Infra.RepositoryTopology].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        if superproject.value:
            attached_validation = cls._detect_attached(
                repository_root.value,
                Path(superproject.value).resolve(),
                workspace_spec,
            )
            if attached_validation.failure:
                return r[m.Infra.RepositoryTopology].fail(
                    attached_validation.error
                )
            return cls._topology_result(
                repository_root.value,
                declared=declared,
                mode=c.Infra.WorkspaceMode.STANDALONE,
                attached=True,
                managed_gitlinks=(),
                external_gitlinks=(),
            )
        submodules = cls._declared_submodule_paths(repository_root.value)
        if submodules.failure:
            return r[m.Infra.RepositoryTopology].fail(
                submodules.error or "unable to resolve declared Git submodules"
            )
        classified = cls._classify_gitlinks(workspace_spec, submodules.value)
        if classified.failure:
            return r[m.Infra.RepositoryTopology].fail(
                classified.error or "unable to classify declared Git submodules"
            )
        managed_gitlinks, external_gitlinks = classified.value
        return cls._topology_result(
            repository_root.value,
            declared=declared,
            mode=(
                c.Infra.WorkspaceMode.WORKSPACE
                if managed_gitlinks
                else c.Infra.WorkspaceMode.STANDALONE
            ),
            attached=False,
            managed_gitlinks=managed_gitlinks,
            external_gitlinks=external_gitlinks,
        )

    @staticmethod
    def _topology_result(
        repository_root: Path,
        *,
        declared: m.Infra.RepositoryRef | None,
        mode: c.Infra.WorkspaceMode,
        attached: bool,
        managed_gitlinks: t.StrSequence,
        external_gitlinks: t.StrSequence,
    ) -> p.Result[m.Infra.RepositoryTopology]:
        """Build the typed runtime projection from one completed inspection."""
        overlay_enabled = bool(declared and declared.beads)
        if attached and overlay_enabled:
            return r[m.Infra.RepositoryTopology].fail(
                "Beads overlay is forbidden for an attached Git submodule"
            )
        if mode is c.Infra.WorkspaceMode.WORKSPACE and overlay_enabled:
            return r[m.Infra.RepositoryTopology].fail(
                "Beads overlay is only valid for independent standalone projects"
            )
        projected_repository = declared
        if declared is not None:
            role = (
                c.Infra.RepositoryRole.WORKSPACE_ROOT
                if mode is c.Infra.WorkspaceMode.WORKSPACE
                else c.Infra.RepositoryRole.STANDALONE
            )
            profile = (
                c.Infra.MakeProfile.WORKSPACE_ROOT
                if mode is c.Infra.WorkspaceMode.WORKSPACE
                else c.Infra.MakeProfile.STANDALONE
            )
            checkout = (
                c.Infra.CheckoutKind.SUBMODULE
                if attached
                else (
                    c.Infra.CheckoutKind.ROOT
                    if mode is c.Infra.WorkspaceMode.WORKSPACE
                    else c.Infra.CheckoutKind.INDEPENDENT
                )
            )
            projected_repository = m.Infra.RepositoryRef.model_validate({
                **declared.model_dump(),
                "role": role,
                "profile": profile,
                "checkout": checkout,
            })
        return r[m.Infra.RepositoryTopology].ok(
            m.Infra.RepositoryTopology(
                repository_root=repository_root,
                mode=mode,
                attached=attached,
                managed_gitlinks=managed_gitlinks,
                external_gitlinks=external_gitlinks,
                beads_enabled=(
                    mode is c.Infra.WorkspaceMode.WORKSPACE or overlay_enabled
                )
                and not attached,
                repository=projected_repository,
            )
        )

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Project the public mode from the canonical topology inspection."""
        inspected = self.inspect(project_root)
        if inspected.failure:
            return r[c.Infra.WorkspaceMode].fail(
                inspected.error or "unable to inspect repository topology"
            )
        return r[c.Infra.WorkspaceMode].ok(inspected.value.mode)

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
