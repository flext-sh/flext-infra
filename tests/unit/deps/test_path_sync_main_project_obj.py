from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
import tomlkit
from flext_tests import tm
from tomlkit.toml_document import TOMLDocument

from tests import m, r, u


def _project(path: Path) -> m.Infra.ProjectInfo:
    return m.Infra.ProjectInfo(
        path=path,
        name="test",
        stack="test-stack",
        has_tests=False,
        has_src=False,
    )


class _SilentLogger:
    """No-op logger mock for path_sync_module tests."""

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

    monkeypatch.setattr(
        "flext_infra.FlextInfraUtilitiesDiscovery.discover_projects",
        _discover_projects,
    )
    monkeypatch.setattr(
        u.Cli,
        "toml_read_document",
        staticmethod(_read_document),
    )

    tm.that(u.Infra.main(), eq=0)


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

    monkeypatch.setattr(
        "flext_infra.FlextInfraUtilitiesDiscovery.discover_projects",
        _discover_projects,
    )
    monkeypatch.setattr(
        u.Cli,
        "toml_read_document",
        staticmethod(_read_document),
    )

    tm.that(u.Infra.main(), eq=0)
