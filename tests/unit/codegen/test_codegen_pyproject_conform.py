"""Public behavior tests for autonomous FLEXT pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import c, m, t, u


def _repository(
    distribution: str,
    *,
    url: str,
    branch: str,
    path: str,
    role: c.Infra.RepositoryRole = c.Infra.RepositoryRole.WORKSPACE_MEMBER,
    package: bool = True,
) -> m.Infra.RepositoryRef:
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=url,
        branch=branch,
        path=Path(path),
        role=role,
        provider="example",
        profile=(
            c.Infra.MakeProfile.WORKSPACE_ROOT
            if role == c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.MakeProfile.WORKSPACE_MEMBER
        ),
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role == c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=package,
        editable=role != c.Infra.RepositoryRole.WORKSPACE_ROOT,
        read_only=False,
    )


def _fixtures() -> tuple[
    m.Infra.WorkspaceSpec, tuple[m.Infra.RepositoryRef, ...], m.Infra.ToolchainSpec
]:
    root = _repository(
        "fleet-root",
        url="https://git.example/root/fleet-root.git",
        branch="root-line",
        path="",
        role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
        package=False,
    )
    member = _repository(
        "flext-member",
        url="https://git.example/work/flext-member.git",
        branch="member-line",
        path="packages/member",
    )
    external = _repository(
        "flext-external",
        url="ssh://git@git.example/deps/flext-external.git",
        branch="feature/arbitrary",
        path="vendor/external",
    )
    tests = _repository(
        "flext-tests",
        url="https://git.example/tools/flext-tests.git",
        branch="tests-line",
        path="tools/tests",
    )
    infra = _repository(
        "flext-infra",
        url="https://git.example/tools/flext-infra.git",
        branch="infra-line",
        path="tools/infra",
    )
    non_package = _repository(
        "flext-docs",
        url="https://git.example/deps/flext-docs.git",
        branch="docs-line",
        path="docs",
        package=False,
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="fleet-root",
        repository=root,
        members=(member,),
    )
    toolchain = m.Infra.ToolchainSpec(
        python_version="3.13.11",
        uv_version="0.11.29",
        uv_link_mode="copy",
        kubectl_version="1.32.0",
        helm_version="3.19.4",
        kind_version="0.31.0",
    )
    return workspace, (external, member, tests, infra, non_package), toolchain


def _payload(rendered: str) -> t.JsonDict:
    return dict(t.Cli.JSON_MAPPING_ADAPTER.validate_python(tomllib.loads(rendered)))


def _table(payload: t.JsonDict, key: str) -> t.JsonDict:
    return dict(t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload[key]))


class TestsFlextInfraCodegenPyprojectConform:
    """Exercise only the public u.Infra conformance contract."""

    def test_full_conform_uses_bare_metadata_and_exact_root_sources(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        source = """[project]
name = "fleet-root"
dependencies = [
    "flext-external[fast] @ https://old.example/archive.whl; python_version >= '3.12'",
    "flext-external[fast]>=9; python_version >= '3.12'",
    "flext-external[slow] @ ../external",
    "requests>=2",
]

[project.optional-dependencies]
docs = ["flext-external[docs] @ file:///tmp/external; sys_platform == 'linux'"]

[dependency-groups]
dev = ["flext-external[test]==1", "pytest>=8"]
codegen = ["flext-external[codegen] @ git+https://old.example/repo.git@old"]

[tool.uv]
override-dependencies = ["stale>=1"]

[tool.uv.workspace]
members = ["stale"]

[tool.uv.sources.stale]
path = "../stale"

[tool.uv.sources.fleet-root]
workspace = true

[tool.uv.sources.flext-member]
git = "https://wrong.example/member.git"
branch = "wrong"
"""
        first = u.Infra.pyproject_conform(
            source, repositories=repositories, workspace=workspace, toolchain=toolchain
        )
        tm.that(first.success, eq=True, msg=first.error)
        payload = _payload(first.value)
        project = _table(payload, "project")
        dependencies = project["dependencies"]
        tm.that(
            dependencies,
            eq=[
                "flext-external[fast]; python_version >= '3.12'",
                "flext-external[slow]",
                "requests>=2",
            ],
        )
        optional = _table(project, "optional-dependencies")
        tm.that(optional["docs"], eq=["flext-external[docs]; sys_platform == 'linux'"])
        groups = _table(payload, "dependency-groups")
        tm.that(groups["dev"], has="flext-external[test]")
        tm.that(groups["codegen"], has="flext-external[codegen]")
        uv = _table(_table(payload, "tool"), "uv")
        tm.that("override-dependencies" not in uv, eq=True)
        tm.that(uv["workspace"], eq={"members": ["packages/member"]})
        tm.that(
            _table(uv, "sources"),
            eq={
                "flext-member": {"workspace": True},
                "flext-external": {
                    "git": "ssh://git@git.example/deps/flext-external.git",
                    "branch": "feature/arbitrary",
                },
                "flext-tests": {
                    "git": "https://git.example/tools/flext-tests.git",
                    "branch": "tests-line",
                },
                "flext-infra": {
                    "git": "https://git.example/tools/flext-infra.git",
                    "branch": "infra-line",
                },
            },
        )
        tm.that(
            tuple(_table(uv, "sources")),
            eq=("flext-member", "flext-external", "flext-tests", "flext-infra"),
        )
        second = u.Infra.pyproject_conform(
            first.value,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=first.value)

    def test_full_conform_preserves_distinct_dev_dependency_variants(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        source = f'''[project]
name = "{workspace.name}"

[project.optional-dependencies]
dev = ["flext-external[docs]; python_version >= '3.13'"]

[dependency-groups]
dev = ["flext-external[test]; python_version < '3.13'"]
codegen = [
    "flext-infra[docs]; python_version >= '3.13'",
    "flext-infra[test]; python_version < '3.13'",
]
'''
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
        )
        tm.that(
            groups["codegen"],
            eq=[
                "flext-infra[docs]; python_version >= '3.13'",
                "flext-infra[test]; python_version < '3.13'",
                "flext-infra",
            ],
        )
        second = u.Infra.pyproject_conform(
            first.value,
            repositories=repositories,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True, msg=second.error)
        tm.that(second.value, eq=first.value)

    def test_dependency_only_root_validates_exact_typed_resolution(self) -> None:
        workspace, repositories, _ = _fixtures()
        source = """[project]
name = "fleet-root"
dependencies = ["flext-external[one] @ ../old", "flext-external[two]>=4"]

[tool.uv.workspace]
members = ["packages/member"]

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
"""
        first = u.Infra.pyproject_dependencies_conform(
            source, repositories=repositories, workspace=workspace
        )
        tm.that(first.success, eq=True, msg=first.error)
        tm.that(
            _table(_payload(first.value), "project")["dependencies"],
            eq=["flext-external[one]", "flext-external[two]"],
        )
        second = u.Infra.pyproject_dependencies_conform(
            first.value, repositories=repositories, workspace=workspace
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=first.value)

    def test_non_root_removes_workspace_and_sources(self) -> None:
        workspace, repositories, _ = _fixtures()
        source = """[project]
name = "flext-member"
dependencies = ["flext-external @ https://old.example/archive.whl"]

[tool.uv]
required-version = ">=0.9"

[tool.uv.workspace]
members = ["stale"]

[tool.uv.sources.flext-external]
git = "https://old.example/repo.git"
"""
        result = u.Infra.pyproject_dependencies_conform(
            source, repositories=repositories, workspace=workspace
        )
        tm.that(result.success, eq=True, msg=result.error)
        uv = _table(_table(_payload(result.value), "tool"), "uv")
        tm.that(uv, eq={"required-version": ">=0.9"})
        second = u.Infra.pyproject_dependencies_conform(
            result.value, repositories=repositories, workspace=workspace
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=result.value)

    def test_full_non_root_removes_empty_uv_and_is_idempotent(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        source = """[project]
name = "flext-member"
dependencies = ["flext-external[fast] @ ../external; python_version > '3.11'"]

[project.optional-dependencies]
docs = ["flext-external[docs]>=8"]

[dependency-groups]
dev = ["flext-external[test] @ file:///tmp/external"]

[tool.uv.workspace]
members = ["stale"]

[tool.uv.sources.flext-external]
path = "../external"
editable = true
"""
        first = u.Infra.pyproject_conform(
            source, repositories=repositories, workspace=workspace, toolchain=toolchain
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
            toolchain=toolchain,
        )
        tm.that(second.success, eq=True)
        tm.that(second.value, eq=first.value)

    def test_dependency_only_root_rejects_override_and_source_drift(self) -> None:
        workspace, repositories, _ = _fixtures()
        valid = """[project]
name = "fleet-root"

[tool.uv]
override-dependencies = ["stale"]

[tool.uv.workspace]
members = ["packages/member"]

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
        source = f'''[project]
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
'''
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
            first.value, repositories=repositories, workspace=workspace, toolchain=toolchain
        )
        tm.that(second.success, eq=True, msg=second.error)
        tm.that(second.value, eq=first.value)

    def test_unknown_and_conflicting_repository_resolution_fail_closed(self) -> None:
        workspace, repositories, toolchain = _fixtures()
        unknown = u.Infra.pyproject_conform(
            '[project]\nname = "fleet-root"\ndependencies = ["flext-unknown"]\n',
            repositories=repositories,
            workspace=workspace,
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
        conflict = u.Infra.pyproject_conform(
            '[project]\nname = "fleet-root"\ndependencies = ["flext-external"]\n',
            repositories=conflicting,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(conflict.failure, eq=True)
        tm.that(conflict.error or "", has="catalog conflicts")
        member_conflict = (
            *repositories,
            _repository(
                "flext-member",
                url="https://other.example/flext-member.git",
                branch="other",
                path="other-member",
            ),
        )
        member_result = u.Infra.pyproject_conform(
            '[project]\nname = "fleet-root"\ndependencies = []\n',
            repositories=member_conflict,
            workspace=workspace,
            toolchain=toolchain,
        )
        tm.that(member_result.failure, eq=True)
        tm.that(member_result.error or "", has="catalog conflicts")
