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
    FlextInfraWorkspaceGovernanceMixin, s[c.Infra.WorkspaceMode]
):
    """Classify a repository only from files and Git facts inside that checkout."""

    @staticmethod
    def _beads_path(repository_root: Path) -> Path:
        """Return the mandatory repository-local Beads identity path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME

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
        """Load and validate the required local ``config/beads.yaml``."""
        resolved_root = repository_root.expanduser().resolve()
        beads_path = cls._beads_path(resolved_root)
        if not beads_path.is_file():
            return r[m.Infra.BeadsProjectSpec].fail(
                f"repository-local Beads configuration is required: {beads_path}"
            )
        loaded = u.Cli.config_load(beads_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.BeadsProjectSpec].fail(
                loaded.error or f"invalid Beads configuration: {beads_path}"
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

    @staticmethod
    def _gitmodule_contract(
        workspace_root: Path, subproject_path: Path
    ) -> p.Result[tuple[str, str]]:
        """Read one exact URL/branch pair from the local ``.gitmodules``."""
        contract = u.Infra.gitmodule_contract(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=workspace_root, member_path=subproject_path.as_posix()
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
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[m.Infra.RepositoryRef].fail(origin.error)
        if declared_url is not None and u.Infra.git_remote_identity(
            origin.value
        ) != u.Infra.git_remote_identity(declared_url):
            return r[m.Infra.RepositoryRef].fail(
                f"subproject origin differs from its .gitmodules URL: {path.as_posix()}"
            )
        effective_url = declared_url or origin.value
        provider_result = cls._provider_for_url(effective_url)
        if provider_result.failure:
            return r[m.Infra.RepositoryRef].fail(provider_result.error)
        provider = provider_result.value
        role = (
            c.Infra.RepositoryRole.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.RepositoryRole.STANDALONE
        )
        project_name = metadata.value.project.name
        repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=effective_url,
            path=path,
            role=role,
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
    def _load_subprojects(
        cls, repository_root: Path
    ) -> p.Result[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]:
        """Validate every direct governed .gitmodules entry before planning writes."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        result_type = r[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]
        if declared.failure:
            return result_type.fail(
                declared.error or "unable to read local .gitmodules"
            )
        subprojects: list[m.Infra.RepositoryRef] = []
        seen: set[Path] = set()
        for path in declared.value:
            if path in seen:
                return result_type.fail(
                    f"duplicate .gitmodules path: {path.as_posix()}"
                )
            seen.add(path)
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
            subproject_root = (repository_root / path).resolve()
            if not subproject_root.is_relative_to(repository_root):
                return result_type.fail(
                    f"subproject escapes workspace root: {path.as_posix()}"
                )
            if not subproject_root.is_dir():
                return result_type.fail(
                    f"governed subproject checkout is missing: {path.as_posix()}"
                )
            beads = cls.load_beads_spec(subproject_root)
            if beads.failure:
                return result_type.fail(beads.error)
            repository = cls._local_repository_ref(
                subproject_root,
                path=path,
                checkout=c.Infra.CheckoutKind.SUBMODULE,
                declared_url=declared_url,
            )
            if repository.failure:
                return result_type.fail(repository.error)
            subprojects.append(repository.value)
        return result_type.ok((tuple(subprojects), ()))

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
        beads = cls.load_beads_spec(resolved_root)
        if beads.failure:
            return r[m.Infra.WorkspaceSpec].fail(beads.error)
        repository = cls._local_repository_ref(resolved_root)
        if repository.failure:
            return r[m.Infra.WorkspaceSpec].fail(repository.error)
        topology = cls._load_subprojects(resolved_root)
        if topology.failure:
            return r[m.Infra.WorkspaceSpec].fail(topology.error)
        subprojects, external = topology.value
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=beads.value.workspace,
                beads=beads.value,
                repository=repository.value,
                subprojects=subprojects,
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
                beads=workspace.beads,
                canonical_project_name=canonical_project_name,
                baseline_branch=provider.branch,
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
    def resolve_workspace_root(repository_root: Path) -> p.Result[Path]:
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

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify solely by the requested repository's own ``.gitmodules``."""
        try:
            resolved_root = project_root.expanduser().resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        if not resolved_root.is_dir():
            return r[c.Infra.WorkspaceMode].fail(
                f"project root is not a directory: {resolved_root}"
            )
        return r[c.Infra.WorkspaceMode].ok(
            c.Infra.WorkspaceMode.WORKSPACE
            if (resolved_root / c.Infra.GITMODULES).is_file()
            else c.Infra.WorkspaceMode.STANDALONE
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute workspace detection for the configured root."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
