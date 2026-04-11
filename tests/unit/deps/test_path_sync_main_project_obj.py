from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_tests import tm

from flext_infra import FlextInfraUtilitiesDependencyPathSync
from tests import m, r


def _project(path: Path) -> m.Infra.ProjectInfo:
    return m.Infra.ProjectInfo(
        path=path,
        name="test",
        stack="test-stack",
        has_tests=False,
        has_src=False,
    )


def _service(
    projects: Sequence[m.Infra.ProjectInfo],
) -> FlextInfraUtilitiesDependencyPathSync:
    class _TestPathSync(FlextInfraUtilitiesDependencyPathSync):
        @staticmethod
        @override
        def discover_projects(
            workspace_root: Path,
        ) -> r[Sequence[m.Infra.ProjectInfo]]:
            _ = workspace_root
            return r[Sequence[m.Infra.ProjectInfo]].ok(projects)

    return _TestPathSync()


def test_main_project_obj_not_dict_first_loop(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        'project = "not-a-dict"\n',
        encoding="utf-8",
    )
    tm.that(
        _service([]).execute(
            m.Infra.PathSyncCommand.model_validate({
                "workspace": str(tmp_path),
                "mode": "standalone",
            })
        ),
        eq=0,
    )


def test_main_project_obj_not_dict_second_loop(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "workspace"\n',
        encoding="utf-8",
    )
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text(
        'project = "not-a-dict"\n',
        encoding="utf-8",
    )
    tm.that(
        _service([_project(project_dir)]).execute(
            m.Infra.PathSyncCommand.model_validate({
                "workspace": str(tmp_path),
                "mode": "standalone",
            })
        ),
        eq=0,
    )
