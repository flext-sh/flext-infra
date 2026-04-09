"""Edge-case tests for FlextInfraDiscoveryService.

Covers uncovered lines: non-git projects, permission errors,
OSError handling, and submodule name extraction.
"""

from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm

from tests import u


class TestFlextInfraDiscoveryServiceUncoveredLines:
    def test_discover_projects_includes_non_git_flext_projects(
        self,
        tmp_path: Path,
    ) -> None:
        service = u.Infra()
        workspace_root = tmp_path
        non_git_dir = workspace_root / "non_git_project"
        non_git_dir.mkdir()
        (non_git_dir / "pyproject.toml").write_text(
            "[project]\nname='non_git_project'\ndependencies=['flext-core>=0.1.0']\n",
            encoding="utf-8",
        )
        result = service.discover_projects(workspace_root)
        tm.ok(result)
        assert len(result.value) == 1
        assert result.value[0].name == "non_git_project"
        assert result.value[0].path == non_git_dir

    def test_find_all_pyproject_files_with_nonexistent_path(self) -> None:
        service = u.Infra()
        nonexistent = Path("/nonexistent/path/to/workspace")
        result = service.find_all_pyproject_files(nonexistent)
        tm.ok(result)
        assert result.value == []

    def test_find_all_pyproject_files_with_permission_error(
        self,
        tmp_path: Path,
    ) -> None:
        service = u.Infra()
        (tmp_path / "pyproject.toml").touch()
        result = service.find_all_pyproject_files(tmp_path)
        tm.ok(result)
        assert len(result.value) >= 1

    def test_discover_projects_skips_no_pyproject_no_gomod(
        self,
        tmp_path: Path,
    ) -> None:
        service = u.Infra()
        workspace_root = tmp_path
        proj = workspace_root / "incomplete_project"
        proj.mkdir()
        (proj / "pyproject.toml").write_text(
            "[project]\nname='incomplete_project'\n",
            encoding="utf-8",
        )
        result = service.discover_projects(workspace_root)
        tm.ok(result)
        assert not result.value

    def test_find_all_pyproject_files_oserror_on_rglob(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        service = u.Infra()

        def mock_rglob(self: Path, pattern: str) -> None:
            msg = "permission denied"
            raise OSError(msg)

        result = service.find_all_pyproject_files(tmp_path)
        tm.fail(result)
        assert isinstance(result.error, str)
        assert "pyproject file scan failed" in result.error

    def test_submodule_names_with_gitmodules_oserror(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        workspace_root = tmp_path
        gitmodules = workspace_root / ".gitmodules"
        gitmodules.touch()

        def mock_read_text(self: Path, encoding: str | None = None) -> None:
            msg = "permission denied"
            raise OSError(msg)

        result = u.Infra._submodule_names(workspace_root)
        assert result == set()

    def test_submodule_names_with_valid_gitmodules(self, tmp_path: Path) -> None:
        workspace_root = tmp_path
        gitmodules = workspace_root / ".gitmodules"
        gitmodules.write_text(
            '[submodule "sub1"]\n    path = submodule-one\n[submodule "sub2"]\n    path = submodule-two\n',
            encoding="utf-8",
        )
        result = u.Infra._submodule_names(workspace_root)
        assert result == {"submodule-one", "submodule-two"}
