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
from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceGovernanceMixin, s[c.Infra.WorkspaceMode]
):
    """Classify only declared roots and real, declared Git submodules."""

    # A repository classifies itself only: its own .gitmodules means workspace;
    # otherwise it is standalone. Parent and sibling topology is never consulted.

    @staticmethod
    def repository_is_governed(
        repository: m.Infra.RepositoryRef, provider: m.Infra.ProviderSpec
    ) -> bool:
        """Require provider key, host, and organization to agree exactly."""
        if repository.provider != provider.name:
            return False
        provider_url = urlparse(provider.base_url)
        repository_url = urlparse(repository.url)
        provider_path = provider_url.path.strip("/")
        repository_path = repository_url.path.strip("/")
        # CI remotes often omit the ``.git`` suffix; compare on a canonical form.
        repository_name = repository_path.removeprefix(
            f"{provider.organization}/"
        ).removesuffix(".git")
        canonical_path = f"{provider.organization}/{repository_name}.git"
        actual_path = (
            repository_path
            if repository_path.endswith(".git")
            else f"{repository_path}.git"
        )
        return (
            provider_url.scheme == repository_url.scheme
            and provider_url.netloc == repository_url.netloc
            and provider_path == provider.organization
            and bool(repository_name)
            and actual_path == canonical_path
        )

    @classmethod
    def load_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive repository identity and subprojects from live project files."""
        return cls._derive_workspace_spec(
            repository_root, project_metadata=project_metadata
        )

    @classmethod
    def _load_beads_override(
        cls, repository_root: Path
    ) -> p.Result[m.Infra.BeadsOverrideSpec]:
        """Load the repository-local override without parent inference."""
        resolved_root = repository_root.resolve()
        override_path = resolved_root / c.Infra.BEADS_OVERRIDE_RELPATH
        if not override_path.is_file():
            return r[m.Infra.BeadsOverrideSpec].fail(
                f"missing required repository-local Beads override: {override_path}"
            )
        loaded = u.Cli.config_load(override_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.BeadsOverrideSpec].fail(
                loaded.error or f"invalid Beads override: {override_path}"
            )
        try:
            override = m.Infra.BeadsOverrideSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.BeadsOverrideSpec].fail_op(
                f"Beads override validation ({override_path})", exc
            )
        return r[m.Infra.BeadsOverrideSpec].ok(override)

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
            role=c.Infra.RepositoryRole.STANDALONE,
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
        beads_override = cls._load_beads_override(repository_root)
        if beads_override.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                beads_override.error or "unable to resolve Beads override"
            )
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
        mode = (
            c.Infra.WorkspaceMode.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.WorkspaceMode.STANDALONE
        )
        local_repository = m.Infra.RepositoryRef(
            name=project_name,
            distribution=project_name,
            url=repository_url,
            path=Path(),
            role=(
                c.Infra.RepositoryRole.WORKSPACE
                if mode is c.Infra.WorkspaceMode.WORKSPACE
                else c.Infra.RepositoryRole.STANDALONE
            ),
            provider=provider.name,
            checkout=(
                c.Infra.CheckoutKind.ROOT
                if mode is c.Infra.WorkspaceMode.WORKSPACE
                else c.Infra.CheckoutKind.INDEPENDENT
            ),
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
        subprojects: t.MutableSequenceOf[m.Infra.RepositoryRef] = []
        governed_paths: set[Path] = set()
        for path in declared_paths.value:
            derived = cls._derive_governed_member(repository_root, path)
            if derived.failure:
                return r[m.Infra.WorkspaceSpec].fail(
                    derived.error or f"invalid Git submodule: {path.as_posix()}"
                )
            if derived.value:
                project_override = cls._load_beads_override(repository_root / path)
                if project_override.failure:
                    return r[m.Infra.WorkspaceSpec].fail(
                        "workspace project must materialize its local config override: "
                        f"{path.as_posix()}: {project_override.error}"
                    )
                if project_override.value != beads_override.value:
                    return r[m.Infra.WorkspaceSpec].fail(
                        "workspace project Beads override differs from workspace SSOT: "
                        f"{path.as_posix()}/{c.Infra.BEADS_OVERRIDE_RELPATH}"
                    )
            subprojects.extend(derived.value)
            governed_paths.update(subproject.path for subproject in derived.value)
        external_dependency_paths = tuple(
            path for path in declared_paths.value if path not in governed_paths
        )
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=project_name,
                beads=beads_override.value,
                repository=local_repository,
                subprojects=tuple(subprojects),
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
        for member in workspace.subprojects:
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

    @staticmethod
    def resolve_topology_roots(
        repository_root: Path,
    ) -> p.Result[tuple[Path, Path, Path]]:
        """Resolve render and repository identity roots without parent inference."""
        resolved_root = repository_root.expanduser().resolve()
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved_root))
        if identity.failure:
            inside = u.Infra.git_is_inside_work_tree(
                m.Infra.GitRepoRequest(repo_root=resolved_root)
            )
            if inside.failure:
                return r[tuple[Path, Path, Path]].fail(
                    inside.error or "unable to probe Git workspace topology"
                )
            if not inside.value.value:
                return r[tuple[Path, Path, Path]].ok((
                    resolved_root,
                    resolved_root,
                    resolved_root,
                ))
            return r[tuple[Path, Path, Path]].fail(
                identity.error or "unable to resolve Git repository identity"
            )
        primary = u.Infra.git_primary_worktree_root(
            m.Infra.GitRepoRequest(repo_root=identity.value.repo_root)
        )
        if primary.failure:
            return r[tuple[Path, Path, Path]].fail(
                primary.error or "unable to resolve primary worktree"
            )
        identity_root = primary.value.primary_root
        return r[tuple[Path, Path, Path]].ok((
            resolved_root,
            identity_root,
            identity_root,
        ))

    @classmethod
    def resolve_workspace_root(cls, repository_root: Path) -> p.Result[Path]:
        """Resolve the repository's own identity root."""
        topology = cls.resolve_topology_roots(repository_root)
        if topology.failure:
            return r[Path].fail(
                topology.error or "unable to resolve workspace topology"
            )
        return r[Path].ok(topology.value[2])

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
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            return r[tuple[Path, ...]].ok(())
        origin = cls._git_origin_url(repository_root)
        if origin.failure or not origin.value:
            return r[tuple[Path, ...]].ok(())
        if cls._declared_provider_for_url(origin.value) is None:
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
            c.Infra.RepositoryRole.WORKSPACE,
            c.Infra.RepositoryRole.STANDALONE,
        }:
            return r[bool].fail(
                f"unsupported local repository role: {repository.role.value}"
            )
        expected_checkout = {
            c.Infra.RepositoryRole.WORKSPACE: c.Infra.CheckoutKind.ROOT,
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
        attached_marker = cls._declares_attached_standalone(repository_root)
        if attached_marker.failure:
            return r[c.Infra.WorkspaceMode].fail(
                attached_marker.error or "unable to read workspace attachment marker"
            )
        if attached_marker.value:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        if declared.failure:
            return r[c.Infra.WorkspaceMode].fail(
                declared.error or "unable to read Git submodule topology"
            )
        if not declared.value:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        resolved_workspace = workspace_spec
        if resolved_workspace is None:
            # mro-5qfa: an aggregator declares submodules without owning the FLEXT
            # toolchain; .gitmodules alone never promotes it to a workspace root.
            if not cls._declares_workspace_toolchain(repository_root):
                return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
            workspace_result = cls.load_workspace_spec(repository_root)
            if workspace_result.failure:
                return r[c.Infra.WorkspaceMode].fail(
                    workspace_result.error or "unable to derive governed topology"
                )
            resolved_workspace = workspace_result.value
        providers = {item.name: item for item in config.Infra.codegen.providers}
        governed: t.MutableSequenceOf[Path] = []
        declared_set = frozenset(declared.value)
        for member in resolved_workspace.subprojects:
            if member.read_only:
                continue
            provider = providers.get(member.provider)
            if provider is None or not cls.repository_is_governed(member, provider):
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
            declared_url, declared_branch = contract.value
            if declared_url != member.url or not u.Infra.gitmodule_branch_is_governed(
                declared_branch, provider_branch=provider.branch
            ):
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
        cls,
        repository_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None = None,
        *,
        project_metadata: p.ProjectMetadata | None = None,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive the sole conformance target from live Git and typed identity."""
        topology_result = cls.resolve_topology_roots(repository_root)
        if topology_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                topology_result.error or "unable to resolve governing root"
            )
        resolved_root, identity_root, _repository_root = topology_result.value
        resolved_workspace = workspace_spec
        if resolved_workspace is None:
            workspace_result = cls.load_workspace_spec(identity_root)
            if workspace_result.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    workspace_result.error or "unable to derive repository topology"
                )
            resolved_workspace = workspace_result.value
        repository = resolved_workspace.repository
        if repository.read_only:
            return r[m.Infra.RepositoryConformTarget].fail(
                f"repository is an external read-only dependency: {repository.name}"
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
        baseline_branch_result = u.Infra.repository_baseline_branch(
            resolved_root, fallback=provider.branch
        )
        if baseline_branch_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                baseline_branch_result.error
                or f"integration baseline resolution failed: {resolved_root}"
            )
        if not cls.repository_is_governed(repository, provider):
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
        mode_result = cls().detect(identity_root)
        if mode_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                mode_result.error or "unable to infer repository topology"
            )
        make_profile = {
            c.Infra.WorkspaceMode.WORKSPACE: c.Infra.MakeProfile.WORKSPACE,
            c.Infra.WorkspaceMode.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }[mode_result.value]
        # Ephemeral transaction worktrees share storage with the primary checkout.
        # Detect them from Git's canonical topology rather than from a test-only
        # environment flag, so the same code path works for real worktrees and for
        # unit fixtures that simulate CLI transaction scope.
        is_transaction_worktree = identity_root != resolved_root
        # Projection selection: workspace roots always receive the two .beads
        # config files; independent standalones opt in through their repository
        # overlay. Transaction worktrees reuse the governing manifest values.
        beads_enabled = make_profile is c.Infra.MakeProfile.WORKSPACE or (
            make_profile is c.Infra.MakeProfile.STANDALONE
            and (is_transaction_worktree or overlay.beads_enabled)
        )
        routing_only = is_transaction_worktree
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=repository,
                root=resolved_root,
                make_profile=make_profile,
                beads_enabled=beads_enabled,
                routing_only=routing_only,
                canonical_project_name=canonical_project_name,
                baseline_branch=baseline_branch_result.value,
                ci_enabled=overlay.ci_enabled,
                ci_matrix_auto_run=overlay.ci_matrix_auto_run,
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
        contract = u.Infra.gitmodule_contract(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=superproject_root, member_path=member_path
            )
        )
        if contract.failure:
            return r[tuple[str, str]].fail(contract.error)
        return r[tuple[str, str]].ok((contract.value.url, contract.value.branch))

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a repository solely by its own ``.gitmodules`` surface."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        if not resolved_project_root.is_dir():
            return r[c.Infra.WorkspaceMode].fail(
                f"project root is not a directory: {resolved_project_root}"
            )
        return r[c.Infra.WorkspaceMode].ok(
            c.Infra.WorkspaceMode.WORKSPACE
            if (resolved_project_root / c.Infra.GITMODULES).is_file()
            else c.Infra.WorkspaceMode.STANDALONE
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
