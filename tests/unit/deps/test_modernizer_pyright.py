"""Pyright phase tests for deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.deps import (
    FlextInfraEnsurePyrightConfigPhase,
    FlextInfraPyprojectModernizer,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, e, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsModernizerPyright:
    """Declarative tests for generated Pyright configuration."""

    @staticmethod
    @pytest.mark.parametrize("mode", ["basic", c.ParserBooleanToken.OFF])
    def test_native_options_cannot_weaken_strict_analysis(
        tool_config_document: m.Infra.ToolConfigDocument,
        mode: str,
    ) -> None:
        """Native option deltas cannot weaken the required analysis contract."""
        payload = {
            **tool_config_document.model_dump(
                by_alias=True, exclude_computed_fields=True
            ),
            "settings": {
                **tool_config_document.settings,
                c.Infra.PYRIGHT: (
                    *tool_config_document.settings[c.Infra.PYRIGHT],
                    ("typeCheckingMode", mode),
                ),
            },
        }
        with pytest.raises(e.PydanticValidationError, match="strict"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    def test_native_pairs_can_restore_strict_analysis(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """The final native pair elects the analysis mode before validation."""
        expected = u.Infra.native_tool_settings(tool_config_document, c.Infra.PYRIGHT)[
            "typeCheckingMode"
        ]
        payload = {
            **tool_config_document.model_dump(
                by_alias=True, exclude_computed_fields=True
            ),
            "settings": {
                **tool_config_document.settings,
                c.Infra.PYRIGHT: (
                    *tool_config_document.settings[c.Infra.PYRIGHT],
                    ("typeCheckingMode", c.ParserBooleanToken.OFF),
                    ("typeCheckingMode", expected),
                ),
            },
        }
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        tm.that(
            u.Infra.native_tool_settings(validated, c.Infra.PYRIGHT)[
                "typeCheckingMode"
            ],
            eq=expected,
        )

    @staticmethod
    def test_generic_pairs_preserve_types_and_semantic_array_order(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """New tool options round-trip through native TOML without new fields."""
        additions: t.SequenceOf[t.Pair[str, t.JsonValue]] = (
            ("defineConstant", {"FEATURE": True, "MODE": "validation"}),
            ("strict", ["src/z", "src/a"]),
        )
        selected = tool_config_document.model_copy(
            update={
                "settings": {
                    **tool_config_document.settings,
                    c.Infra.PYRIGHT: (
                        *tool_config_document.settings[c.Infra.PYRIGHT],
                        *additions,
                    ),
                }
            }
        )
        phase = FlextInfraEnsurePyrightConfigPhase(
            selected,
            codegen=config.Infra.codegen,
        )
        context = m.Infra.PyprojectAnalyzerContext(is_root=False)
        rendered = tm.ok(
            phase.render_source("[project]\nname='fixture'\n", context=context)
        )
        table = u.Tests.toml_table_at(rendered, "tool", "pyright")
        for key, value in additions:
            tm.that(table[key], eq=value)
        scalar_keys = [
            key
            for key, value in table.items()
            if not isinstance(value, Mapping)
            and not (
                isinstance(value, list) and value and isinstance(value[0], Mapping)
            )
        ]
        tm.that(scalar_keys, eq=sorted(scalar_keys))
        tm.that(tm.ok(phase.render_source(rendered, context=context)), eq=rendered)

    @staticmethod
    def test_editor_projection_preserves_other_tables_and_converges(
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """The editor projection replaces stale environment bindings and converges."""
        source = (
            "# Project-owned metadata\n"
            "[project]\nname='fixture'\nversion='0.1.0'\n"
            "[tool.unrelated]\nkeep='yes'\n"
            "[tool.pyright]\n"
            "venv='old-environment'\nvenvPath='../old-checkout'\n"
            "typeCheckingMode='off'\n"
        )
        phase = FlextInfraEnsurePyrightConfigPhase(
            tool_config_document,
            codegen=config.Infra.codegen,
        )
        context = m.Infra.PyprojectAnalyzerContext(is_root=False)
        first = tm.ok(phase.render_source(source, context=context))
        second = tm.ok(phase.render_source(first, context=context))
        tm.that(second, eq=first)
        document = tm.ok(u.Cli.toml_mapping_from_text_result(first))
        tools = u.Tests.toml_mapping(document["tool"])
        tm.that(tools["unrelated"], eq={"keep": c.ParserBooleanToken.YES})
        tm.that(document["project"], eq={"name": "fixture", "version": "0.1.0"})
        pyright = u.Tests.toml_mapping(tools["pyright"])
        tm.that(pyright["venv"], eq=c.Infra.ENVIRONMENT_DIRECTORY)
        tm.that(pyright["venvPath"], eq=".")
        for key, value in u.Infra.native_tool_settings(
            tool_config_document, c.Infra.PYRIGHT
        ).items():
            tm.that(pyright[key], eq=value)

    @staticmethod
    def _applied(
        tool_config_document: m.Infra.ToolConfigDocument,
        context: m.Infra.PyprojectAnalyzerContext,
    ) -> t.JsonMapping:
        """Apply the phase twice to an empty payload; return the converged table.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        project = context.repository_root if context.is_root else context.project_dir
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        phase = FlextInfraEnsurePyrightConfigPhase(
            tool_config_document,
            codegen=config.Infra.codegen,
        )
        changes = [phase.apply_payload(payload, context=context) for _ in range(2)]
        tm.that(changes[0], empty=False)
        tm.that(changes[1], empty=True)
        pyright = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["pyright"])
        tm.that(pyright["venv"], eq=c.Infra.ENVIRONMENT_DIRECTORY)
        environment_parent = u.type_adapter(str).validate_python(pyright["venvPath"])
        if project is None:
            tm.that(environment_parent, eq=".")
        else:
            tm.that((project / environment_parent).resolve(), eq=project.resolve())
        return pyright

    @staticmethod
    def _sample_project(tmp_path: Path, source_dir_name: str) -> Path:
        """Create one governed flext-sample project with a src package and manifest.

        Returns:
            The resulting ``Path``.

        """
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        project_dir = tmp_path / "flext-sample"
        source_dir = project_dir / source_dir_name / "flext_sample"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("", encoding="utf-8")
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='flext-sample'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(project_dir, "flext-sample")
        u.Tests.initialize_git_repo(project_dir)
        return project_dir

    @staticmethod
    def _workspace(tmp_path: Path, *members: str) -> None:
        """Declare one governed workspace root with governed member manifests."""
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        for member in members:
            package = tmp_path / member / "src" / member.replace("-", "_")
            package.mkdir(parents=True, exist_ok=True)
            (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
            (tmp_path / member / c.PYPROJECT_FILENAME).write_text(
                f"[project]\nname='{member}'\nversion='0.1.0'\n",
                encoding="utf-8",
            )
            u.Tests.write_project_beads_config(tmp_path / member, member)
        u.Tests.declare_workspace_projects(tmp_path, members)
        u.Tests.write_project_beads_config(tmp_path, "workspace")
        u.Tests.initialize_git_repo(tmp_path)

    @staticmethod
    def test_python_discovery_ignores_member_only_container(
        tmp_path: Path,
    ) -> None:
        """A directory containing only nested projects is not a root source tree."""
        root_source = tmp_path / "src"
        root_source.mkdir()
        (root_source / "root.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(tmp_path, "workspace")
        member = tmp_path / "apps" / "member"
        member_source = member / "src" / "member"
        member_source.mkdir(parents=True)
        (member / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='member'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        (member_source / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

        tm.that(
            u.Infra.discover_python_dirs(
                tmp_path,
                workspace_excluded_top_dirs=(
                    FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                        tmp_path,
                    ).unwrap()
                ),
            ),
            eq=["src"],
        )

    @staticmethod
    def test_python_discovery_uses_caller_resolved_exclusions(
        tmp_path: Path,
    ) -> None:
        """Honor the command-scoped topology projection without rediscovery."""
        included = tmp_path / "included"
        excluded = tmp_path / "excluded"
        for directory in (included, excluded):
            directory.mkdir()
            (directory / "module.py").write_text("VALUE = 1\n", encoding="utf-8")

        discovered = u.Infra.discover_python_dirs(
            tmp_path,
            workspace_excluded_top_dirs=frozenset({excluded.name}),
        )

        tm.that(discovered, eq=[included.name])

    def test_root_config_sets_expected_execution_environments(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Render only roots owned by the workspace repository itself."""
        pyright_rules = tool_config_document.tools.pyright
        rules = pyright_rules.path_rules
        self._workspace(tmp_path, "flext-core", "flext-api")
        root_source = tmp_path / rules.source_dir / "workspace"
        root_source.mkdir(parents=True)
        (root_source / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        root_modules = ("worker.py", "worker.pyi")
        for module in root_modules:
            (tmp_path / module).write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / "flext-core" / "tests").mkdir()
        (tmp_path / "flext-core" / "tests" / "test_smoke.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        detached = tmp_path / "demo-migration-tool"
        (detached / "src").mkdir(parents=True)
        (detached / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='demo-migration-tool'\n",
            encoding="utf-8",
        )

        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=True, repository_root=tmp_path),
        )

        tm.that(
            sorted(u.Tests.toml_strings(pyright["exclude"])),
            eq=sorted({
                *rules.default_excludes,
                *config.Infra.codegen.analyzer_exclude_globs,
            }),
        )
        if rules.ignored_diagnostic_globs:
            tm.that(
                sorted(u.Tests.toml_strings(pyright["ignore"])),
                eq=sorted({*rules.ignored_diagnostic_globs}),
            )
        else:
            tm.that(pyright, lacks="ignore")
        tm.that(
            sorted(u.Tests.toml_strings(pyright["include"])),
            eq=sorted([
                rules.source_dir,
                *root_modules,
                f"flext-core/{rules.source_dir}",
                "flext-core/tests",
                f"flext-api/{rules.source_dir}",
            ]),
        )
        discovered_files = {
            path.relative_to(tmp_path).as_posix()
            for pattern in u.Tests.toml_strings(pyright["include"])
            for path in tmp_path.glob(pattern)
            if path.is_dir()
        }
        tm.that(
            {f"flext-core/{rules.source_dir}", f"flext-api/{rules.source_dir}"}
            <= discovered_files,
            eq=True,
        )
        tm.ok("flext-core/tests" in discovered_files)
        environments = {
            environment["root"]: environment
            for item in u.Tests.toml_list(pyright["executionEnvironments"])
            for environment in (u.Tests.toml_mapping(item),)
        }
        tm.that(
            environments["flext-core/tests"]["extraPaths"],
            eq=["flext-core", f"flext-core/{rules.source_dir}"],
        )
        tm.that(
            environments["flext-api"]["extraPaths"],
            eq=["flext-api", f"flext-api/{rules.source_dir}"],
        )
        tm.that(
            environments[rules.source_dir]["extraPaths"],
            eq=[
                rules.source_dir,
                rules.project_root,
                "flext-core/src",
                "flext-api/src",
            ],
        )

    def test_root_config_includes_member_src_paths(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Workspace root execution environments include every member src path.

        Every declared first-party member src path is listed for Pylance resolution.
        """
        pyright_rules = tool_config_document.tools.pyright
        rules = pyright_rules.path_rules
        _ = (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        flext_core = tmp_path / "flext-core"
        flext_api = tmp_path / "flext-api"
        (flext_core / "src").mkdir(parents=True, exist_ok=True)
        (flext_api / "src").mkdir(parents=True, exist_ok=True)
        (flext_core / "src" / "flext_core").mkdir(parents=True, exist_ok=True)
        (flext_core / "src" / "flext_core" / "__init__.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        (flext_api / "src" / "flext_api").mkdir(parents=True, exist_ok=True)
        (flext_api / "src" / "flext_api" / "__init__.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "workspace").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "workspace" / "__init__.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        u.Tests.declare_workspace_projects(tmp_path, ("flext-core", "flext-api"))
        u.Tests.write_project_beads_config(tmp_path, "workspace")
        u.Tests.initialize_git_repo(tmp_path)
        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=True, repository_root=tmp_path),
        )
        envs = pyright["executionEnvironments"]
        tm.that(envs, is_=Sequence)
        if not isinstance(envs, Sequence):
            return
        src_env = None
        for entry in envs:
            environment = u.Cli.toml_unwrap_item(entry)
            if isinstance(environment, MutableMapping) and (
                environment.get("root") == rules.source_dir
            ):
                src_env = environment
                break
        tm.ok(src_env is not None)
        if src_env is None:
            return
        extra_paths = u.Tests.toml_strings(
            u.Cli.toml_unwrap_item(src_env["extraPaths"]),
        )
        tm.ok("flext-core/src" in extra_paths)
        tm.ok("flext-api/src" in extra_paths)

    def test_declared_repository_config_sets_expected_execution_environments(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Render every configured standalone analyzer environment."""
        pyright_rules = tool_config_document.tools.pyright
        rules = pyright_rules.path_rules

        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=False),
        )

        tm.that(
            sorted(u.Tests.toml_strings(pyright["include"])),
            eq=sorted(rules.env_dirs),
        )
        tm.that(
            pyright["executionEnvironments"],
            eq=[
                {
                    "root": env_dir,
                    "reportPrivateUsage": (
                        rules.source_report_private_usage
                        if env_dir == rules.source_dir
                        else rules.test_like_report_private_usage
                    ),
                    "extraPaths": (
                        [rules.source_dir, rules.project_root]
                        if env_dir == rules.source_dir
                        else [rules.project_root, rules.source_dir]
                    ),
                }
                for env_dir in rules.env_dirs
            ],
        )

    @pytest.mark.parametrize("is_root", [False, True])
    def test_package_parent_environment_preserves_strict_included_namespace(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        *,
        is_root: bool,
    ) -> None:
        """A first-party namespace child must not shadow an installed top-level SDK."""
        rules = tool_config_document.tools.pyright.path_rules
        selected = tool_config_document.model_copy(
            update={
                "tools": tool_config_document.tools.model_copy(
                    update={
                        "pyright": tool_config_document.tools.pyright.model_copy(
                            update={
                                "path_rules": rules.model_copy(
                                    update={"project_root_env_dirs": ("infra",)},
                                ),
                            },
                        ),
                    },
                ),
            },
        )
        project = self._sample_project(tmp_path, rules.source_dir)
        namespace = project / "infra" / "pulumi"
        namespace.mkdir(parents=True)
        (namespace / "consumer.py").write_text(
            "import pulumi\nconfig = pulumi.Config()\n"
            "invalid: int = 'strict sentinel'\n",
            encoding="utf-8",
        )
        pyright = self._applied(
            selected,
            m.Infra.PyprojectAnalyzerContext(
                is_root=is_root,
                project_dir=project,
                repository_root=project if is_root else None,
            ),
        )
        tm.ok("infra" in u.Tests.toml_strings(pyright["include"]))
        tm.that(pyright["typeCheckingMode"], eq="strict")
        environments = [
            u.Tests.toml_mapping(item)
            for item in u.Tests.toml_list(pyright["executionEnvironments"])
        ]
        roots = [environment["root"] for environment in environments]
        tm.ok("infra" not in roots)
        tm.that(roots[-1], eq=rules.project_root)
        tm.that(
            environments[-1]["reportPrivateUsage"],
            eq=rules.other_report_private_usage,
        )
        tm.ok(rules.source_dir in roots)
        declared = FlextInfraEnsurePyrightConfigPhase(
            selected,
            codegen=config.Infra.codegen,
        ).environment_payloads_for_dirs(("infra", rules.source_dir))
        tm.that([entry["root"] for entry in declared], eq=roots)

    def test_project_config_uses_canonical_typings_and_fixture_excludes(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Render typed paths and config-owned fixture exclusions."""
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = u.Tests.mk_project(
            tmp_path,
            "flext-sample",
            pyproject="[project]\nname='flext-sample'\nversion='0.1.0'\n",
            with_src=True,
        )
        (project_dir / "src" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        (project_dir / "tests" / "fixtures").mkdir(parents=True)
        (project_dir / "tests" / "test_smoke.py").write_text(
            "VALUE = 1\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project_dir)

        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=False, project_dir=project_dir),
        )

        if rules.ignored_diagnostic_globs:
            tm.that(
                sorted(u.Tests.toml_strings(pyright["ignore"])),
                eq=sorted({*rules.ignored_diagnostic_globs}),
            )
        else:
            tm.that(pyright, lacks="ignore")
        tm.that(
            sorted(u.Tests.toml_strings(pyright["include"])),
            eq=sorted([rules.source_dir, rules.test_like_dirs[0]]),
        )
        # Pyright reads no Git ignore rules: the generated-source trees of the
        # codegen artifact key must reach its exclude list (flext-gknfx).
        tm.that(
            set(u.Tests.toml_strings(pyright["exclude"])).issuperset({
                *rules.default_excludes,
                *config.Infra.codegen.analyzer_exclude_globs,
            }),
            eq=True,
        )

    def test_existing_standalone_uses_complete_declared_roots(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Declared future roots survive alongside existing source discovery."""
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = self._sample_project(tmp_path, rules.source_dir)
        pyproject = project_dir / c.PYPROJECT_FILENAME

        rendered = tm.ok(
            FlextInfraPyprojectModernizer(
                repository_root=project_dir,
                skip_check=True,
                skip_comments=True,
            ).conform_source(
                pyproject.read_text(encoding="utf-8"),
                path=pyproject,
                topology=m.Infra.PyprojectDeclaredTopology(
                    declared_python_dirs=(rules.source_dir, rules.test_like_dirs[0]),
                    declared_python_dirs_are_complete=True,
                ),
                codegen=tm.ok(u.Infra.load_codegen_inputs(project_dir)).spec,
            ),
        )

        tm.that(
            list(u.Tests.toml_strings_at(rendered, "tool", "pyright", "include")),
            eq=[rules.source_dir, rules.test_like_dirs[0]],
        )

    def test_existing_standalone_complete_empty_roots_keep_owned_sources(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """An empty scaffold declaration cannot hide existing owned Python."""
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = self._sample_project(tmp_path, rules.source_dir)

        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(
                is_root=False,
                project_dir=project_dir,
                declared_python_dirs_are_complete=True,
            ),
        )

        tm.that(list(u.Tests.toml_strings(pyright["include"])), eq=[rules.source_dir])
        tm.that(
            [
                u.Tests.toml_mapping(environment)["root"]
                for environment in u.Tests.toml_list(pyright["executionEnvironments"])
            ],
            eq=[rules.source_dir],
        )

    @staticmethod
    @pytest.mark.parametrize("local_environment", [False, True])
    @pytest.mark.parametrize("complete", [False, True])
    @pytest.mark.parametrize(
        ("project_name", "authored_and_planned"),
        [
            ("flext-alpha", ("automation", "future_checks")),
            ("flext-beta", ("quality_tools.py", "generated_checks.pyi")),
        ],
    )
    def test_render_context_retains_actual_and_planned_python_scopes(
        tmp_path: Path,
        project_name: str,
        authored_and_planned: t.Pair[str, str],
        *,
        complete: bool,
        local_environment: bool,
    ) -> None:
        """Rendering keeps arbitrary source roots before and after planned writes."""
        rules = config.Infra.tooling.tools.pyright.path_rules
        project_dir = u.Tests.mk_project(
            tmp_path,
            project_name,
            pyproject=f"[project]\nname='{project_name}'\nversion='0.1.0'\n[tool.flext.docs]\npackage_name='{u.Tests.project_spec(project_name).package_name}'\n",
        )
        u.Tests.initialize_git_repo(project_dir)
        package_name = u.Tests.project_spec(project_name).package_name
        active_roots = (
            rules.source_dir,
            "docs",
            "scripts",
            "examples",
            authored_and_planned[0],
        )
        for root in active_roots:
            directory = project_dir / root / package_name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        root_modules = ("worker.py", "worker.pyi")
        for module in root_modules:
            (project_dir / module).write_text("VALUE = 1\n", encoding="utf-8")
        (project_dir / "historical_guides").mkdir()
        (project_dir / "historical_guides" / "index.md").write_text(
            "Historical notes.\n", encoding="utf-8"
        )
        foreign = project_dir / "foreign_project"
        foreign.mkdir()
        (foreign / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='foreign-project'\n",
            encoding="utf-8",
        )
        (foreign / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        directory = project_dir / next(
            root
            for root in config.Infra.codegen.source_scan_ignored
            if not root.startswith(".")
        )
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        topology = m.Infra.PyprojectDeclaredTopology(
            declared_python_dirs=(rules.source_dir, authored_and_planned[1]),
            declared_python_dirs_are_complete=complete,
            project_kind="core",
        )
        request = m.Infra.ToolingContextRequest(
            environment_dir=(project_dir if local_environment else tmp_path)
            / c.Infra.ENVIRONMENT_DIRECTORY,
            planned_sources={},
            project_name=project_name,
            package_name=package_name,
            path=project_dir / c.PYPROJECT_FILENAME,
            codegen=tm.ok(u.Infra.load_codegen_inputs(project_dir)).spec,
            runtime_dependency_overlay=(),
            declared_project_dependencies=(),
            topology=topology,
        )
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=tmp_path,
            skip_check=True,
            skip_comments=True,
        )
        first_context = tm.ok(modernizer.resolve_tooling_context(request))
        expected_roots = frozenset((*active_roots, authored_and_planned[1]))
        first_pyright = u.Tests.toml_table_at(
            first_context.configuration, "tool", "pyright"
        )
        tm.that(
            frozenset(u.Tests.toml_strings(first_pyright["include"])),
            eq=expected_roots.union(root_modules),
        )
        tm.that(
            frozenset(
                u.Tests.toml_mapping(env)["root"]
                for env in u.Tests.toml_list(first_pyright["executionEnvironments"])
            ),
            eq=expected_roots,
        )
        tm.that(
            set(root_modules).isdisjoint(
                u.Tests.toml_strings(first_pyright["extraPaths"])
            ),
            eq=True,
        )
        for environment in u.Tests.toml_list(first_pyright["executionEnvironments"]):
            tm.that(
                set(root_modules).isdisjoint(
                    u.Tests.toml_strings(
                        u.Tests.toml_mapping(environment)["extraPaths"]
                    )
                ),
                eq=True,
            )
        first = tm.ok(
            modernizer.conform_source(
                (project_dir / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                path=project_dir / c.PYPROJECT_FILENAME,
                format_source=False,
                topology=topology,
                codegen=request.codegen,
            ),
        )
        tm.that(
            list(u.Tests.toml_strings_at(first, "tool", "pyright", "include")),
            eq=list(u.Tests.toml_strings(first_pyright["include"])),
        )
        tm.that(
            sorted(
                str(u.Tests.toml_mapping(env)["root"])
                for env in u.Tests.toml_list(
                    u.Tests.toml_table_at(first, "tool", "pyright")[
                        "executionEnvironments"
                    ],
                )
            ),
            eq=sorted(expected_roots),
        )
        (project_dir / c.PYPROJECT_FILENAME).write_text(first, encoding="utf-8")
        (project_dir / authored_and_planned[1]).mkdir()
        (project_dir / authored_and_planned[1] / "probe.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        second_context = tm.ok(modernizer.resolve_tooling_context(request))
        tm.that(
            second_context.configuration,
            eq=first_context.configuration,
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    first,
                    path=project_dir / c.PYPROJECT_FILENAME,
                    format_source=False,
                    topology=topology,
                    codegen=request.codegen,
                )
            ),
            eq=first,
        )

    def test_workspace_shares_analysis_with_member_local_environments(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """One analyzer includes members without merging their package roots."""
        rules = tool_config_document.tools.pyright.path_rules
        self._workspace(tmp_path, "flext-core")

        fleet = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=True, repository_root=tmp_path),
        )
        declared = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(
                is_root=True,
                repository_root=tmp_path,
                declared_python_dirs=(rules.source_dir,),
            ),
        )

        tm.that(declared, eq=fleet)
        tm.that(
            list(u.Tests.toml_strings(declared["include"])),
            eq=[f"flext-core/{rules.source_dir}"],
        )
        environments = [
            u.Tests.toml_mapping(item)
            for item in u.Tests.toml_list(declared["executionEnvironments"])
        ]
        tm.that(
            [environment["root"] for environment in environments],
            eq=[f"flext-core/{rules.source_dir}", "flext-core"],
        )

    def test_expected_envs_cover_every_analyzer_python_root(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """The phase includes modules but emits environments only for directories.

        ``analyzer_python_roots`` owns productive directories and root modules.
        A Python file under a directory outside
        ``env_dirs`` (docs/ here) separates that owner from the env list.
        """
        rules = tool_config_document.tools.pyright.path_rules
        source = tmp_path / rules.source_dir
        source.mkdir(parents=True)
        (source / "mod.py").write_text("x = 1\n", encoding="utf-8")
        for directory in rules.env_dirs:
            owned = tmp_path / directory
            owned.mkdir(parents=True, exist_ok=True)
            (owned / "owned.py").write_text("VALUE = 1\n", encoding="utf-8")
        outside = tmp_path / "docs" / "tools"
        outside.mkdir(parents=True)
        (outside / "validate_docs.py").write_text("y = 2\n", encoding="utf-8")
        root_modules = ("worker.py", "worker.pyi")
        for module in root_modules:
            (tmp_path / module).write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(tmp_path, "workspace")
        u.Tests.initialize_git_repo(tmp_path)
        excluded_top_dirs = FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
            tmp_path,
        ).unwrap()
        discovered = frozenset(
            u.Infra.discover_python_dirs(
                tmp_path,
                workspace_excluded_top_dirs=excluded_top_dirs,
            ),
        )
        declared = tuple(d for d in rules.env_dirs if d in discovered)

        pyright = self._applied(
            tool_config_document,
            m.Infra.PyprojectAnalyzerContext(is_root=False, project_dir=tmp_path),
        )

        targets = u.Infra.analyzer_python_roots(
            tmp_path,
            declared,
            workspace_excluded_top_dirs=excluded_top_dirs,
        )
        tm.ok(set(root_modules) <= set(targets))
        tm.that(sorted(u.Tests.toml_strings(pyright["include"])), eq=sorted(targets))
        tm.that(
            sorted(
                str(u.Tests.toml_mapping(environment)["root"])
                for environment in u.Tests.toml_list(pyright["executionEnvironments"])
            ),
            eq=sorted(root for root in targets if not (tmp_path / root).is_file()),
        )
        for module in root_modules:
            (tmp_path / module).unlink()
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({
            "tool": {"pyright": pyright}
        })
        phase = FlextInfraEnsurePyrightConfigPhase(
            tool_config_document,
            codegen=tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec,
        )
        tm.that(
            phase.apply_payload(
                payload,
                context=m.Infra.PyprojectAnalyzerContext(
                    is_root=False, project_dir=tmp_path
                ),
            ),
            empty=False,
        )
        retired = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["pyright"])
        tm.that(
            sorted(u.Tests.toml_strings(retired["include"])),
            eq=sorted(set(targets) - set(root_modules)),
        )
        tm.that(
            retired["executionEnvironments"],
            eq=pyright["executionEnvironments"],
        )
