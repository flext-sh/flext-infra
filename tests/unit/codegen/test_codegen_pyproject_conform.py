"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u


def _repository(
    distribution: str,
    *,
    role: c.Infra.RepositoryRole,
    path: str,
) -> m.Infra.RepositoryRef:
    """Build one catalog repository reference."""
    provider = config.Infra.codegen.providers[0]
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=f"{provider.base_url}/{distribution}.git",
        branch=provider.branch,
        path=Path(path),
        role=role,
        provider=provider.name,
        profile=(
            c.Infra.MakeProfile.WORKSPACE_ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.MakeProfile.WORKSPACE_MEMBER
        ),
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=role is not c.Infra.RepositoryRole.WORKSPACE_ROOT,
        editable=role is not c.Infra.RepositoryRole.WORKSPACE_ROOT,
        read_only=False,
    )


def _workspace() -> m.Infra.WorkspaceSpec:
    """Build a typed workspace with one attached package member."""
    return m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="workspace-root",
        repository=_repository(
            "workspace-root",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            path=".",
        ),
        members=(
            _repository(
                "flext-core",
                role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                path="flext-core",
            ),
        ),
    )


class TestsFlextInfraCodegenPyprojectConform:
    """Exercise the public topology-aware conformance facade."""

    def test_workspace_root_uses_only_workspace_provenance(self) -> None:
        """Attached members remain bare requirements backed by uv workspace sources."""
        workspace = _workspace()
        source = """[project]
name = "workspace-root"
dependencies = ["flext-core"]

[tool.uv.workspace]
members = ["flext-core"]

[tool.uv.sources.flext-core]
workspace = true
"""

        result = u.Infra.pyproject_dependencies_conform(
            source,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=["flext-core"])
        tm.that(document["dependency-groups"]["workspace"], eq=["flext-core"])
        tm.that(document["tool"]["uv"]["sources"], eq={"flext-core": {"workspace": True}})

    def test_standalone_uses_catalog_git_provenance(self) -> None:
        """Detached consumers resolve FLEXT dependencies from their declared branch."""
        workspace = _workspace()
        member = workspace.members[0]
        source = """[project]
name = "external-consumer"
dependencies = ["flext-core"]
"""

        result = u.Infra.pyproject_dependencies_conform(
            source,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{member.branch}"],
        )
        tm.that("tool" not in document or "uv" not in document["tool"], eq=True)

    def test_attached_member_rejects_direct_git_or_path_sources(self) -> None:
        """A workspace member cannot carry a second direct dependency source."""
        workspace = _workspace()
        member = workspace.members[0]
        source = (
            '[project]\nname = "attached-consumer"\n'
            f'dependencies = ["{member.distribution} @ git+{member.url}@{member.branch}"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            source,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="attached workspace dependency declares Git source")
