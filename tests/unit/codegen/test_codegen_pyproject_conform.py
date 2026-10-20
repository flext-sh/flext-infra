"""Public behavior tests for topology-aware pyproject conformance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodegenPyprojectConform:
    """Tests for ``FlextInfraCodegenPyprojectConform``."""

    def test_workspace_provisions_member_toml_arrays(
        self,
        tmp_path: Path,
    ) -> None:
        """Member extras and included groups reach the root provisioning contract."""
        member = self._repository(
            "fixture-member",
            role=c.Infra.MakeProfile.STANDALONE,
            path="fixture-member",
        )
        workspace = u.Tests.workspace_spec(
            self._repository(
                "workspace",
                role=c.Infra.MakeProfile.WORKSPACE,
                path=".",
            ),
            subprojects=(member,),
        )
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                path,
                '[project]\nname = "fixture-member"\n'
                'dependencies = ["fixture-runtime>=1"]\n'
                "[project.optional-dependencies]\n"
                'feature = ["fixture-extra>=2"]\n'
                "[dependency-groups]\n"
                'base = ["fixture-tool>=3"]\n'
                'dev = [{include-group = "base"}, "fixture-checker>=4"]\n',
            ),
        )
        captured = tm.ok(
            u.Cli.atomic_read_binary_file_state(path, required=True),
        )
        options = u.Infra.PyprojectConformOptions(
            repository_root=tmp_path,
            member_declarations=(captured,),
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "workspace"\ndependencies = []\n',
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
                options=options,
            ),
        )
        dev = u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")
        tm.that(dev, has=["fixture-tool>=3", "fixture-checker>=4"])
        tm.that(workspace.integration, none=False)
        tm.that(
            dev,
            has=(
                f"{member.distribution}[feature] @ "
                f"git+{member.url}@{workspace.integration.branch}"
            ),
        )
        repeated = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
                options=options,
            ),
        )
        tm.that(repeated, eq=rendered)

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
        expected = [
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
        inputs = FlextInfraCodegenConform.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=config.Infra.codegen,
            tooling_runtime=None,
            managed_artifacts=tm.ok(
                u.Infra.snapshot_project_managed_artifacts(tmp_path)
            ),
        )
        first = tm.ok(
            FlextInfraCodegenConform.compose_project_artifact(
                tmp_path,
                c.PYPROJECT_FILENAME,
                source,
                render_inputs=inputs,
            )
        ).rendered
        first_tools = u.Tests.toml_mapping(u.Tests.toml_payload(first)["tool"])
        first_pyright = u.Tests.toml_mapping(first_tools["pyright"])
        tm.that(first_pyright["executionEnvironments"], eq=expected)
        (tmp_path / c.PYPROJECT_FILENAME).write_text(first, encoding=c.DEFAULT_ENCODING)
        second = tm.ok(
            FlextInfraCodegenConform.compose_project_artifact(
                tmp_path,
                c.PYPROJECT_FILENAME,
                first,
                render_inputs=inputs,
            )
        ).rendered
        second_tools = u.Tests.toml_mapping(u.Tests.toml_payload(second)["tool"])
        second_pyright = u.Tests.toml_mapping(second_tools["pyright"])
        tm.that(second_pyright["executionEnvironments"], eq=expected)
        tm.that(second, eq=first)

    @staticmethod
    def _repository(
        distribution: str,
        *,
        role: c.Infra.MakeProfile,
        path: str,
    ) -> m.Infra.RepositoryRef:
        provider = u.Tests.provider()
        return m.Infra.RepositoryRef(
            name=distribution,
            distribution=distribution,
            url=f"{provider.base_url}/{distribution}.git",
            path=Path(path),
            role=role,
            provider=provider.name,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=role is not c.Infra.MakeProfile.WORKSPACE,
            editable=role is not c.Infra.MakeProfile.WORKSPACE,
            read_only=False,
        )

    def _workspace(
        self,
        *,
        role: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE,
    ) -> m.Infra.WorkspaceSpec:
        return u.Tests.workspace_spec(
            self._repository("workspace", role=role, path="."),
            subprojects=(
                (
                    self._repository(
                        "flext-core",
                        role=c.Infra.MakeProfile.STANDALONE,
                        path="flext-core",
                    ),
                )
                if role is c.Infra.MakeProfile.STANDALONE
                else ()
            ),
        )

    @staticmethod
    def _uv_resolution(
        toolchain: p.Infra.ToolchainSpec,
    ) -> m.Infra.UvResolutionSpec:
        """Route the toolchain's uv resolver keys the way conform declares them.

        Returns:
            The resulting ``m.Infra.UvResolutionSpec``.

        """
        return m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )

    @staticmethod
    def _detached_dev_floors() -> t.StrSequence:
        """SSOT dev floors seeded for a project outside the workspace overlay.

        A source-less internal dependency is legal only for the workspace
        context root; every other project must carry its declared direct Git
        source (the scaffold seeds exactly this line), so the same SSOT floor
        set is rendered the way a real detached checkout declares it.

        Returns:
            The resulting ``t.StrSequence``.

        """
        branch = u.Tests.provider_branch()
        return tuple(
            (
                f"{floor} @ git+{u.Tests.WorktreeFixture.governed_repository_url(name)}"
                f"@{branch}"
                if (name := u.Infra.dep_name(floor))
                and name.startswith("flext-")
                and "@" not in floor
                else floor
            )
            for floor in config.Infra.codegen.scaffold.project.dev
        )

    def test_leaf_conformance_preserves_parent_workspace_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """A generated leaf remains usable from its declared parent workspace."""
        parent = tmp_path / "parent"
        root = parent / "member"
        root.mkdir(parents=True)
        (parent / "pyproject.toml").write_text(
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
        (root / "pyproject.toml").write_text(rendered, encoding="utf-8")
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
                    str(root / "pyproject.toml"),
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
        expected = [
            requirement
            for requirement in config.Infra.codegen.toolchain.uv_constraint_dependencies
            if u.Infra.dep_name(requirement) != "uv"
        ]
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

    @pytest.mark.parametrize("live_readme", [None, "docs/consumer.md"])
    def test_custom_metadata_preserves_authored_absence(
        self,
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

    @pytest.mark.parametrize("invalid_surface", ["rendered", "live"])
    def test_overlay_retains_native_toml_failure_context(
        self,
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
            for item in config.Infra.codegen.managed_files
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
            u.Tests.toml_table_at(project_override, "tool", tool_table)["value"],
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
            u.Tests.toml_table_at(tool_override, "tool", tool_table)["value"],
            eq="live",
        )

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
                u.Infra.native_tool_setting(
                    config.Infra.tooling, "pytest.ini_options", "markers", list[str]
                ),
            ),
        ],
    )
    def test_overlay_replaces_duplicated_managed_lists(
        self,
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
        declare_optional: bool,
    ) -> None:
        """PEP 735 groups never create references to absent PEP 621 extras."""
        policy = u.Infra.native_tool_setting(
            config.Infra.tooling, "deptry", "optional_dependencies_dev_groups", list[str]
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
                options=u.Infra.PyprojectConformOptions(
                    flext_line=dependency_source,
                    repository_root=tmp_path,
                ),
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
                options=u.Infra.PyprojectConformOptions(
                    flext_line=dependency_source,
                    repository_root=tmp_path,
                ),
            ),
        )
        tm.that(second, eq=first)

    def test_generated_floor_source_does_not_source_custom_dependencies(self) -> None:
        """Provider facts apply only to generated floors, not arbitrary bare deps."""
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
        tm.fail(result, has="internal dependency declares no direct git source")

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

    def test_standalone_requires_declared_git_source(self) -> None:
        """A source-less internal dependency outside the workspace overlay fails.

        The workspace attaches only flext-core, whose declaration supplies the
        source; the infrastructure distribution is internal and unattached.
        """
        unattached = config.Infra.codegen.infra_repository.distribution
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{unattached}"]\n',
            workspace=self._workspace(role=c.Infra.MakeProfile.STANDALONE),
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        tm.fail(result, has="internal dependency declares no direct git source")

    def test_standalone_canonicalizes_the_declared_git_source(self) -> None:
        """The declared requirement line is the only URL and branch authority."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        member = workspace.subprojects[0]
        declared = (
            f"{member.distribution} @ git+{member.url}@{u.Tests.provider_branch()}"
        )
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{declared}"]\n',
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        rendered = tm.ok(result)
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(declared,),
        )

    def test_conformance_deletes_empty_uv_constraint_key(self) -> None:
        """A constraint set holding only the uv pin removes the key entirely."""
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"uv_link_mode": "copy", "uv_constraint_dependencies": ("uv>=0",)},
        )
        source = """[project]
name = "external-consumer"
dependencies = ["requests>=2"]

[tool.uv]
constraint-dependencies = ["uv>=0"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )

        uv_config = u.Tests.toml_table_at(conformed, "tool", "uv")
        tm.that(uv_config["link-mode"], eq=toolchain.uv_link_mode)
        tm.ok("constraint-dependencies" not in uv_config)

    def test_standalone_rejects_non_https_manifest_provenance(self) -> None:
        """Test standalone rejects non https manifest provenance."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        member = workspace.subprojects[0]
        declared = (
            f"{member.distribution} @ git+{member.url}@{u.Tests.provider_branch()}"
        )
        invalid_workspace = workspace.model_copy(
            update={
                "subprojects": (
                    member.model_copy(
                        update={"url": "git@github.com:flext-sh/flext-core.git"},
                    ),
                ),
            },
        )
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{declared}"]\n',
            workspace=invalid_workspace,
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        tm.fail(result, has="internal dependency manifest provenance must be HTTPS")

    def test_full_conformance_is_idempotent_without_uv_version_pin(self) -> None:
        """Test full conformance is idempotent without uv version pin."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"uv_link_mode": "copy"},
        )
        required_dev = self._detached_dev_floors()
        declared_member_source = (
            f"flext-core @ git+{workspace.subprojects[0].url}@"
            f"{u.Tests.provider_branch()}"
        )
        source = f"""[project]
name = "external-consumer"
dependencies = ["{declared_member_source}", "requests>=2"]

[dependency-groups]
dev = ["custom-tool>=1"]

[tool.uv]
required-version = ">=0"
exclude-newer = "7 days"
exclude-newer-package = {{ cryptography = false }}
[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=required_dev,
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=workspace,
                required_dev_dependencies=required_dev,
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        uv = u.Tests.toml_table_at(first, "tool", "uv")
        tm.that(second, eq=first)
        tm.that(uv["link-mode"], eq=toolchain.uv_link_mode)
        # The supply-chain cooldown is exterminated fleet-wide (flext-fphyv):
        # uv resolves every version published up to now, and a removed
        # declaration exterminates the keys everywhere (flext-gzfd2 class), so
        # pre-existing projections carrying the old cap converge to no keys.
        tm.ok("exclude-newer" not in uv)
        tm.ok("exclude-newer-package" not in uv)
        tm.ok("required-version" not in uv)
        tm.that(
            "python-interpreter-path"
            not in u.Tests.toml_table_at(first, "tool", "pyrefly"),
            eq=True,
        )
        dev_group = u.Tests.toml_strings_at(first, "dependency-groups", "dev")
        tm.ok("custom-tool>=1" in dev_group)
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
        rendered_names = {u.Infra.dep_name(requirement) for requirement in dev_group}
        for requirement in required_dev:
            tm.ok(u.Infra.dep_name(requirement) in rendered_names)
        tm.that(
            u.Tests.toml_strings_at(first, "project", "dependencies")[0],
            eq=(
                f"{workspace.subprojects[0].distribution} @ "
                f"git+{workspace.subprojects[0].url}@{u.Tests.provider_branch()}"
            ),
        )

    def test_conformance_never_writes_the_project_version(self) -> None:
        """The release protocol is the only version writer; conform reads only."""
        workspace = self._workspace().model_copy(
            update={"project": u.Tests.project_spec("external-consumer")},
        )
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "external-consumer"\n'
                'version = "0.0.1"\ndependencies = []\n',
                workspace=workspace,
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(u.Tests.toml_table_at(conformed, "project")["version"], eq="0.0.1")

    def test_ssot_required_dev_floor_replaces_stale_same_name_pin(self) -> None:
        """Toolchain required_dev floors win over older same-package member pins."""
        workspace = self._workspace()
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
                workspace=workspace,
                required_dev_dependencies=("rumdl>=0.2.45",),
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        dev_group = u.Tests.toml_strings_at(conformed, "dependency-groups", "dev")
        tm.ok("rumdl>=0.2.45" in dev_group)
        tm.ok("rumdl>=0.2.46" not in dev_group)
        tm.ok("custom-tool>=1" in dev_group)

    def test_conform_retires_dependency_edge_suppression(self) -> None:
        """Conformance preserves real declared edges and removes retired suppression."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        dependency = "example-dependency>=1"
        exclusion = '{ package = {name="example-dependency"}, dependencies=["other"] }'
        source = f"""[project]
name = "{workspace.repository.distribution}"
dependencies = ["{dependency}"]
[tool.uv]
exclude-dependencies = [{exclusion}]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(
                    config.Infra.codegen.toolchain,
                ),
            ),
        )
        uv = u.Tests.toml_table_at(conformed, "tool", "uv")
        tm.ok("exclude-dependencies" not in uv)
        project = u.Tests.toml_table_at(conformed, "project")
        tm.ok(dependency in u.Tests.toml_strings(project["dependencies"]))

    @staticmethod
    def test_workspace_root_keeps_dependency_resolution_unsuppressed(
        tmp_path: Path,
    ) -> None:
        """Adding a declared member never manufactures dependency-edge exclusions."""
        rendered = u.Tests.scaffold_text(
            tmp_path / "fixture-project",
            c.PYPROJECT_FILENAME,
            members=("fixture-member",),
        )
        uv = u.Tests.toml_table_at(rendered, "tool", "uv")
        tm.ok("exclude-dependencies" not in uv)

    @staticmethod
    def test_scaffold_omits_diagnostic_suppression_catalogs(tmp_path: Path) -> None:
        """The shipped Jinja surface cannot restore retired exemption tables."""
        rendered = u.Tests.scaffold_text(
            tmp_path / "no-suppression-project",
            c.PYPROJECT_FILENAME,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
        )
        lint = u.Tests.toml_table_at(rendered, "tool", "ruff", "lint")
        for key in (
            "extend-ignore",
            "per-file-ignores",
            "extend-per-file-ignores",
        ):
            tm.that(lint, lacks=key)
        tm.that(
            lint["ignore"], eq=sorted(config.Infra.tooling.tools.ruff.lint.rule_owners)
        )
        mypy = u.Tests.toml_table_at(rendered, "tool", "mypy")
        policy = config.Infra.tooling.tools.mypy
        if policy.ruling_disable_error_codes:
            tm.that(
                mypy["disable_error_code"],
                eq=list(policy.ruling_disable_error_codes),
            )
        else:
            tm.that(mypy, lacks="disable_error_code")
        tm.that(mypy, lacks="ignore_errors")
        for entry in u.Tests.toml_list(mypy.get("overrides", [])):
            override = u.Tests.toml_mapping(entry)
            tm.that(override, lacks="disable_error_code")
            tm.that(override, lacks="ignore_errors")

    @staticmethod
    def test_scaffold_mypy_policy_matches_ssot_and_converges(tmp_path: Path) -> None:
        """The actual Jinja scaffold preserves typed policy on repeated rendering."""
        root = tmp_path / "fixture-project"
        surface = c.Infra.CodegenConformSurface.PYPROJECT
        first = u.Tests.scaffold_text(root, c.PYPROJECT_FILENAME, what=surface)
        mypy = u.Tests.toml_table_at(first, "tool", "mypy")
        policy = config.Infra.tooling.tools.mypy
        if policy.ruling_disable_error_codes:
            tm.that(
                mypy["disable_error_code"],
                eq=list(policy.ruling_disable_error_codes),
            )
        else:
            tm.that(mypy, lacks="disable_error_code")
        for key, value in u.Infra.native_tool_settings(
            config.Infra.tooling, "mypy"
        ).items():
            tm.that(mypy[key], eq=value)
        tm.that(
            u.Tests.toml_table_at(first, "tool", "pydantic-mypy"),
            eq=u.Infra.native_tool_settings(
                config.Infra.tooling, "pydantic-mypy"
            ),
        )
        tm.that(
            u.Tests.scaffold_text(root, c.PYPROJECT_FILENAME, what=surface),
            eq=first,
        )

    @staticmethod
    @pytest.mark.parametrize("members", [(), ("fixture-member",)])
    def test_scaffold_pyrefly_policy_matches_ssot_and_converges(
        tmp_path: Path,
        members: t.StrSequence,
    ) -> None:
        """Both repository roles render each declared diagnostic exactly once."""
        root = tmp_path / "fixture-project"
        surface = c.Infra.CodegenConformSurface.PYPROJECT
        first = u.Tests.scaffold_text(
            root,
            c.PYPROJECT_FILENAME,
            members=members,
            what=surface,
        )
        tm.that(
            u.Tests.toml_table_at(first, "tool", "pyrefly", "errors"),
            eq=u.Infra.native_tool_settings(
                config.Infra.tooling, "pyrefly.errors"
            ),
        )
        tm.that(
            u.Tests.scaffold_text(
                root,
                c.PYPROJECT_FILENAME,
                members=members,
                what=surface,
            ),
            eq=first,
        )

    @staticmethod
    def test_pyrefly_diagnostic_pairs_elect_the_last_declared_value() -> None:
        """A later layer replaces a diagnostic through the common registry."""
        registry = dict(config.Infra.tooling.settings)
        registry["pyrefly.errors"] = (
            ("bad-argument-count", "warn"),
            ("bad-argument-count", "error"),
        )
        validated = m.Infra.ToolConfigDocument.model_validate({
            **config.Infra.tooling.model_dump(by_alias=True),
            "settings": registry,
        })
        tm.that(
            u.Infra.native_tool_settings(validated, "pyrefly.errors"),
            eq={"bad-argument-count": "error"},
        )

    @staticmethod
    @pytest.mark.parametrize("selection", ["reordered", "subset", "empty"])
    def test_pyrefly_policy_preserves_valid_diagnostic_selections(
        selection: str,
    ) -> None:
        """Validation does not freeze the selected diagnostic set or its order."""
        policy = config.Infra.tooling
        errors = tuple(policy.settings["pyrefly.errors"])
        if selection == "reordered":
            selected = tuple(reversed(errors))
        elif selection == "subset":
            selected = errors[::2]
        else:
            selected = ()
        registry = dict(policy.settings)
        registry["pyrefly.errors"] = selected
        validated = m.Infra.ToolConfigDocument.model_validate({
            **policy.model_dump(by_alias=True),
            "settings": registry,
        })
        tm.that(tuple(validated.settings["pyrefly.errors"]), eq=selected)

    @staticmethod
    def _assert_unmanaged_tool_tables_survive(
        live: str,
        rendered: str,
        document: t.JsonMapping,
    ) -> None:
        """`ruff` is managed: the rendered projection wins over the live file.

        `bandit` is unmanaged and live-only, so it survives untouched.
        """
        tool = tm.not_none(u.Cli.toml_mapping_child(document, "tool"))
        ruff = tm.not_none(u.Cli.toml_mapping_child(tool, "ruff"))
        bandit = tm.not_none(u.Cli.toml_mapping_child(tool, "bandit"))
        live_tool = u.Tests.toml_table_at(live, "tool")
        rendered_payload = tm.not_none(u.Cli.toml_mapping_from_text(rendered))
        rendered_tool = tm.not_none(u.Cli.toml_mapping_child(rendered_payload, "tool"))
        rendered_ruff = tm.not_none(u.Cli.toml_mapping_child(rendered_tool, "ruff"))
        tm.that(ruff["line-length"], eq=rendered_ruff["line-length"])
        live_bandit = u.Cli.toml_mapping_child(live_tool, "bandit")
        tm.that(bandit["skips"], eq=(live_bandit or {}).get("skips"))

    def test_overlay_preserves_custom_scripts_and_unmanaged_tools(self) -> None:
        """Package requirements survive without restoring stale profile pins."""
        rendered = """[project]
name = "flext"
dependencies = ["pydantic>=2"]
scripts = {flext = "flext.cli:main"}

[dependency-groups]
codegen = [
    "flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev",
]
dev = ["rumdl>=0.2.45"]

[tool.ruff]
line-length = 88
"""
        live = """[project]
name = "flext"
dependencies = [
    "pydantic>=1",
    "beartype>=0.22",
    "custom-runtime[feature]>=2; python_version < '3.14'",
    "custom-runtime[feature]>=3; python_version >= '3.14'",
]
scripts = {flext = "flext.workspace:main", flext-dev = "flext.dev:main"}

[dependency-groups]
codegen = ["obsolete-codegen"]
dev = ["rumdl>=0.2.40", "custom-audit>=1"]

[tool.ruff]
line-length = 120

[tool.bandit]
skips = ["B101"]
"""
        live_document = tm.not_none(u.Cli.toml_parse_text(live))
        u.Infra.sync_member_dev_provenance(
            live_document,
            custom=(),
            group=c.Infra.DependencyGroup.CODEGEN,
        )
        live = u.Cli.toml_dumps(live_document)
        first = tm.ok(u.Infra.overlay_preserved(rendered, live))
        document = tm.not_none(u.Cli.toml_mapping_from_text(first))
        project = tm.not_none(u.Cli.toml_mapping_child(document, "project"))
        expected_requirements = frozenset({
            "pydantic>=2",
            "beartype>=0.22",
            "custom-runtime[feature]>=2; python_version < '3.14'",
            "custom-runtime[feature]>=3; python_version >= '3.14'",
        })
        tm.that(
            frozenset(u.Tests.toml_strings_at(first, "project", "dependencies")),
            eq=expected_requirements,
        )
        tm.that(tm.ok(u.Infra.overlay_preserved(rendered, first)), eq=first)
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=self._workspace(),
                required_dev_dependencies=("rumdl>=0.2.45",),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(
            frozenset(
                u.Tests.toml_strings_at(conformed, "project", "dependencies"),
            ),
            eq=expected_requirements,
        )
        repeated = tm.ok(u.Infra.overlay_preserved(rendered, conformed))
        tm.that(
            frozenset(
                u.Tests.toml_strings_at(repeated, "project", "dependencies"),
            ),
            eq=expected_requirements,
        )
        # Membership alone hides a required-first / alphabetical oscillation.
        # Exercise both public owners; neither may reorder the other's output.
        canonical_dependencies = u.Tests.toml_strings_at(
            conformed,
            "project",
            "dependencies",
        )
        tm.that(
            u.Tests.toml_strings_at(first, "project", "dependencies"),
            eq=canonical_dependencies,
        )
        tm.that(
            u.Tests.toml_strings_at(repeated, "project", "dependencies"),
            eq=canonical_dependencies,
        )
        dev = u.Tests.toml_strings_at(conformed, "dependency-groups", "dev")
        tm.ok("custom-audit>=1" in dev)
        tm.ok("rumdl>=0.2.45" in dev)
        tm.ok("rumdl>=0.2.40" not in dev)
        tm.that(
            tuple(u.Tests.toml_strings_at(first, "dependency-groups", "codegen")),
            eq=(
                (
                    "flext-infra @ git+https://github.com/flext-sh/flext-infra.git"
                    "@0.12.0-dev"
                ),
            ),
        )
        tm.ok("flext-dev" in u.Tests.toml_mapping(project["scripts"]))
        self._assert_unmanaged_tool_tables_survive(live, rendered, document)
