from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
import tomlkit
from flext_tests import tf, tm
from tomlkit.toml_document import TOMLDocument

from flext_core import r
from flext_infra import (
    FlextInfraExtraPathsManager,
    t,
)


@pytest.fixture
def pyright_content() -> str:
    return "[tool.pyright]\nextraPaths = []\n"


def _create_pyproject(directory: Path, content: str) -> Path:
    return tf.create_in(content=content, name="pyproject.toml", directory=directory)


_TEST_WORKSPACE_ROOT = Path(__file__).resolve().parent


def _manager(
    workspace_root: Path | None = None,
) -> FlextInfraExtraPathsManager:
    return FlextInfraExtraPathsManager(
        workspace_root=workspace_root or _TEST_WORKSPACE_ROOT
    )


@pytest.mark.parametrize(
    ("mode", "dry_run", "project_dirs", "expect_fail", "expect_has"),
    [
        ("project", False, ["proj"], False, None),
        ("project", True, ["proj"], False, "old"),
        ("root", False, None, False, None),
        ("none", True, [], False, None),
        ("none", True, None, False, None),
    ],
)
def test_sync_extra_paths_success_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pyright_content: str,
    mode: str,
    dry_run: bool,
    project_dirs: t.StrSequence | None,
    expect_fail: bool,
    expect_has: str | None,
) -> None:
    project_dirs_arg: Sequence[Path] | None = None
    if mode == "project":
        project = tmp_path / "proj"
        project.mkdir()
        content = (
            "[tool.pyright]\nextraPaths = ['old']\n" if dry_run else pyright_content
        )
        pyproject = _create_pyproject(project, content)
        project_dirs_arg = [project] if project_dirs else []
        result = _manager(tmp_path).sync_extra_paths(
            dry_run=dry_run,
            project_dirs=project_dirs_arg,
        )
        tm.ok(result)
        if expect_has:
            tm.that(pyproject.read_text(encoding="utf-8"), has=expect_has)
        return
    if mode == "root":
        _ = _create_pyproject(tmp_path, pyright_content)
        tm.ok(_manager(tmp_path).sync_extra_paths())
        return
    _ = _create_pyproject(tmp_path, pyright_content)
    result = _manager(tmp_path).sync_extra_paths(
        dry_run=dry_run,
        project_dirs=[] if project_dirs == [] else None,
    )
    if expect_fail:
        tm.fail(result)
        return
    tm.ok(result)


def test_sync_extra_paths_missing_root_pyproject(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = monkeypatch
    tm.fail(_manager(tmp_path).sync_extra_paths(), has="Missing")


def test_sync_extra_paths_sync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "proj"
    project.mkdir()

    def _fail_sync(
        _self: FlextInfraExtraPathsManager,
        _pyproject_path: Path,
        *,
        dry_run: bool = False,
        is_root: bool = False,
    ) -> r[bool]:
        _ = _self, _pyproject_path, dry_run, is_root
        return r[bool].fail("sync error")

    monkeypatch.setattr(FlextInfraExtraPathsManager, "sync_one", _fail_sync)
    tm.fail(
        _manager(tmp_path).sync_extra_paths(project_dirs=[project]),
        has="sync error",
    )


@pytest.mark.parametrize(
    ("mode", "argv", "expected_exit"),
    [
        ("root", ["extra_paths.py"], 0),
        ("root", ["extra_paths.py", "--dry-run"], 0),
        ("project", ["extra_paths.py", "--projects", "proj"], 0),
        (
            "multi",
            ["extra_paths.py", "--projects", "proj-a,proj-b"],
            0,
        ),
        ("abs-project", ["prog", "--projects", "project", "--dry-run"], 0),
    ],
)
def test_main_success_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pyright_content: str,
    mode: str,
    argv: t.StrSequence,
    expected_exit: int,
) -> None:
    if mode == "root":
        _ = _create_pyproject(tmp_path, pyright_content)
    if mode == "project":
        project = tmp_path / "proj"
        project.mkdir()
        _ = _create_pyproject(project, pyright_content)
    if mode == "multi":
        for name in ["proj-a", "proj-b"]:
            project = tmp_path / name
            project.mkdir()
            _ = _create_pyproject(project, pyright_content)
    if mode == "abs-project":
        project = tmp_path / "project"
        project.mkdir()
        _ = _create_pyproject(project, pyright_content)
        argv = ["prog", "--projects", str(project), "--dry-run"]
    argv = [argv[0], "--workspace", str(tmp_path), *argv[1:]]
    tm.that(FlextInfraExtraPathsManager.main(argv[1:]), eq=expected_exit)


def test_main_sync_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["extra_paths.py", "--workspace", str(tmp_path)],
    )

    def _fail_sync(
        _self: FlextInfraExtraPathsManager,
        *,
        dry_run: bool = False,
        project_dirs: Sequence[Path] | None = None,
    ) -> r[int]:
        _ = _self, dry_run, project_dirs
        return r[int].fail("sync error")

    monkeypatch.setattr(FlextInfraExtraPathsManager, "sync_extra_paths", _fail_sync)
    tm.that(FlextInfraExtraPathsManager.main(sys.argv[1:]), eq=1)


@pytest.mark.parametrize(
    ("mode", "dry_run", "expected_ok", "expect_fail"),
    [
        ("nonexistent", True, False, False),
        ("invalid", True, False, True),
        ("stubbed", False, True, False),
    ],
)
def test_sync_one_edge_cases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pyright_content: str,
    mode: str,
    dry_run: bool,
    expected_ok: bool,
    expect_fail: bool,
) -> None:
    if mode == "nonexistent":
        tm.that(
            not _manager(tmp_path)
            .sync_one(Path("/nonexistent/pyproject.toml"), dry_run=dry_run)
            .is_success,
            eq=True,
        )
        return
    if mode == "invalid":
        pyproject = _create_pyproject(tmp_path, "invalid toml {")
        result = _manager(tmp_path).sync_one(pyproject, dry_run=dry_run)
        if expect_fail:
            tm.fail(result)
            return
        tm.that(result.is_success, eq=expected_ok)
        return
    pyproject = _create_pyproject(tmp_path, pyright_content)
    doc = tomlkit.document()
    tool = tomlkit.table()
    pyright = tomlkit.table()
    pyright["extraPaths"] = tomlkit.array()
    tool["pyright"] = pyright
    doc["tool"] = tool

    def _read_document(_path: Path) -> r[TOMLDocument]:
        return r[TOMLDocument].ok(doc)

    def _write_document(_path: Path, _doc: TOMLDocument) -> r[bool]:
        return r[bool].ok(True)

    tm.ok(_manager(tmp_path).sync_one(pyproject, is_root=True, dry_run=dry_run))
