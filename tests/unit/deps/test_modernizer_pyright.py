"""Pyright phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING


from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.deps.phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


class TestsFlextInfraDepsModernizerPyright:
    """Declarative tests for generated Pyright configuration."""

    def test_root_config_sets_expected_execution_environments(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render configured root and member analyzer environments."""
        pyright_rules = tool_config_document.tools.pyright
        rules = pyright_rules.path_rules
        _ = (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\n\n"
            "[tool.uv.workspace]\n"
            "members = ['flext-core', 'flext-api']\n",
            encoding="utf-8",
        )
        flext_core = tmp_path / "flext-core"
        flext_api = tmp_path / "flext-api"
        detached_project = tmp_path / "demo-migration-tool"
        (tmp_path / "vendor").mkdir(parents=True, exist_ok=True)
        flext_core.mkdir(parents=True, exist_ok=True)
        flext_api.mkdir(parents=True, exist_ok=True)
        detached_project.mkdir(parents=True, exist_ok=True)
        _ = (flext_core / "pyproject.toml").write_text(
            "[project]\nname='flext-core'\n", encoding="utf-8"
        )
        _ = (flext_api / "pyproject.toml").write_text(
            "[project]\nname='flext-api'\n", encoding="utf-8"
        )
        _ = (detached_project / "pyproject.toml").write_text(
            "[project]\nname='demo-migration-tool'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        (flext_core / "src").mkdir(parents=True, exist_ok=True)
        (flext_core / "tests").mkdir(parents=True, exist_ok=True)
        (flext_api / "src").mkdir(parents=True, exist_ok=True)
        (detached_project / "src").mkdir(parents=True, exist_ok=True)
        (flext_core / "src" / "flext_core").mkdir(parents=True, exist_ok=True)
        (flext_core / "src" / "flext_core" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (flext_core / "tests" / "test_smoke.py").write_text(
            "def test_smoke() -> None:\n    assert True\n", encoding="utf-8"
        )
        (flext_api / "src" / "flext_api").mkdir(parents=True, exist_ok=True)
        (flext_api / "src" / "flext_api" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        doc = u.Cli.toml_document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc, is_root=True, workspace_root=tmp_path
        )

        tool = u.Cli.toml_unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Cli.toml_unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        tm.that(u.Cli.toml_unwrap_item(pyright["venv"]), eq=rules.venv_name)
        tm.that(u.Cli.toml_unwrap_item(pyright["venvPath"]), eq=rules.root_venv_path)
        tm.that(u.Cli.toml_unwrap_item(pyright["reportUntypedBaseClass"]), eq="none")
        tm.that(
            sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["exclude"]))),
            eq=sorted(set(rules.default_excludes)),
        )
        expected_ignores = [*rules.root_typings_paths, *rules.ignored_diagnostic_globs]
        if expected_ignores:
            tm.that(
                sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["ignore"]))),
                eq=sorted(expected_ignores),
            )
        else:
            tm.that(pyright, lacks="ignore")
        tm.that(
            sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))),
            eq=sorted([
                f"flext-api/{rules.source_dir}",
                f"flext-core/{rules.source_dir}",
                f"flext-core/{rules.test_like_dirs[0]}",
            ]),
        )
        tm.that(
            u.Cli.toml_unwrap_item(pyright["executionEnvironments"]),
            eq=[
                {
                    **pyright_rules.lazy_import_suppressions,
                    **pyright_rules.source_env_suppressions,
                    "root": f"flext-api/{rules.source_dir}",
                    "reportPrivateUsage": rules.source_report_private_usage,
                    "extraPaths": [f"flext-api/{rules.source_dir}"],
                },
                {
                    **pyright_rules.lazy_import_suppressions,
                    **pyright_rules.source_env_suppressions,
                    "root": f"flext-core/{rules.source_dir}",
                    "reportPrivateUsage": rules.source_report_private_usage,
                    "extraPaths": [f"flext-core/{rules.source_dir}"],
                },
                {
                    **pyright_rules.lazy_import_suppressions,
                    **pyright_rules.test_like_env_suppressions,
                    "root": f"flext-core/{rules.test_like_dirs[0]}",
                    "reportPrivateUsage": rules.test_like_report_private_usage,
                    "extraPaths": ["flext-core", f"flext-core/{rules.source_dir}"],
                },
            ],
        )

    def test_subproject_config_sets_expected_execution_environments(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render every configured standalone analyzer environment."""
        pyright_rules = tool_config_document.tools.pyright
        rules = pyright_rules.path_rules
        doc = u.Cli.toml_document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc, is_root=False
        )

        tool = u.Cli.toml_unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Cli.toml_unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        tm.that(u.Cli.toml_unwrap_item(pyright["venv"]), eq=rules.venv_name)
        tm.that(u.Cli.toml_unwrap_item(pyright["venvPath"]), eq=rules.project_venv_path)
        tm.that(u.Cli.toml_unwrap_item(pyright["reportUntypedBaseClass"]), eq="none")
        tm.that(
            sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))),
            eq=sorted(rules.env_dirs),
        )
        expected_envs = [
            {
                **pyright_rules.lazy_import_suppressions,
                **(
                    pyright_rules.source_env_suppressions
                    if env_dir == rules.source_dir
                    else (
                        pyright_rules.test_like_env_suppressions
                        if env_dir in rules.test_like_dirs
                        else {}
                    )
                ),
                "root": env_dir,
                "reportPrivateUsage": (
                    rules.source_report_private_usage
                    if env_dir == rules.source_dir
                    else (
                        rules.test_like_report_private_usage
                        if env_dir in rules.test_like_dirs
                        else rules.other_report_private_usage
                    )
                ),
                "extraPaths": (
                    [rules.source_dir]
                    if env_dir == rules.source_dir
                    else [rules.project_root, rules.source_dir]
                ),
            }
            for env_dir in rules.env_dirs
        ]
        tm.that(
            u.Cli.toml_unwrap_item(pyright["executionEnvironments"]), eq=expected_envs
        )

    def test_subproject_config_uses_workspace_typings_and_fixture_excludes(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render typed paths and config-owned fixture exclusions."""
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "src" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests" / "test_smoke.py").write_text(
            "def test_smoke() -> None:\n    assert True\n", encoding="utf-8"
        )
        (project_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
        doc = u.Cli.toml_document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc, is_root=False, project_dir=project_dir
        )

        tool = u.Cli.toml_unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Cli.toml_unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        expected_ignores = [
            *rules.project_typings_paths,
            *rules.ignored_diagnostic_globs,
        ]
        if expected_ignores:
            tm.that(
                sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["ignore"]))),
                eq=sorted(expected_ignores),
            )
        else:
            tm.that(pyright, lacks="ignore")
        tm.that(
            sorted(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))),
            eq=sorted([rules.source_dir, rules.test_like_dirs[0]]),
        )
        exclude = list(u.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["exclude"])))
        tm.that(exclude, has="**/tests/fixtures")
        tm.that(exclude, has="**/tests/fixtures/**")

    def test_pyright_phase_is_idempotent(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Produce no changes after the first canonical phase application."""
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config_document)
        doc = u.Cli.toml_document()

        _ = phase.apply(doc, is_root=False, project_dir=project_dir)
        second_changes = phase.apply(doc, is_root=False, project_dir=project_dir)

        tm.that(second_changes, eq=[])

    def test_existing_standalone_uses_complete_declared_roots(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        source_dir = project_dir / rules.source_dir / "flext_sample"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("", encoding="utf-8")
        pyproject = project_dir / "pyproject.toml"
        source = "[project]\nname='flext-sample'\n"
        pyproject.write_text(source, encoding="utf-8")

        rendered = tm.ok(
            FlextInfraPyprojectModernizer(
                workspace_root=project_dir, skip_check=True, skip_comments=True
            ).conform_source(
                source,
                path=pyproject,
                declared_python_dirs=(rules.source_dir, rules.test_like_dirs[0]),
                declared_python_dirs_are_complete=True,
            )
        )

        payload = u.Cli.toml_mapping_from_text(rendered)
        tm.that(payload, none=False)
        if payload is None:
            return
        tool = u.Cli.toml_mapping_child(payload, "tool")
        tm.that(tool, none=False)
        if tool is None:
            return
        pyright = u.Cli.toml_mapping_child(tool, "pyright")
        tm.that(pyright, none=False)
        if pyright is None:
            return
        tm.that(
            u.Cli.json_as_sequence(pyright.get("include")),
            eq=[rules.source_dir, rules.test_like_dirs[0]],
        )

    def test_existing_standalone_complete_empty_roots_do_not_rediscover_disk(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        source_dir = project_dir / rules.source_dir / "flext_sample"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("", encoding="utf-8")
        doc = u.Cli.toml_document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
            declared_python_dirs=(),
            declared_python_dirs_are_complete=True,
        )

        tool = u.Cli.toml_unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Cli.toml_unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        tm.that(u.Cli.toml_unwrap_item(pyright["include"]), eq=[])
        tm.that(u.Cli.toml_unwrap_item(pyright["executionEnvironments"]), eq=[])

    def test_workspace_root_declared_roots_do_not_override_fleet_discovery(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Render the workspace-root fleet surface even when roots are declared.

        A workspace root owns a real tree, so its analyzer surface is decided by
        that tree's topology. Declared roots are the pre-write scaffold seed and
        must never narrow a real root back to its own local directories, or the
        root renders one shape from the fleet fan-out and another from inside
        itself and no content is a fixed point (mro-dph2).
        """
        rules = tool_config_document.tools.pyright.path_rules
        _ = (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\n\n"
            "[tool.uv.workspace]\n"
            "members = ['flext-core']\n",
            encoding="utf-8",
        )
        flext_core = tmp_path / "flext-core"
        (flext_core / "src" / "flext_core").mkdir(parents=True, exist_ok=True)
        _ = (flext_core / "pyproject.toml").write_text(
            "[project]\nname='flext-core'\n", encoding="utf-8"
        )
        _ = (flext_core / "src" / "flext_core" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config_document)
        fleet_doc = u.Cli.toml_document()
        declared_doc = u.Cli.toml_document()

        _ = phase.apply(fleet_doc, is_root=True, workspace_root=tmp_path)
        _ = phase.apply(
            declared_doc,
            is_root=True,
            workspace_root=tmp_path,
            declared_python_dirs=(rules.source_dir,),
        )

        tm.that(u.Cli.toml_dumps(declared_doc), eq=u.Cli.toml_dumps(fleet_doc))
        declared_tool = u.Cli.toml_unwrap_item(declared_doc["tool"])
        tm.that(declared_tool, is_=MutableMapping)
        if not isinstance(declared_tool, MutableMapping):
            return
        declared_pyright = u.Cli.toml_unwrap_item(declared_tool["pyright"])
        tm.that(declared_pyright, is_=MutableMapping)
        if not isinstance(declared_pyright, MutableMapping):
            return
        tm.that(
            list(
                u.Tests.toml_strings(
                    u.Cli.toml_unwrap_item(declared_pyright["include"])
                )
            ),
            has=f"flext-core/{rules.source_dir}",
        )
