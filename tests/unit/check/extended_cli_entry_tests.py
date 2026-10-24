"""Public CLI entry tests for workspace check commands.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import main
from tests import c, tm, u


class TestsFlextInfraExtendedCliEntry:
    """Tests for the check CLI entry points."""

    @staticmethod
    def _workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        _ = u.Tests.mk_project(
            workspace,
            "p1",
            pyproject='[project]\nname = "p1"\nversion = "0.1.0"\n',
            with_src=True,
        )
        (workspace / "p1/src/p1/__init__.py").write_text(
            '"""Test package."""\n',
            encoding="utf-8",
        )
        u.Tests.declare_workspace_projects(workspace, ("p1",))
        return workspace

    @staticmethod
    def _run_lint(workspace: Path, *scope: str) -> int:
        """Run the public ``check run`` entry for the lint gate.

        Returns:
            The process exit code.

        """
        return main([
            "check",
            "run",
            "--repository-root",
            str(workspace),
            "--gates",
            "lint",
            *scope,
        ])

    @staticmethod
    def test_empty_workspace_errors(tmp_path: Path) -> None:
        """Test empty workspace errors."""
        tm.that(main(["check", "run", "--repository-root", str(tmp_path)]), eq=1)

    @pytest.mark.parametrize("broken", [False, True])
    def test_run_with_projects_reports_member_health(
        self,
        tmp_path: Path,
        *,
        broken: bool,
    ) -> None:
        """An explicit project scope exits 0 when clean and 1 on a member defect."""
        workspace = self._workspace(tmp_path)
        if broken:
            (workspace / "p1" / "src" / "broken.py").write_text(
                "def broken(:\n",
                encoding="utf-8",
            )
        tm.that(self._run_lint(workspace, "--projects", "p1"), eq=int(broken))

    def test_run_without_projects_evaluates_only_the_repository(
        self,
        tmp_path: Path,
    ) -> None:
        """An omitted --projects is the repository itself, never its members.

        The declared member carries a syntax error that a member scan would
        report, so a green run proves the root evaluated only itself.
        """
        workspace = self._workspace(tmp_path)
        (workspace / "pyproject.toml").write_text(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        package = workspace / "src" / "workspace"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text('"""Root package."""\n', encoding="utf-8")
        (workspace / "p1" / "src" / "broken.py").write_text(
            "def broken(:\n",
            encoding="utf-8",
        )
        tm.that(self._run_lint(workspace), eq=0)

    @staticmethod
    def test_check_main_routes_real_help() -> None:
        """Test check main routes real help."""
        tm.that(main(["check", "run", "--help"]), eq=0)

    @staticmethod
    def test_fix_pyrefly_config_routes_real_help() -> None:
        """Test fix pyrefly config routes real help."""
        tm.that(main(["check", "fix-pyrefly-settings", "--help"]), eq=0)

    def test_run_cli_anchors_relative_reports_dir_at_repository_root(
        self,
        tmp_path: Path,
    ) -> None:
        """A relative ``--reports-dir`` never lands under the caller's cwd."""
        workspace = self._workspace(tmp_path)
        caller = tmp_path / "caller"
        caller.mkdir(parents=True, exist_ok=True)
        relative_reports = Path("reports/check")
        with tm.scope(cwd=str(caller)):
            exit_code = self._run_lint(
                workspace,
                "--projects",
                "p1",
                "--reports-dir",
                str(relative_reports),
            )
        tm.that(exit_code, eq=0)
        (report_path,) = (workspace / relative_reports).glob(
            f"*/{c.Infra.CHECK_REPORT_MARKDOWN_FILENAME}",
        )
        tm.ok(u.Infra.check_report_findings(workspace, reports_dir=report_path.parent))
        tm.that(report_path.is_file(), eq=True)
        tm.that((caller / relative_reports).exists(), eq=False)
