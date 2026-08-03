"""Workspace integration overlay adjusts flext-infra provider defaults."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, u
from flext_tests import tm


def _provider(*, name: str = "flext-sh", branch: str = "0.12.0-dev") -> m.Infra.ProviderSpec:
    return m.Infra.ProviderSpec(
        name=name,
        organization=name,
        base_url=f"https://github.com/{name}",
        branch=branch,
    )


def _workspace(
    *, integration: m.Infra.WorkspaceIntegrationSpec | None
) -> m.Infra.WorkspaceSpec:
    return m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="flext",
        repository=m.Infra.RepositoryRef(
            name="flext",
            distribution="flext",
            provider="flext-sh",
            url="https://github.com/flext-sh/flext.git",
            path=Path(),
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            state=c.Infra.RepositoryState.ACTIVE,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
        ),
        members=(
            m.Infra.RepositoryRef(
                name="flext-core",
                distribution="flext-core",
                provider="flext-sh",
                url="https://github.com/flext-sh/flext-core.git",
                path=Path("flext-core"),
                role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                state=c.Infra.RepositoryState.ACTIVE,
                checkout=c.Infra.CheckoutKind.SUBMODULE,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=True,
                editable=True,
                read_only=False,
            ),
        ),
        integration=integration,
    )


def test_resolve_integration_branch_falls_back_to_provider() -> None:
    provider = _provider(branch="0.12.0-dev")
    workspace = _workspace(integration=None)

    tm.that(u.Infra.resolve_integration_branch(workspace, provider), eq="0.12.0-dev")


def test_resolve_integration_branch_uses_workspace_overlay() -> None:
    provider = _provider(branch="0.12.0-dev")
    workspace = _workspace(
        integration=m.Infra.WorkspaceIntegrationSpec(
            provider="flext-sh", branch="hotfix/lane"
        )
    )

    tm.that(u.Infra.resolve_integration_branch(workspace, provider), eq="hotfix/lane")


def test_gitmodule_branch_dot_is_governed() -> None:
    tm.that(
        u.Infra.gitmodule_branch_is_governed(
            c.Infra.FOLLOW_SUPERPROJECT_BRANCH, provider_branch="0.12.0-dev"
        ),
        eq=True,
    )


def test_managed_gitlinks_follow_superproject_branch() -> None:
    """Managed gitlinks always follow the superproject named branch."""
    tm.that(c.Infra.FOLLOW_SUPERPROJECT_BRANCH, eq=".")
    tm.that(
        u.Infra.gitmodule_branch_is_governed(
            ".", provider_branch="0.12.0-dev", integration_branch="0.12.0-dev"
        ),
        eq=True,
    )


__all__: tuple[str, ...] = ()
