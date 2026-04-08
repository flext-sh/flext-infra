from __future__ import annotations

import sys
from collections.abc import MutableSequence, Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import c, m, r, t, u

from flext_infra import (
    FlextInfraDependencyPathSync,
)


def _workspace_root() -> Path:
    return FlextInfraDependencyPathSync.ROOT


def _project(
    path: Path,
    name: str = "flext-core",
    *,
    workspace_role: c.Infra.WorkspaceProjectRole = c.Infra.WorkspaceProjectRole.ATTACHED,
) -> m.Infra.ProjectInfo:
    return m.Infra.ProjectInfo(
        path=path,
        name=name,
        stack="python",
        has_tests=False,
        has_src=False,
        workspace_role=workspace_role,
    )


class _OutputRecorder:
    def __init__(self) -> None:
        self.calls: MutableSequence[str] = []

    def info(self, message: str) -> r[bool]:
        self.calls.append(message)
        return r[bool].ok(True)


def test_main_project_invalid_toml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-workspace"\n')
    project_dir = tmp_path / "flext-core"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("invalid toml [[[")

    def _discover_project(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

    monkeypatch.setattr(FlextInfraDependencyPathSync, "ROOT", tmp_path)
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_project)
    monkeypatch.setattr(sys, "argv", ["prog", "--workspace", str(tmp_path)])
    tm.that(FlextInfraDependencyPathSync.main(), eq=1)


def test_main_project_no_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-workspace"\n')
    project_dir = tmp_path / "flext-core"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\n")

    def _discover_project(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

    monkeypatch.setattr(FlextInfraDependencyPathSync, "ROOT", tmp_path)
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_project)
    monkeypatch.setattr(sys, "argv", ["prog", "--workspace", str(tmp_path)])
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)


def test_main_project_non_string_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-workspace"\n')
    project_dir = tmp_path / "flext-core"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 123\n")

    def _discover_project(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([_project(project_dir)])

    monkeypatch.setattr(FlextInfraDependencyPathSync, "ROOT", tmp_path)
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_project)
    monkeypatch.setattr(sys, "argv", ["prog", "--workspace", str(tmp_path)])
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)


def test_main_discovery_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _discover_fail(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].fail("discovery failed")

    monkeypatch.setattr(u.Infra, "discover_projects", _discover_fail)
    monkeypatch.setattr(sys, "argv", ["sync-paths"])
    tm.that(FlextInfraDependencyPathSync.main(), eq=1)


def test_main_no_changes_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _discover_none(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([])

    def _rewrite_ok(
        _self: FlextInfraDependencyPathSync,
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
        return r[t.StrSequence].ok([])

    monkeypatch.setattr(sys, "argv", ["sync-paths"])
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_none)
    monkeypatch.setattr(FlextInfraDependencyPathSync, "rewrite_dep_paths", _rewrite_ok)
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)


def test_workspace_root_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deep = tmp_path / "a" / "b" / "c" / "d" / "e" / "f"
    deep.mkdir(parents=True)

    def _resolve(_self: Path) -> Path:
        return deep / "test.py"

    monkeypatch.setattr(Path, "resolve", _resolve)
    tm.that(_workspace_root().is_absolute(), eq=True)


def test_main_with_changes_and_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _OutputRecorder()

    def _discover_none(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([])

    def _rewrite_changes(
        _self: FlextInfraDependencyPathSync,
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
        return r[t.StrSequence].ok(["  PEP621: old -> new"])

    monkeypatch.setattr(sys, "argv", ["sync-paths", "--dry-run"])
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_none)
    monkeypatch.setattr(
        FlextInfraDependencyPathSync,
        "rewrite_dep_paths",
        _rewrite_changes,
    )
    monkeypatch.setattr(FlextInfraDependencyPathSync, "_log", recorder)
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)
    tm.that(any("[DRY-RUN]" in call for call in recorder.calls), eq=True)


def test_main_with_changes_no_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _OutputRecorder()

    def _discover_none(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([])

    def _rewrite_changes(
        _self: FlextInfraDependencyPathSync,
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
        return r[t.StrSequence].ok(["  PEP621: old -> new"])

    monkeypatch.setattr(sys, "argv", ["sync-paths"])
    monkeypatch.setattr(u.Infra, "discover_projects", _discover_none)
    monkeypatch.setattr(
        FlextInfraDependencyPathSync,
        "rewrite_dep_paths",
        _rewrite_changes,
    )
    monkeypatch.setattr(FlextInfraDependencyPathSync, "_log", recorder)
    tm.that(FlextInfraDependencyPathSync.main(), eq=0)
    assert len(recorder.calls) > 0


def test_workspace_members_only_include_flext_projects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "flext-workspace"\n')
    flext_core = tmp_path / "flext-core"
    flext_core.mkdir()
    (flext_core / "pyproject.toml").write_text('[project]\nname = "flext-core"\n')
    flexcore = tmp_path / "flexcore"
    flexcore.mkdir()
    (flexcore / "pyproject.toml").write_text('[project]\nname = "flexcore"\n')
    algar = tmp_path / "algar-oud-mig"
    algar.mkdir()
    (algar / "pyproject.toml").write_text('[project]\nname = "algar-oud-mig"\n')
    seen: list[t.StrSequence] = []

    def _discover(
        _root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return r[Sequence[m.Infra.ProjectInfo]].ok([
            _project(
                flext_core,
                "flext-core",
                workspace_role=c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER,
            ),
            _project(flexcore, "flexcore"),
            _project(algar, "algar-oud-mig"),
        ])

    def _rewrite_ok(
        _self: FlextInfraDependencyPathSync,
        _pyproject_path: Path,
        *,
        mode: str,
        internal_names: set[str],
        workspace_members: t.StrSequence = (),
        is_root: bool = False,
        dry_run: bool = False,
    ) -> r[t.StrSequence]:
        _ = (_self, _pyproject_path, mode, internal_names, is_root, dry_run)
        seen.append(tuple(workspace_members))
        return r[t.StrSequence].ok([])

    monkeypatch.setattr(FlextInfraDependencyPathSync, "ROOT", tmp_path)
    monkeypatch.setattr(u.Infra, "discover_projects", _discover)
    monkeypatch.setattr(FlextInfraDependencyPathSync, "rewrite_dep_paths", _rewrite_ok)
    monkeypatch.setattr(sys, "argv", ["sync-paths", "--workspace", str(tmp_path)])

    tm.that(FlextInfraDependencyPathSync.main(), eq=0)
    assert {tuple(item) for item in seen} == {("flext-core",)}
