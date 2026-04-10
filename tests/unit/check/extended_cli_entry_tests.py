"""Public CLI entry tests for workspace check commands."""

from __future__ import annotations

import os
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorkspaceChecker, main
from tests import u


class TestWorkspaceCheckCLI:
    @staticmethod
    def _workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        _ = u.Infra.Tests.mk_project(
            workspace,
            "p1",
            pyproject='[project]\nname = "p1"\nversion = "0.1.0"\n',
            with_src=True,
        )
        return workspace

    def test_no_projects_error(self) -> None:
        tm.that(FlextInfraWorkspaceChecker.main([]), eq=1)

    def test_with_projects_success(self, tmp_path: Path) -> None:
        workspace = self._workspace(tmp_path)
        tm.that(
            FlextInfraWorkspaceChecker.main(
                [
                    "--workspace",
                    str(workspace),
                    "--projects",
                    "p1",
                    "--gates",
                    "lint",
                ],
            ),
            eq=0,
        )

    def test_with_projects_failure(self, tmp_path: Path) -> None:
        workspace = self._workspace(tmp_path)
        broken_file = workspace / "p1" / "src" / "broken.py"
        broken_file.write_text("def broken(:\n", encoding="utf-8")
        tm.that(
            FlextInfraWorkspaceChecker.main(
                [
                    "--workspace",
                    str(workspace),
                    "--projects",
                    "p1",
                    "--gates",
                    "lint",
                ],
            ),
            eq=1,
        )

    def test_check_main_routes_real_help(self) -> None:
        tm.that(main(["check", "run", "--help"]), eq=0)

    def test_fix_pyrefly_config_routes_real_help(self) -> None:
        tm.that(
            FlextInfraWorkspaceChecker.run_cli(["fix-pyrefly-config", "--help"]), eq=0
        )

    def test_run_cli_with_relative_reports_dir(self, tmp_path: Path) -> None:
        workspace = self._workspace(tmp_path)
        current = Path.cwd()
        runner_root = tmp_path / "runner"
        runner_root.mkdir(parents=True, exist_ok=True)
        try:
            os.chdir(runner_root)
            exit_code = FlextInfraWorkspaceChecker.run_cli(
                [
                    "run",
                    "--workspace",
                    str(workspace),
                    "--gates",
                    "lint",
                    "--projects",
                    "p1",
                    "--reports-dir",
                    "reports/check",
                ],
            )
        finally:
            os.chdir(current)
        tm.that(exit_code, eq=0)
        tm.that((runner_root / "reports/check/check-report.md").exists(), eq=True)
        tm.that((runner_root / "reports/check/check-report.sarif").exists(), eq=True)
