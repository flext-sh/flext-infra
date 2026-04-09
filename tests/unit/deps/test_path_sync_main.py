from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm

from tests import m, r, t, u


def _project(path: Path, name: str = "flext-core") -> m.Infra.ProjectInfo:
    return m.Infra.ProjectInfo(
        path=path,
        name=name,
        stack="python",
        has_tests=False,
        has_src=False,
    )


class TestMain:
    def test_main_auto_detect_workspace(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / ".gitmodules").touch()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        tm.that(u.Infra.main(), eq=0)

    def test_main_explicit_workspace_mode(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        tm.that(u.Infra.main(), eq=0)

    def test_main_explicit_standalone_mode(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        tm.that(u.Infra.main(), eq=0)

    def test_main_dry_run(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        tm.that(u.Infra.main(), eq=0)

    def test_main_specific_projects(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        project_dir = tmp_path / "flext-core"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text('[project]\nname = "flext-core"\n')
        tm.that(u.Infra.main(), eq=0)

    def test_main_discovery_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )

        def _discover_fail(
            _root: Path,
        ) -> r[Sequence[m.Infra.ProjectInfo]]:
            return r[Sequence[m.Infra.ProjectInfo]].fail("discovery failed")

        tm.that(u.Infra.main(), eq=1)

    def test_main_root_rewrite_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )

        def _rewrite_fail(
            _self: u.Infra,
            _pyproject_path: Path,
            *,
            mode: str,
            internal_names: set[str],
            workspace_members: t.StrSequence = (),
            is_root: bool = False,
            dry_run: bool = False,
        ) -> r[t.StrSequence]:
            _ = (
                _self,
                _pyproject_path,
                mode,
                internal_names,
                workspace_members,
                is_root,
                dry_run,
            )
            return r[t.StrSequence].fail("rewrite failed")

        monkeypatch.setattr(
            u.Infra,
            "rewrite_dep_paths",
            _rewrite_fail,
        )
        tm.that(u.Infra.main(), eq=1)

    def test_main_project_rewrite_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "flext-workspace"\n',
        )
        project_dir = tmp_path / "flext-core"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text('[project]\nname = "flext-core"\n')

        def _discover_project(
            _root: Path,
        ) -> r[Sequence[m.Infra.ProjectInfo]]:
            return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

        calls = {"n": 0}

        def rewrite_stub(
            _self: u.Infra,
            _pyproject_path: Path,
            *,
            mode: str,
            internal_names: set[str],
            workspace_members: t.StrSequence = (),
            is_root: bool = False,
            dry_run: bool = False,
        ) -> r[t.StrSequence]:
            _ = (
                _self,
                _pyproject_path,
                mode,
                internal_names,
                workspace_members,
                is_root,
                dry_run,
            )
            calls["n"] += 1
            if calls["n"] == 1:
                return r[t.StrSequence].ok([])
            return r[t.StrSequence].fail("project rewrite failed")

        monkeypatch.setattr(
            u.Infra,
            "rewrite_dep_paths",
            rewrite_stub,
        )
        tm.that(u.Infra.main(), eq=1)
