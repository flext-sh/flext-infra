from __future__ import annotations

import tomllib
from collections.abc import (
    Sequence,
)
from pathlib import Path

from flext_tests import tm

from flext_infra import main
from tests import u


def _nested_value(pyproject_path: Path, *keys: str) -> object:
    current = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    for key in keys:
        assert isinstance(current, dict)
        current = current[key]
    return current


def _string_value(pyproject_path: Path, *keys: str) -> str:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, str)
    return value


def _bool_value(pyproject_path: Path, *keys: str) -> bool:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, bool)
    return value


def _string_list_value(pyproject_path: Path, *keys: str) -> list[str]:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, Sequence)
    assert all(isinstance(item, str) for item in value)
    return list(value)


class TestsFlextInfraDepsPathSyncMain:
    """Behavior contract for test_path_sync_main."""

    def test_main_auto_detects_workspace_and_rewrites_internal_paths(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Infra.Tests.create_path_sync_workspace(
            tmp_path,
            root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
                name="flext-workspace",
                dependency_path=".flext-deps/flext-core",
                workspace_members=("flext-core", "flext-cli"),
            ),
            projects={
                "flext-core": u.Infra.Tests.create_path_sync_pyproject(
                    name="flext-core"
                ),
                "flext-cli": u.Infra.Tests.create_path_sync_pyproject(
                    name="flext-cli",
                    dependency_path=".flext-deps/flext-core",
                ),
            },
            gitmodules_members=("flext-core", "flext-cli"),
        )

        exit_code = main([
            "deps",
            "path-sync",
            "--workspace",
            str(workspace),
            "--apply",
        ])

        tm.that(exit_code, eq=0)
        tm.that(
            _string_list_value(workspace / "pyproject.toml", "project", "dependencies"),
            eq=["flext-core"],
        )
        tm.that(
            _string_value(
                workspace / "pyproject.toml",
                "tool",
                "poetry",
                "dependencies",
                "flext-core",
                "path",
            ),
            eq="flext-core",
        )
        tm.that(
            _string_list_value(
                workspace / "pyproject.toml",
                "tool",
                "uv",
                "workspace",
                "members",
            ),
            eq=["flext-cli", "flext-core"],
        )
        tm.that(
            _bool_value(
                workspace / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "workspace",
            ),
            eq=True,
        )
        tm.that(
            _bool_value(
                workspace / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-cli",
                "workspace",
            ),
            eq=True,
        )
        tm.that(
            _string_list_value(
                workspace / "flext-cli" / "pyproject.toml",
                "project",
                "dependencies",
            ),
            eq=["flext-core"],
        )
        tm.that(
            _string_value(
                workspace / "flext-cli" / "pyproject.toml",
                "tool",
                "poetry",
                "dependencies",
                "flext-core",
                "path",
            ),
            eq="../flext-core",
        )
        tm.that(
            _bool_value(
                workspace / "flext-cli" / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "workspace",
            ),
            eq=True,
        )

    def test_run_cli_rewrites_root_and_projects_for_standalone_mode(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = u.Infra.Tests.create_path_sync_workspace(
            tmp_path,
            root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
                name="flext-workspace",
                dependency_path="flext-core",
                workspace_members=("flext-core", "flext-cli"),
            ),
            projects={
                "flext-core": u.Infra.Tests.create_path_sync_pyproject(
                    name="flext-core"
                ),
                "flext-cli": u.Infra.Tests.create_path_sync_pyproject(
                    name="flext-cli",
                    dependency_path="../flext-core",
                ),
            },
        )

        exit_code = main([
            "deps",
            "path-sync",
            "--workspace",
            str(workspace),
            "--mode",
            "standalone",
            "--apply",
        ])

        tm.that(exit_code, eq=0)
        tm.that(
            _string_list_value(workspace / "pyproject.toml", "project", "dependencies"),
            eq=["flext-core"],
        )
        tm.that(
            _string_value(
                workspace / "pyproject.toml",
                "tool",
                "poetry",
                "dependencies",
                "flext-core",
                "path",
            ),
            eq=".flext-deps/flext-core",
        )
        tm.that(
            _string_value(
                workspace / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "path",
            ),
            eq=".flext-deps/flext-core",
        )
        tm.that(
            _bool_value(
                workspace / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "editable",
            ),
            eq=True,
        )
        tm.that(
            _string_value(
                workspace / "flext-cli" / "pyproject.toml",
                "tool",
                "poetry",
                "dependencies",
                "flext-core",
                "path",
            ),
            eq=".flext-deps/flext-core",
        )
        tm.that(
            _string_value(
                workspace / "flext-cli" / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "path",
            ),
            eq=".flext-deps/flext-core",
        )
        tm.that(
            _bool_value(
                workspace / "flext-cli" / "pyproject.toml",
                "tool",
                "uv",
                "sources",
                "flext-core",
                "editable",
            ),
            eq=True,
        )
