"""Tests for the public constants consolidator command service."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import pytest
from flext_tests import tm

from tests import c, t, u


def test_execute_uses_codegen_project_discovery_and_project_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discover_called = 0
    requested_roots: MutableSequence[Path] = []
    project_a = u.Infra.Tests.create_project_info(
        tmp_path / "nested" / c.Infra.Tests.Fixtures.Codegen.PROJECT_A_NAME,
        name=c.Infra.Tests.Fixtures.Codegen.PROJECT_A_NAME,
        stack=c.Infra.Tests.Fixtures.Codegen.PROJECT_STACK,
    )
    project_b = u.Infra.Tests.create_project_info(
        tmp_path / "nested" / c.Infra.Tests.Fixtures.Codegen.PROJECT_B_NAME,
        name=c.Infra.Tests.Fixtures.Codegen.PROJECT_B_NAME,
        stack=c.Infra.Tests.Fixtures.Codegen.PROJECT_STACK,
    )

    def _discover_codegen_projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ):
        nonlocal discover_called
        discover_called += 1
        return u.Infra.Tests.ok_result((project_a, project_b))

    def _discover_projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ):
        message = "execute() must use discover_codegen_projects()"
        raise AssertionError(message)

    def _find_package_dir(project_root: Path) -> Path | None:
        requested_roots.append(project_root)
        return None

    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "discover_codegen_projects",
        _discover_codegen_projects,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "discover_projects",
        _discover_projects,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "find_package_dir",
        _find_package_dir,
    )

    result = u.Infra.Tests.consolidate_codegen(
        workspace_root=tmp_path,
        project=c.Infra.Tests.Fixtures.Codegen.PROJECT_B_NAME,
        dry_run=True,
    )

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
    project = u.Infra.Tests.create_project_info(
        project_root,
        name=c.Infra.Tests.Fixtures.Codegen.DEMO_PROJECT_NAME,
        stack=c.Infra.Tests.Fixtures.Codegen.PROJECT_STACK,
        package_name=c.Infra.Tests.Fixtures.Codegen.PACKAGE_NAME,
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
    ):
        return u.Infra.Tests.ok_result((project,))

    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "discover_codegen_projects",
        _discover_codegen_projects,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "find_package_dir",
        lambda _project_root: package_dir,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "discover_project_package_name",
        lambda **_kwargs: c.Infra.Tests.Fixtures.Codegen.PACKAGE_NAME,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "discover_project_aliases",
        lambda _project_root: {"c": "c"},
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "resolve_constants_facade",
        lambda _package_name: "facade",
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "build_value_map",
        lambda _facade: {},
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "init_rope_project",
        lambda root: rope_roots.append(root) or rope,
    )
    u.Infra.Tests.patch_public_infra(
        monkeypatch,
        "iter_directory_python_files",
        lambda _package_dir: (),
    )

    result = u.Infra.Tests.consolidate_codegen(
        workspace_root=tmp_path,
        dry_run=True,
    )

    tm.ok(result)
    tm.that(tuple(rope_roots), eq=(project_root,))
    tm.that(rope.closed, eq=True)


__all__: t.StrSequence = []
