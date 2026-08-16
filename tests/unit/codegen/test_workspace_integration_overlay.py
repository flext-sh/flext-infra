"""Workspace integration overlay adjusts flext-infra provider defaults."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm


def _provider(
    *, name: str = "flext-sh", branch: str = "0.12.0-dev"
) -> m.Infra.ProviderSpec:
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


def test_resolve_integration_branch_ignores_other_provider_overlay() -> None:
    provider = _provider(branch="0.12.0-dev")
    workspace = _workspace(
        integration=m.Infra.WorkspaceIntegrationSpec(
            provider="datacosmos-br", branch="feature/other"
        )
    )

    tm.that(u.Infra.resolve_integration_branch(workspace, provider), eq=provider.branch)


def test_repository_artifact_authority_uses_repository_url() -> None:
    provider = _provider(branch="0.12.0-dev")
    workspace = _workspace(integration=None)
    repository = workspace.members[0].model_copy(update={"name": "catalog-alias"})

    authority = u.Infra.repository_artifact_authority(repository, provider, workspace)

    tm.that(authority.repository, eq="flext-core")
    tm.that(authority.organization, eq=provider.organization)


def test_gitmodule_branch_dot_is_governed() -> None:
    tm.that(
        u.Infra.gitmodule_branch_is_governed(
            c.Infra.FOLLOW_SUPERPROJECT_BRANCH, provider_branch="0.12.0-dev"
        ),
        eq=True,
    )


def test_managed_gitlinks_pin_resolved_integration_branch() -> None:
    """Managed gitlinks always pin the resolved integration/provider branch."""
    provider = _provider(branch="0.12.0-dev")
    overlaid = _workspace(
        integration=m.Infra.WorkspaceIntegrationSpec(
            provider="flext-sh", branch="hotfix/lane"
        )
    )
    absent = _workspace(integration=None)

    tm.that(u.Infra.resolve_integration_branch(overlaid, provider), eq="hotfix/lane")
    tm.that(u.Infra.resolve_integration_branch(absent, provider), eq="0.12.0-dev")


def test_pre_commit_template_excludes_workspace_member_profile() -> None:
    entry = next(
        item
        for item in config.Infra.codegen.templates.entries
        if item.destination == c.Infra.PRE_COMMIT_CONFIG_FILENAME
    )

    tm.that(c.Infra.MakeProfile.WORKSPACE_MEMBER in entry.profiles, eq=False)


__all__: tuple[str, ...] = ()
