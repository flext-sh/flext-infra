"""Pyright phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import tomlkit
from flext_tests import tm
from tests import m, u

from flext_infra import FlextInfraEnsurePyrightConfigPhase


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


class TestEnsurePyrightConfigPhase:
    """Tests pyright config phase behavior."""

    def test_apply_root_sets_execution_environments(self, tmp_path: Path) -> None:
        tool_config = _test_tool_config()
        rules = tool_config.tools.pyright.path_rules
        flext_core = tmp_path / "flext-core"
        flext_api = tmp_path / "flext-api"
        (tmp_path / "vendor").mkdir(parents=True, exist_ok=True)
        (tmp_path / "typings" / "generated").mkdir(parents=True, exist_ok=True)
        (flext_core / "pyproject.toml").parent.mkdir(parents=True, exist_ok=True)
        (flext_api / "pyproject.toml").parent.mkdir(parents=True, exist_ok=True)
        _ = (flext_core / "pyproject.toml").write_text("", encoding="utf-8")
        _ = (flext_api / "pyproject.toml").write_text("", encoding="utf-8")
        (flext_core / "src").mkdir(parents=True, exist_ok=True)
        (flext_core / "tests").mkdir(parents=True, exist_ok=True)
        (flext_api / "src").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()
        changes = FlextInfraEnsurePyrightConfigPhase(tool_config).apply(
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
        exclude = u.Cli.toml_unwrap_item(pyright["exclude"])
        expected_exclude = sorted(
            set(rules.default_excludes)
            | {
                directory
                for directory in rules.dynamic_exclude_dirs
                if (tmp_path / directory).is_dir()
            },
        )
        tm.that(exclude, eq=expected_exclude)
        ignore = u.Cli.toml_unwrap_item(pyright["ignore"])
        tm.that(
            ignore,
            eq=[*rules.root_typings_paths, *rules.ignored_diagnostic_globs],
        )
        envs = u.Cli.toml_unwrap_item(pyright["executionEnvironments"])
        tm.that(envs, is_=list)
        tm.that(
            envs,
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
        tm.that(
            changes,
            has="tool.pyright.exclude synchronized from discovered dirs",
        )
        tm.that(
            changes,
            has="tool.pyright.ignore synchronized for typings diagnostics",
        )
        tm.that(
            changes,
            has="tool.pyright.executionEnvironments set with tests reportPrivateUsage=none",
        )

    def test_apply_subproject_sets_execution_environments(self) -> None:
        tool_config = _test_tool_config()
        rules = tool_config.tools.pyright.path_rules
        doc = tomlkit.document()
        changes = FlextInfraEnsurePyrightConfigPhase(tool_config).apply(
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
        tm.that(u.Cli.toml_unwrap_item(pyright["venvPath"]), eq=rules.project_venv_path)
        envs = u.Cli.toml_unwrap_item(pyright["executionEnvironments"])
        tm.that(envs, is_=list)
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
            envs,
            eq=expected_envs,
        )
        tm.that(
            changes,
            has="tool.pyright.executionEnvironments set with tests reportPrivateUsage=none",
        )

    def test_apply_subproject_sets_ignore_from_workspace_typings(
        self,
        tmp_path: Path,
    ) -> None:
        tool_config = _test_tool_config()
        rules = tool_config.tools.pyright.path_rules
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
        (tmp_path / "typings").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()
        changes = FlextInfraEnsurePyrightConfigPhase(tool_config).apply(
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
        ignore = u.Cli.toml_unwrap_item(pyright["ignore"])
        tm.that(
            ignore,
            eq=[rules.project_typings_paths[0], *rules.ignored_diagnostic_globs],
        )
        tm.that(
            changes,
            has="tool.pyright.ignore synchronized for typings diagnostics",
        )
