"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u


def _repository(
    distribution: str, *, role: c.Infra.RepositoryRole, path: str
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
            toolchain=toolchain,
        )
        tm.that(root_first.success, eq=True)
        root_rendered = root_first.value
        root_second = u.Infra.pyproject_conform(
            root_rendered,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(root_second.success, eq=True)
        tm.that(root_rendered, eq=root_second.value)
        tm.that(root_rendered, has='required-version = "==0.11.28"')
        tm.that(root_rendered, has='link-mode = "copy"')
        tm.that(root_rendered, has='constraint-dependencies = [\n    "uv==0.11.28",')
        tm.that(root_rendered, has='override-dependencies = ["pathspec>=1.0.0"]')
        tm.that(root_rendered, has='dependencies = [\n    "flext-core[async]",')
        tm.that(root_rendered, has="[tool.uv.workspace]")
        tm.that(root_rendered, has='members = [\n    "flext-core",')
        tm.that(root_rendered, has="[tool.uv.sources.flext-core]")
        tm.that(root_rendered, has="workspace = true")
        tm.that(root_rendered, has='search-path = [\n    ".",\n    "src",\n]')
        tm.that(root_rendered, has='extraPaths = [\n    ".",\n    "src",\n]')
        tm.that(root_rendered, has='mypy_path = [\n    ".",\n    "src",\n]')
        for forbidden in (
            "[tool.poetry]",
            "../flext",
            "/home/marlonsc",
            "editable = true",
            "marker =",
            "\npath =",
            "venvPath",
        ):
            tm.that(forbidden not in root_rendered, eq=True, msg=forbidden)

        root_overlay_source = """[project]
name = "flext"

[tool.uv.sources.flext-core]
workspace = true

[tool.uv.sources.flext-infra]
workspace = true

[tool.uv.sources.flext-tests]
workspace = true

[tool.uv.sources.flext-web]
workspace = true

[tool.uv]
override-dependencies = ["pathspec>=1.0.0"]

[tool.uv.workspace]
members = ["flext-core", "flext-infra", "flext-tests", "flext-web"]
"""
        root_overlay = u.Infra.pyproject_dependencies_conform(
            root_overlay_source, repositories=repositories, workspace=workspace
        )
        tm.that(root_overlay.success, eq=True)
        tm.that(root_overlay.value, has='override-dependencies = ["pathspec>=1.0.0"]')
        tm.that(
            root_overlay.value,
            has='[dependency-groups]\nworkspace = [\n    "flext-core",',
        )
        root_overlay_second = u.Infra.pyproject_dependencies_conform(
            root_overlay.value, repositories=repositories, workspace=workspace
        )
        tm.that(root_overlay_second.success, eq=True)
        tm.that(root_overlay_second.value, eq=root_overlay.value)

        invalid_root_overlay_source = root_overlay_source.replace(
            "[tool.uv.sources.flext-core]\nworkspace = true",
            '[tool.uv.sources.flext-core]\nworkspace = true\ngit = "https://github.com/flext-sh/flext-core.git"',
        )
        invalid_root_overlay = u.Infra.pyproject_dependencies_conform(
            invalid_root_overlay_source, repositories=repositories, workspace=workspace
        )
        tm.that(invalid_root_overlay.failure, eq=True)
        tm.that(
            invalid_root_overlay.error or "",
            has="root uv source is not exclusively workspace-backed: flext-core",
        )

        member_source = """[project]
name = "flext-api"
dependencies = [
    "flext-core[async]>=0.12; python_version >= '3.13'",
    "flext-web @ ../flext-web",
    "zeta>=1",
    "alpha>=1",
    "requests>=2",
]

[project.optional-dependencies]
dev = ["flext-tests", "pytest>=8"]
docs = ["mkdocs>=1"]

[dependency-groups]
codegen = ["flext-infra"]
dev = ["ruff>=0.12"]
workspace = ["stale-member"]

[tool.uv]
required-version = ">=0.9"

[tool.uv.workspace]
members = ["../flext-core"]

[tool.uv.sources.flext-core]
workspace = true

[tool.uv.sources.beartype]
git = "https://github.com/beartype/beartype.git"
tag = "v0.22.9"
"""
        member_first = u.Infra.pyproject_dependencies_conform(
            member_source, repositories=repositories, workspace=workspace
        )
        tm.that(member_first.success, eq=True)
        member_rendered = member_first.value
        member_second = u.Infra.pyproject_dependencies_conform(
            member_rendered, repositories=repositories, workspace=workspace
        )
        tm.that(member_second.success, eq=True)
        tm.that(member_second.value, eq=member_rendered)
        for expected in (
            "flext-core[async]; python_version >= '3.13'",
            '"flext-infra"',
            '"flext-tests"',
            '"flext-web"',
            "[tool.uv.sources.beartype]",
            'tag = "v0.22.9"',
        ):
            tm.that(member_rendered, has=expected)
        for forbidden in (
            "[tool.uv.workspace]",
            "[tool.uv.sources.flext-core]",
            "workspace = true",
            "../flext",
            "stale-member",
            "constraint-dependencies",
        ):
            tm.that(forbidden not in member_rendered, eq=True, msg=forbidden)

        empty_uv_source = """[project]
name = "flext-api"
dependencies = ["flext-core"]
"""
        empty_uv_first = u.Infra.pyproject_dependencies_conform(
            empty_uv_source, repositories=repositories, workspace=workspace
        )
        tm.that(empty_uv_first.success, eq=True)
        empty_uv_rendered = empty_uv_first.value
        empty_uv_second = u.Infra.pyproject_dependencies_conform(
            empty_uv_rendered, repositories=repositories, workspace=workspace
        )
        tm.that(empty_uv_second.success, eq=True)
        tm.that(empty_uv_second.value, eq=empty_uv_rendered)
        tm.that("[tool.uv]" not in empty_uv_rendered, eq=True)

    def test_workspace_root_owns_internal_dependency_sources(self) -> None:
        """Keep published metadata bare and source resolution exclusively at root."""
        member = _member_ref("flext-member-alpha")
        external = _member_ref("flext-external-beta").model_copy(
            update={
                "url": "https://example.invalid/org/flext-external-beta.git",
                "branch": "fixture-branch",
                "path": Path("elsewhere/flext-external-beta"),
            }
        )
        repositories = (member, external)
        workspace = _cosmos_workspace()
        workspace = workspace.model_copy(update={"members": (member,)})
        toolchain = _toolchain()
        root_name = workspace.repository.distribution
        root_source = f"""[project]
name = "{root_name}"
dependencies = [
    "flext-member-alpha[feature] @ file:///tmp/flext-member-alpha; python_version >= '3.13'",
    "flext-external-beta>=9.9",
    "requests>=2",
]

[dependency-groups]
dev = ["flext-external-beta @ ../flext-external-beta", "pytest>=8"]
"""
        first = u.Infra.pyproject_conform(
            root_source,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(first.success, eq=True)
        rendered = first.value
        for expected in (
            "flext-member-alpha[feature]; python_version >= '3.13'",
            '"flext-external-beta"',
            "[tool.uv.sources.flext-member-alpha]",
            "workspace = true",
            "[tool.uv.sources.flext-external-beta]",
            f'git = "{external.url}"',
            f'branch = "{external.branch}"',
        ):
            tm.that(rendered, has=expected)
        for forbidden in ("file://", "../flext-external-beta", ">=9.9"):
            tm.that(forbidden not in rendered, eq=True, msg=forbidden)
        tm.that(f"[tool.uv.sources.{root_name}]" not in rendered, eq=True)
        second = u.Infra.pyproject_conform(
            rendered,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=rendered)

    def test_member_internal_deps_are_bare_without_duplicate_sources(self) -> None:
        """Members publish bare requirements and carry no internal source mapping."""
        repositories = (
            _member_ref("flext-core"),
            _member_ref("flext-cli"),
            _member_ref("flext-tests"),
            _member_ref("flext-infra"),
        )
        workspace = _cosmos_workspace()
        toolchain = _toolchain()
        relative_source = """[project]
name = "cosmos-main"
dependencies = ["flext-core @ file://../flext-core", "flext-cli @ ../flext-cli"]

[dependency-groups]
dev = ["flext-tests @ file:///home/marlonsc/flext/flext-tests"]

[tool.uv.sources.flext-core]
path = "../flext-core"
editable = true

[tool.uv.sources.flext-cli]
workspace = false
path = "../flext-cli"
"""
        first = u.Infra.pyproject_conform(
            relative_source,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(first.success, eq=True)
        rendered = first.value
        for expected in ('"flext-core"', '"flext-cli"', '"flext-tests"'):
            tm.that(rendered, has=expected)
        for forbidden in ("../", "file://", "editable = true", "workspace = false"):
            tm.that(forbidden not in rendered, eq=True, msg=forbidden)
        tm.that("[tool.uv.sources.flext-" not in rendered, eq=True)
        second = u.Infra.pyproject_conform(
            rendered,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=rendered)
