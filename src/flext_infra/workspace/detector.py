"""Strict manifest-backed workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override
from urllib.parse import urlparse

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

    @staticmethod
    def _repository_is_governed(
        repository: m.Infra.RepositoryRef, provider: m.Infra.ProviderSpec
    ) -> bool:
        """Require provider key, host, and organization to agree exactly."""
        if repository.provider != provider.name:
            return False
        provider_url = urlparse(provider.base_url)
        repository_url = urlparse(repository.url)
        provider_path = provider_url.path.strip("/")
        repository_path = repository_url.path.strip("/")
        repository_name = repository_path.removeprefix(
            f"{provider.organization}/"
        ).removesuffix(".git")
        return (
            provider_url.scheme == repository_url.scheme
            and provider_url.netloc == repository_url.netloc
            and provider_path == provider.organization
            and bool(repository_name)
            and repository_path == f"{provider.organization}/{repository_name}.git"
        )

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
        external_paths = cls._validate_observed_dependencies(repository_root, validated)
        if external_paths.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                external_paths.error
                or f"workspace dependency inventory is invalid: {manifest_path}"
            )
        return r[m.Infra.WorkspaceSpec].ok(
            validated.model_copy(
                update={"external_dependency_paths": external_paths.value}
            )
        )

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
        local_repository = repository.model_copy(update={"path": Path()})
        declared_paths = u.Infra.git_declared_submodule_paths(repository_root)
        if declared_paths.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                declared_paths.error or "unable to derive Git submodule topology"
            )
        members: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        governed_paths: set[Path] = set()
        providers = {item.name: item for item in config.Infra.codegen.providers}
        for path in declared_paths.value:
            candidates = tuple(
                item
                for item in config.Infra.codegen.repositories
                if item.path == path and not item.read_only
            )
            if len(candidates) > 1:
                return r[m.Infra.WorkspaceSpec].fail(
                    f"repository catalog duplicates submodule path: {path.as_posix()}"
                )
            if not candidates:
                continue
            candidate = candidates[0]
            provider = providers.get(candidate.provider)
            if provider is None or not cls._repository_is_governed(candidate, provider):
                continue
            contract = cls._gitmodule_contract(repository_root, path.as_posix())
            if contract.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    contract.error or f"invalid Git submodule: {path.as_posix()}"
                )
            if contract.value != (candidate.url, provider.branch):
                continue
            members.append(candidate)
            governed_paths.add(path)
        external_dependency_paths = tuple(
            path for path in declared_paths.value if path not in governed_paths
        )
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_name,
                repository=local_repository,
                members=tuple(members),
                external_dependency_paths=external_dependency_paths,
            )
        )

    @classmethod
    def _validate_observed_dependencies(
        cls, repository_root: Path, workspace: m.Infra.WorkspaceSpec
    ) -> p.Result[tuple[Path, ...]]:
        """Match governed members and external dependencies to live Git topology."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        if declared.failure:
            return r[tuple[Path, ...]].fail(
                declared.error or "unable to read Git submodule topology"
            )
        declared_set = frozenset(declared.value)
        providers = {item.name: item for item in config.Infra.codegen.providers}
        governed_paths: set[Path] = set()
        for member in workspace.members:
            if member.read_only:
                return r[tuple[Path, ...]].fail(
                    f"read-only dependency cannot be a governed member: {member.name}"
                )
            provider = providers.get(member.provider)
            if provider is None or not cls._repository_is_governed(member, provider):
                return r[tuple[Path, ...]].fail(
                    f"external or fork dependency cannot be a governed member: {member.name}"
                )
            if member.path not in declared_set:
                return r[tuple[Path, ...]].fail(
                    "governed workspace member is absent from .gitmodules: "
                    f"{member.path.as_posix()}"
                )
            contract = cls._gitmodule_contract(repository_root, member.path.as_posix())
            if contract.failure:
                return r[tuple[Path, ...]].fail(
                    contract.error or f"invalid governed member: {member.name}"
                )
            if contract.value != (member.url, provider.branch):
                return r[tuple[Path, ...]].fail(
                    f"governed workspace member contract differs: {member.name}"
                )
            governed_paths.add(member.path)
        observed_external = tuple(
            path for path in declared.value if path not in governed_paths
        )
        return r[tuple[Path, ...]].ok(observed_external)

    @staticmethod
    def resolve_workspace_root(repository_root: Path) -> p.Result[Path]:
        """Resolve the manifest owner for a repository or attached member."""
        resolved_root = repository_root.expanduser().resolve()
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=resolved_root,
        )
        if superproject.failure:
            # A path that is not inside ANY Git work tree is a standalone project
            # that owns its own workspace root (covers freshly scaffolded projects
            # before `git init`, and repo-less checkouts). Git reports this with a
            # non-zero rev-parse; confirm it via --is-inside-work-tree so a genuine
            # in-repo failure still fails closed (NOTE mro-p68a.5, agent codex).
            inside_work_tree = u.Cli.capture(
                [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=resolved_root
            )
            if inside_work_tree.failure or inside_work_tree.value.strip() != "true":
                return r[Path].ok(resolved_root)
            return r[Path].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        return r[Path].ok(
            Path(superproject.value).resolve() if superproject.value else resolved_root
        )

    @staticmethod
    def workspace_analysis_exclusion_paths(
        workspace: m.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Return all workspace paths excluded from static analysis scopes.

        Content-only repositories are foreign, read-only trees and therefore
        never enter Ruff or type-checkers. Explicit ``exclusions`` extend that
        same typed scope for non-repository paths without duplicating repository
        declarations.
        """
        seen: set[Path] = set()
        paths: list[Path] = []
        for path in (
            *workspace.external_dependency_paths,
            *(exclusion.path for exclusion in workspace.exclusions),
        ):
            if path not in seen:
                seen.add(path)
                paths.append(path)
        return tuple(paths)

    @classmethod
    def analysis_exclusion_paths(
        cls, repository_root: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Load workspace spec and return all paths excluded from analysis.

        Projects that are neither manifest owners nor catalog-declared FLEXT
        repositories are treated as unmanaged: they carry no workspace-scoped
        exclusions. This keeps Ruff/Pyright discovery phases usable for
        ad-hoc or third-party trees without weakening validation for declared
        FLEXT roots.
        """
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file():
            metadata = u.read_project_metadata(repository_root)
            if metadata.failure:
                # Not a Python project at all: no workspace exclusions apply.
                return r[tuple[Path, ...]].ok(())
            catalog_names = {
                item.name for item in config.Infra.codegen.repositories
            }
            if metadata.value.project.name not in catalog_names:
                # A Python project, but not a catalogued FLEXT workspace.
                return r[tuple[Path, ...]].ok(())
        spec = cls.load_workspace_spec(repository_root)
        if spec.failure:
            return r[tuple[Path, ...]].fail(
                spec.error or f"unable to load workspace spec: {repository_root}"
            )
        return r[tuple[Path, ...]].ok(
            cls.workspace_analysis_exclusion_paths(spec.value)
        )

    @staticmethod
    def _validate_local_repository(repository: m.Infra.RepositoryRef) -> p.Result[bool]:
        """Validate immutable relation metadata for a local manifest owner."""
        if repository.path.as_posix() != ".":
            return r[bool].fail("local repository manifest path must be '.'")
        if repository.state != c.Infra.RepositoryState.ACTIVE:
            return r[bool].fail("local repository must have active state")
        if repository.role not in {
            c.Infra.RepositoryRole.WORKSPACE_ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            c.Infra.RepositoryRole.STANDALONE,
        }:
            return r[bool].fail(
                f"unsupported local repository role: {repository.role.value}"
            )
        expected_checkout = {
            c.Infra.RepositoryRole.WORKSPACE_ROOT: c.Infra.CheckoutKind.ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER: c.Infra.CheckoutKind.SUBMODULE,
            c.Infra.RepositoryRole.STANDALONE: c.Infra.CheckoutKind.INDEPENDENT,
        }[repository.role]
        if repository.checkout is not expected_checkout:
            return r[bool].fail(
                "local repository role/checkout mismatch: "
                f"{repository.role.value}/{repository.checkout.value}"
            )
        if repository.read_only:
            return r[bool].fail("local repository cannot be read-only")
        return r[bool].ok(True)

    @classmethod
    def _unattached_mode(
        cls, repository_root: Path, workspace_spec: m.Infra.WorkspaceSpec | None
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Infer root from actual first-party governed submodule declarations."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        if declared.failure:
            return r[c.Infra.WorkspaceMode].fail(
                declared.error or "unable to read Git submodule topology"
            )
        if not declared.value:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        resolved_workspace = workspace_spec
        if resolved_workspace is None:
            workspace_result = cls.load_workspace_spec(repository_root)
            if workspace_result.failure:
                return r[c.Infra.WorkspaceMode].fail(
                    workspace_result.error or "unable to derive governed topology"
                )
            resolved_workspace = workspace_result.value
        providers = {item.name: item for item in config.Infra.codegen.providers}
        governed: t.MutableSequenceOf[Path] = []
        declared_set = frozenset(declared.value)
        for member in resolved_workspace.members:
            if member.read_only:
                continue
            provider = providers.get(member.provider)
            if provider is None or not cls._repository_is_governed(member, provider):
                return r[c.Infra.WorkspaceMode].fail(
                    "mutable workspace member is not first-party governed: "
                    f"{member.name}"
                )
            if member.path not in declared_set:
                return r[c.Infra.WorkspaceMode].fail(
                    "governed workspace member is absent from .gitmodules: "
                    f"{member.path.as_posix()}"
                )
            contract = cls._gitmodule_contract(repository_root, member.path.as_posix())
            if contract.failure:
                return r[c.Infra.WorkspaceMode].fail(
                    contract.error or f"invalid governed member: {member.name}"
                )
            if contract.value != (member.url, provider.branch):
                return r[c.Infra.WorkspaceMode].fail(
                    f"governed workspace member contract differs: {member.name}"
                )
            governed.append(member.path)
        return r[c.Infra.WorkspaceMode].ok(
            c.Infra.WorkspaceMode.WORKSPACE
            if governed
            else c.Infra.WorkspaceMode.STANDALONE
        )

    @classmethod
    def conform_target(
        cls, repository_root: Path, workspace_spec: m.Infra.WorkspaceSpec | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive the sole conformance target from live Git and typed identity."""
        resolved_root = repository_root.expanduser().resolve()
        governing_root_result = cls.resolve_workspace_root(resolved_root)
        if governing_root_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                governing_root_result.error or "unable to resolve governing root"
            )
        governing_root = governing_root_result.value
        resolved_workspace = workspace_spec
        if resolved_workspace is None:
            workspace_result = cls.load_workspace_spec(governing_root)
            if workspace_result.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    workspace_result.error or "unable to load governing workspace"
                )
            resolved_workspace = workspace_result.value
        if resolved_root == governing_root:
            repository = resolved_workspace.repository
        else:
            try:
                relative_path = resolved_root.relative_to(governing_root)
            except ValueError as exc:
                return r[m.Infra.RepositoryConformTarget].fail_op(
                    "Conformance target resolution", exc
                )
            matches = tuple(
                item
                for item in resolved_workspace.members
                if item.path == relative_path
            )
            if len(matches) != 1:
                return r[m.Infra.RepositoryConformTarget].fail(
                    "attached repository is an external read-only dependency, "
                    f"not one governed member: {relative_path.as_posix()}"
                )
            repository = matches[0]
        if repository.read_only:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository is an external read-only dependency: {repository.name}"
            )
        metadata = u.read_project_metadata(resolved_root)
        if metadata.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                metadata.error or f"unable to read project metadata: {resolved_root}"
            )
        canonical_project_name = metadata.value.project.name
        if canonical_project_name != repository.distribution:
            return r[m.Infra.RepositoryConformTarget].fail(
                "project metadata and repository identity differ: "
                f"{canonical_project_name} != {repository.distribution}"
            )
        providers = tuple(
            item
            for item in config.Infra.codegen.providers
            if item.name == repository.provider
        )
        if len(providers) != 1:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        provider = providers[0]
        if not cls._repository_is_governed(repository, provider):
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository is an external or fork URL: {repository.url}"
            )
        overlays = tuple(
            item
            for item in resolved_workspace.repository_policy_overlays
            if item.project == canonical_project_name
        )
        if len(overlays) > 1:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository policy overlay is duplicated: {canonical_project_name}"
            )
        overlay = (
            overlays[0]
            if overlays
            else m.Infra.RepositoryPolicyOverlaySpec(project=canonical_project_name)
        )
        mode_result = cls().detect(resolved_root)
        if mode_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                mode_result.error or "unable to infer repository topology"
            )
        attached = resolved_root != governing_root
        make_profile = (
            c.Infra.MakeProfile.WORKSPACE_ROOT
            if mode_result.value is c.Infra.WorkspaceMode.WORKSPACE
            else c.Infra.MakeProfile.STANDALONE
        )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=repository,
                root=resolved_root,
                make_profile=make_profile,
                beads_enabled=(
                    False
                    if attached
                    else make_profile is c.Infra.MakeProfile.WORKSPACE_ROOT
                    or overlay.beads_enabled
                ),
                canonical_project_name=canonical_project_name,
                baseline_branch=provider.branch,
                ci_enabled=overlay.ci_enabled,
                external_dependency_paths=(
                    resolved_workspace.external_dependency_paths
                ),
                technical_branch_patterns=(
                    config.Infra.codegen.branch_policy.technical_branch_patterns
                ),
                governed_branch_patterns=(
                    config.Infra.codegen.branch_policy.governed_branch_patterns
                ),
            )
        )

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
        declared_paths = u.Infra.git_declared_submodule_paths(superproject_root)
        if declared_paths.failure:
            return r[c.Infra.WorkspaceMode].fail(
                declared_paths.error or "unable to read Git submodule topology"
            )
        if Path(member_path) not in declared_paths.value:
            return r[c.Infra.WorkspaceMode].fail(
                f"Git submodule path is not declared: {member_path}"
            )

        parent_manifest = cls._manifest_path(superproject_root)
        if not parent_manifest.is_file():
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
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
        if not declared_members:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        if len(declared_members) != 1:
            return r[c.Infra.WorkspaceMode].fail(
                f"Git submodule path is not one active workspace member: {member_path}"
            )
        declared = declared_members[0]
        if (
            declared.state != c.Infra.RepositoryState.ACTIVE
            or declared.role != c.Infra.RepositoryRole.WORKSPACE_MEMBER
            or declared.checkout != c.Infra.CheckoutKind.SUBMODULE
        ):
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member role/state/checkout mismatch: {member_path}"
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
                local_repository.role,
                local_repository.state,
                local_repository.checkout,
                local_repository.codegen,
                local_repository.package,
                local_repository.editable,
                local_repository.read_only,
            )
            comparable_declared = (
                declared.name,
                declared.distribution,
                declared.provider,
                declared.url,
                declared.role,
                declared.state,
                declared.checkout,
                declared.codegen,
                declared.package,
                declared.editable,
                declared.read_only,
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
        provider = next(
            (
                item
                for item in config.Infra.codegen.providers
                if item.name == declared.provider
            ),
            None,
        )
        if provider is None:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member provider is unknown: {declared.provider}"
            )
        if gitmodule_branch != provider.branch:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member branch mismatch: {member_path}"
            )
        if member_head.value != gitlink_head:
            return r[c.Infra.WorkspaceMode].fail(
                "workspace member gitlink mismatch: "
                f"{member_path} expected {gitlink_head} got {member_head.value}"
            )
        return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode from typed manifests and real Git metadata."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        if not resolved_project_root.is_dir():
            return r[c.Infra.WorkspaceMode].fail(
                f"project root is not a directory: {resolved_project_root}"
            )

        workspace_spec: m.Infra.WorkspaceSpec | None = None
        local_manifest = self._manifest_path(resolved_project_root)
        if local_manifest.is_file():
            local_result = self.load_workspace_spec(resolved_project_root)
            if local_result.failure:
                return r[c.Infra.WorkspaceMode].fail(local_result.error)
            # mro-i6nq.10: Unwrap only after the fail-closed result branch.
            local_spec = local_result.unwrap()
            local_contract = self._validate_local_repository(local_spec.repository)
            if local_contract.failure:
                return r[c.Infra.WorkspaceMode].fail(local_contract.error)
            workspace_spec = local_spec

        git_probe = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=resolved_project_root,
        )
        if git_probe.failure:
            return r[c.Infra.WorkspaceMode].fail(
                git_probe.error or "unable to execute Git workspace probe"
            )
        if git_probe.value.exit_code != 0:
            if (resolved_project_root / c.Infra.GIT_DIR).exists():
                return r[c.Infra.WorkspaceMode].fail(
                    git_probe.value.stderr.strip() or "invalid Git repository metadata"
                )
            return self._unattached_mode(resolved_project_root, workspace_spec)

        superproject_result = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=resolved_project_root,
        )
        if superproject_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                superproject_result.error or "unable to resolve Git superproject"
            )
        if not superproject_result.value:
            return self._unattached_mode(resolved_project_root, workspace_spec)
        return self._detect_attached(
            resolved_project_root,
            Path(superproject_result.value).resolve(),
            workspace_spec,
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
