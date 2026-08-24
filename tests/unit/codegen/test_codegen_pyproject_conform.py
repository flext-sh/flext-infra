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


def _project_spec(*, version: str) -> m.Infra.ProjectSpec:
    """Build project metadata whose non-version fields come from the SSOT."""
    scaffold = config.Infra.codegen.scaffold.project
    return m.Infra.ProjectSpec(
        package_name="external_consumer",
        class_stem="ExternalConsumer",
        namespace="ExternalConsumer",
        constant_name="external-consumer",
        namespace_attribute="external_consumer",
        alias="external_consumer",
        environment_prefix="EXTERNAL_CONSUMER_",
        description="Conformance fixture project",
        version=version,
        license=scaffold.supported_licenses[0],
        author_name="Test Author",
        author_email="test@example.com",
        upstream=scaffold.dependency_profiles[0].upstream,
        homepage="https://example.com/external-consumer",
        documentation="https://example.com/external-consumer/docs",
        workspace_root_rel=".",
        year=2026,
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
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                first,
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
            providers=config.Infra.codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        tm.fail(result, has="attached workspace dependency declares direct source")

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

[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
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
        tm.that(document["tool"]["uv"]["exclude-newer"], eq=toolchain.uv_exclude_newer)
        # Why (flext-6itas.4): exclude-newer-package merges boolean exclusions
        # with per-package RFC 3339 cutoffs (b3f3fb75c added
        # dependency_cooldown_overrides so a floor published after the shared
        # cooldown can get its own cutoff instead of only a name-only bypass).
        expected_exclude_newer_package = {
            package: False
            for package in toolchain.dependency_cooldown_exclusions
            if package not in toolchain.dependency_cooldown_overrides
        }
        expected_exclude_newer_package.update(toolchain.dependency_cooldown_overrides)
        tm.that(
            document["tool"]["uv"]["exclude-newer-package"],
            eq=expected_exclude_newer_package,
        )
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
        # workspace member, which dependency provenance rewrites to its pinned
        # git requirement (measured: "flext-tests" renders as
        # "flext-tests @ git+.../flext-tests.git@<branch>"). Asserting by
        # package name keeps both shapes in scope without re-encoding either.
        rendered_names = {
            u.Infra.dep_name(requirement)
            for requirement in document["dependency-groups"]["dev"]
        }
        for requirement in required_dev:
            tm.that(u.Infra.dep_name(requirement) in rendered_names, eq=True)
        tm.that(
            document["project"]["dependencies"][0],
            eq=(
                f"{workspace.members[0].distribution} @ "
                f"git+{workspace.members[0].url}@{_PROVIDER_SPEC.branch}"
            ),
        )

    def test_declared_manifest_version_is_projected_onto_project_table(self) -> None:
        """The manifest owns the release version; conformance projects it.

        Why (hq-36xk): the scaffold template renders `version = "{{ version }}"`
        but carries `overwrite: false`, so on an existing repository nothing
        propagated a manifest bump into `[project].version`. Deriving the
        expectation from the same spec production reads keeps this test valid
        when the declared version legitimately changes.
        """
        project = config.Infra.codegen.scaffold.project
        declared = _project_spec(version="9.9.9")
        workspace = _workspace().model_copy(update={"project": declared})
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "external-consumer"\n'
                'version = "0.0.1"\ndependencies = []\n',
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=project.dev,
            )
        )
        document = tomllib.loads(conformed)
        tm.that(document["project"]["version"], eq=declared.version)

    def test_project_version_conformance_is_idempotent(self) -> None:
        """A pyproject already matching the manifest is left byte-identical."""
        project = config.Infra.codegen.scaffold.project
        declared = _project_spec(version="9.9.9")
        workspace = _workspace().model_copy(update={"project": declared})
        source = (
            '[project]\nname = "external-consumer"\n'
            f'version = "{declared.version}"\ndependencies = []\n'
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=project.dev,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=project.dev,
            )
        )
        tm.that(second, eq=first)
        tm.that(tomllib.loads(first)["project"]["version"], eq=declared.version)

    def test_workspace_without_project_metadata_leaves_version_untouched(self) -> None:
        """A topology-only manifest declares no version, so none is projected."""
        workspace = _workspace()
        tm.that(workspace.project is None, eq=True)
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "external-consumer"\n'
                'version = "0.0.1"\ndependencies = []\n',
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
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
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=("rumdl>=0.2.45",),
            )
        )
        document = tomllib.loads(conformed)
        tm.that("rumdl>=0.2.45" in document["dependency-groups"]["dev"], eq=True)
        tm.that("rumdl>=0.2.46" not in document["dependency-groups"]["dev"], eq=True)
        tm.that("custom-tool>=1" in document["dependency-groups"]["dev"], eq=True)

    def test_tool_flext_workspace_marker_is_preserved(self) -> None:
        """Preserve [tool.flext] policy while removing legacy tool.poetry."""
        workspace = _workspace()
        source = """[project]
name = "external-consumer"
dependencies = []

[tool.flext.workspace]
attached = true

[tool.poetry]
name = "legacy-packaging"
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
            )
        )
        document = tomllib.loads(conformed)
        tm.that(document["tool"]["flext"]["workspace"]["attached"], eq=True)
        tm.that("poetry" not in document["tool"], eq=True)

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
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
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
