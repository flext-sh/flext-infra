"""Canonical repository-to-provider resolution utilities."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraUtilitiesRepository:
    """Resolve provider-owned policy for one governed repository."""

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
    def repository_baseline_branch(
        cls,
        repository: p.Infra.RepositoryRef,
        providers: t.SequenceOf[m.Infra.ProviderSpec],
    ) -> p.Result[str]:
        """Return the provider-owned integration baseline for ``repository``."""
        provider = cls.repository_provider(repository, providers)
        if provider.failure:
            return r[str].fail(
                provider.error or "repository provider resolution failed"
            )
        return r[str].ok(provider.value.branch)

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
                return r[m.Infra.RepositoryConformTarget].fail(
                    loaded.error or "workspace manifest load failed"
                )
            resolved_workspace = loaded.value
        return FlextInfraWorkspaceDetector.conform_target(
            repository_root, resolved_workspace
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesRepository",)
