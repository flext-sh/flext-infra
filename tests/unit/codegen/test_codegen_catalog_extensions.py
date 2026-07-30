"""Repository-local workspace manifests are the sole consumer authority."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u


def _repository(
    name: str,
    *,
    path: str,
    role: c.Infra.RepositoryRole,
    state: c.Infra.RepositoryState = c.Infra.RepositoryState.ACTIVE,
) -> m.Infra.RepositoryRef:
    profile = (
        c.Infra.MakeProfile.WORKSPACE_ROOT
        if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
        else c.Infra.MakeProfile.WORKSPACE_MEMBER
    )
    return m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        provider="acme-hosting",
        url=f"https://github.com/acme-hosting/{name}.git",
        branch="development",
        path=Path(path),
        role=role,
        state=state,
        profile=profile,
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=(
            c.Infra.CodegenKind.NONE
            if role is c.Infra.RepositoryRole.CONTENT_ONLY
            else c.Infra.CodegenKind.CONFORM
        ),
        package=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        read_only=role is c.Infra.RepositoryRole.CONTENT_ONLY,
    )


class TestsCodegenCatalogExtensions:
    def test_beads_toolchain_uses_an_immutable_release_selector(self) -> None:
        selector = config.Infra.codegen.toolchain.beads_version

        version_parts = selector.split(".")
        is_semver = len(version_parts) == 3 and all(
            part.isdecimal() for part in version_parts
        )
        is_commit = len(selector) == 40 and all(
            char in "0123456789abcdef" for char in selector
        )
        tm.that(is_semver or is_commit, eq=True)

    def test_bootstrap_toolchain_uses_immutable_release_selectors(self) -> None:
        toolchain = config.Infra.codegen.toolchain

        for selector in (toolchain.uv_version, toolchain.mise_version):
            version_parts = selector.split(".")
            tm.that(len(version_parts), eq=3)
            tm.that(all(part.isdecimal() for part in version_parts), eq=True)

        uv_floor = toolchain.uv_bootstrap_required_version
        tm.that(uv_floor, has=">=")
        floor_version = uv_floor.lstrip(">= ")
        version_parts = floor_version.split(".")
        tm.that(len(version_parts), eq=3)
        tm.that(all(part.isdecimal() for part in version_parts), eq=True)

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = _repository(
            "acme-platform", path=".", role=c.Infra.RepositoryRole.WORKSPACE_ROOT
        ).model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(name="audit", default_what="all"),
                ),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher="scripts/dispatch.py", roots=("scripts",)
                ),
            }
        )
        project = m.Infra.ProjectSpec(
            package_name="acme_platform",
            class_stem="AcmePlatform",
            namespace="AcmePlatform",
            constant_name="acme-platform",
            namespace_attribute="acme_platform",
            alias="acme",
            environment_prefix="ACME_PLATFORM_",
            description="Product-neutral platform fixture",
            version="0.1.0",
            license="MIT",
            author_name="Acme Team",
            author_email="engineering@example.com",
            upstream="flext_core",
            homepage="https://example.com/acme-platform",
            documentation="https://example.com/acme-platform/docs",
            workspace_root_rel=".",
            year=2026,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root.name,
            repository=root,
            project=project,
            members=(
                _repository(
                    "acme-charts",
                    path="acme-charts",
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                ),
            ),
            content_only=(
                _repository(
                    "acme-content",
                    path="acme-content",
                    role=c.Infra.RepositoryRole.CONTENT_ONLY,
                    state=c.Infra.RepositoryState.CONTENT_ONLY,
                ),
            ),
        )
        member_root = tmp_path / "acme-charts"
        member_root.mkdir()
        (member_root / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "acme-charts"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            encoding="utf-8",
        )
        tm.ok(
            u.Cli.run_checked(["git", "init", "-q", "-b", "development"], cwd=member_root)
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "add", c.Infra.PYPROJECT_FILENAME], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial fixture"], cwd=member_root
            )
        )
        analysis_exclusions = tuple(
            path.as_posix()
            for path in FlextInfraWorkspaceDetector.workspace_analysis_exclusion_paths(
                workspace
            )
        )
        tooling = tm.ok(
            FlextInfraPyprojectModernizer(
                workspace_root=tmp_path, skip_check=True
            ).resolve_tooling_context(
                project_name=root.distribution,
                package_name=project.package_name,
                path=tmp_path / c.Infra.PYPROJECT_FILENAME,
                declared_python_dirs=(
                    config.Infra.tooling.tools.pyright.path_rules.env_dirs
                ),
                analysis_exclusions=analysis_exclusions,
            )
        )
        tm.that(tooling.ruff_exclude, has="acme-content")
        tm.that(tooling.pyright_exclude, has="acme-content")

        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            m.Infra.CodegenConformRequest(
                root=tmp_path,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        plan = tm.ok(result)
        tm.that(
            tuple(item.name for item in plan.repositories),
            eq=(root.name, "acme-charts"),
        )
        external_root = (tmp_path / "acme-content").resolve()
        tm.that(
            any(
                external_root == file.path or external_root in file.path.parents
                for file in plan.files
            ),
            eq=False,
        )
        tm.that(external_root.exists(), eq=False)
        root_makefile = next(
            file
            for file in plan.files
            if file.path == tmp_path.resolve() / c.Infra.MAKEFILE_FILENAME
        )
        tm.that(root_makefile.rendered, has="WORKSPACE_MEMBERS := acme-charts")
        tm.that("acme-content" in root_makefile.rendered, eq=False)
        workflows = tuple(
            file
            for file in plan.files
            if ".github/workflows" in file.path.as_posix()
        )
        tm.that(workflows, len=4)
        for workflow in workflows:
            tm.that("acme-content" in workflow.rendered, eq=False)
        gitmodules = next(
            file.rendered for file in plan.files if file.path.name == ".gitmodules"
        )
        tm.that(gitmodules, has="flext-managed = true")
        tm.that(gitmodules, has="flext-managed = false")
        mise = tomllib.loads(
            next(file.rendered for file in plan.files if file.path.name == ".mise.toml")
        )
        tm.that(
            mise["tools"]["go:github.com/steveyegge/beads/cmd/bd"],
            eq=config.Infra.codegen.toolchain.beads_version,
        )
        pyproject = tomllib.loads(
            next(
                file.rendered
                for file in plan.files
                if file.path.name == c.Infra.PYPROJECT_FILENAME
            )
        )
        tools = pyproject["tool"]
        tm.that(tools["ruff"]["exclude"], has="acme-content")
        tm.that(tools["pyright"]["exclude"], has="acme-content")


__all__: tuple[str, ...] = ()
