"""Manifest and Git topology mechanics for workspace detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceTopologyMixin(FlextInfraWorkspaceGovernanceMixin):
    """Own the canonical workspace manifest and observed Git contract."""

    @staticmethod
    def _manifest_path(repository_root: Path) -> Path:
        """Return the repository-local topology manifest path."""
        config_dir = t.Infra.PATH_ADAPTER.validate_python(c.CONFIG_DIR_NAME)
        manifest_name = t.Infra.PATH_ADAPTER.validate_python(
            c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        return repository_root / config_dir / manifest_name

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the local manifest or derive it from project and Git SSOTs."""
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file():
            return cls._derive_workspace_spec(repository_root)
        loaded = u.Cli.config_load(manifest_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                loaded.error or f"invalid workspace manifest: {manifest_path}"
            )
        try:
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
        """Derive a manifest from project identity and live Git submodules."""
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                metadata.error
                or f"cannot derive workspace spec without metadata: {repository_root}"
            )
        return cls._derive_workspace_identity(
            repository_root,
            metadata.value.project.name,
            metadata.value.package_name,
        )

    @classmethod
    def _derive_workspace_identity(
        cls, repository_root: Path, project_name: str, package_name: str
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Build the derived workspace after canonical project metadata loads."""
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                origin.error or f"unable to read Git origin: {repository_root}"
            )
        provider = cls._provider_for_url(origin.value)
        root_branch = u.Infra.repository_baseline_branch(
            repository_root, declared_branch=provider.branch
        )
        if root_branch.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                root_branch.error
                or f"unable to derive repository integration branch: {repository_root}"
            )
        declared_paths = u.Infra.git_declared_submodule_paths(repository_root)
        if declared_paths.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                declared_paths.error or "unable to derive Git submodule topology"
            )
        derived = cls._derive_members(repository_root, tuple(declared_paths.value))
        if derived.failure:
            return r[m.Infra.WorkspaceSpec].fail(derived.error)
        members, governed_paths = derived.value
        repository_url = origin.value or (
            f"{provider.base_url.rstrip('/')}/{project_name}.git"
        )
        root_role = (
            c.Infra.RepositoryRole.WORKSPACE_ROOT
            if members
            else c.Infra.RepositoryRole.STANDALONE
        )
        local_repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=repository_url,
            path=Path(),
            role=root_role,
            provider=provider.name,
            branch=root_branch.value,
            checkout=(
                c.Infra.CheckoutKind.ROOT
                if members
                else c.Infra.CheckoutKind.INDEPENDENT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=(repository_root / c.Infra.DEFAULT_SRC_DIR / package_name).is_dir(),
            editable=False,
            read_only=False,
        )
        external_paths = tuple(
            path for path in declared_paths.value if path not in governed_paths
        )
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_name,
                repository=local_repository,
                members=members,
                external_dependency_paths=external_paths,
            )
        )

    @classmethod
    def _derive_member(
        cls, repository_root: Path, path: Path
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Derive one governed member, or identify an external dependency."""
        contract = cls._gitmodule_contract(repository_root, path.as_posix())
        if contract.failure:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                contract.error or f"invalid Git submodule: {path.as_posix()}"
            )
        member_url, member_branch = contract.value
        provider = cls._declared_provider_for_url(member_url)
        if provider is None:
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(())
        member_root = repository_root / path
        metadata = u.read_project_metadata(member_root)
        if metadata.failure:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                metadata.error
                or f"cannot derive governed member metadata: {member_root}"
            )
        member_name = metadata.value.project.name
        member_package = (
            member_root / c.Infra.DEFAULT_SRC_DIR / metadata.value.package_name
        ).is_dir()
        member = m.Infra.RepositoryRef(
            name=member_name,
            distribution=member_name,
            url=member_url,
            path=path,
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider=provider.name,
            branch=member_branch,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=member_package,
            editable=member_package,
            read_only=False,
        )
        if not cls._repository_is_governed(member, provider):
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(())
        return r[tuple[m.Infra.RepositoryRef, ...]].ok((member,))

    @classmethod
    def _derive_members(
        cls, repository_root: Path, declared_paths: tuple[Path, ...]
    ) -> p.Result[tuple[tuple[m.Infra.RepositoryRef, ...], frozenset[Path]]]:
        """Partition declared gitlinks into governed and external paths."""
        members: list[m.Infra.RepositoryRef] = []
        governed_paths: set[Path] = set()
        for path in declared_paths:
            derived = cls._derive_member(repository_root, path)
            if derived.failure:
                return r.fail(r.require_error(derived))
            if not derived.value:
                continue
            members.extend(derived.value)
            governed_paths.add(path)
        return r.ok((tuple(members), frozenset(governed_paths)))

    @staticmethod
    def _validate_live_member_checkout(
        repository_root: Path, member: m.Infra.RepositoryRef
    ) -> p.Result[Path]:
        """Accept a pre-gitlink member only when its real checkout exists."""
        if not (repository_root / member.path / c.Infra.GIT_DIR).exists():
            return r[Path].fail(
                "governed workspace member is absent from .gitmodules "
                f"and has no live checkout: {member.path.as_posix()}"
            )
        return r[Path].ok(member.path)

    @classmethod
    def _validate_observed_member(
        cls,
        repository_root: Path,
        member: m.Infra.RepositoryRef,
        declared_paths: frozenset[Path],
        providers: dict[str, m.Infra.ProviderSpec],
    ) -> p.Result[Path]:
        """Validate one governed manifest member against observed Git state."""
        if member.read_only:
            return r[Path].fail(
                f"read-only dependency cannot be a governed member: {member.name}"
            )
        provider = providers.get(member.provider)
        if provider is None or not cls._repository_is_governed(member, provider):
            return r[Path].fail(
                f"external or fork dependency cannot be a governed member: {member.name}"
            )
        if member.path not in declared_paths:
            return cls._validate_live_member_checkout(repository_root, member)
        contract = cls._gitmodule_contract(repository_root, member.path.as_posix())
        if contract.failure:
            return r[Path].fail(
                contract.error or f"invalid governed member: {member.name}"
            )
        if contract.value != (member.url, member.branch):
            return r[Path].fail(
                f"governed workspace member contract differs: {member.name}"
            )
        return r[Path].ok(member.path)

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
        declared_paths = frozenset(declared.value)
        providers = {item.name: item for item in config.Infra.codegen.providers}
        governed_paths: set[Path] = set()
        for member in workspace.members:
            observed = cls._validate_observed_member(
                repository_root, member, declared_paths, providers
            )
            if observed.failure:
                return r.fail(r.require_error(observed))
            governed_paths.add(observed.value)
        external_paths = tuple(
            path for path in declared.value if path not in governed_paths
        )
        return r.ok(external_paths)

    @staticmethod
    def _gitmodule_section(
        superproject_root: Path, member_path: str
    ) -> p.Result[str]:
        """Resolve exactly one .gitmodules section for a member path."""
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
            return r[str].fail(entries.error or "unable to read Git submodule paths")
        matching_keys: list[str] = []
        for line in entries.value.splitlines():
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                return r[str].fail("malformed Git submodule path entry")
            key, path = parts
            if path == member_path:
                matching_keys.append(key)
        if len(matching_keys) != 1:
            return r[str].fail(
                f"Git submodule path must be declared exactly once: {member_path}"
            )
        return r[str].ok(matching_keys[0].removesuffix(".path"))

    @staticmethod
    def _gitmodule_value(
        superproject_root: Path, section: str, key: str, member_path: str
    ) -> p.Result[str]:
        """Read one required value from an exact .gitmodules section."""
        value = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get",
                f"{section}.{key}",
            ],
            cwd=superproject_root,
        )
        if value.failure or not value.value:
            return r[str].fail(
                value.error or f"Git submodule {key} is missing: {member_path}"
            )
        return r[str].ok(value.value)

    @classmethod
    def _gitmodule_contract(
        cls, superproject_root: Path, member_path: str
    ) -> p.Result[tuple[str, str]]:
        """Read the exact URL and branch for one declared Git submodule path."""
        gitmodules_path = superproject_root / c.Infra.GITMODULES
        if not gitmodules_path.is_file():
            return r[tuple[str, str]].fail(
                f"Git superproject has no {c.Infra.GITMODULES}: {superproject_root}"
            )
        section = cls._gitmodule_section(superproject_root, member_path)
        if section.failure:
            return r[tuple[str, str]].fail(section.error)
        url = cls._gitmodule_value(
            superproject_root, section.value, "url", member_path
        )
        if url.failure:
            return r[tuple[str, str]].fail(url.error)
        branch = cls._gitmodule_value(
            superproject_root, section.value, "branch", member_path
        )
        if branch.failure:
            return r[tuple[str, str]].fail(branch.error)
        return r[tuple[str, str]].ok((url.value, branch.value))


__all__: list[str] = ["FlextInfraWorkspaceTopologyMixin"]
