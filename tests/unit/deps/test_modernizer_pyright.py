"""Pyright phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

import tomlkit
from flext_tests._utilities.matchers import tm

from flext_infra.deps.phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


class TestsFlextInfraDepsModernizerPyright:
    """Declarative tests for generated Pyright configuration."""

    def test_root_config_sets_expected_execution_environments(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
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
        doc = tomlkit.document()

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
            eq=sorted(
                set(rules.default_excludes)
                | {
                    directory
                    for directory in rules.dynamic_exclude_dirs
                    if (tmp_path / directory).is_dir()
                }
            ),
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
                    "root": f"flext-api/{rules.source_dir}",
                    "reportPrivateUsage": rules.source_report_private_usage,
                    "extraPaths": [f"flext-api/{rules.source_dir}"],
                },
                {
                    "root": f"flext-core/{rules.source_dir}",
                    "reportPrivateUsage": rules.source_report_private_usage,
                    "extraPaths": [f"flext-core/{rules.source_dir}"],
                },
                {
                    "root": f"flext-core/{rules.test_like_dirs[0]}",
                    "reportPrivateUsage": rules.test_like_report_private_usage,
                    "extraPaths": ["flext-core", f"flext-core/{rules.source_dir}"],
                },
            ],
        )

    def test_subproject_config_sets_expected_execution_environments(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
        doc = tomlkit.document()

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
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "src" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests" / "test_smoke.py").write_text(
            "def test_smoke() -> None:\n    assert True\n", encoding="utf-8"
        )
        (project_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()

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
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc, is_root=False, project_dir=project_dir)
        second_changes = phase.apply(doc, is_root=False, project_dir=project_dir)

        tm.that(second_changes, eq=[])
