"""Behavior contract for FlextInfraUtilitiesScopeSelector.scope_resolve.

Covers each ``c.Infra.ScopeLevel`` (workspace, project, projects, files,
module, namespace), determinism (sorted + deduplicated file lists),
workspace-root containment (path-traversal escape attempts return
``r.fail``), and the explicit-files validation surface.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from flext_infra._models.scope import FlextInfraModelsScope
from tests import c, m, u  # noqa: F401  (m kept for narrowing parity)


class TestsFlextInfraUtilitiesScopeSelector:
    """Behavior contract for the scope selector."""

    @staticmethod
    def _scaffold_workspace(tmp_path: Path) -> Path:
        # Build a tiny workspace with two projects. Each project has a
        # canonical ``src/<package>/`` layout with one models file plus a
        # second non-canonical module so MODULE / NAMESPACE selectors have
        # something deterministic to resolve.
        workspace = tmp_path / "workspace"
        for project in ("flext_alpha", "flext_beta"):
            pkg_dir = workspace / project / "src" / project
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
            (pkg_dir / "models.py").write_text("class Anchor: ...\n", encoding="utf-8")
            (pkg_dir / "extras.py").write_text("VALUE = 1\n", encoding="utf-8")
            (workspace / project / "pyproject.toml").write_text(
                textwrap.dedent(
                    f"""\
                    [project]
                    name = "{project.replace("_", "-")}"
                    version = "0.1.0"
                    """,
                ),
                encoding="utf-8",
            )
        (workspace / "pyproject.toml").write_text(
            textwrap.dedent(
                """\
                [project]
                name = "workspace"
                version = "0.1.0"

                [tool.flext.workspace]
                attached = false
                """,
            ),
            encoding="utf-8",
        )
        return workspace

    def test_workspace_level_lists_all_python_files_sorted(
        self, tmp_path: Path
    ) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=workspace)
        assert result.success, result.error
        resolution = result.value
        assert isinstance(resolution, FlextInfraModelsScope.ScopeResolution)
        assert resolution.level is c.Infra.ScopeLevel.WORKSPACE
        assert resolution.workspace_root == workspace
        assert list(resolution.files) == sorted(resolution.files)
        assert len(resolution.files) == len(set(resolution.files))
        assert all(file.is_relative_to(workspace) for file in resolution.files)
        assert all(file.suffix == ".py" for file in resolution.files)
        assert any(file.name == "models.py" for file in resolution.files)

    def test_project_level_filters_to_one_project_tree(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(workspace_root=workspace, project="flext_alpha")
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.PROJECT
        assert all("flext_alpha" in file.parts for file in resolution.files)
        assert not any("flext_beta" in file.parts for file in resolution.files)

    def test_projects_level_unions_named_projects(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=workspace, projects=("flext_alpha", "flext_beta")
        )
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.PROJECTS
        names = {part for file in resolution.files for part in file.parts}
        assert "flext_alpha" in names
        assert "flext_beta" in names

    def test_files_level_validates_each_file_inside_workspace(
        self, tmp_path: Path
    ) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        target = workspace / "flext_alpha" / "src" / "flext_alpha" / "models.py"
        result = u.Infra.scope_resolve(workspace_root=workspace, files=(target,))
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.FILES
        assert tuple(resolution.files) == (target.resolve(),)

    def test_files_level_rejects_path_traversal_escape(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        outside = tmp_path / "outside.py"
        outside.write_text("X = 1\n", encoding="utf-8")
        result = u.Infra.scope_resolve(workspace_root=workspace, files=(outside,))
        assert result.success is False
        assert result.error
        assert "outside" in result.error

    def test_module_level_resolves_dotted_path_to_file(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=workspace, module="flext_alpha.extras"
        )
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.MODULE
        assert len(resolution.files) == 1
        assert resolution.files[0].name == "extras.py"

    def test_namespace_level_targets_canonical_facade_within_project(
        self, tmp_path: Path
    ) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=workspace, project="flext_alpha", namespace="m"
        )
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.NAMESPACE
        assert all(file.name == "models.py" for file in resolution.files)
        assert len(resolution.files) == 1

    def test_resolution_is_deterministic_across_runs(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        first = u.Infra.scope_resolve(workspace_root=workspace).value
        second = u.Infra.scope_resolve(workspace_root=workspace).value
        assert tuple(first.files) == tuple(second.files)

    def test_unknown_project_returns_fail(self, tmp_path: Path) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        result = u.Infra.scope_resolve(
            workspace_root=workspace, project="flext_does_not_exist"
        )
        assert result.success is False
        assert result.error

    @pytest.mark.parametrize(
        "ns",
        ["c", "p", "t", "u"],
    )
    def test_namespace_level_other_aliases_dispatch(
        self, tmp_path: Path, ns: str
    ) -> None:
        workspace = self._scaffold_workspace(tmp_path)
        # Add a constants.py / protocols.py / typings.py / utilities.py
        # under flext_alpha so each canonical alias has a target.
        canon_path = (
            workspace
            / "flext_alpha"
            / "src"
            / "flext_alpha"
            / c.Infra.NAMESPACE_TO_CANONICAL_FILENAME[ns]
        )
        canon_path.write_text("MARKER = 1\n", encoding="utf-8")
        result = u.Infra.scope_resolve(
            workspace_root=workspace, project="flext_alpha", namespace=ns
        )
        assert result.success, result.error
        resolution = result.value
        assert resolution.level is c.Infra.ScopeLevel.NAMESPACE
        assert resolution.files
        assert resolution.files[0].name == c.Infra.NAMESPACE_TO_CANONICAL_FILENAME[ns]
