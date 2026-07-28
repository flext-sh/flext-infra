"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u


def _repository(
    distribution: str, *, role: c.Infra.RepositoryRole, path: str
) -> m.Infra.RepositoryRef:
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
    return m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="workspace-root",
        repository=_repository(
            "workspace-root", role=c.Infra.RepositoryRole.WORKSPACE_ROOT, path="."
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
    def test_workspace_root_uses_workspace_provenance(self) -> None:
        workspace = _workspace()
        result = u.Infra.pyproject_dependencies_conform(
            """[project]
name = "workspace-root"
dependencies = ["flext-core"]

[tool.uv.workspace]
members = ["flext-core"]

[tool.uv.sources.flext-core]
workspace = true
""",
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=["flext-core"])
        tm.that(document["dependency-groups"]["workspace"], eq=["flext-core"])

    def test_standalone_uses_catalog_git_provenance(self) -> None:
        workspace = _workspace()
        member = workspace.members[0]
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{member.branch}"],
        )

    def test_attached_member_removes_direct_source(self) -> None:
        workspace = _workspace()
        member = workspace.members[0]
        result = u.Infra.pyproject_dependencies_conform(
            (
                '[project]\nname = "attached-consumer"\n'
                f'dependencies = ["{member.distribution} @ git+{member.url}@{member.branch}"]\n'
            ),
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=[member.distribution])

    def test_full_conformance_is_idempotent_without_uv_version_pin(self) -> None:
        workspace = _workspace()
        repositories = (
            workspace.repository,
            *workspace.members,
            *config.Infra.codegen.repositories,
        )
        toolchain = m.Infra.ToolchainSpec(
            python_version="3.13",
            uv_link_mode="copy",
            kubectl_version="1.32.0",
            helm_version="3.19.4",
            kind_version="0.31.0",
            taplo_version="0.10.0",
        )
        source = """[project]
name = "external-consumer"
dependencies = ["flext-core @ ../flext-core", "requests>=2"]

[tool.uv]
required-version = "==0.11.28"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                repositories=repositories,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                repositories=repositories,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
            )
        )
        document = tomllib.loads(first)
        tm.that(second, eq=first)
        tm.that(document["tool"]["uv"]["link-mode"], eq=toolchain.uv_link_mode)
        tm.that("required-version" not in document["tool"]["uv"], eq=True)
        tm.that(
            document["project"]["dependencies"][0],
            eq=(
                f"{workspace.members[0].distribution} @ "
                f"git+{workspace.members[0].url}@{workspace.members[0].branch}"
            ),
        )
