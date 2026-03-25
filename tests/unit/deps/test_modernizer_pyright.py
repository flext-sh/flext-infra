"""Pyright phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraEnsurePyrightConfigPhase, m, u


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
        changes = FlextInfraEnsurePyrightConfigPhase(_test_tool_config()).apply(
            doc,
            is_root=True,
            workspace_root=tmp_path,
        )
        tool = u.Infra.unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Infra.unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        exclude = u.Infra.unwrap_item(pyright["exclude"])
        rules = _test_tool_config().tools.pyright.path_rules
        expected_exclude = sorted(
            set(rules.default_excludes)
            | {
                directory
                for directory in rules.dynamic_exclude_dirs
                if (tmp_path / directory).is_dir()
            },
        )
        tm.that(exclude, eq=expected_exclude)
        ignore = u.Infra.unwrap_item(pyright["ignore"])
        tm.that(ignore, eq=["typings", "typings/generated"])
        envs = u.Infra.unwrap_item(pyright["executionEnvironments"])
        tm.that(envs, is_=list)
        tm.that(
            envs,
            eq=[
                {
                    "root": "flext-api/src",
                    "reportPrivateUsage": "error",
                    "extraPaths": ["flext-api/src"],
                },
                {
                    "root": "flext-core/src",
                    "reportPrivateUsage": "error",
                    "extraPaths": ["flext-core/src"],
                },
                {
                    "root": "flext-core/tests",
                    "reportPrivateUsage": "none",
                    "extraPaths": ["flext-core", "flext-core/src"],
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
        doc = tomlkit.document()
        changes = FlextInfraEnsurePyrightConfigPhase(_test_tool_config()).apply(
            doc,
            is_root=False,
        )
        tool = u.Infra.unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Infra.unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        envs = u.Infra.unwrap_item(pyright["executionEnvironments"])
        tm.that(envs, is_=list)
        tm.that(
            envs,
            eq=[
                {"root": "src", "reportPrivateUsage": "error", "extraPaths": ["src"]},
                {
                    "root": "tests",
                    "reportPrivateUsage": "none",
                    "extraPaths": [".", "src"],
                },
            ],
        )
        tm.that(
            changes,
            has="tool.pyright.executionEnvironments set with tests reportPrivateUsage=none",
        )

    def test_apply_subproject_sets_ignore_from_workspace_typings(
        self,
        tmp_path: Path,
    ) -> None:
        project_dir = tmp_path / "flext-sample"
        (project_dir / "src").mkdir(parents=True, exist_ok=True)
        (project_dir / "tests").mkdir(parents=True, exist_ok=True)
        (tmp_path / "typings").mkdir(parents=True, exist_ok=True)
        doc = tomlkit.document()
        changes = FlextInfraEnsurePyrightConfigPhase(_test_tool_config()).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
        )
        tool = u.Infra.unwrap_item(doc["tool"])
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pyright = u.Infra.unwrap_item(tool["pyright"])
        tm.that(pyright, is_=MutableMapping)
        if not isinstance(pyright, MutableMapping):
            return
        ignore = u.Infra.unwrap_item(pyright["ignore"])
        tm.that(ignore, eq=["../typings"])
        tm.that(
            changes,
            has="tool.pyright.ignore synchronized for typings diagnostics",
        )
