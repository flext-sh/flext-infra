"""Public runner tests for ``FlextInfraWorkspaceChecker``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import FlextInfraWorkspaceChecker
from tests import u


class TestsExtendedProjectRunners:
    """Exercise runner behavior through the public checker API only."""

    def test_run_projects_records_requested_gates(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Infra.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project_dir / "src" / "test.py").write_text("value = 1\n", encoding="utf-8")
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        for command in ("ruff", "pyrefly"):
            script = fake_bin / command
            script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            script.chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        try:
            result = checker.run_projects(
                ["p1"],
                ["lint", "format", "pyrefly"],
                reports_dir=tmp_path / "reports",
            )
        finally:
            os.environ["PATH"] = original_path

        assert result.success
        assert {"lint", "format", "pyrefly"} <= set(result.value[0].gates)

    @pytest.mark.parametrize("gate_method", ["lint", "format"])
    def test_public_method_returns_gate_result(
        self, gate_method: str, tmp_path: Path
    ) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = u.Infra.Tests.mk_project(tmp_path, "p1", with_src=True)
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

        assert result.success
        assert result.value.gate == gate_method
