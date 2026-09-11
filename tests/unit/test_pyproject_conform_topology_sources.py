"""Tests for canonical dependency source selection by topology role.

The repository root owns the local ``workspace = true`` overlay. Publishable
projects keep their direct Git requirement with the configured branch so the
same package metadata resolves standalone; uv applies the root overlay when
resolving them inside the workspace (a member ``[tool.uv.sources]`` git entry
is rejected by uv itself, so the inline form is the only valid dual-context
declaration).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u
from tests import TestsFlextInfraUtilities as tu, u as test_u

_ROLE = c.Infra.MakeProfile
# Provider identity, branch and base URL come from the config SSOT, never from
# literals repeated in the test.
_PROVIDER_SPEC = config.Infra.codegen.providers[0]


def _member_ref(distribution: str, path: str) -> m.Infra.RepositoryRef:
    """Declare one standalone-capable member through the provider contract."""
    return test_u.Tests.repository_ref(
        distribution, role=_ROLE.STANDALONE, path=Path(path)
    )


def _workspace(*members: m.Infra.RepositoryRef) -> m.Infra.WorkspaceSpec:
    """Compose one workspace fixture from its declared member references."""
    return m.Infra.WorkspaceSpec(
        name="workspace",
        beads=test_u.Tests.beads_project("workspace"),
        repository=test_u.Tests.repository_ref("workspace"),
        subprojects=tuple(members),
    )


def _inline_requirement(ref: m.Infra.RepositoryRef) -> str:
    """Render the direct-source form derived from the same declared contract."""
    return f"{ref.distribution} @ git+{ref.url}@{_PROVIDER_SPEC.branch}"


def _assert_direct_source(rendered: str, ref: m.Infra.RepositoryRef) -> None:
    """Assert the canonical standalone output: one direct Git requirement."""
    dependencies = tu.Tests.toml_strings_at(rendered, "project", "dependencies")
    tm.that(dependencies, eq=(_inline_requirement(ref),))
    parsed = tu.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
    tool = parsed.get("tool")
    uv_sources = (
        tu.Tests.toml_mapping(tu.Tests.toml_mapping(tool).get("uv")).get("sources")
        if tool
        else None
    )
    tm.that(not uv_sources, eq=True)


class TestsFlextInfraPyprojectConformTopologySources:
    def test_repository_root_never_gets_git_specifier(self) -> None:
        workspace = _workspace(_member_ref("flext-core", "flext-core"))
        root_source = (
            "[project]\n"
            'name = "workspace"\n'
            'version = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
            "\n[dependency-groups]\n"
            'workspace = ["flext-core"]\n'
            "\n[tool.uv.workspace]\n"
            'members = ["flext-core"]\n'
            "\n[tool.uv.sources.flext-core]\n"
            "workspace = true\n"
        )

        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                root_source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.WORKSPACE,
            )
        )

        group = tu.Tests.toml_strings_at(rendered, "dependency-groups", "workspace")
        runtime = tu.Tests.toml_strings_at(rendered, "project", "dependencies")
        parsed = tu.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        tool = tu.Tests.toml_mapping(parsed["tool"])
        uv = tu.Tests.toml_mapping(tool["uv"])
        sources = tu.Tests.toml_mapping(uv["sources"])

        tm.that(group, eq=("flext-core",))
        tm.that(runtime, eq=("flext-core",))
        member_overlay = tu.Tests.toml_mapping(sources["flext-core"])
        tm.that(member_overlay.get("workspace"), eq=True)
        tm.that("git" in member_overlay, eq=False)

    def test_external_consumer_keeps_direct_git_requirement(self) -> None:
        workspace = _workspace(_member_ref("flext-core", "flext-core"))
        core = workspace.subprojects[0]
        external = (
            "[project]\n"
            'name = "acme-platform"\n'
            'version = "0.1.0"\n'
            f'dependencies = ["{_inline_requirement(core)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                external,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.STANDALONE,
            )
        )

        _assert_direct_source(rendered, core)

    def test_publishable_project_keeps_catalog_git_provenance(self) -> None:
        workspace = _workspace(
            _member_ref("flext-core", "flext-core"),
            _member_ref("flext-api", "flext-api"),
        )
        provider = workspace.subprojects[0]
        publishable_project = (
            f'[project]\nname = "{workspace.subprojects[1].distribution}"\n'
            'version = "0.1.0"\n'
            f'dependencies = ["{_inline_requirement(provider)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                publishable_project,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.WORKSPACE,
            )
        )

        _assert_direct_source(rendered, provider)

    def test_publishable_project_pins_unmapped_provider_source_to_branch(self) -> None:
        """Derive the declared branch for a provider absent from subprojects."""
        workspace = _workspace(
            _member_ref("flext-core", "flext-core"),
            _member_ref("flext-api", "flext-api"),
        )
        consumer = workspace.subprojects[1]
        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                (
                    f'[project]\nname = "{consumer.distribution}"\n'
                    'version = "0.1.0"\n'
                    'dependencies = ["flext-unmapped @ '
                    'git+https://github.com/flext-sh/flext-unmapped.git@main"]\n'
                ),
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.WORKSPACE,
            )
        )

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

    def test_root_workspace_overlay_resolves_publishable_project_with_uv(
        self, tmp_path: Path
    ) -> None:
        """Prove uv resolves project Git metadata through the root overlay."""
        workspace = _workspace(
            _member_ref("flext-core", "flext-core"),
            _member_ref("flext-api", "flext-api"),
        )
        provider, consumer = workspace.subprojects
        root = tmp_path / "workspace"
        provider_root = root / provider.path
        consumer_root = root / consumer.path
        provider_root.mkdir(parents=True)
        consumer_root.mkdir(parents=True)
        root_source = f"""[project]
name = "{workspace.repository.distribution}"
version = "0.1.0"
dependencies = ["{provider.distribution}", "{consumer.distribution}"]

[tool.uv]
package = false

[tool.uv.workspace]
members = ["{provider.path.as_posix()}", "{consumer.path.as_posix()}"]

[tool.uv.sources.{provider.distribution}]
workspace = true

[tool.uv.sources.{consumer.distribution}]
workspace = true
"""
        root_rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                root_source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.WORKSPACE,
            )
        )
        consumer_rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                (
                    f'[project]\nname = "{consumer.distribution}"\n'
                    'version = "0.1.0"\n'
                    f'dependencies = ["{_inline_requirement(provider)}"]\n'
                ),
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.WORKSPACE,
            )
        )
        (root / c.Infra.PYPROJECT_FILENAME).write_text(root_rendered, encoding="utf-8")
        (provider_root / c.Infra.PYPROJECT_FILENAME).write_text(
            (f'[project]\nname = "{provider.distribution}"\nversion = "0.1.0"\n'),
            encoding="utf-8",
        )
        (consumer_root / c.Infra.PYPROJECT_FILENAME).write_text(
            consumer_rendered, encoding="utf-8"
        )

        lock_result = tm.ok(
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

        tm.that(u.Cli.process_succeeded(lock_result.outcome), eq=True)
        lock_content = (root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8")
        packages = tu.Tests.toml_tables_at(lock_content, "package")
        provider_packages = [
            package for package in packages if package["name"] == provider.distribution
        ]
        tm.that(len(provider_packages), eq=1)
        provider_source = tu.Tests.toml_mapping(provider_packages[0]["source"])
        tm.that(provider_source.get("editable"), eq=provider.path.as_posix())
        tm.that("git" in provider_source, eq=False)

    def test_standalone_resolves_dependency_groups_with_direct_requirements(
        self,
    ) -> None:
        """Dev-group members resolve standalone through direct Git requirements."""
        workspace = _workspace(_member_ref("flext-core", "flext-core"))
        core = workspace.subprojects[0]
        member_source = (
            "[project]\n"
            'name = "flext-tests"\n'
            'version = "0.1.0"\n'
            "\n[dependency-groups]\n"
            f'dev = ["{_inline_requirement(core)}"]\n'
        )

        rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                member_source,
                providers=config.Infra.codegen.providers,
                workspace=workspace,
                workspace_mode=_ROLE.STANDALONE,
            )
        )

        group = tu.Tests.toml_strings_at(rendered, "dependency-groups", "dev")
        parsed = tu.Tests.toml_mapping(u.Cli.toml_parse_text(rendered))
        tool = parsed.get("tool")
        uv_sources = (
            tu.Tests.toml_mapping(tu.Tests.toml_mapping(tool).get("uv")).get("sources")
            if tool
            else None
        )

        tm.that(group, eq=(_inline_requirement(core),))
        tm.that(not uv_sources, eq=True)
