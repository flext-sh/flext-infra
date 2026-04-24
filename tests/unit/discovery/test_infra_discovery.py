"""Tests for FlextInfraDiscoveryService.

Tests cover project discovery, pyproject file discovery, and error handling.
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path

import pytest
from flext_tests import tm

from tests import c, m, t, u


class TestsFlextInfraDiscoveryInfraDiscovery:
    @pytest.fixture
    def service(self) -> u.Infra:
        return u.Infra()

    @pytest.fixture
    def workspace_with_projects(self, tmp_path: Path) -> Path:
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace'\n\n"
            "[tool.uv.workspace]\n"
            "members = ['project2']\n",
            encoding="utf-8",
        )
        proj1 = tmp_path / "project1"
        proj1.mkdir()
        (proj1 / "pyproject.toml").write_text(
            "[project]\nname='project1'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        (proj1 / "src").mkdir()
        (proj1 / "tests").mkdir()
        proj2 = tmp_path / "project2"
        proj2.mkdir()
        (proj2 / "pyproject.toml").write_text(
            "[project]\nname='project2'\n",
            encoding="utf-8",
        )
        invalid = tmp_path / "invalid"
        invalid.mkdir()
        (invalid / "pyproject.toml").write_text(
            "[project]\nname='invalid'\n",
            encoding="utf-8",
        )
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "pyproject.toml").write_text(
            "[project]\nname='hidden'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        return tmp_path

    def test_discover_projects_happy_path(
        self,
        service: u.Infra,
        workspace_with_projects: Path,
    ) -> None:
        result = service.discover_projects(workspace_with_projects)
        tm.ok(result)
        projects = result.value
        assert len(projects) == 2
        assert projects[0].name == "project1"
        assert projects[1].name == "project2"
        assert projects[0].has_tests is True
        assert projects[0].has_src is True
        assert projects[1].has_src is False
        assert projects[1].has_tests is False
        assert projects[0].workspace_role == c.Infra.WorkspaceProjectRole.ATTACHED
        assert (
            projects[1].workspace_role == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
        )

    def test_discover_projects_empty_workspace(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        result = service.discover_projects(tmp_path)
        tm.ok(result)
        assert result.value == []

    def test_discover_projects_nonexistent_path(
        self,
        service: u.Infra,
    ) -> None:
        nonexistent = Path("/nonexistent/path/to/workspace")
        result = service.discover_projects(nonexistent)
        tm.fail(result)
        assert isinstance(result.error, str)
        assert isinstance(result.error, str)
        assert "discovery failed" in result.error

    def test_find_all_pyproject_files_happy_path(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "project1").mkdir()
        (tmp_path / "project1" / "pyproject.toml").touch()
        (tmp_path / "project2").mkdir()
        (tmp_path / "project2" / "pyproject.toml").touch()
        (tmp_path / "project2" / "subdir").mkdir()
        (tmp_path / "project2" / "subdir" / "pyproject.toml").touch()
        result = service.find_all_pyproject_files(tmp_path)
        tm.ok(result)
        files = result.value
        assert len(files) == 3
        assert all(f.name == "pyproject.toml" for f in files)

    def test_find_all_pyproject_files_with_skip_dirs(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "project1").mkdir()
        (tmp_path / "project1" / "pyproject.toml").touch()
        (tmp_path / "skip_me").mkdir()
        (tmp_path / "skip_me" / "pyproject.toml").touch()
        result = service.find_all_pyproject_files(
            tmp_path,
            skip_dirs=frozenset({"skip_me"}),
        )
        tm.ok(result)
        files = result.value
        assert len(files) == 1
        assert "skip_me" not in str(files[0])

    def test_find_all_pyproject_files_with_project_paths(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        proj1 = tmp_path / "project1"
        proj2 = tmp_path / "project2"
        proj1.mkdir()
        proj2.mkdir()
        (proj1 / "pyproject.toml").touch()
        (proj2 / "pyproject.toml").touch()
        result = service.find_all_pyproject_files(tmp_path, project_paths=[proj1])
        tm.ok(result)
        files = result.value
        assert len(files) == 1
        assert files[0].parent == proj1

    def test_discover_projects_result_type(
        self,
        service: u.Infra,
        workspace_with_projects: Path,
    ) -> None:
        result = service.discover_projects(workspace_with_projects)
        tm.ok(result)
        projects: Sequence[m.Infra.ProjectInfo] = result.value
        for item in projects:
            assert isinstance(item, m.Infra.ProjectInfo)

    def test_discover_projects_empty_workspace_v2(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        result = service.discover_projects(tmp_path)
        tm.ok(result)
        assert result.value == []

    def test_discover_projects_prefers_workspace_children_over_root_project(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='workspace-root'\ndependencies=['flext-core>=0.1.0']\n\n"
            "[tool.uv.workspace]\n"
            "members = ['project2']\n",
            encoding="utf-8",
        )
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / "pyproject.toml").write_text(
            "[project]\nname='project1'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / "pyproject.toml").write_text(
            "[project]\nname='project2'\n",
            encoding="utf-8",
        )

        result = service.discover_projects(tmp_path)

        tm.ok(result)
        tm.that([project.name for project in result.value], eq=["project1", "project2"])

    def test_discover_projects_derives_package_name_from_hatch_packages(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        project = tmp_path / "project1"
        package_dir = project / "src" / "custom_pkg"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (project / "pyproject.toml").write_text(
            "[project]\n"
            "name='project1'\n"
            "dependencies=['flext-core>=0.1.0']\n\n"
            "[tool.hatch.build.targets.wheel]\n"
            "packages=['src/custom_pkg']\n",
            encoding="utf-8",
        )

        result = service.discover_projects(tmp_path)

        tm.ok(result)
        assert len(result.value) == 1
        assert result.value[0].package_name == "custom_pkg"

    def test_discover_projects_accepts_standalone_governed_root_without_core_dep(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        package_dir = tmp_path / "src" / "demo_pkg"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "Makefile").write_text("check:\n\t@true\n", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\nversion='0.1.0'\n",
            encoding="utf-8",
        )

        result = service.discover_projects(tmp_path)

        tm.ok(result)
        assert len(result.value) == 1
        assert result.value[0].path == tmp_path.resolve()
        assert result.value[0].name == "demo-project"
        assert result.value[0].package_name == "demo_pkg"


__all__: t.StrSequence = []
