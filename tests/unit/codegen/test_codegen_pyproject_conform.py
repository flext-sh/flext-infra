"""Public behavior tests for topology-aware pyproject conformance."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u

_PROVIDER_SPEC = tm.ok(
    u.Infra.repository_provider(
        test_u.Tests.repository_ref("provider-fixture"), config.Infra.codegen.providers
    )
)


def _provider(name: str) -> m.Infra.ProviderSpec:
    matches = tuple(
        provider for provider in config.Infra.codegen.providers if provider.name == name
    )
    tm.that(len(matches), eq=1)
    (provider,) = matches
    return provider


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
            if role is c.Infra.RepositoryRole.WORKSPACE
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=role is not c.Infra.RepositoryRole.WORKSPACE,
        editable=role is not c.Infra.RepositoryRole.WORKSPACE,
        read_only=False,
    )


def _project_spec(*, version: str) -> m.Infra.ProjectSpec:
    """Build project metadata whose non-version fields come from the SSOT."""
    return test_u.Tests.project_spec("external-consumer").model_copy(
        update={"version": version}
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
            "workspace", role=c.Infra.RepositoryRole.WORKSPACE, path="."
        ),
        subprojects=(
            _repository(
                "flext-core", role=c.Infra.RepositoryRole.STANDALONE, path="flext-core"
            ),
        ),
    )


class TestsFlextInfraCodegenPyprojectConform:
    def test_composition_root_uses_only_declared_path_provenance(self) -> None:
        workspace = _workspace()
        result = u.Infra.pyproject_dependencies_conform(
            """[project]
name = "workspace"
dependencies = ["flext-core"]

[tool.uv.workspace]
members = []

[tool.uv.sources.flext-core]
path = "flext-core"
editable = true
""",
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=["flext-core"])
        tm.that("workspace" not in document.get("dependency-groups", {}), eq=True)
        tm.that(
            document["tool"]["uv"]["sources"]["flext-core"],
            eq={"path": "flext-core", "editable": True},
        )

    def test_full_conformance_drops_unused_gitlink_sources_and_preserves_foreign(
        self,
    ) -> None:
        workspace = _workspace()
        unused = _repository(
            "flext-api", role=c.Infra.RepositoryRole.STANDALONE, path="flext-api"
        )
        workspace = workspace.model_copy(
            update={"subprojects": (*workspace.subprojects, unused)}
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                """[project]
name = "workspace"
version = "0.1.0"
dependencies = ["flext-core"]

[dependency-groups]
workspace = ["flext-core", "flext-api"]

[tool.uv.workspace]
members = ["flext-core", "flext-api"]

[tool.uv.sources.flext-core]
workspace = true

[tool.uv.sources.flext-api]
workspace = true

[tool.uv.sources.acme-tool]
git = "https://example.com/acme-tool.git"
""",
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=(),
            )
        )

        document = tomllib.loads(rendered)
        uv = document["tool"]["uv"]
        tm.that(uv["workspace"]["members"], eq=[])
        tm.that(
            uv["sources"],
            eq={
                "flext-core": {"path": "flext-core", "editable": True},
                "acme-tool": {"git": "https://example.com/acme-tool.git"},
            },
        )
        tm.that("workspace" not in document.get("dependency-groups", {}), eq=True)

    def test_standalone_uses_catalog_git_provenance(self) -> None:
        workspace = _workspace()
        member = workspace.subprojects[0]
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )
        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{_PROVIDER_SPEC.branch}"],
        )

    def test_submodule_checkout_owns_empty_uv_workspace_boundary(self) -> None:
        repository = _repository(
            "workspace-member", role=c.Infra.RepositoryRole.STANDALONE, path="."
        )
        workspace = _workspace().model_copy(
            update={"repository": repository, "subprojects": ()}
        )
        result = u.Infra.pyproject_dependencies_conform(
            """[project]
name = "workspace-member"

[tool.uv.workspace]
""",
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        uv = document.get("tool", {}).get("uv", {})
        tm.that(uv["workspace"]["members"], eq=[])

    def test_standalone_root_owns_empty_uv_workspace_boundary(self) -> None:
        repository = _repository(
            "standalone-root", role=c.Infra.RepositoryRole.STANDALONE, path="."
        ).model_copy(update={"checkout": c.Infra.CheckoutKind.ROOT})
        workspace = _workspace().model_copy(
            update={"repository": repository, "subprojects": ()}
        )
        result = u.Infra.pyproject_dependencies_conform(
            """[project]
name = "standalone-root"

[tool.uv]
link-mode = "copy"
""",
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(document["tool"]["uv"]["workspace"]["members"], eq=[])
        tm.that(document["tool"]["uv"]["link-mode"], eq="copy")

    def test_standalone_boundary_prevents_parent_workspace_adoption(
        self, tmp_path: Path
    ) -> None:
        """Real uv keeps recursive member lock, environment, and dist local."""
        parent = tmp_path / "parent"
        child = parent / "child"
        sibling = parent / "sibling"
        package = child / "src" / "child"
        package.mkdir(parents=True)
        sibling.mkdir()
        (package / "__init__.py").write_text('"""Fixture."""\n', encoding="utf-8")
        (sibling / "pyproject.toml").write_text(
            '[project]\nname = "sibling"\nversion = "0.0.0"\n'
            "\n[tool.uv.workspace]\nmembers = []\n",
            encoding="utf-8",
        )
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "parent"\nversion = "0.0.0"\n'
            'dependencies = ["child", "sibling"]\n'
            "\n[tool.uv.workspace]\nmembers = []\n"
            '\n[tool.uv.sources.child]\npath = "child"\neditable = true\n'
            '\n[tool.uv.sources.sibling]\npath = "sibling"\neditable = true\n',
            encoding="utf-8",
        )
        parent_lock = parent / "uv.lock"
        parent_lock.write_text("parent lock sentinel\n", encoding="utf-8")
        parent_dist = parent / "dist"
        parent_dist.mkdir()
        parent_artifact = parent_dist / "parent-sentinel.whl"
        parent_artifact.write_text("parent artifact sentinel\n", encoding="utf-8")
        uv_version = config.Infra.codegen.toolchain.uv_version
        uv_major, uv_minor = (int(part) for part in uv_version.split("."))
        uv_build_ceiling = f"{uv_major}.{uv_minor + 1}"
        workspace = _workspace().model_copy(
            update={
                "repository": _repository(
                    "child", role=c.Infra.RepositoryRole.STANDALONE, path="."
                ),
                "subprojects": (),
            }
        )
        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                '[project]\nname = "child"\nversion = "0.0.0"\n'
                'requires-python = ">=3.13"\n'
                f'\n[build-system]\nrequires = ["uv_build>={uv_version},'
                f'<{uv_build_ceiling}"]\n'
                'build-backend = "uv_build"\n',
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )
        (child / "pyproject.toml").write_text(rendered, encoding="utf-8")

        workspace_result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "workspace", "dir", "--project", str(child)], cwd=child
            )
        )
        lock_result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "lock", "--offline", "--project", str(child)], cwd=child
            )
        )
        sync_result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "sync", "--offline", "--project", str(child)],
                cwd=child,
                env={"UV_PROJECT_ENVIRONMENT": str(child / ".venv")},
            )
        )
        build_result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "build", "--offline", "--project", str(child)], cwd=child
            )
        )

        for result in (workspace_result, lock_result, sync_result, build_result):
            output = result.stdout + result.stderr
            tm.that(result.exit_code, eq=0, msg=output)
            tm.that(output.lower(), lacks="nested workspace")
        tm.that(workspace_result.stdout.strip(), eq=str(child))
        tm.that((child / "uv.lock").is_file(), eq=True)
        tm.that(tuple((child / "dist").glob("child-*")), len=2)
        tm.that(parent_lock.read_text(encoding="utf-8"), eq="parent lock sentinel\n")
        tm.that(
            parent_artifact.read_text(encoding="utf-8"), eq="parent artifact sentinel\n"
        )
        tm.that(tuple(parent_dist.iterdir()), eq=(parent_artifact,))

    def test_standalone_derives_bare_internal_dependency_from_config_authority(
        self,
    ) -> None:
        workspace = _workspace().model_copy(update={"subprojects": ()})
        source = config.Infra.codegen.infra_repository
        provider = _provider(source.provider)
        result = u.Infra.pyproject_dependencies_conform(
            '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[
                f"flext-core @ git+{provider.base_url}/flext-core.git@{provider.branch}"
            ],
        )

    def test_bare_internal_dependency_requires_exactly_one_configured_provider(
        self,
    ) -> None:
        workspace = _workspace().model_copy(update={"subprojects": ()})
        source = config.Infra.codegen.infra_repository
        selected = _provider(source.provider)
        missing = tuple(
            provider
            for provider in config.Infra.codegen.providers
            if provider.name != source.provider
        )
        duplicate = (*config.Infra.codegen.providers, selected)

        for providers in (missing, duplicate):
            codegen = config.Infra.codegen.model_copy(update={"providers": providers})
            result = u.Infra.pyproject_dependencies_conform(
                '[project]\nname = "external-consumer"\ndependencies = ["flext-core"]\n',
                codegen=codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )

            tm.fail(
                result, has="configured repository provider must resolve exactly once"
            )

    def test_standalone_resolves_explicit_https_internal_dependency(self) -> None:
        workspace = _workspace().model_copy(update={"subprojects": ()})
        provider = _provider("datacosmos-br")
        requirement = (
            "flext-core @ "
            f"git+{provider.base_url.rstrip('/')}/flext-core.git@stale-branch"
        )
        result = u.Infra.pyproject_dependencies_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{requirement}"]\n',
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        expected = (
            f"flext-core @ git+{provider.base_url.rstrip('/')}/"
            f"flext-core.git@{provider.branch}"
        )
        tm.that(document["project"]["dependencies"], eq=[expected])

    def test_standalone_resolves_explicit_ssh_internal_dependency(self) -> None:
        workspace = _workspace().model_copy(update={"subprojects": ()})
        provider = _provider("datacosmos-br")
        requirement = (
            "flext-core @ git+ssh://git@github.com/"
            f"{provider.organization}/flext-core.git@stale-branch"
        )
        result = u.Infra.pyproject_dependencies_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{requirement}"]\n',
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))
        expected = (
            f"flext-core @ git+{provider.base_url.rstrip('/')}/"
            f"flext-core.git@{provider.branch}"
        )
        tm.that(document["project"]["dependencies"], eq=[expected])

    def test_standalone_rejects_explicit_internal_dependency_identity_mismatch(
        self,
    ) -> None:
        workspace = _workspace().model_copy(update={"subprojects": ()})
        provider = _PROVIDER_SPEC
        raw_url = (
            "git+ssh://git@github.com/"
            f"{provider.organization}/different-project.git@{provider.branch}"
        )
        result = u.Infra.pyproject_dependencies_conform(
            (
                '[project]\nname = "external-consumer"\n'
                f'dependencies = ["flext-core @ {raw_url}"]\n'
            ),
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        error = tm.fail(result, has="repository identity does not match distribution")
        tm.that(error, lacks=raw_url)

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
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                first,
                codegen=config.Infra.codegen,
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
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
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
            codegen=config.Infra.codegen,
            workspace=invalid_workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
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
                "members = []\n"
                "\n[tool.uv.sources.flext-core]\n"
                'path = "flext-core"\n'
                "editable = true\n"
            ),
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
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

[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=toolchain,
                required_dev_dependencies=required_dev,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                codegen=config.Infra.codegen,
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
        expected_exclude_newer_package: dict[str, bool | str] = {
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
        # workspace project, which dependency provenance rewrites to its pinned
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
                f"{workspace.subprojects[0].distribution} @ "
                f"git+{workspace.subprojects[0].url}@{_PROVIDER_SPEC.branch}"
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
                codegen=config.Infra.codegen,
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
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                toolchain=config.Infra.codegen.toolchain,
                required_dev_dependencies=project.dev,
            )
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                codegen=config.Infra.codegen,
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
                codegen=config.Infra.codegen,
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
                codegen=config.Infra.codegen,
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
                codegen=config.Infra.codegen,
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
