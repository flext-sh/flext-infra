"""Tests for FlextInfraConfigFixer — process_file, run, find, fix methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraConfigFixer, FlextInfraExtraPathsManager
from tests import u


class TestConfigFixerProcessFile:
    """Test FlextInfraConfigFixer.process_file."""

    def test_process_file_missing_file(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.fail(fixer.process_file(tmp_path / "missing.toml"), has="failed to read")

    def test_process_file_invalid_toml(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid [[[")
        tm.fail(fixer.process_file(pyproject), has="TOML parse failed")

    def test_process_file_no_pyrefly_section(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool]\nother = true\n")
        result = fixer.process_file(pyproject)
        tm.ok(result)
        tm.that(result.value, empty=True)

    def test_process_file_dry_run_no_write(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        original = "[tool.pyrefly]\nsearch-path = []\n"
        pyproject.write_text(original)
        result = fixer.process_file(pyproject, dry_run=True)
        tm.ok(result)
        tm.that(pyproject.read_text(), eq=original)

    def test_process_file_syncs_search_path_from_public_manager(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "typings" / "generated").mkdir(parents=True)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.pyrefly]\nsearch-path = []\n", encoding="utf-8")

        result = FlextInfraConfigFixer(workspace=tmp_path).process_file(pyproject)

        tm.ok(result)
        tm.that(result.value, has="synchronized search-path from YAML rules")
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        tm.that(
            payload["tool"]["pyrefly"]["search-path"],
            eq=FlextInfraExtraPathsManager(workspace=tmp_path).pyrefly_search_paths(
                project_dir=tmp_path,
                is_root=True,
            ),
        )

    def test_process_file_removes_ignored_sub_configs_via_public_api(
        self,
        tmp_path: Path,
    ) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            (
                "[tool.pyrefly]\n"
                'search-path = ["src"]\n'
                "sub-settings = [\n"
                '  { matches = "*.py", ignore = true },\n'
                '  { matches = "*.pyi", ignore = false },\n'
                "]\n"
            ),
            encoding="utf-8",
        )

        result = FlextInfraConfigFixer(workspace=tmp_path).process_file(pyproject)

        tm.ok(result)
        tm.that(result.value, has="removed ignore=true sub-settings for '*.py'")
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        tm.that(
            payload["tool"]["pyrefly"]["sub-settings"],
            eq=[{"matches": "*.pyi", "ignore": False}],
        )

    def test_process_file_syncs_root_project_excludes_via_public_api(
        self,
        tmp_path: Path,
    ) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            ('[tool.pyrefly]\nsearch-path = ["src"]\nproject-excludes = []\n'),
            encoding="utf-8",
        )

        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.process_file(pyproject)

        tm.ok(result)
        tm.that(result.value, has="synchronized project-excludes from YAML rules")
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        config_result = u.Infra.load_tool_config()
        tm.ok(config_result)
        tm.that(
            payload["tool"]["pyrefly"]["project-excludes"],
            eq=sorted(set(config_result.value.tools.pyrefly.project_exclude_globs)),
        )


class TestConfigFixerRun:
    """Test FlextInfraConfigFixer.run."""

    def test_run_with_empty_projects(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        result = fixer.run([])
        tm.ok(result)
        tm.that(len(result.value), gte=0)

    def test_run_with_nonexistent_projects(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.ok(fixer.run(["nonexistent"]))

    def test_run_with_dry_run_flag(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.ok(fixer.run([], dry_run=True))

    def test_run_with_verbose_flag(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.ok(fixer.run([], verbose=True))


class TestConfigFixerExecute:
    """Test FlextInfraConfigFixer.execute method."""

    def test_execute_returns_failure(self, tmp_path: Path) -> None:
        fixer = FlextInfraConfigFixer(workspace=tmp_path)
        tm.fail(fixer.execute(), has="Use execute_command() directly")


class TestConfigFixerToArray:
    """Test u.Cli.toml_array."""

    def test_to_array_creates_array(self, tmp_path: Path) -> None:
        items = ["a", "b", "c"]
        arr = u.Cli.toml_array(items)
        tm.that(len(arr), eq=3)
        assert "a" in list(arr)
