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
        distribution: str, *, provider: m.Infra.ProviderSpec
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
            provider=provider.name,
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

    @staticmethod
    def workspace_spec_load(repository_root: Path) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load governed topology and derive observed external Git dependencies."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)

    @staticmethod
    def repository_conform_target(
        repository_root: Path,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Return typed effective policy inferred from live repository topology."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return FlextInfraWorkspaceDetector.conform_target(repository_root)


__all__: tuple[str, ...] = ("FlextInfraUtilitiesRepository",)
