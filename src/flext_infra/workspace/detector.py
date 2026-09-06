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
        """Return the mandatory repository-local Beads identity path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME

    @staticmethod
    def _workspace_manifest_path(repository_root: Path) -> Path:
        """Return the optional, explicitly selected workspace manifest path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME

    @classmethod
    def _submodule_beads_route_error(
        cls,
        subproject_root: Path,
        repository_root: Path,
        workspace_beads: m.Infra.BeadsProjectSpec,
    ) -> str | None:
        member_beads = subproject_root / c.Infra.BEADS_DIRNAME
        member_identity = (
            subproject_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME
        )
        workspace_route = repository_root / c.Infra.BEADS_DIRNAME
        if not member_beads.is_symlink():
            return f"missing required workspace Beads ledger route: {member_beads}"
        if member_beads.resolve() != workspace_route.resolve():
            return (
                "workspace Beads ledger route must resolve to "
                f"{workspace_route}, got {member_beads.resolve()}"
            )
        if not member_identity.is_file():
            return f"missing required member Beads routing identity: {member_identity}"
        member_identity_result = cls.load_beads_spec(subproject_root)
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
        """Require the provider key and the owned canonical URL to agree."""
        if repository.provider != provider.name:
            return False
        return FlextInfraWorkspaceDetector._provider_owns_url(provider, repository.url)

    @classmethod
    def load_beads_spec(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.BeadsProjectSpec]:
        """Load and validate the required local ``config/beads.yaml``."""
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

    @classmethod
    def _declared_provider_for_url(cls, url: str) -> m.Infra.ProviderSpec | None:
        """Return the exact configured provider owning ``url``."""
        for provider in config.Infra.codegen.providers:
            if cls._provider_owns_url(provider, url):
                return provider
        return None

    @classmethod
    def _provider_for_url(cls, url: str) -> p.Result[m.Infra.ProviderSpec]:
        """Resolve one configured provider, failing closed without leaking the URL."""
        declared = cls._declared_provider_for_url(url)
        if declared is not None:
            return r[m.Infra.ProviderSpec].ok(declared)
        return r[m.Infra.ProviderSpec].fail(
            "repository owner must resolve exactly once"
        )

    @staticmethod
    def _manifest_git_contradictions(
        declared: m.Infra.RepositoryRef, observed: m.Infra.RepositoryRef
    ) -> list[str]:
        """Describe every manifest identity or topology conflict with Git."""
        comparisons = (
            (
                declared.name != observed.name,
                f"name {declared.name!r} != {observed.name!r}",
            ),
            (
                declared.distribution != observed.distribution,
                f"distribution {declared.distribution!r} != {observed.distribution!r}",
            ),
            (
                declared.provider != observed.provider,
                f"provider {declared.provider!r} != {observed.provider!r}",
            ),
            (
                declared.path != observed.path,
                f"path {declared.path.as_posix()!r} != {observed.path.as_posix()!r}",
            ),
            (
                declared.role is not observed.role,
                f"role {declared.role.value!r} != {observed.role.value!r}",
            ),
        )
        contradictions = [message for differs, message in comparisons if differs]
        if u.Infra.git_remote_identity(declared.url) != u.Infra.git_remote_identity(
            observed.url
        ):
            contradictions.append("url identity differs from Git origin")
        # Why (cosmos-d0qn4): a repository-local manifest carries the
        # repository's own coordinates. Whether that repository is currently
        # checked out as a submodule is a fact of the parent's Git tree, not of
        # the manifest, so the same manifest must load both standalone (its own
        # CI observes root) and inside a workspace (the parent's conform
        # observes submodule). Only a manifest that claims to be a submodule
        # while Git shows a standalone checkout contradicts reality.
        if (
            declared.checkout is c.Infra.CheckoutKind.SUBMODULE
            and observed.checkout is not c.Infra.CheckoutKind.SUBMODULE
        ):
            contradictions.append(
                "checkout "
                f"{declared.checkout.value!r} contradicts the observed topology"
            )
        return contradictions

    @classmethod
    def _manifest_repository_ref(
        cls,
        repository_root: Path,
        *,
        observed: m.Infra.RepositoryRef,
        beads: m.Infra.BeadsProjectSpec,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Load a selected repository manifest and reconcile it with Git truth.

        A checkout without ``config/workspace.yaml`` remains a valid observed
        repository. Once the manifest exists, however, its complete typed
        ``repository`` record is authoritative for repository policy and must
        agree with the immutable identity and topology observed from Git.
        """
        manifest_path = cls._workspace_manifest_path(repository_root)
        if not manifest_path.is_file():
            return r[m.Infra.RepositoryRef].ok(observed)
        loaded = u.Cli.config_load(manifest_path, expand_env=False)
        if loaded.failure:
            error = loaded.error
            if error is None:
                msg = "workspace manifest load failed without an error"
                raise RuntimeError(msg)
            return r[m.Infra.RepositoryRef].fail(
                f"invalid workspace manifest ({manifest_path}): {error}"
            )
        try:
            manifest = m.Infra.WorkspaceManifestSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.RepositoryRef].fail_op(
                f"workspace manifest model validation ({manifest_path})", exc
            )
        declared = manifest.repository
        contradictions = cls._manifest_git_contradictions(declared, observed)
        if contradictions:
            return r[m.Infra.RepositoryRef].fail(
                f"workspace manifest contradicts Git ({manifest_path}): "
                + "; ".join(contradictions)
            )
        provider = cls._provider_for_url(observed.url)
        if provider.failure:
            error = provider.error
            if error is None:
                msg = "repository owner resolution failed without an error"
                raise RuntimeError(msg)
            return r[m.Infra.RepositoryRef].fail(error)
        if not cls.repository_is_governed(declared, provider.value):
            return r[m.Infra.RepositoryRef].fail(
                f"workspace manifest repository is not governed: {manifest_path}"
            )
        if manifest.ledger_id is not None and manifest.ledger_id != beads.database:
            return r[m.Infra.RepositoryRef].fail(
                "workspace manifest ledger_id contradicts Beads identity "
                f"({manifest_path}): {manifest.ledger_id!r} != {beads.database!r}"
            )
        if (
            manifest.ledger_prefix is not None
            and manifest.ledger_prefix != beads.issue_prefix
        ):
            return r[m.Infra.RepositoryRef].fail(
                "workspace manifest ledger_prefix contradicts Beads identity "
                f"({manifest_path}): {manifest.ledger_prefix!r} != "
                f"{beads.issue_prefix!r}"
            )
        if observed.checkout is c.Infra.CheckoutKind.SUBMODULE:
            # Git owns the checkout relationship; the manifest owns policy.
            return r[m.Infra.RepositoryRef].ok(
                declared.model_copy(update={"checkout": observed.checkout})
            )
        return r[m.Infra.RepositoryRef].ok(declared)

    @staticmethod
    def _gitmodule_contract(
        repository_root: Path, declared_path: Path
    ) -> p.Result[tuple[str, str]]:
        """Read one exact URL/branch pair from the local ``.gitmodules``."""
        contract = u.Infra.gitmodule_contract(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=repository_root, member_path=declared_path.as_posix()
            )
        )
        if contract.failure:
            return r[tuple[str, str]].fail(
                contract.error
                or f"invalid .gitmodules entry: {declared_path.as_posix()}"
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
                f"declared_repository origin differs from its .gitmodules URL: {path.as_posix()}"
            )
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
                f"repository is not governed by provider {provider.name}: {effective_url}"
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
        baseline = u.Infra.repository_baseline_branch(repository_root)
        integration_branch = baseline.value if baseline.success else None
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
        """Load one governed entry, or its declared path for external entries.

        A submodule whose ``.gitmodules`` section explicitly sets
        ``flext-managed`` to anything other than ``true`` is a vendored or
        fork checkout the workspace never governs: it classifies as an
        external dependency without provider or branch policy validation,
        the same contract lane provisioning already applies. Governed
        declared_repositories must resolve to a declared provider and integrate on the
        provider line or on the repository's published integration branch.
        """
        result_type = r[m.Infra.RepositoryRef | Path]
        if path.is_absolute() or not path.parts or ".." in path.parts:
            return result_type.fail(f"invalid .gitmodules path: {path.as_posix()}")
        contract = cls._gitmodule_contract(repository_root, path)
        if contract.failure:
            return result_type.fail(contract.error)
        declared_url, declared_branch = contract.value
        sections = u.Infra.git_submodule_sections(
            m.Infra.GitRepoRequest(repo_root=repository_root)
        )
        if sections.failure:
            return result_type.fail(
                sections.error or "failed to classify submodule declarations"
            )
        section = sections.value.get(path.as_posix())
        if section is not None:
            managed = u.Infra.git_submodule_config_value(
                m.Infra.GitSubmoduleConfigRequest(
                    repo_root=repository_root, section=section, key="flext-managed"
                )
            )
            if managed.failure:
                return result_type.fail(
                    managed.error or f"failed to classify gitlink: {path.as_posix()}"
                )
            if managed.value.text and managed.value.text.lower() != "true":
                return result_type.ok(path)
        provider_result = cls._provider_for_url(declared_url)
        if provider_result.failure:
            return result_type.fail(provider_result.error)
        provider = provider_result.value
        if not u.Infra.gitmodule_branch_is_governed(
            declared_branch,
            provider_branch=provider.branch,
            integration_branch=integration_branch,
        ):
            return result_type.fail(
                "governed declared_repository branch differs from provider policy: "
                f"{path.as_posix()}"
            )
        declared_repository_root = (repository_root / path).resolve()
        if not declared_repository_root.is_relative_to(repository_root):
            return result_type.fail(
                f"declared_repository escapes repository root: {path.as_posix()}"
            )
        if not declared_repository_root.is_dir():
            return result_type.fail(
                f"governed declared_repository checkout is missing: {path.as_posix()}"
            )
        if not (declared_repository_root / c.Infra.PYPROJECT_FILENAME).is_file():
            return result_type.ok(path)
        route_error = (
            cls._submodule_beads_route_error(
                declared_repository_root, repository_root, workspace_beads
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
                "workspace member must inherit the workspace Beads ledger: "
                f"{route_error}"
            )
        repository = cls._local_repository_ref(
            declared_repository_root,
            path=path,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            declared_url=declared_url,
        )
        if repository.failure:
            return result_type.fail(repository.error)
        return result_type.ok(repository.value)

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the repository-local manifest, or derive it from the SSOT catalog."""
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file():
            return cls._derive_workspace_spec(
                repository_root, project_metadata=project_metadata
            )
        declared = cls.load_workspace_declaration(repository_root)
        if declared.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                declared.error or f"invalid workspace manifest: {manifest_path}"
            )
        validated = declared.value
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
    def load_workspace_declaration(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Parse the repository-local manifest without observing Git topology."""
        manifest_path = cls._manifest_path(repository_root)
        if not manifest_path.is_file():
            return r[m.Infra.WorkspaceSpec].fail(
                f"repository declares no workspace manifest: {manifest_path}"
            )
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
    def load_projection_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load only repository-owned declarations needed by scoped projection."""
        manifest_path = cls._manifest_path(repository_root)
        if manifest_path.is_file():
            return cls.load_workspace_declaration(repository_root)
        resolved_metadata = project_metadata
        if resolved_metadata is None:
            metadata = u.read_project_metadata(repository_root)
            if metadata.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    metadata.error
                    or f"cannot derive projection identity: {repository_root}"
                )
            resolved_metadata = metadata.value
        project_name = resolved_metadata.project.name
        repository_url = resolved_metadata.project.urls.repository
        if not repository_url:
            return r[m.Infra.WorkspaceSpec].fail(
                "manifestless projection requires project.urls.Repository: "
                f"{repository_root}"
            )
        provider = cls._declared_provider_for_url(repository_url)
        if provider is None:
            return r[m.Infra.WorkspaceSpec].fail(
                "project.urls.Repository is not owned by a declared provider: "
                f"{repository_url}"
            )
        canonical_url = (
            repository_url
            if repository_url.endswith(".git")
            else f"{repository_url}.git"
        )
        repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=canonical_url,
            path=Path(),
            role=c.Infra.RepositoryRole.STANDALONE,
            provider=provider.name,
            checkout=c.Infra.CheckoutKind.INDEPENDENT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=False,
            read_only=False,
        )
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_name,
                repository=repository,
            )
        )

    @classmethod
    def declared_conform_target(
        cls,
        repository_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec,
        *,
        project_metadata: p.ProjectMetadata | None = None,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive one target exclusively from repository-owned declarations."""
        resolved_root = repository_root.expanduser().resolve()
        repository = workspace_spec.repository
        local_contract = cls._validate_local_repository(repository)
        if local_contract.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                local_contract.error or "invalid local repository declaration"
            )
        resolved_metadata = project_metadata
        if resolved_metadata is None:
            metadata = u.read_project_metadata(resolved_root)
            if metadata.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    metadata.error
                    or f"unable to read project metadata: {resolved_root}"
                )
            resolved_metadata = metadata.value
        canonical_project_name = resolved_metadata.project.name
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
        if not cls.repository_is_governed(repository, provider):
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository is an external or fork URL: {repository.url}"
            )
        overlays = tuple(
            item
            for item in workspace_spec.repository_policy_overlays
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
        make_profile = {
            c.Infra.RepositoryRole.WORKSPACE_ROOT: c.Infra.MakeProfile.WORKSPACE_ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER: (
                c.Infra.MakeProfile.WORKSPACE_MEMBER
            ),
            c.Infra.RepositoryRole.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }.get(repository.role)
        if make_profile is None:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"unsupported local repository role: {repository.role.value}"
            )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=repository,
                root=resolved_root,
                make_profile=make_profile,
                beads_enabled=(
                    make_profile is c.Infra.MakeProfile.WORKSPACE_ROOT
                    or (
                        make_profile is c.Infra.MakeProfile.STANDALONE
                        and overlay.beads_enabled
                    )
                ),
                canonical_project_name=canonical_project_name,
                baseline_branch=u.Infra.resolve_integration_branch(
                    workspace_spec, provider
                ),
                ci_enabled=overlay.ci_enabled,
                ci_matrix_auto_run=overlay.ci_matrix_auto_run,
                external_dependency_paths=workspace_spec.external_dependency_paths,
                technical_branch_patterns=(
                    config.Infra.codegen.branch_policy.technical_branch_patterns
                ),
                governed_branch_patterns=(
                    config.Infra.codegen.branch_policy.governed_branch_patterns
                ),
            )
        )

    @classmethod
    def _derive_governed_member(
        cls, repository_root: Path, path: Path
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Derive zero or one governed member from a declared Git submodule."""
        contract = cls._gitmodule_contract(repository_root, path.as_posix())
        if contract.failure:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                contract.error or f"invalid Git submodule: {path.as_posix()}"
            )
        member_url, member_branch = contract.value
        member_provider = cls._provider_for_url(member_url)
        if not u.Infra.gitmodule_branch_is_governed(
            member_branch, provider_branch=member_provider.branch
        ):
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(())
        member = m.Infra.RepositoryRef(
            name=path.name,
            distribution=path.name,
            url=member_url,
            path=path,
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider=member_provider.name,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        if not cls.repository_is_governed(member, member_provider):
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(())
        return r[tuple[m.Infra.RepositoryRef, ...]].ok((member,))

    @classmethod
    def _derive_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive the spec from the repository itself, never from a registry.

        Operator law: flext-infra owns generic conform behaviour and must not
        carry a catalog of the projects it serves. A repository that ships no
        ``config/workspace.yaml`` is therefore derived from two sources it
        owns outright: its ``pyproject.toml`` metadata for identity, and its
        live Git submodule contract for members. Nothing is fabricated and
        nothing is looked up in flext-infra.
        """
        resolved_metadata = project_metadata
        if resolved_metadata is None:
            metadata = u.read_project_metadata(repository_root)
            if metadata.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    metadata.error
                    or (
                        "cannot derive workspace spec without metadata: "
                        f"{repository_root}"
                    )
                )
            resolved_metadata = metadata.value
        project_name = resolved_metadata.project.name
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                origin.error or f"unable to read Git origin: {repository_root}"
            )
        provider = cls._provider_for_url(origin.value)
        # A checkout with no declared origin (fresh scaffold, transaction
        # worktree) still has a canonical identity: the provider contract plus
        # its own project name. That is derived, not looked up in a registry.
        repository_url = origin.value or (
            f"{provider.base_url.rstrip('/')}/{project_name}.git"
        )
        local_repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=repository_url,
            path=Path(),
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            provider=provider.name,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=False,
            read_only=False,
        )
        declared_paths = u.Infra.git_declared_submodule_paths(repository_root)
        if declared_paths.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                declared_paths.error or "unable to derive Git submodule topology"
            )
        members: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        governed_paths: set[Path] = set()
        for path in declared_paths.value:
            derived = cls._derive_governed_member(repository_root, path)
            if derived.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    derived.error or f"invalid Git submodule: {path.as_posix()}"
                )
            members.extend(derived.value)
            governed_paths.update(member.path for member in derived.value)
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

    @staticmethod
    def _git_origin_url(repository_root: Path) -> p.Result[str]:
        """Read the repository's own declared origin, or an empty remote."""
        result = u.Infra.git_remote_url(
            m.Infra.GitRemoteUrlRequest(repo_root=repository_root, remote="origin")
        )
        if result.failure:
            # A repository with no origin is still a valid standalone checkout;
            # it simply has no provider-governed identity to match.
            return r[str].ok("")
        return r[str].ok(result.value.text.strip())

    @staticmethod
    def _declared_provider_for_url(url: str) -> m.Infra.ProviderSpec | None:
        """Return the declared provider owning ``url``, or ``None`` if ungoverned.

        Providers are generic policy (host, organization, integration branch)
        and remain flext-infra's to own. Which projects exist under them is
        not, so the match is made against the URL the repository itself
        declares.
        """
        parsed = urlparse(url)
        for provider in config.Infra.codegen.providers:
            provider_url = urlparse(provider.base_url)
            if (
                provider_url.scheme == parsed.scheme
                and provider_url.netloc == parsed.netloc
                and parsed.path.strip("/").startswith(f"{provider.organization}/")
            ):
                return provider
        return None

    @classmethod
    def _provider_for_url(cls, url: str) -> m.Infra.ProviderSpec:
        """Resolve the declared provider owning ``url``, else the default one."""
        return cls._declared_provider_for_url(url) or config.Infra.codegen.providers[0]

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
            if provider is None or not cls.repository_is_governed(member, provider):
                return r[tuple[Path, ...]].fail(
                    f"external or fork dependency cannot be a governed member: {member.name}"
                )
            if member.path not in declared_set:
                # The typed manifest is the topology SSOT: a governed member
                # may already be an initialized checkout that Git has not yet
                # recorded as a submodule (conform seeds .gitmodules later).
                # Accept it only when the live directory is a real Git
                # checkout; a manifest row with no checkout and no gitlink is
                # still an invalid topology and fails closed below.
                member_checkout = repository_root / member.path
                if not (member_checkout / ".git").exists():
                    return r[tuple[Path, ...]].fail(
                        "governed workspace member is absent from .gitmodules "
                        f"and has no live checkout: {member.path.as_posix()}"
                    )
                governed_paths.add(member.path)
                continue
            contract = cls._gitmodule_contract(repository_root, member.path.as_posix())
            if contract.failure:
                return r[tuple[Path, ...]].fail(
                    contract.error or f"invalid governed member: {member.name}"
                )
            declared_url, declared_branch = contract.value
            if declared_url != member.url or not u.Infra.gitmodule_branch_is_governed(
                declared_branch, provider_branch=provider.branch
            ):
                return r[tuple[Path, ...]].fail(
                    f"governed workspace member contract differs: {member.name}"
                )
            governed_paths.add(member.path)
        observed_external = tuple(
            path for path in declared.value if path not in governed_paths
        )
        return r[tuple[Path, ...]].ok(observed_external)

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
        make_profile = workspace.repository.role
        # The provider default is the fallback, never the answer: this
        # repository's own published integration branch decides. Line 206 of
        # this same file already derives it that way for submodule discovery;
        # the conform target must not disagree with it.
        baseline_result = u.Infra.repository_baseline_branch(
            resolved_root,
            fallback=provider.branch,
            preference=(
                config.Infra.codegen.branch_policy.integration_branch_preference
            ),
        )
        if baseline_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                baseline_result.error
                or f"integration baseline resolution failed: {resolved_root}"
            )
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=workspace.repository,
                root=resolved_root,
                make_profile=make_profile,
                beads=workspace.beads,
                canonical_project_name=canonical_project_name,
                baseline_branch=baseline_result.value,
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
        if not cls._beads_path(repository_root.expanduser().resolve()).is_file():
            return r[tuple[Path, ...]].ok(())
        origin = cls._git_origin_url(repository_root)
        if origin.failure or cls._declared_provider_for_url(origin.value) is None:
            return r[tuple[Path, ...]].ok(())
        workspace = cls.load_workspace_spec(repository_root)
        if workspace.failure:
            return r[tuple[Path, ...]].fail(workspace.error)
        return r[tuple[Path, ...]].ok(
            cls.workspace_analysis_exclusion_paths(workspace.value)
        )

    def detect(self, project_root: Path) -> p.Result[c.Infra.MakeProfile]:
        """Classify from governed members, not mere vendored Git topology."""
        try:
            resolved_root = project_root.expanduser().resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.MakeProfile].fail_op("Workspace detection", exc)
        if not resolved_root.is_dir():
            return r[c.Infra.MakeProfile].fail(
                f"project root is not a directory: {resolved_root}"
            )
        workspace = self.load_workspace_spec(resolved_root)
        if workspace.failure:
            return r[c.Infra.MakeProfile].fail(workspace.error)
        return r[c.Infra.MakeProfile].ok(workspace.value.repository.role)

    @override
    def execute(self) -> p.Result[c.Infra.MakeProfile]:
        """Execute workspace detection for the configured root."""
        return self.detect(self.repository_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
