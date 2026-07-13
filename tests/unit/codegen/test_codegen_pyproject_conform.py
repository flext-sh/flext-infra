"""Public behavior tests for deterministic Git-first pyproject conformance."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, m, u


class TestsFlextInfraCodegenPyprojectConform:
    """Exercise only the public u.Infra conformance contract."""

    def test_git_first_render_is_complete_and_idempotent(self) -> None:
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
        )
        workspace = m.Infra.WorkspaceSpec(
            version=1,
            name="flext",
            repository=root,
            members=(core,),
        )
        toolchain = m.Infra.ToolchainSpec(
            python_version="3.13.11",
            python_minor_version="3.13",
            python_required_version=">=3.13.11,<3.14",
            uv_version="0.11.28",
            uv_required_version="==0.11.28",
        )
        source = """[project]
name = "flext"
dependencies = ["flext-core @ file:///home/marlonsc/flext/flext-core", "requests>=2"]

[project.optional-dependencies]
dev = ["flext-tests @ ../flext-tests", "pytest>=8"]
docs = ["mkdocs>=1"]

[dependency-groups]
dev = ["ruff>=0.12"]
workspace = ["stale-member"]

[tool.poetry]
name = "legacy"

[tool.uv]
required-version = ">=0.9"

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

        first = u.Infra.pyproject_conform(
            source,
            repositories=(core, infra, tests),
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(first.success, eq=True)
        rendered = first.value
        second = u.Infra.pyproject_conform(
            rendered,
            repositories=(core, infra, tests),
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=rendered)
        tm.that(rendered, has='required-version = "==0.11.28"')
        tm.that(rendered, has='git = "https://github.com/flext-sh/flext-core.git"')
        tm.that(rendered, has='branch = "0.12.0-dev"')
        tm.that(rendered, has='workspace = ["flext-core"]')
        for forbidden in (
            "[tool.poetry]",
            "[tool.uv.workspace]",
            "../flext",
            "/home/marlonsc",
            "editable = true",
            "marker =",
            "\npath =",
            "workspace = true",
        ):
            tm.that(forbidden not in rendered, eq=True, msg=forbidden)
