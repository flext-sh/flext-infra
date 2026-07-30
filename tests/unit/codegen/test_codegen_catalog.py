"""Typed repository-catalog consumer contract."""

from __future__ import annotations

from flext_infra import c, config, m
from flext_tests import tm


def test_codegen_catalog_builds_every_declared_workspace_from_typed_ssot() -> None:
    """Round-trip workspace groups without freezing current catalog values."""
    repositories = config.Infra.codegen.repositories
    names = tuple(repository.name for repository in repositories)
    tm.that(len(names), eq=len(set(names)))

    roots = tuple(
        repository
        for repository in repositories
        if repository.role is c.Infra.RepositoryRole.WORKSPACE_ROOT
    )
    tm.that(bool(roots), eq=True)
    for root in roots:
        members = tuple(
            repository
            for repository in repositories
            if repository.provider == root.provider
            and repository.role is c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        content_only = tuple(
            repository
            for repository in repositories
            if repository.provider == root.provider
            and repository.role is c.Infra.RepositoryRole.CONTENT_ONLY
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root.name,
            repository=root,
            members=members,
            content_only=content_only,
        )
        consumed = (workspace.repository, *workspace.members, *workspace.content_only)
        tm.that(consumed, eq=(root, *members, *content_only))
