"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u

_PROVIDER_SPEC = config.Infra.codegen.providers[0]


def _repository(
    distribution: str, *, role: c.Infra.MakeProfile, path: str
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
            if role is c.Infra.MakeProfile.WORKSPACE
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=role is not c.Infra.MakeProfile.WORKSPACE,
        editable=role is not c.Infra.MakeProfile.WORKSPACE,
        read_only=False,
    )


def _workspace() -> m.Infra.WorkspaceSpec:
    return m.Infra.WorkspaceSpec(
        beads=m.Infra.BeadsProjectSpec(
            version=c.Infra.BEADS_CONFIG_VERSION,
            workspace="flext",
            database="flext",
            issue_prefix="flext",
        ),
        name="workspace",
        repository=_repository(
            "workspace", role=c.Infra.MakeProfile.WORKSPACE, path="."
        ),
        subprojects=(
            _repository(
                "flext-core", role=c.Infra.MakeProfile.STANDALONE, path="flext-core"
            ),
        ),
    )


class TestsFlextInfraCodegenPyprojectConform:
    def test_workspace_root_uses_workspace_provenance(self) -> None:
        workspace = _workspace()
        result = u.Infra.pyproject_dependencies_conform(
            """[project]
name = "workspace"
dependencies = ["flext-core"]

[tool.uv.workspace]
members = ["flext-core"]

[tool.uv.sources.flext-core]
workspace = true
""",
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.MakeProfile.WORKSPACE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=["flext-core"])
        tm.that(document["dependency-groups"]["workspace"], eq=["flext-core"])

    def test_standalone_uses_catalog_git_provenance(self) -> None:
        workspace = _workspace()
        member = workspace.subprojects[0]
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.MakeProfile.STANDALONE,
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
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                first,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
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
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
            )
        )

        uv_config = tomllib.loads(conformed)["tool"]["uv"]
        tm.that(uv_config["link-mode"], eq="copy")
        tm.that("constraint-dependencies" not in uv_config, eq=True)

    def test_standalone_rejects_non_https_catalog_provenance(self) -> None:
        workspace = _workspace()
        member = workspace.subprojects[0].model_copy(
            update={"url": "git@github.com:flext-sh/flext-core.git"}
        )
        invalid_workspace = workspace.model_copy(update={"subprojects": (member,)})
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            providers=config.Infra.codegen.providers,
            workspace=invalid_workspace,
            workspace_mode=c.Infra.MakeProfile.STANDALONE,
        )
        tm.that(result.failure, eq=True)

    def test_workspace_rejects_conflicting_direct_source(self) -> None:
        workspace = _workspace()
        member = workspace.subprojects[0]
        result = u.Infra.pyproject_dependencies_conform(
            (
                '[project]\nname = "workspace"\n'
                f'dependencies = ["{member.distribution} @ git+{member.url}@{_PROVIDER_SPEC.branch}"]\n'
                "\n[tool.uv.workspace]\n"
                'members = ["flext-core"]\n'
                "\n[tool.uv.sources.flext-core]\n"
                "workspace = true\n"
            ),
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.MakeProfile.WORKSPACE,
        )
        tm.fail(result, has="workspace dependency declares a conflicting direct source")

    def test_full_conformance_is_idempotent_without_uv_version_pin(self) -> None:
        workspace = _workspace()
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
exclude-newer = "7 days"
exclude-newer-package = { cryptography = false }

[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=required_dev,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=required_dev,
            )
        )
        document = tomllib.loads(first)
        tm.that(second, eq=first)
        tm.that(document["tool"]["uv"]["link-mode"], eq=toolchain.uv_link_mode)
        tm.that(document["tool"]["uv"], lacks="exclude-newer")
        tm.that(document["tool"]["uv"], lacks="exclude-newer-package")
        tm.that("required-version" not in document["tool"]["uv"], eq=True)
        tm.that("python-interpreter-path" not in document["tool"]["pyrefly"], eq=True)
        tm.that("custom-tool>=1" in document["dependency-groups"]["dev"], eq=True)
        # Why (CodeRabbit 3742335224): assert the exact requirement the typed
        # SSOT declares, not merely the package name. A name-only assertion
        # stays green even if the generated floor drifts away from the owner.
        # Why (hq-36xk): the requirement was selected by hardcoding the
        # "pre-commit" package name, which 30b4a37f5 removed from the SSOT when
        # it retired the legacy work lifecycle. `next()` then raised
        # StopIteration and the test failed for a reason unrelated to what it
        # measures. The expectation now derives from the same SSOT sequence
        # production reads, so it survives any legitimate change to that set.
        # A declared floor reaches the rendered group verbatim UNLESS it names a
        # workspace project, which dependency provenance rewrites to its tracked
        # integration-branch source. Asserting by package name keeps both shapes
        # in scope without re-encoding either.
        rendered_names = {
            u.Infra.dep_name(requirement)
            for requirement in document["dependency-groups"]["dev"]
        }
        for requirement in required_dev:
            tm.that(u.Infra.dep_name(requirement) in rendered_names, eq=True)
        tm.that(
            document["project"]["dependencies"][0],
            eq=(
                f"{workspace.subprojects[0].distribution} @ "
                f"git+{workspace.subprojects[0].url}@{_PROVIDER_SPEC.branch}"
            ),
        )

    def test_conformance_never_writes_the_project_version(self) -> None:
        """The release protocol is the only version writer; conform reads only."""
        workspace = _workspace().model_copy(
            update={"project": test_u.Tests.project_spec("external-consumer")}
        )
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "external-consumer"\n'
                'version = "0.0.1"\ndependencies = []\n',
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
            )
        )
        tm.that(tomllib.loads(conformed)["project"]["version"], eq="0.0.1")

    def test_ssot_required_dev_floor_replaces_stale_same_name_pin(self) -> None:
        """Toolchain required_dev floors win over older same-package member pins."""
        workspace = _workspace()
        toolchain = config.Infra.codegen.toolchain
        source = """[project]
name = "external-consumer"
dependencies = []

[dependency-groups]
dev = ["rumdl>=0.2.46", "custom-tool>=1"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=("rumdl>=0.2.45",),
            )
        )
        document = tomllib.loads(conformed)
        tm.that("rumdl>=0.2.45" in document["dependency-groups"]["dev"], eq=True)
        tm.that("rumdl>=0.2.46" not in document["dependency-groups"]["dev"], eq=True)
        tm.that("custom-tool>=1" in document["dependency-groups"]["dev"], eq=True)

    def test_exclude_dependencies_emit_for_standalone_without_project_key(self) -> None:
        """Standalone member CI needs scoped excludes without the routing key."""
        workspace = _workspace()
        exclusion = m.Infra.UvScopedDependencyExclusionSpec(
            project="flext-infra",
            package=m.Infra.UvPackageSelectorSpec(name="flext-tests"),
            dependencies=("flext-infra",),
        )
        source = """[project]
name = "flext-infra"
dependencies = []
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.MakeProfile.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
                uv_exclude_dependencies=(exclusion,),
            )
        )
        document = tomllib.loads(conformed)
        excludes = document["tool"]["uv"]["exclude-dependencies"]
        tm.that(
            excludes,
            eq=[{"package": {"name": "flext-tests"}, "dependencies": ["flext-infra"]}],
        )
        tm.that("project" not in excludes[0], eq=True)
