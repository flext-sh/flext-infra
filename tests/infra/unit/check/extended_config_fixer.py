"""Tests for FlextInfraConfigFixer — process_file, run, find, fix methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import tomlkit
from flext_tests import u

from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer


class TestConfigFixerProcessFile:
    """Test FlextInfraConfigFixer.process_file."""

    def test_process_file_missing_file(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        u.Tests.Matchers.fail(
            fixer.process_file(tmp_path / "missing.toml"), has="failed to read"
        )

    def test_process_file_invalid_toml(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid [[[")
        u.Tests.Matchers.fail(fixer.process_file(pyproject), has="failed to parse")

    def test_process_file_no_pyrefly_section(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool]\nother = true\n")
        result = fixer.process_file(pyproject)
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(result.value, eq=[])

    def test_process_file_dry_run_no_write(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        original = "[tool.pyrefly]\nsearch-path = []\n"
        pyproject.write_text(original)
        result = fixer.process_file(pyproject, dry_run=True)
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(pyproject.read_text(), eq=original)


class TestConfigFixerRun:
    """Test FlextInfraConfigFixer.run."""

    def test_run_with_empty_projects(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        result = fixer.run([])
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(len(result.value) >= 0, eq=True)

    def test_run_with_nonexistent_projects(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        u.Tests.Matchers.ok(fixer.run(["nonexistent"]))

    def test_run_with_dry_run_flag(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        u.Tests.Matchers.ok(fixer.run([], dry_run=True))

    def test_run_with_verbose_flag(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        u.Tests.Matchers.ok(fixer.run([], verbose=True))


class TestConfigFixerFindPyprojectFiles:
    """Test FlextInfraConfigFixer.find_pyproject_files."""

    def test_find_pyproject_files_empty_workspace(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        result = fixer.find_pyproject_files()
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(len(result.value) >= 0, eq=True)

    def test_find_pyproject_files_with_specific_paths(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        result = fixer.find_pyproject_files(project_paths=[tmp_path / "p1"])
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(len(result.value) >= 0, eq=True)

    def test_find_pyproject_files_with_project_paths(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        proj1 = tmp_path / "proj1"
        proj2 = tmp_path / "proj2"
        proj1.mkdir()
        proj2.mkdir()
        (proj1 / "pyproject.toml").touch()
        (proj2 / "pyproject.toml").touch()
        u.Tests.Matchers.ok(fixer.find_pyproject_files([proj1, proj2]))


class TestConfigFixerExecute:
    """Test FlextInfraConfigFixer.execute method."""

    def test_execute_returns_failure(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        u.Tests.Matchers.fail(fixer.execute(), has="Use run()")


class TestConfigFixerFixSearchPaths:
    """Test FlextInfraConfigFixer._fix_search_paths_tk method."""

    def test_fix_search_paths_normalizes_root_paths(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        (tmp_path / "typings" / "generated").mkdir(parents=True)
        pyrefly = tomlkit.document()
        pyrefly["search-path"] = ["../typings/generated", "../typings"]
        fixes = fixer._fix_search_paths_tk(pyrefly, tmp_path)
        u.Tests.Matchers.that(len(fixes) > 0, eq=True)
        u.Tests.Matchers.that(
            "typings/generated" in str(pyrefly["search-path"]), eq=True
        )

    def test_fix_search_paths_removes_nonexistent(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["search-path"] = ["nonexistent"]
        fixes = fixer._fix_search_paths_tk(pyrefly, tmp_path)
        u.Tests.Matchers.that(len(fixes) > 0, eq=True)

    def test_fix_search_paths_skips_non_list(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["search-path"] = "not-a-list"
        fixes = fixer._fix_search_paths_tk(pyrefly, tmp_path)
        u.Tests.Matchers.that(len(fixes), eq=0)


class TestConfigFixerRemoveIgnoreSubConfig:
    """Test FlextInfraConfigFixer._remove_ignore_sub_config_tk method."""

    def test_remove_ignore_sub_config_removes_ignored(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["sub-config"] = [
            {"matches": "*.py", "ignore": True},
            {"matches": "*.pyi", "ignore": False},
        ]
        fixes = fixer._remove_ignore_sub_config_tk(pyrefly)
        u.Tests.Matchers.that(len(fixes) > 0, eq=True)
        sub_config = pyrefly["sub-config"]
        u.Tests.Matchers.that(str(sub_config), contains="*.pyi")

    def test_remove_ignore_sub_config_skips_non_list(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["sub-config"] = "not-a-list"
        fixes = fixer._remove_ignore_sub_config_tk(pyrefly)
        u.Tests.Matchers.that(len(fixes), eq=0)


class TestConfigFixerEnsureProjectExcludes:
    """Test FlextInfraConfigFixer._ensure_project_excludes_tk method."""

    def test_ensure_project_excludes_adds_missing(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["project-excludes"] = tomlkit.array()
        fixes = fixer._ensure_project_excludes_tk(pyrefly)
        u.Tests.Matchers.that(len(fixes) > 0, eq=True)
        project_excludes = pyrefly["project-excludes"]
        u.Tests.Matchers.that(len(str(project_excludes)) > 0, eq=True)

    def test_ensure_project_excludes_skips_existing(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        pyrefly = tomlkit.document()
        pyrefly["project-excludes"] = ["**/*_pb2*.py", "**/*_pb2_grpc*.py"]
        fixes = fixer._ensure_project_excludes_tk(pyrefly)
        u.Tests.Matchers.that(len(fixes), eq=0)


class TestConfigFixerToArray:
    """Test FlextInfraConfigFixer._to_array static method."""

    def test_to_array_creates_array(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace_root=tmp_path)
        items = ["a", "b", "c"]
        arr = fixer._to_array(items)
        u.Tests.Matchers.that(len(arr), eq=3)
        u.Tests.Matchers.that("a" in arr, eq=True)
