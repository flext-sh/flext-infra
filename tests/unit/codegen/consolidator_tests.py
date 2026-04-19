"""Tests for the public constants consolidator command service."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from tests import c, m, p, t, u


def test_execute_uses_codegen_project_discovery_and_project_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discover_called = 0
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
    for project in (project_a, project_b):
        package_dir = project.path / "src" / project.name.replace("-", "_")
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")

    def _projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> p.Result[tuple[m.Infra.ProjectInfo, ...]]:
        nonlocal discover_called
        discover_called += 1
        return u.Infra.Tests.ok_result((project_a, project_b))

    def _unexpected_public_project_discovery(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> p.Result[tuple[m.Infra.ProjectInfo, ...]]:
        message = "execute() must use projects()"
        raise AssertionError(message)

    # Patch flext_infra.u (not tests.u) since consolidator imports from flext_infra
    monkeypatch.setattr(u.Infra, "projects", staticmethod(_projects))
    monkeypatch.setattr(
        u.Infra,
        "discover_projects",
        staticmethod(_unexpected_public_project_discovery),
    )

    result = u.Infra.Tests.consolidate_codegen(
        workspace_root=tmp_path,
        project=c.Infra.Tests.Fixtures.Codegen.PROJECT_B_NAME,
        dry_run=True,
    )

    tm.ok(result)
    tm.that(discover_called, eq=1)
    tm.that(result.value, has="Found 0 canonical matches across 1 projects")


def test_execute_scans_real_package_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "projects" / "demo"
    package_dir = project_root / "src" / "demo_pkg"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "constants.py").write_text(
        "class DemoConstants:\n    pass\n\nc = DemoConstants\n",
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    project = u.Infra.Tests.create_project_info(
        project_root,
        name=c.Infra.Tests.Fixtures.Codegen.DEMO_PROJECT_NAME,
        stack=c.Infra.Tests.Fixtures.Codegen.PROJECT_STACK,
        package_name=c.Infra.Tests.Fixtures.Codegen.PACKAGE_NAME,
    )

    def _projects(
        *_args: t.Scalar,
        **_kwargs: t.Scalar,
    ) -> p.Result[tuple[m.Infra.ProjectInfo, ...]]:
        return u.Infra.Tests.ok_result((project,))

    # Patch flext_infra.u (not tests.u) since consolidator imports from flext_infra
    monkeypatch.setattr(u.Infra, "projects", staticmethod(_projects))

    result = u.Infra.Tests.consolidate_codegen(
        workspace_root=tmp_path,
        dry_run=True,
    )

    tm.ok(result)
    tm.that(result.value, has="Found 0 canonical matches across 1 projects")


__all__: t.StrSequence = []
