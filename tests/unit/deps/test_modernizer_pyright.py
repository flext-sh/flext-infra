"""Pyright phase tests for deps modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.deps import (
    FlextInfraEnsurePyrightConfigPhase,
    FlextInfraPyprojectModernizer,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsModernizerPyright:
    """Declarative tests for generated Pyright configuration."""

    @staticmethod
    def _applied(
        tool_config_document: m.Infra.ToolConfigDocument,
        context: m.Infra.PyprojectAnalyzerContext,
    ) -> t.JsonMapping:
        """Apply the phase twice to an empty payload; return the converged table.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config_document)
        changes = [phase.apply_payload(payload, context=context) for _ in range(2)]
        tm.that(changes[0], empty=False)
        tm.that(changes[1], empty=True)
        pyright = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["pyright"])
        # Shared config leaves environment selection to Make.
        tm.that(pyright, lacks="venv")
        tm.that(pyright, lacks="venvPath")
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
        (project_dir / "pyproject.toml").write_text(
            "[project]\nname='flext-sample'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(project_dir, "flext-sample")
        return project_dir

    @staticmethod
    def _workspace(tmp_path: Path, *members: str) -> None:
        """Declare one governed workspace root with governed member manifests."""
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        for member in members:
            package = tmp_path / member / "src" / member.replace("-", "_")
            package.mkdir(parents=True, exist_ok=True)
            (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
            (tmp_path / member / "pyproject.toml").write_text(
                f"[project]\nname='{member}'\nversion='0.1.0'\n",
                encoding="utf-8",
            )
            u.Tests.write_project_beads_config(tmp_path / member, member)
        u.Tests.declare_workspace_projects(tmp_path, members)
        u.Tests.write_project_beads_config(tmp_path, "workspace")

    @staticmethod
    def test_python_discovery_ignores_member_only_container(
        tmp_path: Path,
    ) -> None:
        """A directory containing only nested projects is not a root source tree."""
        root_source = tmp_path / "src"
        root_source.mkdir()
        (root_source / "root.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(tmp_path, "workspace")
        member = tmp_path / "apps" / "member"
        member_source = member / "src" / "member"
        member_source.mkdir(parents=True)
        (member / "pyproject.toml").write_text(
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
        (detached / "pyproject.toml").write_text(
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
                *config.Infra.codegen.generated_source_globs,
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
            list(u.Tests.toml_strings(pyright["include"])),
            eq=[rules.source_dir, *root_modules],
        )
        tm.that(
            pyright["executionEnvironments"],
            eq=[
                {
                    "root": rules.source_dir,
                    "reportPrivateUsage": rules.source_report_private_usage,
                    "extraPaths": [rules.source_dir, "flext-core/src", "flext-api/src"],
                },
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
        _ = (tmp_path / "pyproject.toml").write_text(
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
        tm.that(src_env is not None, eq=True)
        if src_env is None:
            return
        extra_paths = u.Tests.toml_strings(
            u.Cli.toml_unwrap_item(src_env.get("extraPaths", ())),
        )
        tm.that("flext-core/src" in extra_paths, eq=True)
        tm.that("flext-api/src" in extra_paths, eq=True)

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
                        [rules.source_dir]
                        if env_dir == rules.source_dir
                        else [rules.project_root, rules.source_dir]
                    ),
                }
                for env_dir in rules.env_dirs
            ],
        )

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
                *config.Infra.codegen.generated_source_globs,
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
        pyproject = project_dir / "pyproject.toml"

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
    @pytest.mark.parametrize("complete", [False, True])
    @pytest.mark.parametrize(
        ("project_name", "authored_root", "planned_root"),
        [
            ("flext-alpha", "automation", "future_checks"),
            ("flext-beta", "quality_tools.py", "generated_checks.pyi"),
        ],
    )
    def test_render_context_retains_actual_and_planned_python_scopes(
        tmp_path: Path,
        project_name: str,
        authored_root: str,
        planned_root: str,
        *,
        complete: bool,
    ) -> None:
        """Rendering keeps arbitrary source roots before and after planned writes."""
        rules = config.Infra.tooling.tools.pyright.path_rules
        project_dir = u.Tests.mk_project(
            tmp_path,
            project_name,
            pyproject=f"[project]\nname='{project_name}'\nversion='0.1.0'\n",
        )
        package_name = u.Tests.project_spec(project_name).package_name
        active_roots = (rules.source_dir, "docs", "scripts", "examples", authored_root)
        for root in active_roots:
            directory = project_dir / root / package_name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        root_modules = ("worker.py", "worker.pyi")
        for module in root_modules:
            (project_dir / module).write_text("VALUE = 1\n", encoding="utf-8")
        historical = project_dir / "historical_guides"
        historical.mkdir()
        (historical / "index.md").write_text("Historical notes.\n", encoding="utf-8")
        foreign = project_dir / "foreign_project"
        foreign.mkdir()
        (foreign / "pyproject.toml").write_text(
            "[project]\nname='foreign-project'\n",
            encoding="utf-8",
        )
        (foreign / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        artifact_root = next(
            root
            for root in config.Infra.codegen.source_scan_ignored
            if not root.startswith(".")
        )
        artifact = project_dir / artifact_root
        artifact.mkdir(parents=True, exist_ok=True)
        (artifact / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        path = project_dir / "pyproject.toml"
        topology = m.Infra.PyprojectDeclaredTopology(
            declared_python_dirs=(rules.source_dir, planned_root),
            declared_python_dirs_are_complete=complete,
        )
        request = m.Infra.ToolingContextRequest(
            planned_sources={},
            project_name=project_name,
            package_name=package_name,
            path=path,
            scaffold_project=config.Infra.codegen.scaffold.project,
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
        expected_roots = frozenset((*active_roots, planned_root))
        tm.that(
            frozenset(first_context.pyright_include),
            eq=expected_roots.union(root_modules),
        )
        tm.that(
            frozenset(env.root for env in first_context.pyright_execution_environments),
            eq=expected_roots,
        )
        tm.that(
            set(root_modules).isdisjoint(first_context.pyright_extra_paths),
            eq=True,
        )
        for environment in first_context.pyright_execution_environments:
            tm.that(set(root_modules).isdisjoint(environment.extra_paths), eq=True)
        first = tm.ok(
            modernizer.conform_source(
                path.read_text(encoding="utf-8"),
                path=path,
                format_source=False,
                topology=topology,
            ),
        )
        tm.that(
            list(u.Tests.toml_strings_at(first, "tool", "pyright", "include")),
            eq=list(first_context.pyright_include),
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
        path.write_text(first, encoding="utf-8")
        planned = project_dir / planned_root
        planned.mkdir()
        (planned / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
        second_context = tm.ok(modernizer.resolve_tooling_context(request))
        tm.that(second_context.pyright_include, eq=first_context.pyright_include)
        tm.that(
            second_context.pyright_execution_environments,
            eq=first_context.pyright_execution_environments,
        )
        second = tm.ok(
            modernizer.conform_source(
                first,
                path=path,
                format_source=False,
                topology=topology,
            ),
        )
        tm.that(second, eq=first)

    def test_repository_root_never_adopts_member_analyzer_roots(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """Keep member projects under their own manifests and native gates."""
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
        tm.that(declared, lacks="include")
        tm.that(declared["executionEnvironments"], eq=[])

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
        outside = tmp_path / "docs" / "tools"
        outside.mkdir(parents=True)
        (outside / "validate_docs.py").write_text("y = 2\n", encoding="utf-8")
        root_modules = ("worker.py", "worker.pyi")
        for module in root_modules:
            (tmp_path / module).write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(tmp_path, "workspace")
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
        tm.that(set(root_modules) <= set(targets), eq=True)
        tm.that(sorted(u.Tests.toml_strings(pyright["include"])), eq=sorted(targets))
        tm.that(
            sorted(
                str(u.Tests.toml_mapping(environment)["root"])
                for environment in u.Tests.toml_list(pyright["executionEnvironments"])
            ),
            eq=sorted(root for root in targets if not (tmp_path / root).is_file()),
        )
