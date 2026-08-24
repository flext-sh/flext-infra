"""Single-rule Git workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, override
from urllib.parse import urlparse

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s
from flext_infra.workspace._governance import FlextInfraWorkspaceGovernanceMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceGovernanceMixin, s[c.Infra.WorkspaceMode]
):
    """Classify workspace roots and members from Git topology alone.

    SINGLE RULE: a repository declaring ``.gitmodules`` is a workspace;
    a repository without it is standalone. A submodule member is a
    ``WORKSPACE_MEMBER``; a member that itself declares ``.gitmodules``
    is a workspace root for its own subtree (recursion is implicit in
    the rule). No registry, no manifest file, no attachment markers.
    """

    @staticmethod
    def _strip_symbols(name: str) -> str:
        """Derive a Beads-safe namespace by stripping every non-alphanumeric."""
        return re.sub(r"[^a-zA-Z0-9]", "", name)

    @classmethod
    def _derive_ledger_identity(cls, canonical_project_name: str) -> tuple[str, str]:
        """Return ``(ledger_prefix, ledger_id)`` derived from the project name.

        Both strip ``-``, ``_`` and every other symbol (``ai-hub`` ->
        ``aihub``). Exceptions are declared per-project in ``pyproject.toml``
        at ``[tool.flext.project]`` (``ledger_prefix`` / ``ledger_id``).\
        """
        prefix_override, id_override = cls._ledger_overrides()
        derived = cls._strip_symbols(canonical_project_name)
        return (prefix_override or derived, id_override or derived)

    @staticmethod
    def _ledger_overrides() -> tuple[str | None, str | None]:
        """Read ``[tool.flext.project]`` ledger overrides from this checkout."""
        # Overrides travel with the repository itself; the detector never
        # consults any registry or manifest outside the checkout.
        from flext_infra.utilities import u as utilities

        payload = utilities.Cli.toml_read_json(Path.cwd() / c.Infra.PYPROJECT_FILENAME)
        if payload.failure or not isinstance(payload.value, dict):
            return None, None
        tool_val = payload.value.get("tool")
        if not isinstance(tool_val, dict):
            return None, None
        flext_val = tool_val.get("flext")
        if not isinstance(flext_val, dict):
            return None, None
        flext_project = flext_val.get("project")
        if not isinstance(flext_project, dict):
            return None, None
        prefix = flext_project.get("ledger_prefix")
        ledger = flext_project.get("ledger_id")
        return (
            prefix if isinstance(prefix, str) and prefix else None,
            ledger if isinstance(ledger, str) and ledger else None,
        )

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
        """Derive the workspace spec from live Git and project metadata.

        Topology comes from ``.gitmodules``; identity comes from
        ``pyproject.toml``; ledger identity is derived from the project
        name. The superseded ``config/workspace.yaml`` manifest is gone.
        """
        return cls._derive_workspace_spec(
            repository_root, project_metadata=project_metadata
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
        return r[tuple[m.Infra.RepositoryRef, ...]].ok((member,))

    @classmethod
    def _derive_workspace_spec(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Derive the spec from the repository itself, never from a registry.

        Operator law: flext-infra owns generic conform behaviour and must not
        carry a catalog of the projects it serves. Identity comes from the
        repository's ``pyproject.toml``; members from its live Git submodule
        contract; ledger identity is derived from the project name with
        per-project ``[tool.flext.project]`` overrides. Nothing is fabricated
        and nothing is looked up in flext-infra.
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
        members: list[m.Infra.RepositoryRef] = []
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
        ledger_prefix, ledger_id = cls._derive_ledger_identity(project_name)

        # Derive canonical ProjectSpec from PEP 621 metadata (SSOT)
        package_name = resolved_metadata.package_name or project_name.replace("-", "_")
        class_stem = resolved_metadata.class_stem or u.derive_class_stem(project_name)
        derived_ns = class_stem.removeprefix("Flext")
        project_namespace = derived_ns or class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        authors = tuple(resolved_metadata.project.authors)
        first_author = authors[0] if authors else None
        author_name = first_author.name if first_author else "FLEXT Team"
        author_email = first_author.email if first_author else "team@flext.dev"
        urls = resolved_metadata.project.urls
        homepage = (
            urls.homepage
            if urls and urls.homepage
            else origin.value.removesuffix(".git")
        )
        documentation = urls.documentation if urls and urls.documentation else homepage
        description = (
            resolved_metadata.project.description
            or f"{class_stem} — FLEXT typed integration package"
        )
        version = resolved_metadata.project.version or "0.12.0.dev0"

        # Determine upstream from dependencies
        upstream = "flext_core"
        for dep in resolved_metadata.project.dependencies:
            if dep.startswith(("flext-cli", "flext_cli")):
                upstream = "flext_cli"
                break

        project_spec = m.Infra.ProjectSpec(
            package_name=package_name,
            class_stem=class_stem,
            namespace=project_namespace,
            constant_name=project_name,
            namespace_attribute=alias,
            alias=alias,
            environment_prefix=f"{package_name.upper()}_",
            description=description,
            version=version,
            license="MIT",
            author_name=author_name,
            author_email=author_email,
            upstream=upstream,
            homepage=homepage
            or f"https://github.com/{provider.organization}/{project_name}",
            documentation=documentation
            or f"https://github.com/{provider.organization}/{project_name}",
            workspace_root_rel=".",
            year=2026,
        )

        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=project_name,
                ledger_id=ledger_id,
                ledger_prefix=ledger_prefix,
                repository=local_repository,
                project=project_spec,
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

    @staticmethod
    def resolve_topology_roots(
        repository_root: Path,
    ) -> p.Result[tuple[Path, Path, Path]]:
        """Resolve render, primary identity, and governing workspace roots."""
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
        superproject = u.Infra.git_superproject_working_tree(
            m.Infra.GitRepoRequest(repo_root=identity_root)
        )
        if superproject.failure:
            return r[tuple[Path, Path, Path]].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        governing_root = (
            Path(superproject.value.text).resolve()
            if superproject.value.text.strip()
            else identity_root
        )
        return r[tuple[Path, Path, Path]].ok((
            resolved_root,
            identity_root,
            governing_root,
        ))

    @classmethod
    def resolve_workspace_root(cls, repository_root: Path) -> p.Result[Path]:
        """Resolve the governing workspace root for a repository or member."""
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

        External dependency submodules are foreign trees and therefore never
        enter Ruff or type-checkers.
        """
        return tuple(workspace.external_dependency_paths)

    @classmethod
    def analysis_exclusion_paths(
        cls, repository_root: Path
    ) -> p.Result[tuple[Path, ...]]:
        """Derive workspace-scoped analysis exclusions from live Git.

        Projects whose origin resolves to no declared provider are unmanaged:
        they carry no workspace-scoped exclusions. This keeps Ruff/Pyright
        discovery usable for ad-hoc or third-party trees without weakening
        validation for governed FLEXT checkouts.
        """
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

    @classmethod
    def _unattached_mode(cls, repository_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a root with no Git superproject by the single rule."""
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        if declared.failure:
            return r[c.Infra.WorkspaceMode].fail(
                declared.error or "unable to read Git submodule topology"
            )
        return r[c.Infra.WorkspaceMode].ok(
            c.Infra.WorkspaceMode.WORKSPACE
            if declared.value
            else c.Infra.WorkspaceMode.STANDALONE
        )

    @classmethod
    def conform_target(
        cls, repository_root: Path, *, project_metadata: p.ProjectMetadata | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Derive the sole conformance target from live Git and typed identity."""
        topology_result = cls.resolve_topology_roots(repository_root)
        if topology_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                topology_result.error or "unable to resolve governing root"
            )
        resolved_root, identity_root, governing_root = topology_result.value
        workspace_result = cls.load_workspace_spec(governing_root)
        if workspace_result.failure:
            return r[m.Infra.RepositoryConformTarget].fail(
                workspace_result.error or "unable to load governing workspace"
            )
        resolved_workspace = workspace_result.value
        if identity_root == governing_root:
            repository = resolved_workspace.repository
        else:
            try:
                relative_path = identity_root.relative_to(governing_root)
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
        # Gate (PD): project name starting with 'flext-' must be a submodule of flext
        if (
            canonical_project_name.startswith("flext-")
            and identity_root != governing_root
            and resolved_workspace.name != "flext"
        ):
            return r[m.Infra.RepositoryConformTarget].fail(
                f"FLEXT project must be a submodule of flext: {canonical_project_name}"
            )
        # Gate (PC): flext-core dependency requires make gen conformance
        declared_deps = tuple(resolved_metadata.project.dependencies)
        has_flext_core = any(
            dep.startswith(("flext-core", "flext_core")) for dep in declared_deps
        )
        if has_flext_core and repository.codegen is c.Infra.CodegenKind.NONE:
            return r[m.Infra.RepositoryConformTarget].fail(
                "projects declaring flext-core must be generated by make gen: "
                f"{canonical_project_name}"
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
            c.Infra.WorkspaceMode.WORKSPACE: c.Infra.MakeProfile.WORKSPACE_ROOT,
            c.Infra.WorkspaceMode.WORKSPACE_MEMBER: (
                c.Infra.MakeProfile.WORKSPACE_MEMBER
            ),
            c.Infra.WorkspaceMode.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }[mode_result.value]
        # Ephemeral transaction worktrees share storage with the primary checkout.
        # Detect them from Git's canonical topology rather than from a test-only
        # environment flag, so the same code path works for real worktrees and for
        # unit fixtures that simulate CLI transaction scope.
        is_transaction_worktree = identity_root != resolved_root
        # Beads participation: the workspace root owns the tracker; an
        # independent standalone opts in through its overlay; ephemeral
        # transaction worktrees route to the principal ledger; members consume
        # the governing ledger without owning it.
        beads_enabled = make_profile is c.Infra.MakeProfile.WORKSPACE_ROOT or (
            make_profile is c.Infra.MakeProfile.STANDALONE
            and (is_transaction_worktree or overlay.beads_enabled)
        )
        routing_only = is_transaction_worktree and (
            make_profile is c.Infra.MakeProfile.STANDALONE
        )
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

    @classmethod
    def _detect_attached(
        cls, project_root: Path, superproject_root: Path
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a real Git submodule against its superproject topology."""
        member_root_result = u.Infra.git_show_toplevel(
            m.Infra.GitRepoRequest(repo_root=project_root)
        )
        if member_root_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                member_root_result.error or "unable to resolve Git repository root"
            )
        member_root = member_root_result.value.workspace_root.resolve()
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
        # The URL/branch contract of this member is validated fail-closed when
        # the parent workspace spec is derived (see _derive_governed_member);
        # membership itself is proven by Git's own declared topology here.
        return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.WORKSPACE_MEMBER)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode from live Git topology alone."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        if not resolved_project_root.is_dir():
            return r[c.Infra.WorkspaceMode].fail(
                f"project root is not a directory: {resolved_project_root}"
            )

        git_probe = u.Infra.git_is_inside_work_tree(
            m.Infra.GitRepoRequest(repo_root=resolved_project_root)
        )
        if git_probe.failure:
            return r[c.Infra.WorkspaceMode].fail(
                git_probe.error or "unable to execute Git workspace probe"
            )
        if not git_probe.value.value:
            if (resolved_project_root / c.Infra.GIT_DIR).exists():
                return r[c.Infra.WorkspaceMode].fail("invalid Git repository metadata")
            return self._unattached_mode(resolved_project_root)

        superproject_result = u.Infra.git_superproject_working_tree(
            m.Infra.GitRepoRequest(repo_root=resolved_project_root)
        )
        if superproject_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                superproject_result.error or "unable to resolve Git superproject"
            )
        if not superproject_result.value.text:
            return self._unattached_mode(resolved_project_root)
        return self._detect_attached(
            resolved_project_root, Path(superproject_result.value.text).resolve()
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
