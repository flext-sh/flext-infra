"""Public tests for workspace checker project execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import u


class TestRunProjectsPublicBehavior:
    """Verify project execution through the public checker methods."""

    @staticmethod
    def _install_fake_ruff(tmp_path: Path, body: str) -> str:
        """Install a deterministic Ruff executable and return the prior path."""
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        ruff = fake_bin / "ruff"
        ruff.write_text(body, encoding="utf-8")
        ruff.chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        return original_path

    def test_invalid_gates_fail(self, tmp_path: Path) -> None:
        """Reject a gate name that is outside the public registry."""
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["p1"], ["invalid_gate"], reports_dir=tmp_path / "reports"
        )

        tm.fail(result)

    def test_missing_projects_are_skipped(self, tmp_path: Path) -> None:
        """Return an empty success when selected projects do not exist."""
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["nonexistent"], ["lint"], reports_dir=tmp_path / "reports"
        )

        tm.ok(result)
        tm.that(result.value, eq=())

    @pytest.mark.parametrize("report_name", ["check-report.md", "check-report.sarif"])
    def test_run_projects_creates_reports(
        self, tmp_path: Path, report_name: str
    ) -> None:
        """Create each canonical workspace report after a successful run."""
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
        tm.that((tmp_path / "reports" / report_name).exists(), eq=True)

    def test_run_projects_creates_project_scoped_reports_dir(
        self, tmp_path: Path
    ) -> None:
        """Create a project-scoped report directory for each checked project."""
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
        tm.that((tmp_path / "reports" / "p1").is_dir(), eq=True)

    def test_fail_fast_stops_after_first_failed_project(self, tmp_path: Path) -> None:
        """Stop project execution immediately after the first failed gate."""
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
                'printf \'[{"filename":"src/test.py",'
                '"location":{"row":1,"column":1},'
                '"code":"F401","message":"unused"}]\'\n'
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
        """Preserve individual error totals across mixed project outcomes."""
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
                '  printf \'[{"filename":"src/test.py",'
                '"location":{"row":1,"column":1},'
                '"code":"F401","message":"unused"}]\'\n'
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
        """Return only the requested project's public check result."""
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
