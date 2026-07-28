"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm


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

    def test_full_conform_preserves_distinct_dev_dependency_variants(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        source = f"""[project]
name = "{workspace.name}"

[project.optional-dependencies]
dev = ["flext-external[docs]; python_version >= '3.13'"]

[dependency-groups]
dev = ["flext-external[test]; python_version < '3.13'"]
codegen = [
    "flext-infra[docs]; python_version >= '3.13'",
    "flext-infra[test]; python_version < '3.13'",
]
"""
        first = u.Infra.pyproject_conform(
            source, repositories=repositories, workspace=workspace, toolchain=toolchain
        )
        tm.that(first.success, eq=True, msg=first.error)
        groups = _table(_payload(first.value), "dependency-groups")
        tm.that(
            groups["dev"],
            eq=[
                "flext-external[docs]; python_version >= '3.13'",
                "flext-external[test]; python_version < '3.13'",
                "flext-tests",
            ],
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

    def test_dependency_only_root_validates_exact_typed_resolution(self) -> None:
        workspace, repositories, _ = _fixtures()
        root_overlay_source = """[project]
name = "fleet-root"
dependencies = ["flext-external[one] @ ../old", "flext-external[two]>=4"]

[tool.uv.sources.flext-member]
workspace = true

[tool.uv.sources.flext-external]
git = "ssh://git@git.example/deps/flext-external.git"
branch = "feature/arbitrary"

[tool.uv.sources.flext-tests]
git = "https://git.example/tools/flext-tests.git"
branch = "tests-line"

[tool.uv.sources.flext-infra]
git = "https://git.example/tools/flext-infra.git"
branch = "infra-line"

[tool.uv.workspace]
members = ["packages/member"]
"""
        root_overlay = u.Infra.pyproject_dependencies_conform(
            root_overlay_source,
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        tm.that(root_overlay.success, eq=True, msg=root_overlay.error)
        tm.that(
            _table(_payload(root_overlay.value), "project")["dependencies"],
            eq=["flext-external[one]", "flext-external[two]"],
        )
        root_overlay_second = u.Infra.pyproject_dependencies_conform(
            root_overlay.value,
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        tm.that(root_overlay_second.success, eq=True)
        tm.that(root_overlay_second.value, eq=root_overlay.value)

        invalid_root_overlay_source = root_overlay_source.replace(
            "[tool.uv.sources.flext-core]\nworkspace = true",
            '[tool.uv.sources.flext-core]\nworkspace = true\ngit = "https://github.com/flext-sh/flext-core.git"',
        )
        invalid_root_overlay = u.Infra.pyproject_dependencies_conform(
            invalid_root_overlay_source,
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
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
link-mode = "copy"
constraint-dependencies = ["uv>=0"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                source,
                repositories=(workspace.repository, *workspace.members),
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
                f'dependencies = ["{member.distribution} @ git+{member.url}@{member.branch}"]\n'
                "\n[tool.uv.workspace]\n"
                'members = ["flext-core"]\n'
                "\n[tool.uv.sources.flext-core]\n"
                "workspace = true\n"
            ),
            repositories=(workspace.repository, *workspace.members),
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
        tm.that(empty_uv_second.success, eq=True)
        tm.that(empty_uv_second.value, eq=empty_uv_rendered)
        tm.that("[tool.uv]" not in empty_uv_rendered, eq=True)

    def test_full_non_root_removes_empty_uv_and_is_idempotent(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        required_dev = config.Infra.codegen.scaffold.project.dev
        source = """[project]
name = "external-consumer"
dependencies = ["flext-core @ ../flext-core", "requests>=2"]

[dependency-groups]
dev = ["flext-external[test] @ file:///tmp/external"]

[tool.uv.workspace]
members = ["stale"]

[tool.uv.sources.flext-external]
path = "../external"
editable = true
"""
        first = u.Infra.pyproject_conform(
            source,
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            toolchain=toolchain,
        )
        tm.that(first.success, eq=True, msg=first.error)
        payload = _payload(first.value)
        tm.that(
            _table(payload, "project")["dependencies"],
            eq=["flext-external[fast]; python_version > '3.11'"],
        )
        tm.that(
            _table(_table(payload, "project"), "optional-dependencies")["docs"],
            eq=["flext-external[docs]"],
        )
        tm.that(_table(payload, "dependency-groups")["dev"], has="flext-external[test]")
        tm.that(
            _table(_table(payload, "tool"), "uv"),
            eq={"required-version": "==0.11.29", "link-mode": "copy"},
        )
        second = u.Infra.pyproject_conform(
            first.value,
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=first.value)

    def test_dependency_only_root_rejects_override_and_source_drift(self) -> None:
        workspace, repositories, _ = _fixtures()
        valid = """[project]
name = "fleet-root"

[tool.uv]
required-version = ">=0"

[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        override = u.Infra.pyproject_dependencies_conform(
            valid, repositories=repositories, workspace=workspace
        )
        tm.that(override.failure, eq=True)
        tm.that(override.error or "", has="override-dependencies")
        drift = valid.replace('override-dependencies = ["stale"]\n\n', "").replace(
            'branch = "feature/arbitrary"', 'branch = "wrong"'
        )
        drift_result = u.Infra.pyproject_dependencies_conform(
            drift, repositories=repositories, workspace=workspace
        )
        tm.that(drift_result.failure, eq=True)
        tm.that(drift_result.error or "", has="sources differ")
        exact = valid.replace('override-dependencies = ["stale"]\n\n', "")
        wrong_order = exact.replace(
            "[tool.uv.sources.flext-member]\nworkspace = true\n\n"
            "[tool.uv.sources.flext-external]\n"
            'git = "ssh://git@git.example/deps/flext-external.git"\n'
            'branch = "feature/arbitrary"',
            "[tool.uv.sources.flext-external]\n"
            'git = "ssh://git@git.example/deps/flext-external.git"\n'
            'branch = "feature/arbitrary"\n\n'
            "[tool.uv.sources.flext-member]\nworkspace = true",
        )
        order_result = u.Infra.pyproject_dependencies_conform(
            wrong_order, repositories=repositories, workspace=workspace
        )
        tm.that(order_result.failure, eq=True)
        tm.that(order_result.error or "", has="sources differ")
        extra_key = wrong_order.replace(
            'branch = "feature/arbitrary"',
            'branch = "feature/arbitrary"\ntag = "forbidden"',
        )
        extra_result = u.Infra.pyproject_dependencies_conform(
            extra_key, repositories=repositories, workspace=workspace
        )
        tm.that(extra_result.failure, eq=True)
        tm.that(extra_result.error or "", has="sources differ")

    def test_full_conform_rewrites_wrong_source_order_and_is_idempotent(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        repository_by_name = {
            repository.distribution: repository for repository in repositories
        }
        external = repository_by_name["flext-external"]
        tests = repository_by_name["flext-tests"]
        infra = repository_by_name["flext-infra"]
        member = workspace.members[0]
        source = f"""[project]
name = "{workspace.name}"

[tool.uv.workspace]
members = ["{member.path.as_posix()}"]

[tool.uv.sources.flext-external]
git = "{external.url}"
branch = "{external.branch}"

[tool.uv.sources.{member.distribution}]
workspace = true

[tool.uv.sources.flext-tests]
git = "{tests.url}"
branch = "{tests.branch}"

[tool.uv.sources.flext-infra]
git = "{infra.url}"
branch = "{infra.branch}"
"""
        first = u.Infra.pyproject_conform(
            source, repositories=repositories, workspace=workspace, toolchain=toolchain
        )
        tm.that(first.success, eq=True, msg=first.error)
        sources = _table(_table(_table(_payload(first.value), "tool"), "uv"), "sources")
        tm.that(
            tuple(sources),
            eq=(member.distribution, "flext-external", "flext-tests", "flext-infra"),
        )
        second = u.Infra.pyproject_conform(
            first.value,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True, msg=second.error)
        tm.that(second.value, eq=first.value)

    def test_unknown_and_conflicting_repository_resolution_fail_closed(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        unknown = u.Infra.pyproject_conform(
            '[project]\nname = "fleet-root"\ndependencies = ["flext-unknown"]\n',
            repositories=repositories,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            toolchain=toolchain,
        )
        tm.that(unknown.failure, eq=True)
        tm.that(unknown.error or "", has="lacks required distribution")
        conflicting = (
            *repositories,
            _repository(
                "flext-external",
                url="https://other.example/flext-external.git",
                branch="other",
                path="other",
            ),
        )
