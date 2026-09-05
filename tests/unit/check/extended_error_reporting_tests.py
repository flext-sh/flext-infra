"""Public error-reporting tests for workspace gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class TestGateErrorReportingPublicBehavior:
    """Verify gate issue parsing through the public ``check()`` contract."""

    def test_mypy_ignores_empty_lines_in_json_output(self, tmp_path: Path) -> None:
        proj_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        fake_modules = tmp_path / "fake_modules" / "mypy"
        fake_modules.mkdir(parents=True, exist_ok=True)
        (fake_modules / "__init__.py").write_text("", encoding="utf-8")
        (fake_modules / "__main__.py").write_text(
            (
                "import sys\n"
                'sys.stdout.write(\'{"file":"a.py","line":1,"column":0,"code":"E001","message":"Error","severity":"error"}\\n\')\n'
                "sys.stdout.write('\\n')\n"
                'sys.stdout.write(\'{"file":"b.py","line":2,"column":0,"code":"E002","message":"Error","severity":"error"}\\n\')\n'
                "raise SystemExit(1)\n"
            ),
            encoding="utf-8",
        )
        original_pythonpath = os.environ.get("PYTHONPATH")
        fake_pythonpath = str(fake_modules.parent)
        os.environ["PYTHONPATH"] = (
            f"{fake_pythonpath}:{original_pythonpath}"
            if original_pythonpath
            else fake_pythonpath
        )
        try:
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = original_pythonpath

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)

    def test_ruff_format_deduplicates_reported_files(self, tmp_path: Path) -> None:
        proj_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        fake_pkg = tmp_path / "fake_modules" / "ruff"
        fake_pkg.mkdir(parents=True, exist_ok=True)
        (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
        (fake_pkg / "__main__.py").write_text(
            (
                "import sys\n"
                "sys.stdout.write(\n"
                "    '--> src/file.py:1:1\\n'\n"
                "    '--> src/file.py:1:1\\n'\n"
                "    '--> src/other.py:1:1\\n'\n"
                ")\n"
                "raise SystemExit(1)\n"
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
        try:
            result = u.Tests.run_gate_check(
                FlextInfraRuffFormatGate, tmp_path, proj_dir
            )
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)

    def test_workspace_checker_emits_gate_process_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "p1")
        (project_dir / "README.md").write_text("# Project\n", encoding="utf-8")
        runner = u.Tests.command_runner(stderr="rumdl execution failed", returncode=2)

        def create_gate(
            _registry: FlextInfraGateRegistry, _gate_id: str, repository_root: Path
        ) -> FlextInfraMarkdownGate:
            return FlextInfraMarkdownGate(repository_root, runner=runner)

        monkeypatch.setattr(FlextInfraGateRegistry, "create", create_gate)

        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["p1"], ["markdown"], reports_dir=tmp_path / "reports"
        )

        tm.ok(result)
        tm.that(result.value[0].passed, eq=False)
        captured = capsys.readouterr()
        tm.that(f"{captured.out}\n{captured.err}", has="rumdl execution failed")

    def test_workspace_checker_emits_parsed_gate_issue(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "p1")
        (project_dir / "README.md").write_text("# Project\n", encoding="utf-8")
        diagnostic = "README.md:3:2: [MD057] Relative link 'missing.md' does not exist"
        runner = u.Tests.command_runner(stdout=diagnostic, returncode=1)

        def create_gate(
            _registry: FlextInfraGateRegistry, _gate_id: str, repository_root: Path
        ) -> FlextInfraMarkdownGate:
            return FlextInfraMarkdownGate(repository_root, runner=runner)

        monkeypatch.setattr(FlextInfraGateRegistry, "create", create_gate)

        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["p1"], ["markdown"], reports_dir=tmp_path / "reports"
        )

        tm.ok(result)
        tm.that(result.value[0].passed, eq=False)
        captured = capsys.readouterr()
        tm.that(
            f"{captured.out}\n{captured.err}",
            has="README.md:3:2 [MD057] Relative link 'missing.md' does not exist",
        )
