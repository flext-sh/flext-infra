from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_tests import tm

from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraUtilitiesDependencyPathSync,
    main,
)
from tests import u


def _nested_value(pyproject_path: Path, *keys: str) -> object:
    current: object = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    for key in keys:
        assert isinstance(current, dict)
        current = current[key]
    return current


def _string_value(pyproject_path: Path, *keys: str) -> str:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, str)
    return value


def _string_list_value(pyproject_path: Path, *keys: str) -> list[str]:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, Sequence)
    assert all(isinstance(item, str) for item in value)
    return list(value)


def _mapping_value(pyproject_path: Path, *keys: str) -> Mapping[str, object]:
    value = _nested_value(pyproject_path, *keys)
    assert isinstance(value, Mapping)
    return value


def test_run_cli_dry_run_preserves_pyproject_files(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_path_sync_workspace(
        tmp_path,
        root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
            name="flext-workspace",
            dependency_path=".flext-deps/flext-core",
            workspace_members=("flext-core", "flext-cli"),
        ),
        projects={
            "flext-core": u.Infra.Tests.create_path_sync_pyproject(name="flext-core"),
            "flext-cli": u.Infra.Tests.create_path_sync_pyproject(
                name="flext-cli",
                dependency_path=".flext-deps/flext-core",
            ),
        },
        gitmodules_members=("flext-core", "flext-cli"),
    )
    before_root = (workspace / "pyproject.toml").read_text(encoding="utf-8")
    before_cli = (workspace / "flext-cli" / "pyproject.toml").read_text(
        encoding="utf-8",
    )

    exit_code = main([
        "deps",
        "path-sync",
        "--workspace",
        str(workspace),
        "--mode",
        "workspace",
    ])

    tm.that(exit_code, eq=0)
    tm.that(
        (workspace / "pyproject.toml").read_text(encoding="utf-8"),
        eq=before_root,
    )
    tm.that(
        (workspace / "flext-cli" / "pyproject.toml").read_text(encoding="utf-8"),
        eq=before_cli,
    )


def test_execute_only_rewrites_selected_projects(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_path_sync_workspace(
        tmp_path,
        root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
            name="flext-workspace",
            dependency_path=".flext-deps/flext-core",
            workspace_members=("flext-core", "flext-api", "flext-cli"),
        ),
        projects={
            "flext-core": u.Infra.Tests.create_path_sync_pyproject(name="flext-core"),
            "flext-cli": u.Infra.Tests.create_path_sync_pyproject(
                name="flext-cli",
                dependency_path=".flext-deps/flext-core",
            ),
            "flext-api": u.Infra.Tests.create_path_sync_pyproject(
                name="flext-api",
                dependency_path=".flext-deps/flext-core",
            ),
        },
    )
    before_root = (workspace / "pyproject.toml").read_text(encoding="utf-8")
    before_api = (workspace / "flext-api" / "pyproject.toml").read_text(
        encoding="utf-8",
    )
    exit_code = FlextInfraUtilitiesDependencyPathSync().execute(
        FlextInfraModelsDeps.PathSyncCommand(
            workspace=str(workspace),
            apply=True,
            projects=["flext-cli"],
            mode="workspace",
        )
    )

    tm.that(exit_code, eq=0)
    tm.that(
        (workspace / "pyproject.toml").read_text(encoding="utf-8"),
        eq=before_root,
    )
    tm.that(
        (workspace / "flext-api" / "pyproject.toml").read_text(encoding="utf-8"),
        eq=before_api,
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


def test_main_keeps_uv_workspace_members_limited_to_real_members(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_path_sync_workspace(
        tmp_path,
        root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
            name="flext-workspace",
            dependency_path=".flext-deps/flext-core",
            workspace_members=("flext-core",),
        ),
        projects={
            "flext-core": u.Infra.Tests.create_path_sync_pyproject(name="flext-core"),
            "algar-oud-mig": u.Infra.Tests.create_path_sync_pyproject(
                name="algar-oud-mig",
                dependency_path=".flext-deps/flext-core",
            ),
        },
        gitmodules_members=("flext-core",),
    )

    exit_code = main(["deps", "path-sync", "--workspace", str(workspace), "--apply"])

    tm.that(exit_code, eq=0)
    tm.that(
        _string_list_value(
            workspace / "pyproject.toml",
            "tool",
            "uv",
            "workspace",
            "members",
        ),
        eq=["flext-core"],
    )
    assert "algar-oud-mig" not in _mapping_value(
        workspace / "pyproject.toml",
        "tool",
        "uv",
        "sources",
    )
