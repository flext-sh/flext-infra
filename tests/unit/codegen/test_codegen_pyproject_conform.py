"""Public behavior tests for topology-aware pyproject conformance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConformExecute
from tests import c, m, t, tm, u
from tests.unit.codegen.pyproject_conform_support import (
    TestsFlextInfraPyprojectConformSupport,
)


class TestsFlextInfraCodegenPyprojectConform(TestsFlextInfraPyprojectConformSupport):
    """Pyproject conformance: topology, metadata overlay and dev floors."""

    def test_artifact_composition_preserves_pyright_first_match_resolution(
        self,
        tmp_path: Path,
    ) -> None:
        """Public composition preserves narrow-first roots and ordered local paths."""
        workspace = self._workspace()
        privacy = config.Infra.tooling.tools.pyright.path_rules
        environments = (
            m.Infra.PyrightConfig.ExecutionEnvironment(
                root="fixture-member/z_checked/inner",
                extra_paths=(
                    "fixture-member/z_checked/support",
                    "fixture-member/src",
                ),
                report_private_usage=privacy.test_like_report_private_usage,
            ),
            m.Infra.PyrightConfig.ExecutionEnvironment(
                root="fixture-member/a_checked",
                extra_paths=(
                    "fixture-member/src",
                    "fixture-member/a_checked/support",
                ),
                report_private_usage=privacy.test_like_report_private_usage,
            ),
            m.Infra.PyrightConfig.ExecutionEnvironment(
                root="fixture-member",
                extra_paths=("fixture-member", "fixture-member/src"),
                report_private_usage=privacy.other_report_private_usage,
            ),
        )
        expected: list[t.JsonValue] = [
            environment.model_dump(mode="json", by_alias=True)
            for environment in environments
        ]
        payload: t.JsonMapping = {
            "project": {
                "name": workspace.repository.distribution,
                "version": "0.1.0",
                "dependencies": [],
            },
            "dependency-groups": {"codegen": [u.Tests.flext_source(config.Infra.name)]},
            "tool": {"pyright": {"executionEnvironments": expected}},
        }
        source = u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload))
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            source, encoding=c.DEFAULT_ENCODING
        )
        u.Tests.initialize_git_repo(tmp_path)
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        target = m.Infra.RepositoryConformTarget(
            repository=workspace.repository,
            root=tmp_path,
            toolchain_root=tmp_path,
            make_profile=workspace.repository.role,
            canonical_project_name=workspace.repository.distribution,
            ci_enabled=False,
            gascity_enabled=False,
        )
        inputs = FlextInfraCodegenConformExecute.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=config.Infra.codegen,
            tooling_runtime=None,
            managed_artifacts=tm.ok(
                u.Infra.snapshot_project_managed_artifacts(tmp_path)
            ),
        )
        first = tm.ok(
            FlextInfraCodegenConformExecute.compose_project_artifact(
                tmp_path,
                c.PYPROJECT_FILENAME,
                source,
                render_inputs=inputs,
            )
        )
        first_tools = u.Tests.toml_mapping(u.Tests.toml_payload(first)["tool"])
        first_pyright = u.Tests.toml_mapping(first_tools["pyright"])
        tm.that(first_pyright["executionEnvironments"], eq=expected)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(first, encoding=c.DEFAULT_ENCODING)
        second = tm.ok(
            FlextInfraCodegenConformExecute.compose_project_artifact(
                tmp_path,
                c.PYPROJECT_FILENAME,
                first,
                render_inputs=inputs,
            )
        )
        second_tools = u.Tests.toml_mapping(u.Tests.toml_payload(second)["tool"])
        second_pyright = u.Tests.toml_mapping(second_tools["pyright"])
        tm.that(second_pyright["executionEnvironments"], eq=expected)
        tm.that(second, eq=first)

    def test_leaf_conformance_preserves_parent_workspace_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """A generated leaf remains usable from its declared parent workspace."""
        parent = tmp_path / "parent"
        root = parent / "member"
        root.mkdir(parents=True)
        (parent / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "parent"\nversion = "1.0"\n'
            "dependencies = []\n"
            '[tool.uv.workspace]\nmembers = ["member"]\n',
            encoding="utf-8",
        )
        workspace = u.Tests.workspace_spec(
            self._repository("member", role=c.Infra.MakeProfile.STANDALONE, path="."),
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "member"\nversion = "1.0"\n'
                'requires-python = ">=3.13"\ndependencies = []\n',
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        (root / c.PYPROJECT_FILENAME).write_text(rendered, encoding="utf-8")
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "pip",
                    "install",
                    "--dry-run",
                    "--offline",
                    "--python",
                    sys.executable,
                    "-r",
                    str(root / c.PYPROJECT_FILENAME),
                ],
                cwd=parent,
            ),
        )
        tm.fail((root / "uv.lock").exists())
        tm.fail((parent / "uv.lock").exists())

    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_global_constraints_apply_without_direct_runtime_requirements(
        self,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Every profile receives SSOT constraints even for indirect dependencies."""
        content = (
            '[project]\nname = "workspace"\nversion = "1.2.3"\ndependencies = []\n'
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                content,
                workspace=self._workspace(role=profile),
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        uv_config = u.Tests.toml_table_at(first, "tool", "uv")
        expected = list(config.Infra.codegen.toolchain.uv_constraint_dependencies)
        tm.that(expected, empty=False)
        tm.that(uv_config.get("constraint-dependencies", []), eq=expected)
        tm.that(u.Tests.toml_strings_at(first, "project", "dependencies"), eq=())
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=self._workspace(role=profile),
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(second, eq=first)

    @staticmethod
    def test_custom_entry_point_groups_survive_conformance() -> None:
        """Plugin registrations remain owned by their declaring distribution."""
        rendered = '[project]\nname = "sample"\n'
        live = (
            '[project]\nname = "sample"\n'
            '[project.entry-points."example.plugins"]\n'
            'sample = "sample.plugin:main"\n'
        )

        overlaid = tm.ok(u.Infra.overlay_preserved(rendered, live))

        tm.that(
            u.Tests.toml_table_at(
                overlaid,
                "project",
                "entry-points",
                "example.plugins",
            )["sample"],
            eq="sample.plugin:main",
        )

    @staticmethod
    @pytest.mark.parametrize("live_readme", [None, "docs/consumer.md"])
    def test_custom_metadata_preserves_authored_absence(
        live_readme: t.StrippedStr | None,
    ) -> None:
        """A scaffold default cannot introduce an authored resource requirement."""
        preserved = ("readme",)
        scaffold_readme = config.Infra.codegen.scaffold.project.readme
        rendered = (
            '[project]\nname = "sample"\n'
            f"readme = {tm.ok(u.Cli.json_dumps(scaffold_readme))}\n"
        )
        live = '[project]\nname = "sample"\n'
        if live_readme is not None:
            live += f"readme = {tm.ok(u.Cli.json_dumps(live_readme))}\n"

        first = tm.ok(
            u.Infra.overlay_preserved(rendered, live, preserve_project_keys=preserved),
        )
        project = u.Tests.toml_table_at(first, "project")
        tm.that("readme" in project, eq=live_readme is not None)
        tm.that(project.get("readme"), eq=live_readme)
        second = tm.ok(
            u.Infra.overlay_preserved(rendered, first, preserve_project_keys=preserved),
        )
        tm.that(second, eq=first)

    @staticmethod
    def test_new_project_keeps_scaffold_defaults_at_a_fixed_point() -> None:
        """Initial creation retains defaults without changing the next projection."""
        preserved = ("readme",)
        readme = config.Infra.codegen.scaffold.project.readme
        rendered = (
            f'[project]\nname = "sample"\nreadme = {tm.ok(u.Cli.json_dumps(readme))}\n'
        )
        first = tm.ok(
            u.Infra.overlay_preserved(rendered, None, preserve_project_keys=preserved),
        )
        tm.that(u.Tests.toml_table_at(first, "project")["readme"], eq=readme)
        second = tm.ok(
            u.Infra.overlay_preserved(rendered, first, preserve_project_keys=preserved),
        )
        tm.that(second, eq=first)

    @staticmethod
    def test_custom_metadata_outside_the_render_is_not_removed() -> None:
        """An authored dynamic version is not replaced by a static scaffold value."""
        preserved = ("version",)
        rendered = '[project]\nname = "sample"\nversion = "1.2.3"\n'
        live = '[project]\nname = "sample"\ndynamic = ["version"]\n'
        first = tm.ok(
            u.Infra.overlay_preserved(rendered, live, preserve_project_keys=preserved),
        )
        project = u.Tests.toml_table_at(first, "project")
        tm.fail("version" in project)
        tm.that(project["dynamic"], eq=["version"])
        second = tm.ok(
            u.Infra.overlay_preserved(rendered, first, preserve_project_keys=preserved),
        )
        tm.that(second, eq=first)

    @staticmethod
    @pytest.mark.parametrize("invalid_surface", ["rendered", "live"])
    def test_overlay_retains_native_toml_failure_context(
        invalid_surface: str,
    ) -> None:
        """A parse failure identifies its input and retains the native cause."""
        valid = "[project]\n"
        invalid = "[project]\nkey =\n"
        result = u.Infra.overlay_preserved(
            invalid if invalid_surface == "rendered" else valid,
            invalid if invalid_surface == "live" else valid,
        )
        tm.fail(result, has=f"{invalid_surface} pyproject is not valid TOML")
        native = tm.not_none(result.exception)
        tm.that(type(native).__name__, eq="TOMLDecodeError")
        tm.that(result.error, has=str(native))
        tm.that(result.error, has=f"line {len(invalid.splitlines())}")

    @staticmethod
    def test_overlay_defaults_only_the_omitted_policy() -> None:
        """Explicit empty policies survive default resolution of the other policy."""
        spec = next(
            item
            for item in config.Infra.codegen.managed_file_specs
            if item.path.as_posix() == c.PYPROJECT_FILENAME
        )
        project_key = spec.preserve_project_keys[0]
        tool_table = spec.managed_tool_tables[0]
        rendered = (
            f'[project]\n{project_key} = "rendered"\n'
            f'[tool.{tool_table}]\nvalue = "rendered"\n'
        )
        live = (
            f'[project]\n{project_key} = "live"\n[tool.{tool_table}]\nvalue = "live"\n'
        )
        project_override = tm.ok(
            u.Infra.overlay_preserved(rendered, live, preserve_project_keys=()),
        )
        tm.that(
            u.Tests.toml_table_at(project_override, "project")[project_key],
            eq="rendered",
        )
        tm.that(
            u.Tests.toml_table_at(project_override, "tool", *tool_table.split("."))[
                "value"
            ],
            eq="rendered",
        )
        tool_override = tm.ok(
            u.Infra.overlay_preserved(rendered, live, managed_tool_tables=()),
        )
        tm.that(
            u.Tests.toml_table_at(tool_override, "project")[project_key],
            eq="live",
        )
        tm.that(
            u.Tests.toml_table_at(tool_override, "tool", *tool_table.split("."))[
                "value"
            ],
            eq="live",
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("table_path", "key", "expected"),
        [
            (
                ("ruff", "lint"),
                "select",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "select", list[str]
                ),
            ),
            (
                ("ruff", "lint"),
                "extend-safe-fixes",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "extend-safe-fixes", list[str]
                ),
            ),
            (
                ("ruff", "lint"),
                "unfixable",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff.lint", "unfixable", list[str]
                ),
            ),
            (
                ("coverage", "report"),
                "exclude_also",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "coverage.report", "exclude_also", list[str]
                ),
            ),
            (
                ("coverage", "run"),
                "omit",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "coverage.run", "omit", list[str]
                ),
            ),
            (
                ("pytest", "ini_options"),
                "addopts",
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "pytest.ini_options", "addopts", list[str]
                ),
            ),
            (
                ("pytest", "ini_options"),
                "markers",
                config.Infra.tooling.tools.pytest.standard_markers,
            ),
        ],
    )
    def test_overlay_replaces_duplicated_managed_lists(
        table_path: t.StrSequence,
        key: str,
        expected: t.StrSequence,
    ) -> None:
        """Replace stale multiplicity without changing SSOT or CUSTOM tables."""
        header = f'[project]\nname = "workspace"\n[tool.{".".join(table_path)}]\n'
        rendered = header + f"{key} = {tm.ok(u.Cli.json_dumps(list(expected)))}\n"
        live = (
            header
            + f"{key} = {tm.ok(u.Cli.json_dumps([*expected, *expected]))}\n"
            + '[tool.recovery_regression]\nvalue = "custom"\n'
        )

        first = tm.ok(u.Infra.overlay_preserved(rendered, live))

        tm.that(
            u.Tests.toml_strings_at(first, "tool", *table_path, key),
            eq=tuple(expected),
        )
        tm.that(
            u.Tests.toml_table_at(first, "tool", "recovery_regression")["value"],
            eq="custom",
        )
        tm.that(tm.ok(u.Infra.overlay_preserved(rendered, first)), eq=first)

    @pytest.mark.parametrize("declare_optional", [False, True])
    def test_deptry_dev_groups_follow_declared_optional_groups(
        self,
        *,
        declare_optional: bool,
    ) -> None:
        """PEP 735 groups never create references to absent PEP 621 extras."""
        policy = u.Infra.native_tool_setting(
            config.Infra.tooling,
            "deptry",
            "optional_dependencies_dev_groups",
            list[str],
        )
        optional: t.JsonDict = {
            group: ["requests"] for group in policy if declare_optional
        }
        source = u.Cli.toml_dumps(
            u.Cli.toml_document_from_mapping({
                "project": {
                    "name": "workspace",
                    "dependencies": [],
                    "optional-dependencies": optional,
                },
                "dependency-groups": {str(c.Infra.DEV): ["pytest"]},
                "tool": {
                    "deptry": {
                        "optional_dependencies_dev_groups": ["absent-fixture-extra"],
                    },
                },
            }),
        )
        workspace = self._workspace()
        resolution = self._uv_resolution(config.Infra.codegen.toolchain)
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=resolution,
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(
                conformed,
                "tool",
                "deptry",
                "optional_dependencies_dev_groups",
            ),
            eq=tuple(group for group in policy if group in optional),
        )
        tm.that(
            u.Tests.toml_table_at(conformed, "project", "optional-dependencies"),
            eq=optional,
        )
        repeated = tm.ok(
            u.Infra.pyproject_conform(
                conformed,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=resolution,
            ),
        )
        tm.that(repeated, eq=conformed)

    def test_custom_typing_and_feature_extras_survive_conformance(self) -> None:
        """CUSTOM PEP 621 extras survive projection and dependency normalization."""
        live = (
            '[project]\nname = "workspace"\nversion = "1.2.3"\n'
            'description = "custom project"\ndependencies = []\n'
            "[project.optional-dependencies]\n"
            'typings = ["types-requests>=2.0"]\nfeature = ["requests"]\n'
        )
        rendered = '[project]\nname = "workspace"\nversion = "0.0.0"\n'
        overlaid = tm.ok(u.Infra.overlay_preserved(rendered, live))
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                overlaid,
                workspace=self._workspace(),
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        original = u.Tests.toml_mapping(u.Tests.toml_payload(live)["project"])
        project = u.Tests.toml_mapping(
            u.Tests.toml_payload(conformed)["project"],
        )
        tm.that(project["optional-dependencies"], eq=original["optional-dependencies"])
        tm.that(project["version"], eq=original["version"])
        tm.that(project["description"], eq=original["description"])
        repeated = tm.ok(u.Infra.overlay_preserved(rendered, conformed))
        tm.that(
            u.Tests.toml_mapping(u.Tests.toml_payload(repeated)["project"])[
                "optional-dependencies"
            ],
            eq=original["optional-dependencies"],
        )

    @pytest.mark.parametrize(
        "role",
        [
            c.Infra.MakeProfile.STANDALONE,
            c.Infra.MakeProfile.WORKSPACE,
        ],
    )
    def test_generated_dev_floors_follow_publication_topology(
        self,
        tmp_path: Path,
        role: c.Infra.MakeProfile,
    ) -> None:
        """All profiles retain Git floors; only the root selects local paths."""
        provider = u.Tests.provider()
        branch = u.Tests.provider_branch()
        floors = tuple(config.Infra.codegen.scaffold.project.dev)
        internal = tuple(
            name
            for floor in floors
            if (name := u.Infra.dep_name(floor))
            and name.startswith("flext-")
            and floor.strip() == name
        )
        is_root = role is c.Infra.MakeProfile.WORKSPACE
        workspace = u.Tests.workspace_spec(
            self._repository("consumer", role=role, path="."),
            subprojects=(
                tuple(
                    self._repository(
                        name,
                        role=c.Infra.MakeProfile.STANDALONE,
                        path=name,
                    )
                    for name in internal
                )
                if is_root
                else ()
            ),
        )
        for member in workspace.subprojects:
            path = tmp_path / member.path / c.PYPROJECT_FILENAME
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'[project]\nname = "{member.distribution}"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
        dependency_source = m.Infra.WorkspaceIntegrationSpec(
            provider=provider.name,
            branch=branch,
            base_url=provider.base_url,
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "consumer"\ndependencies = []\n',
                workspace=workspace,
                required_dev_dependencies=floors,
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
                options=u.Infra.PyprojectConformOptions(flext_line=dependency_source),
            ),
        )
        dev = u.Tests.toml_strings_at(first, "dependency-groups", "dev")
        sources = u.Tests.toml_mapping(
            u.Tests.toml_table_at(first, "tool", "uv").get("sources", {}),
        )
        # A member render is context-independent: attached to a superproject
        # or standalone, it carries git-sourced floors and no fleet source, so
        # it installs from a clone. Only the workspace root redirects members.
        for name in internal:
            expected = (
                f"{name} @ git+{dependency_source.base_url}/{name}.git"
                f"@{dependency_source.branch}"
            )
            tm.ok(expected in dev)
            tm.that(name in sources, eq=is_root)
            if is_root:
                member = next(
                    ref for ref in workspace.subprojects if ref.distribution == name
                )
                tm.that(
                    sources[name],
                    eq={"path": member.path.as_posix(), "editable": member.editable},
                )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=workspace,
                required_dev_dependencies=floors,
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
                options=u.Infra.PyprojectConformOptions(flext_line=dependency_source),
            ),
        )
        tm.that(second, eq=first)

    def test_generated_floor_source_does_not_source_custom_dependencies(self) -> None:
        """Provider facts apply only to generated floors; bare deps stay untouched."""
        provider = u.Tests.provider()
        unattached = config.Infra.codegen.infra_repository.distribution
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "consumer"\ndependencies = ["{unattached}"]\n',
            workspace=u.Tests.workspace_spec(
                self._repository(
                    "consumer",
                    role=c.Infra.MakeProfile.STANDALONE,
                    path=".",
                ),
            ),
            required_dev_dependencies=(),
            options=u.Infra.PyprojectConformOptions(
                flext_line=m.Infra.WorkspaceIntegrationSpec(
                    provider=provider.name,
                    branch=u.Tests.provider_branch(),
                    base_url=provider.base_url,
                ),
            ),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        rendered = tm.ok(result)
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(unattached,),
        )

    def test_generated_floor_preserves_existing_inline_source(self) -> None:
        """A bare floor cannot replace the live dependency's declared Git source."""
        provider = u.Tests.provider()
        floor = config.Infra.codegen.infra_repository.distribution
        declared = (
            f"{floor} @ git+{provider.base_url}/custom-{floor}.git"
            f"@{u.Tests.provider_branch()}-custom"
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "consumer"\ndependencies = []\n'
                f'[dependency-groups]\ndev = ["{declared}"]\n',
                workspace=u.Tests.workspace_spec(
                    self._repository(
                        "consumer",
                        role=c.Infra.MakeProfile.STANDALONE,
                        path=".",
                    ),
                ),
                required_dev_dependencies=(floor,),
                options=u.Infra.PyprojectConformOptions(
                    flext_line=m.Infra.WorkspaceIntegrationSpec(
                        provider=provider.name,
                        branch=u.Tests.provider_branch(),
                        base_url=provider.base_url,
                    ),
                ),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "dependency-groups", "dev"),
            eq=(declared,),
        )
