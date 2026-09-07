"""Repository-local workspace detection from immutable Git topology inputs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s
from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceGovernanceMixin, s[c.Infra.MakeProfile]
):
    """Classify a repository only from files and Git facts inside that checkout."""

    @staticmethod
    def _beads_path(repository_root: Path) -> Path:
        """Return the dormant repository-local Beads identity path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME

    @staticmethod
    def _workspace_manifest_path(repository_root: Path) -> Path:
        """Return the optional, explicitly selected workspace manifest path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME

    @classmethod
    def _composed_beads_identity_error(
        cls, declared_repository_root: Path, workspace_beads: m.Infra.BeadsProjectSpec
    ) -> str | None:
        member_identity = (
            declared_repository_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME
        )
        # Detection observes the topology; it does not enforce the ledger-route
        # prohibition. Refusing to load a workspace because one composed project
        # still carries the old cross-project symlink makes the migration
        # impossible to perform — nothing can plan the fix for a repository it
        # cannot describe. `codegen conform` owns the prohibition and rejects
        # the link there, per repository and within the requested scope.
        if not member_identity.is_file():
            return f"missing required member Beads routing identity: {member_identity}"
        member_identity_result = cls.load_beads_spec(declared_repository_root)
        if member_identity_result.failure:
            return member_identity_result.error
        member_identity = member_identity_result.value
        member_key = (
            member_identity.workspace,
            member_identity.database,
            member_identity.issue_prefix,
        )
        workspace_key = (
            workspace_beads.workspace,
            workspace_beads.database,
            workspace_beads.issue_prefix,
        )
        if member_key != workspace_key:
            return (
                "member Beads routing identity differs from the workspace ledger: "
                f"{member_key} != {workspace_key}"
            )
        return None

    @staticmethod
    def _provider_owns_url(provider: m.Infra.ProviderSpec, url: str) -> bool:
        """Require the remote identity to name this provider's organization.

        Compares the normalized ``owner/repository`` identity instead of the raw
        URL. CI rewrites private submodule origins to SSH deploy-key URLs, and
        ``urlparse`` cannot read SCP-style Git syntax: ``git@host:org/repo.git``
        yields an empty scheme and netloc, so comparing those fields rejected
        every SSH remote for every provider. ``git_remote_identity`` is the
        owner that already normalizes HTTPS, SSH and Host-alias forms — this
        class uses it to compare declared and live origins — and the
        organization is the discriminator, exactly as ``_provider_for_url``
        documents.
        """
        organization, separator, repository = u.Infra.git_remote_identity(
            url
        ).partition("/")
        return (
            bool(separator)
            and bool(repository)
            and organization == provider.organization.casefold()
        )

    @staticmethod
    def repository_is_governed(
        repository: m.Infra.RepositoryRef, provider: m.Infra.ProviderSpec
    ) -> bool:
        """Require the declared provider and semantic remote owner to agree."""
        if repository.provider != provider.name:
            return False
        resolved = u.Infra.remote_provider(repository.url, (provider,))
        return resolved.success and resolved.value.name == provider.name

    @classmethod
    def load_beads_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.BeadsProjectSpec]:
        """Load dormant Beads data only when an explicit future route selects it."""
        resolved_root = repository_root.expanduser().resolve()
        beads_path = cls._beads_path(resolved_root)
        if not beads_path.is_file():
            return r[m.Infra.BeadsProjectSpec].fail(
                f"missing required repository-local Beads configuration: {beads_path}"
            )
        loaded = u.Cli.config_load(beads_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.BeadsProjectSpec].fail(
                f"invalid repository-local Beads configuration ({beads_path}): "
                f"{loaded.error or 'configuration load failed'}"
            )
        try:
            validated = m.Infra.BeadsProjectSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.BeadsProjectSpec].fail_op(
                f"Beads configuration model validation ({beads_path})", exc
            )
        return r[m.Infra.BeadsProjectSpec].ok(validated)

    @staticmethod
    def _git_origin_url(repository_root: Path) -> p.Result[str]:
        """Read the repository's required origin without inventing one."""
        result = u.Infra.git_remote_url(
            m.Infra.GitRemoteUrlRequest(repo_root=repository_root, remote="origin")
        )
        if result.failure or not result.value.text.strip():
            return r[str].fail(
                result.error or f"repository origin is required: {repository_root}"
            )
        return r[str].ok(result.value.text.strip())

    @staticmethod
    def _provider_for_url(url: str) -> p.Result[m.Infra.ProviderSpec]:
        """Resolve one configured provider, failing closed when none owns the URL."""
        return u.Infra.remote_provider(url, config.Infra.codegen.providers)

    @classmethod
    def _repository_origin_url(
        cls,
        repository_root: Path,
        *,
        path: Path = Path(),
        declared_url: str | None = None,
    ) -> p.Result[str]:
        """Return the origin after proving any declared Git identity agrees."""
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[str].fail(origin.error)
        if declared_url is not None and u.Infra.git_remote_identity(
            origin.value
        ) != u.Infra.git_remote_identity(declared_url):
            return r[str].fail(
                f"subproject origin differs from its .gitmodules URL: {path.as_posix()}"
            )
        return r[str].ok(origin.value)

    @staticmethod
    def _gitmodule_contract(
        repository_root: Path, declared_repository_path: Path
    ) -> p.Result[tuple[str, str]]:
        """Read one exact URL/branch pair from the local ``.gitmodules``."""
        contract = u.Infra.gitmodule_contract(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=repository_root,
                member_path=declared_repository_path.as_posix(),
            )
        )
        if contract.failure:
            return r[tuple[str, str]].fail(
                contract.error
                or f"invalid .gitmodules entry: {subproject_path.as_posix()}"
            )
        return r[tuple[str, str]].ok((contract.value.url, contract.value.branch))

    @classmethod
    def _local_repository_ref(
        cls,
        repository_root: Path,
        *,
        path: Path = Path(),
        checkout: c.Infra.CheckoutKind = c.Infra.CheckoutKind.ROOT,
        declared_url: str | None = None,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Build repository policy from local metadata and an immutable Git URL."""
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return r[m.Infra.RepositoryRef].fail(
                metadata.error or f"unable to read project metadata: {repository_root}"
            )
        origin = cls._repository_origin_url(
            repository_root, path=path, declared_url=declared_url
        )
        if origin.failure:
            return r[m.Infra.RepositoryRef].fail(origin.error)
        effective_url = declared_url or origin.value
        provider_result = cls._provider_for_url(effective_url)
        if provider_result.failure:
            return r[m.Infra.RepositoryRef].fail(provider_result.error)
        provider = provider_result.value
        role = (
            c.Infra.MakeProfile.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.MakeProfile.STANDALONE
        )
        project_name = metadata.value.project.name
        remote_identity = u.Infra.remote_repository_ref(
            project_name, url=effective_url, providers=config.Infra.codegen.providers
        )
        if remote_identity.failure:
            return r[m.Infra.RepositoryRef].fail(
                remote_identity.error
                or "PEP 621 distribution and Git repository identity conflict"
            )
        if remote_identity.value.provider != provider.name:
            return r[m.Infra.RepositoryRef].fail(
                "Git repository provider conflicts with its resolved owner"
            )
        repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=effective_url,
            path=path,
            workspace_mode=role,
            provider=provider.name,
            checkout=checkout,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=checkout is c.Infra.CheckoutKind.SUBMODULE,
            read_only=False,
        )
        if not cls.repository_is_governed(repository, provider):
            return r[m.Infra.RepositoryRef].fail(
                f"repository identity is not governed by provider {provider.name}"
            )
        return r[m.Infra.RepositoryRef].ok(repository)

    @classmethod
    def _load_declared_repositories(
        cls, repository_root: Path, *, workspace_beads: m.Infra.BeadsProjectSpec
    ) -> p.Result[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]:
        """Validate every direct governed .gitmodules entry before planning writes."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        result_type = r[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]
        if declared.failure:
            return result_type.fail(
                declared.error or "unable to read local .gitmodules"
            )
        declared_repositories: list[m.Infra.RepositoryRef] = []
        external: list[Path] = []
        seen: set[Path] = set()
        for path in declared.value:
            if path in seen:
                return result_type.fail(
                    f"duplicate .gitmodules path: {path.as_posix()}"
                )
            seen.add(path)
            loaded = cls._load_declared_repository(
                repository_root,
                path,
                integration_branch=integration_branch,
                workspace_beads=workspace_beads,
            )
            if loaded.failure:
                return result_type.fail(loaded.error)
            if isinstance(loaded.value, Path):
                external.append(loaded.value)
                continue
            declared_repositories.append(loaded.value)
        return result_type.ok((tuple(declared_repositories), tuple(external)))

    @classmethod
    def _load_declared_repository(
        cls,
        repository_root: Path,
        path: Path,
        *,
        integration_branch: str | None = None,
        workspace_beads: m.Infra.BeadsProjectSpec,
    ) -> p.Result[m.Infra.RepositoryRef | Path]:
        """Load one governed Python entry or classify its non-Python checkout."""
        result_type = r[m.Infra.RepositoryRef | Path]
        if path.is_absolute() or not path.parts or ".." in path.parts:
            return result_type.fail(f"invalid .gitmodules path: {path.as_posix()}")
        contract = cls._gitmodule_contract(repository_root, path)
        if contract.failure:
            return result_type.fail(contract.error)
        declared_url, declared_branch = contract.value
        provider_result = cls._provider_for_url(declared_url)
        if provider_result.failure:
            return result_type.fail(provider_result.error)
        provider = provider_result.value
        if not u.Infra.gitmodule_branch_is_governed(
            declared_branch, provider_branch=provider.branch
        ):
            return result_type.fail(
                "governed subproject branch differs from provider policy: "
                f"{path.as_posix()}"
            )
        declared_repository_root = (repository_root / path).resolve()
        if not declared_repository_root.is_relative_to(repository_root):
            return result_type.fail(
                f"subproject escapes workspace root: {path.as_posix()}"
            )
        if not declared_repository_root.is_dir():
            return result_type.fail(
                f"governed subproject checkout is missing: {path.as_posix()}"
            )
        if not (declared_repository_root / c.Infra.PYPROJECT_FILENAME).is_file():
            return result_type.ok(path)
        route_error = (
            cls._composed_beads_identity_error(
                declared_repository_root, workspace_beads
            )
            if (declared_repository_root / c.Infra.BEADS_DIRNAME).is_symlink()
            else None
        )
        if (
            route_error is None
            and not (declared_repository_root / c.Infra.BEADS_DIRNAME).is_symlink()
        ):
            beads = cls.load_beads_spec(declared_repository_root)
            if beads.failure:
                return result_type.fail(beads.error)
        if route_error is not None:
            return result_type.fail(
                "composed project must follow the workspace Beads ledger: "
                f"{route_error}"
            )
        repository = cls._local_repository_ref(
            declared_repository_root,
            path=path,
            composed=True,
            declared_url=declared_url,
        )
        if repository.failure:
            return result_type.fail(repository.error)
        return result_type.ok(repository.value)

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load local identity and validate local, read-only Git topology."""
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        if not resolved_root.is_dir():
            return r[m.Infra.WorkspaceSpec].fail(
                f"repository root is not a directory: {resolved_root}"
            )
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved_root))
        if identity.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(identity)
        beads_result = cls.load_beads_spec(resolved_root)
        member_root = identity.value.primary_root
        member_beads = member_root / c.Infra.BEADS_DIRNAME
        if identity.value.is_attached_submodule and member_beads.is_symlink():
            superproject_root = identity.value.superproject_root
            if superproject_root is None:
                return r[m.Infra.WorkspaceSpec].fail(
                    f"Git submodule has no superproject: {resolved_root}"
                )
            inherited_beads = cls.load_beads_spec(superproject_root)
            if inherited_beads.failure:
                return r[m.Infra.WorkspaceSpec].from_failure(inherited_beads)
            try:
                member_path = member_root.relative_to(superproject_root)
            except ValueError:
                return r[m.Infra.WorkspaceSpec].fail(
                    f"Git submodule escapes its superproject: {member_root}"
                )
            baseline = u.Infra.repository_baseline_branch(superproject_root)
            loaded_member = cls._load_declared_repository(
                superproject_root,
                member_path,
                integration_branch=baseline.value if baseline.success else None,
                workspace_beads=inherited_beads.value,
            )
            if loaded_member.failure or isinstance(loaded_member.value, Path):
                return r[m.Infra.WorkspaceSpec].fail(
                    loaded_member.error
                    or "Git submodule is not a declared governed project: "
                    f"{resolved_root}"
                )
            route_error = cls._composed_beads_identity_error(
                resolved_root, inherited_beads.value
            )
        checkout = (
            c.Infra.CheckoutKind.SUBMODULE
            if identity.value.is_submodule
            else c.Infra.CheckoutKind.ROOT
        )
        repository = cls._local_repository_ref(resolved_root, checkout=checkout)
        if repository.failure:
            return r[m.Infra.WorkspaceSpec].fail(repository.error)
        topology = cls._load_declared_repositories(
            resolved_root, workspace_beads=beads.value
        )
        if topology.failure:
            return r[m.Infra.WorkspaceSpec].fail(topology.error)
        declared_repositories, external = topology.value
        observed_repository = repository.value.model_copy(
            update={
                "role": (
                    c.Infra.MakeProfile.WORKSPACE
                    if declared_repositories
                    else c.Infra.MakeProfile.STANDALONE
                )
            }
        )
        declared_repository = cls._manifest_repository_ref(
            resolved_root, observed=observed_repository, beads=beads.value
        )
        if declared_repository.failure:
            return r[m.Infra.WorkspaceSpec].fail(declared_repository.error)
        repository_ref = declared_repository.value
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=beads.value.workspace,
                beads=beads.value,
                repository=repository_ref,
                declared_repositories=declared_repositories,
                external_dependency_paths=external,
            )
        )

    @classmethod
    def conform_target(
        cls,
        repository_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None = None,
        *,
        project_metadata: p.ProjectMetadata | None = None,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Resolve a target exclusively from the requested checkout."""
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        workspace = workspace_spec
        if workspace is None:
            loaded = cls.load_workspace_spec(resolved_root)
            if loaded.failure:
                return r[m.Infra.RepositoryConformTarget].fail(loaded.error)
            workspace = loaded.value
        if workspace.repository.path != Path():
            return r[m.Infra.RepositoryConformTarget].fail(
                "local workspace repository path must be '.'"
            )
        providers = tuple(
            provider
            for provider in config.Infra.codegen.providers
            if provider.name == workspace.repository.provider
        )
        if len(providers) != 1:
            return r[m.Infra.RepositoryConformTarget].fail(
                "repository provider must resolve exactly once: "
                f"{workspace.repository.provider}"
            )
        (provider,) = providers
        baseline = u.Infra.repository_baseline_branch(
            resolved_root, fallback=provider.branch
        )
        if baseline.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                baseline.error or "repository integration baseline resolution failed"
            )
        metadata = u.read_project_metadata(resolved_root)
        if metadata.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                metadata.error or f"unable to read project metadata: {resolved_root}"
            )
        canonical_project_name = metadata.value.project.name
        if canonical_project_name != workspace.repository.distribution:
            return r[m.Infra.RepositoryConformTarget].fail(
                "project metadata and repository identity differ: "
                f"{canonical_project_name} != {workspace.repository.distribution}"
            )
        make_profile = (
            c.Infra.MakeProfile.WORKSPACE
            if (resolved_root / c.Infra.GITMODULES).is_file()
            else c.Infra.MakeProfile.STANDALONE
        )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=workspace.repository,
                root=resolved_root,
                make_profile=make_profile,
                canonical_project_name=canonical_project_name,
                baseline_branch=baseline.value,
                ci_enabled=True,
                external_dependency_paths=workspace.external_dependency_paths,
                technical_branch_patterns=(
                    config.Infra.codegen.branch_policy.technical_branch_patterns
                ),
                governed_branch_patterns=(
                    config.Infra.codegen.branch_policy.governed_branch_patterns
                ),
            )
        )

    @staticmethod
    def resolve_repository_root(repository_root: Path) -> p.Result[Path]:
        """Return the requested checkout; parent and primary trees are irrelevant."""
        resolved_root = repository_root.expanduser().resolve()
        if not resolved_root.is_dir():
            return r[Path].fail(f"repository root is not a directory: {resolved_root}")
        return r[Path].ok(resolved_root)

    @staticmethod
    def workspace_analysis_exclusion_paths(
        workspace: m.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Return read-only external Git dependencies excluded from analysis."""
        return workspace.external_dependency_paths

    @classmethod
    def analysis_exclusion_paths(
        cls, repository_root: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Load exclusions for governed repositories; ignore ungoverned trees."""
        origin = cls._git_origin_url(repository_root)
        if origin.failure or cls._provider_for_url(origin.value).failure:
            return r[tuple[Path, ...]].ok(())
        workspace = cls.load_workspace_spec(repository_root)
        if workspace.failure:
            return r[tuple[Path, ...]].fail(workspace.error)
        return r[tuple[Path, ...]].ok(
            cls.workspace_analysis_exclusion_paths(workspace.value)
        )

    def detect(self, project_root: Path) -> p.Result[c.Infra.MakeProfile]:
        """Classify solely by the requested repository's own ``.gitmodules``."""
        try:
            resolved_root = project_root.expanduser().resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.MakeProfile].fail_op("Workspace detection", exc)
        if not resolved_root.is_dir():
            return r[c.Infra.MakeProfile].fail(
                f"project root is not a directory: {resolved_root}"
            )
        return r[c.Infra.MakeProfile].ok(
            c.Infra.MakeProfile.WORKSPACE
            if (resolved_root / c.Infra.GITMODULES).is_file()
            else c.Infra.MakeProfile.STANDALONE
        )

    @override
    def execute(self) -> p.Result[c.Infra.MakeProfile]:
        """Execute workspace detection for the configured root."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
