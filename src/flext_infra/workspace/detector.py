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
        workspace_root: Path,
        workspace_beads: m.Infra.BeadsProjectSpec,
    ) -> str | None:
        member_beads = subproject_root / c.Infra.BEADS_DIRNAME
        member_identity = (
            subproject_root
            / c.CONFIG_DIR_NAME
            / c.Infra.BEADS_CONFIG_FILENAME
        )
        workspace_route = workspace_root / c.Infra.BEADS_DIRNAME
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
        """Resolve one configured provider, failing closed without leaking the URL.

        Every configured provider is hosted on the same forge, so the host alone
        does not identify one: matching on it returned whichever provider came
        first in the list, and `repository_is_governed` then rejected the
        repository for belonging to a different organization than the one just
        chosen for it. The organization is the discriminator, and
        `_declared_provider_for_url` already applies it.
        """
        provider = cls._declared_provider_for_url(url)
        if provider is None:
            return r[m.Infra.ProviderSpec].fail(
                "repository owner must resolve exactly once"
            )
        return r[m.Infra.ProviderSpec].ok(provider)

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
        allowed_checkout_kinds = (
            {c.Infra.CheckoutKind.SUBMODULE}
            if observed.checkout is c.Infra.CheckoutKind.SUBMODULE
            else {c.Infra.CheckoutKind.ROOT, c.Infra.CheckoutKind.INDEPENDENT}
        )
        if declared.checkout not in allowed_checkout_kinds:
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
        if (
            manifest.ledger_id is not None
            and manifest.ledger_id != beads.database
        ):
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
        return r[m.Infra.RepositoryRef].ok(declared)

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
    def _load_subprojects(
        cls, repository_root: Path, *, workspace_beads: m.Infra.BeadsProjectSpec
    ) -> p.Result[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]:
        """Validate every direct governed .gitmodules entry before planning writes."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        result_type = r[tuple[tuple[m.Infra.RepositoryRef, ...], tuple[Path, ...]]]
        if declared.failure:
            return result_type.fail(
                declared.error or "unable to read local .gitmodules"
            )
        subprojects: list[m.Infra.RepositoryRef] = []
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
            loaded = cls._load_subproject(
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
            subprojects.append(loaded.value)
        return result_type.ok((tuple(subprojects), tuple(external)))

    @classmethod
    def _load_subproject(
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
        subprojects must resolve to a declared provider and integrate on the
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
        if not (subproject_root / c.Infra.PYPROJECT_FILENAME).is_file():
            return result_type.ok(path)
        route_error = cls._submodule_beads_route_error(
            subproject_root, repository_root, workspace_beads
        )
        if route_error is not None:
            return result_type.fail(
                "workspace member must inherit the workspace Beads ledger: "
                f"{route_error}"
            )
        repository = cls._local_repository_ref(
            subproject_root,
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
        """Load local identity and validate local, read-only Git topology."""
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        if not resolved_root.is_dir():
            return r[m.Infra.WorkspaceSpec].fail(
                f"repository root is not a directory: {resolved_root}"
            )
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved_root))
        if identity.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                identity.error or "failed to resolve local Git identity"
            )
        if identity.value.is_submodule:
            residue = cls._submodule_beads_residue(resolved_root)
            if residue is not None:
                return r[m.Infra.WorkspaceSpec].fail(
                    "workspace member must inherit the workspace Beads ledger; "
                    f"forbidden member state exists: {residue}"
                )
        beads_result = cls.load_beads_spec(resolved_root)
        if beads_result.failure and identity.value.is_submodule:
            superproject_root = identity.value.superproject_root
            if superproject_root is None:
                return r[m.Infra.WorkspaceSpec].fail(beads_result.error)
            inherited = cls.load_workspace_spec(superproject_root)
            if inherited.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    inherited.error or "workspace member ledger inheritance failed"
                )
            member = next(
                (
                    item
                    for item in inherited.value.subprojects
                    if item.path is not None
                    and (superproject_root / item.path).resolve() == resolved_root
                ),
                None,
            )
            if member is None:
                return r[m.Infra.WorkspaceSpec].fail(
                    "Git submodule is not declared as a governed workspace member: "
                    f"{resolved_root}"
                )
            beads_result = r[m.Infra.BeadsProjectSpec].ok(inherited.value.beads)
        if beads_result.failure:
            return r[m.Infra.WorkspaceSpec].fail(beads_result.error)
        beads = beads_result
        repository = cls._local_repository_ref(
            resolved_root,
            checkout=(
                c.Infra.CheckoutKind.SUBMODULE
                if identity.value.is_submodule
                else c.Infra.CheckoutKind.ROOT
            ),
        )
        if repository.failure:
            return r[m.Infra.WorkspaceSpec].fail(repository.error)
        topology = cls._load_subprojects(
            resolved_root, workspace_beads=beads.value
        )
        if topology.failure:
            return r[m.Infra.WorkspaceSpec].fail(topology.error)
        subprojects, external = topology.value
        observed_repository = repository.value.model_copy(
            update={
                "role": (
                    c.Infra.MakeProfile.WORKSPACE
                    if subprojects
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
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
