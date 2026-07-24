"""Public behavior tests for autonomous FLEXT pyproject conformance."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, m, u


def _member_ref(distribution: str) -> m.Infra.RepositoryRef:
    """Build one flext-sh workspace member repository reference."""
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=f"https://github.com/flext-sh/{distribution}.git",
        branch="0.12.0-dev",
        path=Path(distribution),
        role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        provider="flext-sh",
        profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        checkout=c.Infra.CheckoutKind.SUBMODULE,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=True,
        read_only=False,
    )


def _cosmos_workspace() -> m.Infra.WorkspaceSpec:
    """Build a cosmos-main-like root whose members are not flext projects."""
    root = m.Infra.RepositoryRef(
        name="cosmos-main",
        distribution="cosmos-main",
        url="https://github.com/datacosmos-br/cosmos-main.git",
        branch="main",
        path=Path(),
        role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
        provider="datacosmos-br",
        profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        checkout=c.Infra.CheckoutKind.ROOT,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=False,
        editable=False,
        read_only=False,
    )
    charts = m.Infra.RepositoryRef(
        name="cosmos-charts",
        distribution="cosmos-charts",
        url="https://github.com/datacosmos-br/cosmos-charts.git",
        branch="main",
        path=Path("apps/cosmos-charts"),
        role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        provider="datacosmos-br",
        profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        checkout=c.Infra.CheckoutKind.SUBMODULE,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=True,
        read_only=False,
    )
    return m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="cosmos-main",
        repository=root,
        members=(charts,),
    )


def _toolchain() -> m.Infra.ToolchainSpec:
    """Build the canonical 0.12 toolchain specification."""
    return m.Infra.ToolchainSpec(
        python_version="3.13.11",
        uv_version="0.11.29",
        uv_link_mode="copy",
        kubectl_version="1.32.0",
        helm_version="3.19.4",
        kind_version="0.31.0",
    )


class TestsFlextInfraCodegenPyprojectConform:
    """Exercise only the public u.Infra conformance contract."""

    def test_root_workspace_and_autonomous_member_are_idempotent(self) -> None:
        """Keep the root local while rendering member dependencies from Git."""
        # NOTE (multi-agent, mro-wkii.17.9): one real public round-trip proves
        # migration and a byte-identical second render without mocks or writes.
        root = m.Infra.RepositoryRef(
            name="flext",
            distribution="flext",
            url="https://github.com/flext-sh/flext.git",
            branch="0.12.0-dev",
            path=Path(),
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            provider="flext-sh",
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
        )
        core = m.Infra.RepositoryRef(
            name="flext-core",
            distribution="flext-core",
            url="https://github.com/flext-sh/flext-core.git",
            branch="0.12.0-dev",
            path=Path("flext-core"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider="flext-sh",
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        infra = m.Infra.RepositoryRef(
            name="flext-infra",
            distribution="flext-infra",
            url="https://github.com/flext-sh/flext-infra.git",
            branch="0.12.0-dev",
            path=Path("flext-infra"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider="flext-sh",
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        tests = m.Infra.RepositoryRef(
            name="flext-tests",
            distribution="flext-tests",
            url="https://github.com/flext-sh/flext-tests.git",
            branch="0.12.0-dev",
            path=Path("flext-tests"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider="flext-sh",
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        web = m.Infra.RepositoryRef(
            name="flext-web",
            distribution="flext-web",
            url="https://github.com/flext-sh/flext-web.git",
            branch="0.12.0-dev",
            path=Path("flext-web"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            provider="flext-sh",
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="flext",
            repository=root,
            members=(core, infra, tests, web),
        )
        toolchain = m.Infra.ToolchainSpec(
            python_version="3.13.11",
            uv_version="0.11.28",
            uv_link_mode="copy",
            kubectl_version="1.32.0",
            helm_version="3.19.4",
            kind_version="0.31.0",
        )
        repositories = (core, infra, tests, web)
        root_source = """[project]
name = "flext"
dependencies = ["flext-core[async] @ file:///home/marlonsc/flext/flext-core", "requests>=2"]

[project.optional-dependencies]
dev = ["flext-tests @ ../flext-tests", "pytest>=8"]
docs = ["mkdocs>=1"]

[dependency-groups]
codegen = ["flext-infra"]
dev = ["ruff>=0.12"]
workspace = []

[tool.poetry]
name = "legacy"

[tool.uv]
required-version = ">=0.9"
override-dependencies = ["pathspec>=1.0.0"]

[tool.uv.workspace]
members = ["flext-core"]

[tool.uv.sources.flext-core]
path = "../flext-core"
editable = true
marker = "python_version >= '3.13'"

[tool.pyrefly]
search-path = [".", "src", "../flext-core/src"]

[tool.pyright]
extraPaths = [".", "src", "../flext-core/src"]
venvPath = "/home/marlonsc/flext"

[tool.mypy]
mypy_path = [".", "src", "../flext-core/src"]
"""

        root_first = u.Infra.pyproject_conform(
            root_source,
            repositories=repositories,
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
        tm.that(
            root_rendered,
            has='dependencies = [\n    "flext-core[async] @ git+https://github.com/flext-sh/flext-core.git@0.12.0-dev",',
        )
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
            "flext-core[async] @ git+https://github.com/flext-sh/flext-core.git@0.12.0-dev; python_version >= '3.13'",
            "flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev",
            "flext-tests @ git+https://github.com/flext-sh/flext-tests.git@0.12.0-dev",
            "flext-web @ git+https://github.com/flext-sh/flext-web.git@0.12.0-dev",
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

[tool.uv.sources.flext-core]
workspace = true
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

    def test_workspace_root_renders_inline_git_urls_for_flext_deps(self) -> None:
        """Root flext-* deps render inline PEP508 Git URLs, never plain names."""
        repositories = (
            _member_ref("flext-core"),
            _member_ref("flext-cli"),
            _member_ref("flext-tests"),
            _member_ref("flext-infra"),
        )
        workspace = _cosmos_workspace()
        toolchain = _toolchain()
        root_source = """[project]
name = "cosmos-main"
dependencies = ["flext-core", "flext-cli", "requests>=2"]

[dependency-groups]
dev = ["flext-tests", "pytest>=8"]
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
            "flext-core @ git+https://github.com/flext-sh/flext-core.git@0.12.0-dev",
            "flext-cli @ git+https://github.com/flext-sh/flext-cli.git@0.12.0-dev",
            "flext-tests @ git+https://github.com/flext-sh/flext-tests.git@0.12.0-dev",
        ):
            tm.that(rendered, has=expected)
        # NOTE: no bare plain flext-* requirement survives at the workspace root.
        for bare in ('"flext-core"', '"flext-cli"', '"flext-tests"', '"flext-infra"'):
            tm.that(bare not in rendered, eq=True, msg=bare)
        # NOTE: [tool.uv.sources] keeps only {workspace=true} members, no flext-*.
        tm.that("[tool.uv.sources.flext-" not in rendered, eq=True)
        tm.that(rendered, has="[tool.uv.sources.cosmos-charts]")
        tm.that(rendered, has="workspace = true")
        second = u.Infra.pyproject_conform(
            rendered,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=rendered)

    def test_relative_path_flext_deps_are_rewritten_to_inline_git_urls(self) -> None:
        """The no-relative-path law: file://, ../ and {path=} never survive."""
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
        for expected in (
            "flext-core @ git+https://github.com/flext-sh/flext-core.git@0.12.0-dev",
            "flext-cli @ git+https://github.com/flext-sh/flext-cli.git@0.12.0-dev",
            "flext-tests @ git+https://github.com/flext-sh/flext-tests.git@0.12.0-dev",
        ):
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
