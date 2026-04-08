from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm
from tests import FlextInfraTestHelpers as h, m
from tomlkit.toml_document import TOMLDocument

from flext_core import r
from flext_infra import FlextInfraDependencyPathSync, path_sync as path_sync_module


def _project(path: Path) -> m.Infra.ProjectInfo:
    return m.Infra.ProjectInfo(
        path=path,
        name="test",
        stack="test-stack",
        has_tests=False,
        has_src=False,
    )


class _SilentLogger:
    """No-op logger mock for path_sync tests."""

    def info(self, _message: str) -> None:
        pass


def test_main_project_obj_not_dict_first_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").touch()

    def _discover_projects(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

    def _read_document(_path: Path) -> r[TOMLDocument]:
        return r[TOMLDocument].ok(tomlkit.parse('[project]\nvalue = "not-a-dict"\n'))

    monkeypatch.setattr(sys, "argv", ["sync-paths", "--workspace", str(tmp_path)])
    monkeypatch.setattr(
        "flext_infra.FlextInfraUtilitiesDiscovery.discover_projects",
        _discover_projects,
    )
    monkeypatch.setattr(
        path_sync_module.u.Cli,
        "toml_read_document",
        staticmethod(_read_document),
    )

    monkeypatch.setattr(FlextInfraDependencyPathSync, "_log", _SilentLogger())
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)


def test_main_project_obj_not_dict_second_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    def _discover_projects(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

    def _read_document(_path: Path) -> r[TOMLDocument]:
        return r[TOMLDocument].ok(tomlkit.parse('[project]\nvalue = "not-a-dict"\n'))

    monkeypatch.setattr(sys, "argv", ["sync-paths", "--workspace", str(tmp_path)])
    monkeypatch.setattr(
        "flext_infra.FlextInfraUtilitiesDiscovery.discover_projects",
        _discover_projects,
    )
    monkeypatch.setattr(
        path_sync_module.u.Cli,
        "toml_read_document",
        staticmethod(_read_document),
    )

    monkeypatch.setattr(FlextInfraDependencyPathSync, "_log", _SilentLogger())
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)


def test_helpers_alias_is_reachable_project_obj() -> None:
    tm.that(hasattr(h, "assert_ok"), eq=True)
