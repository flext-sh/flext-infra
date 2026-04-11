from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import main
from tests import u


def test_main_returns_error_for_missing_workspace_root(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    exit_code = main([
        "deps",
        "path-sync",
        "--workspace",
        str(missing_root),
        "--mode",
        "workspace",
    ])

    tm.that(exit_code, eq=1)


def test_main_returns_error_for_invalid_root_pyproject(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_path_sync_workspace(
        tmp_path,
        root_pyproject="invalid toml [[[",
    )

    exit_code = main([
        "deps",
        "path-sync",
        "--workspace",
        str(workspace),
        "--mode",
        "workspace",
    ])

    tm.that(exit_code, eq=1)


def test_main_returns_error_for_invalid_member_project_pyproject(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_path_sync_workspace(
        tmp_path,
        root_pyproject=u.Infra.Tests.create_path_sync_pyproject(
            name="flext-workspace",
            dependency_path=".flext-deps/flext-core",
            workspace_members=("flext-core",),
        ),
        projects={"flext-core": "invalid toml [[["},
        gitmodules_members=("flext-core",),
    )

    exit_code = main([
        "deps",
        "path-sync",
        "--workspace",
        str(workspace),
        "--mode",
        "workspace",
    ])

    tm.that(exit_code, eq=1)
