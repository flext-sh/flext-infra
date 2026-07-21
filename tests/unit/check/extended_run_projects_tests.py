"""Public tests for workspace checker project execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestRunProjectsPublicBehavior:
    """Verify project execution through the public checker methods."""

    @staticmethod
    def _install_fake_ruff(
        tmp_path: Path,
        *,
        default_stdout: str,
        default_exit: int,
        per_project: dict[str, tuple[str, int]] | None = None,
    ) -> str:
        """Install a fake ``python -m ruff`` module (venv-anchored gate).

        Emits ``default_stdout``/``default_exit`` unless the current project
        directory name matches a ``per_project`` key, mirroring how ruff is now
        invoked through the workspace interpreter rather than a PATH binary.
        """
        fake_pkg = tmp_path / "fake_modules" / "ruff"
        fake_pkg.mkdir(parents=True, exist_ok=True)
        (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
        (fake_pkg / "__main__.py").write_text(
            (
                "import sys\n"
                "from pathlib import Path\n"
                f"per_project = {per_project or {}!r}\n"
                f"default = ({default_stdout!r}, {default_exit!r})\n"
                "stdout, code = per_project.get(Path.cwd().name, default)\n"
                "sys.stdout.write(stdout)\n"
                "raise SystemExit(code)\n"
            ),
            encoding="utf-8",
        )
        original_pythonpath = os.environ.get("PYTHONPATH")
        fake_pythonpath = str(fake_pkg.parent)
        os.environ["PYTHONPATH"] = (
            f"{fake_pythonpath}:{original_pythonpath}"
            if original_pythonpath
            else fake_pythonpath
        )
        return original_pythonpath or ""

    def test_invalid_gates_fail(self, tmp_path: Path) -> None:
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["p1"], ["invalid_gate"], reports_dir=tmp_path / "reports"
        )

        tm.fail(result)

    def test_missing_projects_are_skipped(self, tmp_path: Path) -> None:
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["nonexistent"], ["lint"], reports_dir=tmp_path / "reports"
        )

        tm.ok(result)
        tm.that(result.value, eq=())

    @pytest.mark.parametrize("report_name", ["check-report.md", "check-report.sarif"])
    def test_run_projects_creates_reports(
        self, tmp_path: Path, report_name: str
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        original_path = self._install_fake_ruff(
            tmp_path, "#!/usr/bin/env bash\nprintf '[]'\nexit 0\n"
        )
        try:
            result = checker.run_projects(
                ["p1"], ["lint"], reports_dir=tmp_path / "reports"
            )
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        assert (tmp_path / "reports" / report_name).exists()

    def test_run_projects_creates_project_scoped_reports_dir(
        self, tmp_path: Path
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        original_path = self._install_fake_ruff(
            tmp_path, "#!/usr/bin/env bash\nprintf '[]'\nexit 0\n"
        )
        try:
            result = checker.run_projects(
                ["p1"], ["lint"], reports_dir=tmp_path / "reports"
            )
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        assert (tmp_path / "reports" / "p1").is_dir()

    def test_fail_fast_stops_after_first_failed_project(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        for name in ("p1", "p2", "p3"):
            project_dir = u.Tests.mk_project(tmp_path, name, with_src=True)
            (project_dir / "src" / "test.py").write_text(
                "value = 1\n", encoding="utf-8"
            )
        original_path = self._install_fake_ruff(
            tmp_path,
            (
                "#!/usr/bin/env bash\n"
                'printf \'[{"filename":"src/test.py","location":{"row":1,"column":1},"code":"F401","message":"unused"}]\'\n'
                "exit 1\n"
            ),
        )
        try:
            result = checker.run_projects(
                ["p1", "p2", "p3"],
                ["lint"],
                reports_dir=tmp_path / "reports",
                fail_fast=True,
            )
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        tm.that(len(result.value), eq=1)

    def test_run_projects_reports_mixed_project_errors(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        for name in ("p1", "p2"):
            project_dir = u.Tests.mk_project(tmp_path, name, with_src=True)
            (project_dir / "src" / "test.py").write_text(
                "value = 1\n", encoding="utf-8"
            )
        original_path = self._install_fake_ruff(
            tmp_path,
            (
                "#!/usr/bin/env bash\n"
                'if [ "$(basename "$PWD")" = \'p1\' ]; then\n'
                '  printf \'[{"filename":"src/test.py","location":{"row":1,"column":1},"code":"F401","message":"unused"}]\'\n'
                "  exit 1\n"
                "fi\n"
                "printf '[]'\n"
                "exit 0\n"
            ),
        )
        try:
            result = checker.run_projects(
                ["p1", "p2"], ["lint"], reports_dir=tmp_path / "reports"
            )
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        tm.that(len(result.value), eq=2)
        tm.that(result.value[0].total_errors, eq=1)
        tm.that(result.value[1].total_errors, eq=0)

    def test_run_project_returns_single_project_result(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        original_path = self._install_fake_ruff(
            tmp_path, "#!/usr/bin/env bash\nprintf '[]'\nexit 0\n"
        )
        try:
            result = checker.run_project("p1", ["lint"])
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        tm.that(len(result.value), eq=1)
