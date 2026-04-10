"""Public error-reporting tests for workspace gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import (
    FlextInfraGoGate,
    FlextInfraMypyGate,
    FlextInfraRuffFormatGate,
)
from tests import u


class TestGateErrorReportingPublicBehavior:
    """Verify gate issue parsing through the public ``check()`` contract."""

    def test_mypy_ignores_empty_lines_in_json_output(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1", with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        fake_modules = tmp_path / "fake_modules" / "mypy"
        fake_modules.mkdir(parents=True, exist_ok=True)
        (fake_modules / "__init__.py").write_text("", encoding="utf-8")
        (fake_modules / "__main__.py").write_text(
            (
                "import sys\n"
                'print(\'{"file":"a.py","line":1,"column":0,"code":"E001","message":"Error","severity":"error"}\')\n'
                "print()\n"
                'print(\'{"file":"b.py","line":2,"column":0,"code":"E002","message":"Error","severity":"error"}\')\n'
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
            result = u.Infra.Tests.run_gate_check(
                FlextInfraMypyGate,
                tmp_path,
                proj_dir,
            )
        finally:
            if original_pythonpath is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = original_pythonpath

        assert not result.result.passed
        assert len(result.issues) == 2

    def test_go_gate_ignores_empty_lines_in_gofmt_output(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test\n", encoding="utf-8")
        (proj_dir / "main.go").write_text("package main\n", encoding="utf-8")
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        (fake_bin / "go").write_text(
            "#!/usr/bin/env bash\nexit 0\n",
            encoding="utf-8",
        )
        (fake_bin / "gofmt").write_text(
            (
                "#!/usr/bin/env bash\n"
                "printf 'src/file.go\\n\\nsrc/other.go\\n'\n"
                "exit 1\n"
            ),
            encoding="utf-8",
        )
        (fake_bin / "go").chmod(0o755)
        (fake_bin / "gofmt").chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        try:
            result = u.Infra.Tests.run_gate_check(FlextInfraGoGate, tmp_path, proj_dir)
        finally:
            os.environ["PATH"] = original_path

        assert not result.result.passed
        assert len(result.issues) == 2

    def test_ruff_format_deduplicates_reported_files(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1", with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        (fake_bin / "ruff").write_text(
            (
                "#!/usr/bin/env bash\n"
                "cat <<'EOF'\n"
                "--> src/file.py:1:1\n"
                "--> src/file.py:1:1\n"
                "--> src/other.py:1:1\n"
                "EOF\n"
                "exit 1\n"
            ),
            encoding="utf-8",
        )
        (fake_bin / "ruff").chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraRuffFormatGate,
                tmp_path,
                proj_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert not result.result.passed
        assert len(result.issues) == 2
