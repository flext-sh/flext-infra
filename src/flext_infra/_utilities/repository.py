"""Canonical repository-to-provider resolution utilities."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraUtilitiesRepository:
    """Resolve provider-owned policy for one governed repository."""

    @staticmethod
    def derived_repository_ref(
        distribution: str,
        *,
        provider: m.Infra.ProviderSpec,
        role: c.Infra.MakeProfile = c.Infra.MakeProfile.STANDALONE,
        kind: c.Infra.ProjectKind = c.Infra.ProjectKind.INTERNAL_FLEXT,
    ) -> m.Infra.RepositoryRef:
        """Derive one repository reference from generic provider policy.

        flext-infra owns no catalog of the projects it serves, so a governed
        distribution that the live workspace does not declare is still
        resolvable: its canonical source is the provider contract plus its own
        distribution name. Nothing here is looked up; everything is derived.
        """
        return m.Infra.RepositoryRef(
            name=distribution,
            distribution=distribution,
            url=f"{provider.base_url.rstrip('/')}/{distribution}.git",
            path=Path(distribution),
            role=role,
            provider=provider.name,
            kind=kind,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )

    @classmethod
    def configured_repository_ref(
        cls, *, codegen: m.Infra.CodegenConfigSpec
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Derive one repository from the unique provider selected by config."""
        source = codegen.infra_repository
        matches = tuple(
            provider
            for provider in codegen.providers
            if provider.name == source.provider
        )
        if len(matches) != 1:
            return r[m.Infra.RepositoryRef].fail(
                "configured repository provider must resolve exactly once: "
                f"{source.provider}"
            )
        (provider,) = matches
        return r[m.Infra.RepositoryRef].ok(
            cls.derived_repository_ref(source.distribution, provider=provider)
        )

    @staticmethod
    def repository_provider(
        repository: p.Infra.RepositoryRef, providers: t.SequenceOf[m.Infra.ProviderSpec]
    ) -> p.Result[m.Infra.ProviderSpec]:
        """Return the unique typed provider declared by ``repository.provider``."""
        matches = tuple(
            provider for provider in providers if provider.name == repository.provider
        )
        if len(matches) != 1:
            return r[m.Infra.ProviderSpec].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        return r[m.Infra.ProviderSpec].ok(matches[0])

    @classmethod
    def repository_page_url(
        cls,
        repository: p.Infra.RepositoryRef,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[str]:
        """Return the provider HTTPS page of one repository, whatever its transport.

        CI rewrites member origins to SSH deploy-key URLs, so the clone URL is
        never a page URL: the page is the declared provider base URL plus the
        repository segment of the transport-stable ``owner/repository`` identity.
        """
        provider = cls.repository_provider(repository, providers)
        if provider.failure:
            return r[str].from_failure(provider)
        owner, separator, name = (
            FlextInfraUtilitiesGitWorktreeDiscoveryMixin.git_remote_identity(
                repository.url
            ).partition("/")
        )
        if (
            not separator
            or not name
            or owner != provider.value.organization.casefold()
        ):
            return r[str].fail(
                "repository URL does not identify a repository of provider "
                f"{provider.value.name}: {repository.name}"
            )
        return r[str].ok(f"{provider.value.base_url.rstrip('/')}/{name}")

    @classmethod
    def project_urls(
        cls,
        repository: p.Infra.RepositoryRef,
        project: m.Infra.ProjectSpec | None,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[m.Infra.ProjectUrls]:
        """Resolve ``[project.urls]`` from the manifest, never from a live pyproject.

        A declared ``project`` owns homepage and documentation; a repository
        without one publishes its provider page for both. The repository URL is
        always the provider page of the declared repository.
        """
        page = cls.repository_page_url(repository, providers)
        if page.failure:
            return r[m.Infra.ProjectUrls].from_failure(page)
        return r[m.Infra.ProjectUrls].ok(
            m.Infra.ProjectUrls(
                homepage=page.value if project is None else project.homepage,
                documentation=(
                    page.value if project is None else project.documentation
                ),
                repository=page.value,
            )
        )

    @staticmethod
    def resolve_integration_branch(
        workspace: m.Infra.WorkspaceSpec, provider: m.Infra.ProviderSpec
    ) -> str:
        """Return the provider-owned integration branch."""
        del workspace
        provider_branch: str = provider.branch
        return provider_branch

    @staticmethod
    def gitmodule_branch_is_governed(
        declared_branch: str,
        *,
        provider_branch: str,
        integration_branch: str | None = None,
    ) -> bool:
        """Accept follow-superproject (``.``) or the resolved integration line."""
        if declared_branch == c.Infra.FOLLOW_SUPERPROJECT_BRANCH:
            return True
        if declared_branch == provider_branch:
            return True
        return integration_branch is not None and declared_branch == integration_branch

    @classmethod
    def repository_baseline_branch(
        cls,
        repository_root: Path,
        fallback: str | None = None,
        preference: t.VariadicTuple[str] | None = None,
    ) -> p.Result[str]:
        """Return the integration baseline the repository actually publishes.

        A provider declares one default branch, but managed repositories under
        the same provider legitimately integrate on different branches. The
        baseline is therefore derived from live Git: the published
        remote-tracking integration branch wins.

        ``preference`` is the ordered set of names to try, owned by
        ``codegen.branch_policy.integration_branch_preference`` so a workspace
        declares its own release line instead of asking for a constant in this
        package. Omitting it uses the built-in conventional ordering.

        ``fallback`` carries the provider default for a repository that cannot
        have published anything yet (project creation). Without it, a checkout
        with no integration branch fails closed instead of guessing.
        """
        from flext_infra import u

        candidates = preference or c.Infra.INTEGRATION_BRANCH_PREFERENCE
        for candidate in candidates:
            reference = f"refs/remotes/origin/{candidate}"
            resolved = u.Infra.git_ref_exists(
                m.Infra.GitRefRequest(repo_root=repository_root, reference=reference)
            )
            if resolved.success and resolved.value.value:
                return r[str].ok(candidate)
        if fallback:
            return r[str].ok(fallback)
        return r[str].fail(
            "repository publishes no integration branch "
            f"({', '.join(candidates)}): {repository_root}"
        )

    @staticmethod
    def workspace_spec_load(repository_root: Path) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load governed topology and derive observed external Git dependencies."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)

    @staticmethod
    def repository_conform_target(
        repository_root: Path, workspace: m.Infra.WorkspaceSpec | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Return typed effective policy inferred from live repository topology."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        resolved_workspace = workspace
        if resolved_workspace is None:
            loaded = FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)
            if loaded.failure:
                return r[m.Infra.RepositoryConformTarget].from_failure(loaded)
            resolved_workspace = loaded.value
        return FlextInfraWorkspaceDetector.conform_target(
            repository_root, resolved_workspace
        )


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesRepository",)
