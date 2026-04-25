"""Tests for u.Infra.scope_resolve — typed scope selector (Lane A-CH Task 0.4).

Validates each level (module, namespace, project, projects, files, workspace),
deterministic ordering, deduplication, path-traversal rejection, and namespace
alias parsing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import m, u


def _make_workspace(tmp_path: Path, *, project: str = "flext-foo") -> Path:
    """Build a minimal workspace tree with one project."""
    proj_dir = tmp_path / project
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    pkg = proj_dir / "src" / project.replace("-", "_")
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models.py").write_text("X = 1\n", encoding="utf-8")
    return tmp_path


class TestsFlextInfraUtilitiesScopeSelector:
    """Behavior contract for scope_resolve."""

    def test_workspace_default_when_no_selector(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws)
        assert result.success is True
        assert result.value.level == m.Infra.ScopeLevel.WORKSPACE

    def test_resolves_module_to_single_file(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=ws, module="flext_foo.models"
        )
        assert result.success is True
        resolution = result.value
        assert resolution.level == m.Infra.ScopeLevel.MODULE
        assert resolution.module == "flext_foo.models"
        assert len(resolution.files) == 1
        assert resolution.files[0].name == "models.py"

    def test_module_unknown_returns_fail(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=ws, module="flext_does_not_exist.x"
        )
        assert result.success is False

    def test_module_path_traversal_returns_fail(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws, module="..escape")
        assert result.success is False

    def test_resolves_namespace_alias_and_path(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws, namespace="m.Cli")
        assert result.success is True
        resolution = result.value
        assert resolution.level == m.Infra.ScopeLevel.NAMESPACE
        assert resolution.namespace_alias == "m"
        assert resolution.namespace_path == ("Cli",)

    def test_namespace_unknown_alias_returns_fail(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws, namespace="zzz.X")
        assert result.success is False

    def test_resolves_single_project(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws, project="flext-foo")
        assert result.success is True
        assert result.value.level == m.Infra.ScopeLevel.PROJECT
        assert result.value.projects == ("flext-foo",)

    def test_project_missing_returns_fail(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=ws, project="flext-missing")
        assert result.success is False

    def test_resolves_multiple_projects_sorted_deduplicated(
        self, tmp_path: Path
    ) -> None:
        ws = _make_workspace(tmp_path)
        # add second project
        (ws / "flext-bar").mkdir()
        (ws / "flext-bar" / "pyproject.toml").write_text("", encoding="utf-8")
        result = u.Infra.scope_resolve(
            workspace_root=ws, projects=("flext-foo", "flext-bar", "flext-foo")
        )
        assert result.success is True
        assert result.value.level == m.Infra.ScopeLevel.PROJECTS
        assert result.value.projects == ("flext-bar", "flext-foo")

    def test_resolves_files_sorted_deduplicated(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        target = ws / "flext-foo" / "src" / "flext_foo" / "models.py"
        result = u.Infra.scope_resolve(
            workspace_root=ws,
            files=(target, target),
        )
        assert result.success is True
        assert result.value.level == m.Infra.ScopeLevel.FILES
        assert len(result.value.files) == 1

    def test_files_outside_workspace_returns_fail(self, tmp_path: Path) -> None:
        ws = _make_workspace(tmp_path)
        outside = tmp_path / ".." / "outside.py"
        result = u.Infra.scope_resolve(workspace_root=ws, files=(outside,))
        assert result.success is False
