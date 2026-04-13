"""Pyright phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraEnsurePyrightConfigPhase
from tests import m, u


class TestDepsModernizerPyright:
    """Declarative tests for generated Pyright configuration."""

    def test_root_config_sets_expected_execution_environments(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
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
        algar = tmp_path / "algar-oud-mig"
        (tmp_path / "vendor").mkdir(parents=True, exist_ok=True)
        (tmp_path / "typings" / "generated").mkdir(parents=True, exist_ok=True)
        flext_core.mkdir(parents=True, exist_ok=True)
        flext_api.mkdir(parents=True, exist_ok=True)
        algar.mkdir(parents=True, exist_ok=True)
        _ = (flext_core / "pyproject.toml").write_text(
            "[project]\nname='flext-core'\n",
            encoding="utf-8",
        )
        _ = (flext_api / "pyproject.toml").write_text(
            "[project]\nname='flext-api'\n",
            encoding="utf-8",
        )
        _ = (algar / "pyproject.toml").write_text(
            "[project]\nname='algar-oud-mig'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        (flext_core / "src").mkdir(parents=True, exist_ok=True)
        (flext_core / "tests").mkdir(parents=True, exist_ok=True)
        (flext_api / "src").mkdir(parents=True, exist_ok=True)
        (algar / "src").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc,
            is_root=True,
            workspace_root=tmp_path,
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
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["exclude"]))
            ),
            eq=sorted(
                set(rules.default_excludes)
                | {
                    directory
                    for directory in rules.dynamic_exclude_dirs
                    if (tmp_path / directory).is_dir()
                },
            ),
        )
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["ignore"]))
            ),
            eq=sorted([*rules.root_typings_paths, *rules.ignored_diagnostic_globs]),
        )
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))
            ),
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
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
        doc = tomlkit.document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
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
        tm.that(
            u.Cli.toml_unwrap_item(pyright["venvPath"]),
            eq=rules.project_venv_path,
        )
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))
            ),
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
            u.Cli.toml_unwrap_item(pyright["executionEnvironments"]),
            eq=expected_envs,
        )

    def test_subproject_config_uses_workspace_typings_and_fixture_excludes(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        rules = tool_config_document.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests" / "fixtures").mkdir(parents=True, exist_ok=True)
        (tmp_path / "typings").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()

        _ = FlextInfraEnsurePyrightConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
        )

        tool = u.Cli.toml_unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Cli.toml_unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["ignore"]))
            ),
            eq=sorted([
                rules.project_typings_paths[0],
                *rules.ignored_diagnostic_globs,
            ]),
        )
        tm.that(
            sorted(
                u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["include"]))
            ),
            eq=sorted([rules.source_dir, rules.test_like_dirs[0]]),
        )
        exclude = list(
            u.Infra.Tests.toml_strings(u.Cli.toml_unwrap_item(pyright["exclude"]))
        )
        tm.that(exclude, has="**/tests/fixtures")
        tm.that(exclude, has="**/tests/fixtures/**")

    def test_pyright_phase_is_idempotent(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc, is_root=False, project_dir=project_dir)
        second_changes = phase.apply(doc, is_root=False, project_dir=project_dir)

        tm.that(second_changes, eq=[])
