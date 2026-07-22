"""Public runner tests for ``FlextInfraWorkspaceChecker``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsExtendedProjectRunners:
    """Exercise runner behavior through the public checker API only."""

    def test_run_projects_records_requested_gates(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        fake_modules = tmp_path / "fake_modules"
        for command in ("ruff", "pyrefly"):
            fake_pkg = fake_modules / command
            fake_pkg.mkdir(parents=True, exist_ok=True)
            (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
            (fake_pkg / "__main__.py").write_text(
                "raise SystemExit(0)\n", encoding="utf-8"
            )
        original_pythonpath = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = (
            f"{fake_modules}:{original_pythonpath}"
            if original_pythonpath
            else str(fake_modules)
        )
        try:
            result = checker.run_projects(
                ["p1"], ["lint", "format", "pyrefly"], reports_dir=tmp_path / "reports"
            )
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.ok(result)
        assert {"lint", "format", "pyrefly"} <= set(result.value[0].gates)

    @pytest.mark.parametrize("gate_method", ["lint", "format"])
    def test_public_method_returns_gate_result(
        self, gate_method: str, tmp_path: Path
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        ruff = fake_bin / "ruff"
        ruff.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        ruff.chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        try:
            result = getattr(checker, gate_method)(project_dir)
        finally:
            os.environ["PATH"] = original_path

        tm.ok(result)
        tm.that(result.value.gate, eq=gate_method)
