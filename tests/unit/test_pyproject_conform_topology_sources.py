"""Tests for canonical dependency source selection by topology role.

The composition root owns local path sources for dependencies it actually uses.
Publishable projects retain catalog Git provenance and autonomous uv boundaries.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import TestsFlextInfraUtilities as tu

_ROLE = c.Infra.RepositoryRole
# Provider identity, branch and base URL come from the config SSOT,
# never from literals repeated in the test.
_PROVIDER_SPEC = tm.ok(
    u.Infra.repository_provider(
        tu.Tests.repository_ref("provider-fixture"), config.Infra.codegen.providers
    )
)
_PROVIDER = _PROVIDER_SPEC.name


def _repository(
    distribution: str,
    *,
    role: c.Infra.RepositoryRole,
    path: str,
    checkout: c.Infra.CheckoutKind,
) -> m.Infra.RepositoryRef:
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=f"{_PROVIDER_SPEC.base_url}/{distribution}.git",
        path=Path(path),
        role=role,
        provider=_PROVIDER,
        checkout=checkout,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=True,
        read_only=False,
    )


def _workspace() -> m.Infra.WorkspaceSpec:
    return m.Infra.WorkspaceSpec(
        beads=tu.Tests.beads_project("flext"),
        name="workspace",
        repository=_repository(
            "workspace",
            role=_ROLE.WORKSPACE,
            path=".",
            checkout=c.Infra.CheckoutKind.ROOT,
        ),
        subprojects=(
            _repository(
                "flext-core",
                role=_ROLE.STANDALONE,
                path="flext-core",
                checkout=c.Infra.CheckoutKind.SUBMODULE,
            ),
        ),
    )


def _workspace_with_consumer() -> m.Infra.WorkspaceSpec:
    workspace = _workspace()
    consumer = _repository(
        "flext-api",
        role=_ROLE.STANDALONE,
        path="flext-api",
        checkout=c.Infra.CheckoutKind.SUBMODULE,
    )
    return workspace.model_copy(
        update={"subprojects": (*workspace.subprojects, consumer)}
    )


_PYPROJECT = """[project]
name = "workspace"
version = "0.1.0"
dependencies = ["flext-core"]

[tool.uv.workspace]
members = []

[tool.uv.sources.flext-core]
path = "flext-core"
editable = true
"""


class TestsFlextInfraPyprojectConformTopologySources:
    def test_composition_root_never_gets_git_specifier(self) -> None:
        workspace = _workspace()

        result = u.Infra.pyproject_dependencies_conform(
            _PYPROJECT,
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        rendered = tm.ok(result)
        document = tu.Tests.toml_table_at(rendered)
        runtime = tu.Tests.toml_strings_at(rendered, "project", "dependencies")

        tm.that(document.get("dependency-groups"), none=True)
        tm.that(runtime, eq=("flext-core",))

    def test_external_consumer_keeps_remote_branch_source(self) -> None:
        workspace = _workspace()
        external = (
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            external,
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        rendered = tm.ok(result)
        dependencies = tu.Tests.toml_strings_at(rendered, "project", "dependencies")

        # The expected specifier is derived from the same declared repository
        # contract the generator reads - never a hardcoded URL or branch.
        project = workspace.subprojects[0]
        tm.that(
            dependencies,
            eq=(f"{project.distribution} @ git+{project.url}@{_PROVIDER_SPEC.branch}",),
        )

    def test_publishable_project_keeps_catalog_git_provenance(self) -> None:
        workspace = _workspace_with_consumer()
        provider = workspace.subprojects[0]
        publishable_project = (
            f'[project]\nname = "{workspace.subprojects[1].distribution}"\n'
            'version = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            publishable_project,
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        rendered = tm.ok(result)
        dependencies = tu.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(
            dependencies,
            eq=(
                (
                    f"{provider.distribution} @ git+{provider.url}@"
                    f"{_PROVIDER_SPEC.branch}"
                ),
            ),
        )

    def test_attached_root_rejects_explicit_member_source(self) -> None:
        workspace = _workspace()
        member = workspace.subprojects[0]
        attached_root = _PYPROJECT.replace(
            'dependencies = ["flext-core"]',
            (
                f'dependencies = ["{member.distribution} @ '
                f'git+{member.url}@{_PROVIDER_SPEC.branch}"]'
            ),
            1,
        )

        result = u.Infra.pyproject_dependencies_conform(
            attached_root,
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(result.failure, eq=True)
        tm.that(
            result.error or "",
            has="workspace dependency declares a conflicting direct source",
        )

        local_result = u.Infra.pyproject_dependencies_conform(
            attached_root.replace(
                f"git+{member.url}@{_PROVIDER_SPEC.branch}",
                "file:///outside/flext-core",
            ),
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(local_result.failure, eq=True)
        tm.that(
            local_result.error or "",
            has="workspace dependency declares a conflicting direct source",
        )

    def test_publishable_member_pins_unmapped_provider_source_to_branch(self) -> None:
        """Derive the declared branch for a provider source absent from members."""
        workspace = _workspace_with_consumer()
        consumer = workspace.subprojects[1]
        result = u.Infra.pyproject_dependencies_conform(
            (
                f'[project]\nname = "{consumer.distribution}"\n'
                'version = "0.1.0"\n'
                'dependencies = ["flext-unmapped @ '
                'git+https://github.com/flext-sh/flext-unmapped.git@main"]\n'
            ),
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        rendered = tm.ok(result)
        dependencies = tu.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(
            dependencies,
            eq=(
                (
                    "flext-unmapped @ git+https://github.com/flext-sh/"
                    f"flext-unmapped.git@{_PROVIDER_SPEC.branch}"
                ),
            ),
        )

    def test_root_path_composition_resolves_autonomous_projects_with_uv(
        self, tmp_path: Path
    ) -> None:
        """Prove root and children keep separate locks and environments."""
        workspace = _workspace_with_consumer()
        provider, consumer = workspace.subprojects
        root = tmp_path / "workspace"
        provider_root = root / provider.path
        consumer_root = root / consumer.path
        uv_version = config.Infra.codegen.toolchain.uv_version
        uv_major, uv_minor = (int(part) for part in uv_version.split("."))
        uv_build_ceiling = f"{uv_major}.{uv_minor + 1}"

        def standalone_project(project: m.Infra.RepositoryRef) -> str:
            package = (
                root / project.path / "src" / project.distribution.replace("-", "_")
            )
            package.mkdir(parents=True)
            (package / "__init__.py").write_text(
                '"""Autonomous path fixture."""\n', encoding="utf-8"
            )
            return tm.ok(
                u.Infra.pyproject_dependencies_conform(
                    (
                        f'[project]\nname = "{project.distribution}"\n'
                        'version = "0.1.0"\nrequires-python = ">=3.13"\n'
                        f'\n[build-system]\nrequires = ["uv_build>={uv_version},'
                        f'<{uv_build_ceiling}"]\n'
                        'build-backend = "uv_build"\n'
                    ),
                    codegen=config.Infra.codegen,
                    workspace=workspace,
                    workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
                )
            )

        provider_rendered = standalone_project(provider)
        consumer_rendered = standalone_project(consumer)
        root_source = f"""[project]
name = "{workspace.repository.distribution}"
version = "0.1.0"
dependencies = ["{provider.distribution}", "{consumer.distribution}"]

[tool.uv]
package = false

[tool.uv.workspace]
members = []

[tool.uv.sources.{provider.distribution}]
path = "{provider.path.as_posix()}"
editable = true

[tool.uv.sources.{consumer.distribution}]
path = "{consumer.path.as_posix()}"
editable = true
"""
        root_rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                root_source,
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
            )
        )
        (root / c.Infra.PYPROJECT_FILENAME).write_text(root_rendered, encoding="utf-8")
        (provider_root / c.Infra.PYPROJECT_FILENAME).write_text(
            provider_rendered, encoding="utf-8"
        )
        (consumer_root / c.Infra.PYPROJECT_FILENAME).write_text(
            consumer_rendered, encoding="utf-8"
        )

        child_workspace = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "workspace", "dir", "--project", str(provider_root)],
                cwd=provider_root,
            )
        )
        child_lock = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "lock", "--offline", "--project", str(provider_root)],
                cwd=provider_root,
                env={"UV_CACHE_DIR": str(tmp_path / "uv-cache")},
            )
        )
        child_sync = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "sync", "--offline", "--project", str(provider_root)],
                cwd=provider_root,
                env={
                    "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
                    "UV_PROJECT_ENVIRONMENT": str(provider_root / ".venv"),
                },
            )
        )
        child_lock_content = (provider_root / c.Infra.UV_LOCK_FILENAME).read_text(
            encoding="utf-8"
        )
        root_workspace = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "workspace", "dir", "--project", str(root)], cwd=root
            )
        )
        root_lock = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "lock", "--offline", "--project", str(root)],
                cwd=root,
                timeout=c.DEFAULT_TIMEOUT_SECONDS,
                env={"UV_CACHE_DIR": str(tmp_path / "uv-cache")},
                remove_env_keys=(
                    "MYPYPATH",
                    "PYTHONPATH",
                    "UV_PROJECT",
                    "UV_PROJECT_ENVIRONMENT",
                    "VIRTUAL_ENV",
                ),
            )
        )
        root_sync = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "sync", "--offline", "--project", str(root)],
                cwd=root,
                env={
                    "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
                    "UV_PROJECT_ENVIRONMENT": str(root / ".venv"),
                },
            )
        )

        for result in (
            child_workspace,
            child_lock,
            child_sync,
            root_workspace,
            root_lock,
            root_sync,
        ):
            output = result.stdout + result.stderr
            tm.that(result.exit_code, eq=0, msg=output)
            tm.that(output.lower(), lacks="nested workspace")
        tm.that(child_workspace.stdout.strip(), eq=str(provider_root))
        tm.that(root_workspace.stdout.strip(), eq=str(root))
        tm.that((provider_root / ".venv").is_dir(), eq=True)
        tm.that((root / ".venv").is_dir(), eq=True)
        tm.that((consumer_root / ".venv").exists(), eq=False)
        tm.that((consumer_root / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
        tm.that(
            (provider_root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
            eq=child_lock_content,
        )
        lock_content = (root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8")
        tm.that(lock_content, ne=child_lock_content)
        packages = tu.Tests.toml_tables_at(lock_content, "package")
        provider_packages = [
            package for package in packages if package["name"] == provider.distribution
        ]
        tm.that(len(provider_packages), eq=1)
        provider_source = tu.Tests.toml_mapping(provider_packages[0]["source"])
        tm.that(provider_source.get("editable"), eq=provider.path.as_posix())
        tm.that("git" in provider_source, eq=False)

    def test_root_missing_declared_path_fails_loudly_with_uv(
        self, tmp_path: Path
    ) -> None:
        """Prove a missing physical dependency cannot fall back to a registry."""
        workspace = _workspace()
        member = workspace.subprojects[0]
        root = tmp_path / "workspace"
        root.mkdir()
        source = f"""[project]
name = "{workspace.repository.distribution}"
version = "0.1.0"
dependencies = ["{member.distribution}"]

[tool.uv.workspace]
members = []

[tool.uv.sources.{member.distribution}]
path = "{member.path.as_posix()}"
editable = true
"""
        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                source,
                codegen=config.Infra.codegen,
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
            )
        )
        (root / c.Infra.PYPROJECT_FILENAME).write_text(rendered, encoding="utf-8")

        result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "lock", "--offline", "--project", str(root)],
                cwd=root,
                env={"UV_CACHE_DIR": str(tmp_path / "uv-cache")},
            )
        )

        output = result.stdout + result.stderr
        tm.that(result.exit_code, ne=0)
        tm.that(output, has=member.path.as_posix())
        tm.that((root / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)

    def test_standalone_replaces_workspace_source_with_git_requirement(self) -> None:
        workspace = _workspace()

        result = u.Infra.pyproject_dependencies_conform(
            _PYPROJECT,
            codegen=config.Infra.codegen,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        project = workspace.subprojects[0]
        rendered = tm.ok(result)
        dependencies = tu.Tests.toml_strings_at(rendered, "project", "dependencies")
        tm.that(
            dependencies,
            eq=(f"{project.distribution} @ git+{project.url}@{_PROVIDER_SPEC.branch}",),
        )
        document = tu.Tests.toml_table_at(rendered)
        tool = tu.Tests.toml_mapping(document.get("tool"))
        uv = tu.Tests.toml_mapping(tool.get("uv"))
        boundary = tu.Tests.toml_mapping(uv.get("workspace"))
        tm.that(boundary.get("members"), eq=[])
        tm.that("sources" not in uv, eq=True)
