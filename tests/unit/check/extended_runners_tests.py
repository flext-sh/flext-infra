"""Public runner tests for the Pyrefly and Mypy gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_infra import FlextInfraMypyGate, FlextInfraPyreflyGate
from tests import u


class TestRunnerPublicBehavior:
    """Exercise gate runners through real commands and public ``check()``."""

    @staticmethod
    def _install_fake_pyrefly(
        tmp_path: Path,
        *,
        payload: str | None,
        exit_code: int,
        stderr: str = "",
        log_file: Path | None = None,
    ) -> str:
        fake_bin = tmp_path / "fake_bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        script = fake_bin / "pyrefly"
        script.write_text(
            (
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                "import sys\n"
                f"payload = {payload!r}\n"
                f"stderr_text = {stderr!r}\n"
                f"log_file = {str(log_file) if log_file else None!r}\n"
                "args = sys.argv[1:]\n"
                "output = None\n"
                "for index, arg in enumerate(args):\n"
                "    if arg == '-o' and index + 1 < len(args):\n"
                "        output = Path(args[index + 1])\n"
                "if log_file is not None:\n"
                "    Path(log_file).write_text('\\n'.join(args), encoding='utf-8')\n"
                "if payload is not None and output is not None:\n"
                "    output.write_text(payload, encoding='utf-8')\n"
                "if stderr_text:\n"
                "    print(stderr_text, file=sys.stderr)\n"
                f"raise SystemExit({exit_code})\n"
            ),
            encoding="utf-8",
        )
        script.chmod(0o755)
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{fake_bin}:{original_path}"
        return original_path

    @staticmethod
    def _install_fake_mypy(tmp_path: Path, *, stdout: str, exit_code: int) -> str:
        fake_pkg = tmp_path / "fake_modules" / "mypy"
        fake_pkg.mkdir(parents=True, exist_ok=True)
        (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
        (fake_pkg / "__main__.py").write_text(
            (
                "import sys\n"
                f"sys.stdout.write({stdout!r})\n"
                f"raise SystemExit({exit_code})\n"
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

    def test_run_pyrefly_with_json_output(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload='{"errors": []}',
            exit_code=0,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert result.result.passed

    def test_run_pyrefly_with_errors(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload=(
                '{"errors": [{"path": "a.py", "line": 1, "column": 0, '
                '"name": "E001", "description": "Error", "severity": "error"}]}'
            ),
            exit_code=1,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert not result.result.passed
        assert len(result.issues) == 1

    def test_run_pyrefly_with_invalid_json(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload="invalid json",
            exit_code=1,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert not result.result.passed

    def test_run_pyrefly_with_list_output(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload=(
                '[{"path": "a.py", "line": 1, "column": 0, "name": "E001", '
                '"description": "Error", "severity": "error"}]'
            ),
            exit_code=1,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert len(result.issues) == 1

    def test_run_pyrefly_limits_check_to_local_python_dirs(
        self, tmp_path: Path
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "tests").mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        (proj_dir / "tests" / "test_main.py").write_text("# code\n", encoding="utf-8")
        log_file = tmp_path / "pyrefly-command.txt"
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload='{"errors": []}',
            exit_code=0,
            log_file=log_file,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert result.result.passed
        assert log_file.read_text(encoding="utf-8").splitlines()[0:4] == [
            "check",
            "src",
            "tests",
            "--settings",
        ]

    def test_run_pyrefly_reports_command_failures_without_json(
        self,
        tmp_path: Path,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path,
            payload=None,
            exit_code=1,
            stderr="pyrefly crashed",
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraPyreflyGate,
                tmp_path,
                proj_dir,
                reports_dir=reports_dir,
            )
        finally:
            os.environ["PATH"] = original_path

        assert not result.result.passed
        assert len(result.issues) == 1
        assert result.issues[0].code == "pyrefly-exec"
        assert "pyrefly crashed" in result.issues[0].message

    def test_run_mypy_no_python_dirs(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)

        result = u.Infra.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)

        assert result.result.passed
        assert len(result.issues) == 0

    def test_run_mypy_with_json_output(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_pythonpath = self._install_fake_mypy(
            tmp_path,
            stdout=(
                '{"file": "a.py", "line": 1, "column": 0, "code": "E001", '
                '"message": "Error", "severity": "error"}\n'
            ),
            exit_code=1,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraMypyGate, tmp_path, proj_dir
            )
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        assert not result.result.passed
        assert len(result.issues) == 1

    def test_run_mypy_skips_empty_lines(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_pythonpath = self._install_fake_mypy(
            tmp_path,
            stdout=(
                '{"file": "a.py", "line": 1, "column": 0, "code": "E001", '
                '"message": "Error", "severity": "error"}\n\n'
                '{"file": "b.py", "line": 2, "column": 0, "code": "E002", '
                '"message": "Error", "severity": "error"}\n'
            ),
            exit_code=1,
        )
        try:
            result = u.Infra.Tests.run_gate_check(
                FlextInfraMypyGate, tmp_path, proj_dir
            )
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        assert not result.result.passed
        assert len(result.issues) == 2
