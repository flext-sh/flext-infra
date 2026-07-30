"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm

_PROVIDER_SPEC = config.Infra.codegen.providers[0]


def _repository(
    distribution: str, *, role: c.Infra.RepositoryRole, path: str
) -> m.Infra.RepositoryRef:
    provider = config.Infra.codegen.providers[0]
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=f"{provider.base_url}/{distribution}.git",
        path=Path(path),
        role=role,
        provider=provider.name,
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
            providers=config.Infra.codegen.providers,
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
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{_PROVIDER_SPEC.branch}"],
        )

    def test_dependency_conformance_removes_only_legacy_uv_constraint(self) -> None:
        workspace = _workspace()
        source = """[project]
name = "external-consumer"
dependencies = ["requests>=2"]

[tool.uv]
constraint-dependencies = ["uv>=0", "requests<3"]
"""
        first = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                source,
                repositories=(workspace.repository, *workspace.members),
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                first,
                repositories=(workspace.repository, *workspace.members),
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )

        document = tomllib.loads(first)
        tm.that(second, eq=first)
        tm.that(document["tool"]["uv"]["constraint-dependencies"], eq=["requests<3"])

    def test_dependency_conformance_deletes_empty_uv_constraint_key(self) -> None:
        workspace = _workspace()
        source = """[project]
name = "external-consumer"
dependencies = ["requests>=2"]

[tool.uv]
link-mode = "copy"
constraint-dependencies = ["uv>=0"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                source,
                repositories=(workspace.repository, *workspace.members),
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )

        uv_config = tomllib.loads(conformed)["tool"]["uv"]
        tm.that(uv_config["link-mode"], eq="copy")
        tm.that("constraint-dependencies" not in uv_config, eq=True)

    def test_standalone_rejects_non_https_catalog_provenance(self) -> None:
        workspace = _workspace()
        member = workspace.members[0].model_copy(
            update={"url": "git@github.com:flext-sh/flext-core.git"}
        )
        invalid_workspace = workspace.model_copy(update={"members": (member,)})
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            repositories=(invalid_workspace.repository, member),
            providers=config.Infra.codegen.providers,
            workspace=invalid_workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )
        tm.that(result.failure, eq=True)

    def test_attached_root_rejects_direct_source(self) -> None:
        workspace = _workspace()
        member = workspace.members[0]
        result = u.Infra.pyproject_dependencies_conform(
            (
                '[project]\nname = "workspace-root"\n'
                f'dependencies = ["{member.distribution} @ git+{member.url}@{_PROVIDER_SPEC.branch}"]\n'
                "\n[tool.uv.workspace]\n"
                'members = ["flext-core"]\n'
                "\n[tool.uv.sources.flext-core]\n"
                "workspace = true\n"
            ),
            repositories=(workspace.repository, *workspace.members),
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        tm.fail(result, has="attached workspace dependency declares direct source")

    def test_full_conformance_is_idempotent_without_uv_version_pin(self) -> None:
        workspace = _workspace()
        repositories = (
            workspace.repository,
            *workspace.members,
            *config.Infra.codegen.repositories,
        )
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"uv_link_mode": "copy"}
        )
        required_dev = config.Infra.codegen.scaffold.project.dev
        source = """[project]
name = "external-consumer"
dependencies = ["flext-core @ ../flext-core", "requests>=2"]

[dependency-groups]
dev = ["custom-tool>=1"]

[tool.uv]
required-version = ">=0"

[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                repositories=repositories,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=required_dev,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                repositories=repositories,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=required_dev,
            )
        )
        document = tomllib.loads(first)
        tm.that(second, eq=first)
        tm.that(document["tool"]["uv"]["link-mode"], eq=toolchain.uv_link_mode)
        tm.that("required-version" not in document["tool"]["uv"], eq=True)
        tm.that("python-interpreter-path" not in document["tool"]["pyrefly"], eq=True)
        tm.that("custom-tool>=1" in document["dependency-groups"]["dev"], eq=True)
        tm.that(
            document["project"]["dependencies"][0],
            eq=(
                f"{workspace.members[0].distribution} @ "
                f"git+{workspace.members[0].url}@{_PROVIDER_SPEC.branch}"
            ),
        )
