"""Tests for the public constants consolidator command service."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, p, r, t

from flext_infra import FlextInfraCodegenConsolidator, u as infra_u


def test_execute_uses_codegen_project_discovery_and_project_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discover_called = 0
    requested_roots: MutableSequence[Path] = []
    project_a = m.Infra.ProjectInfo(
        name="project-a",
        path=tmp_path / "nested" / "project-a",
        stack="python/flext",
    )
    project_b = m.Infra.ProjectInfo(
        name="project-b",
        path=tmp_path / "nested" / "project-b",
        stack="python/flext",
    )

    def _discover_codegen_projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> r[Sequence[p.Infra.ProjectInfo]]:
        nonlocal discover_called
        discover_called += 1
        return r[Sequence[p.Infra.ProjectInfo]].ok((project_a, project_b))

    def _discover_projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> r[Sequence[p.Infra.ProjectInfo]]:
        message = "execute() must use discover_codegen_projects()"
        raise AssertionError(message)

    def _find_package_dir(project_root: Path) -> Path | None:
        requested_roots.append(project_root)
        return None

    monkeypatch.setattr(
        infra_u.Infra,
        "discover_codegen_projects",
        staticmethod(_discover_codegen_projects),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "discover_projects",
        staticmethod(_discover_projects),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "find_package_dir",
        staticmethod(_find_package_dir),
    )

    result = FlextInfraCodegenConsolidator.model_validate({
        "workspace_root": tmp_path,
        "project": "project-b",
        "dry_run": True,
    }).execute()

    tm.ok(result)
    tm.that(discover_called, eq=1)
    tm.that(tuple(requested_roots), eq=(project_b.path,))
    tm.that(result.value, has="Found 0 canonical matches across 1 projects")


def test_execute_uses_project_path_and_closes_rope_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "projects" / "demo"
    package_dir = project_root / "src" / "demo_pkg"
    package_dir.mkdir(parents=True)
    project = m.Infra.ProjectInfo(
        name="demo",
        path=project_root,
        stack="python/flext",
        package_name="demo_pkg",
    )
    rope_roots: MutableSequence[Path] = []

    class _FakeRope:
        closed = False

        def close(self) -> None:
            self.closed = True

    rope = _FakeRope()

    def _discover_codegen_projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> r[Sequence[p.Infra.ProjectInfo]]:
        return r[Sequence[p.Infra.ProjectInfo]].ok((project,))

    monkeypatch.setattr(
        infra_u.Infra,
        "discover_codegen_projects",
        staticmethod(_discover_codegen_projects),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "find_package_dir",
        staticmethod(lambda _project_root: package_dir),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "discover_project_package_name",
        staticmethod(lambda **_kwargs: "demo_pkg"),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "discover_project_aliases",
        staticmethod(lambda _project_root: {"c": "c"}),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "resolve_constants_facade",
        staticmethod(lambda _package_name: "facade"),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "build_value_map",
        staticmethod(lambda _facade: {}),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "init_rope_project",
        staticmethod(lambda root: rope_roots.append(root) or rope),
    )
    monkeypatch.setattr(
        infra_u.Infra,
        "iter_directory_python_files",
        staticmethod(lambda _package_dir: ()),
    )

    result = FlextInfraCodegenConsolidator.model_validate({
        "workspace_root": tmp_path,
        "dry_run": True,
    }).execute()

    tm.ok(result)
    tm.that(tuple(rope_roots), eq=(project_root,))
    tm.that(rope.closed, eq=True)


__all__: t.StrSequence = []
