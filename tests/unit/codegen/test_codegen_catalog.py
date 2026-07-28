"""Typed repository-catalog consumer contract."""

from __future__ import annotations

import pytest
from packaging.requirements import Requirement

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


def test_toolchain_rejects_exact_patch_selectors() -> None:
    """Keep runtime selectors on compatible major.minor release lines."""
    payload = config.Infra.codegen.toolchain.model_dump()
    payload["python_version"] = "3.13.11"

    with pytest.raises(ValueError, match="python_version"):
        m.Infra.ToolchainSpec.model_validate(payload)


def test_scaffold_dependencies_delegate_upper_bounds_to_uv() -> None:
    """Keep library requirements floor-only and let uv own concrete resolution."""
    project = config.Infra.codegen.scaffold.project
    requirements = [
        *(
            requirement
            for profile in project.dependency_profiles
            for requirement in (*profile.runtime, *profile.codegen, *profile.dev)
        )
    ]
    forbidden = {"<", "<=", "==", "===", "~="}

    for raw_requirement in requirements:
        parsed = Requirement(raw_requirement)
        tm.that(
            forbidden.isdisjoint(specifier.operator for specifier in parsed.specifier),
            eq=True,
            msg=raw_requirement,
        )
