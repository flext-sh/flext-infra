"""Public runner tests for the Pyrefly and Mypy gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_tests import tm

from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
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
    def _install_fake_mypy(
        tmp_path: Path,
        *,
        stdout: str,
        exit_code: int,
        stderr: str = "",
        log_file: Path | None = None,
    ) -> str:
        fake_pkg = tmp_path / "fake_modules" / "mypy"
        fake_pkg.mkdir(parents=True, exist_ok=True)
        (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
        (fake_pkg / "__main__.py").write_text(
            (
                "import sys\n"
                "from pathlib import Path\n"
                f"sys.stdout.write({stdout!r})\n"
                f"sys.stderr.write({stderr!r})\n"
                f"log_file = {str(log_file) if log_file else None!r}\n"
                "if log_file is not None:\n"
                "    Path(log_file).write_text(\n"
                "        '\\n'.join(sys.argv[1:]), encoding='utf-8'\n"
                "    )\n"
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
        """Verify that a successful Pyrefly JSON report passes."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path, payload='{"errors": []}', exit_code=0
        )
        try:
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=True)

    def test_run_pyrefly_with_errors(self, tmp_path: Path) -> None:
        """Verify that Pyrefly diagnostics fail the gate with issues."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
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
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)

    def test_run_pyrefly_with_invalid_json(self, tmp_path: Path) -> None:
        """Verify that invalid Pyrefly JSON fails the gate."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path, payload="invalid json", exit_code=1
        )
        try:
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=False)

    def test_run_pyrefly_with_list_output(self, tmp_path: Path) -> None:
        """Verify that a list-shaped Pyrefly report yields issues."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
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
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(len(result.issues), eq=1)

    def test_run_pyrefly_limits_check_to_local_python_dirs(
        self, tmp_path: Path
    ) -> None:
        """Verify that Pyrefly checks only local Python directories."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "tests").mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        (proj_dir / "tests" / "test_main.py").write_text("# code\n", encoding="utf-8")
        log_file = tmp_path / "pyrefly-command.txt"
        original_path = self._install_fake_pyrefly(
            tmp_path, payload='{"errors": []}', exit_code=0, log_file=log_file
        )
        try:
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=True)
        tm.that(
            log_file.read_text(encoding="utf-8").splitlines()[0:4],
            eq=["check", "src", "--config", "pyproject.toml"],
        )

    def test_run_pyrefly_uses_project_includes_config(self, tmp_path: Path) -> None:
        """Verify that Pyrefly honors project include configuration."""
        proj_dir = u.Tests.mk_project(
            tmp_path,
            "pyrefly-project",
            pyproject="[tool.pyrefly]\nproject-includes = ['src/**/*.py*']\n",
            with_src=True,
        )
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        log_file = tmp_path / "pyrefly-config-command.txt"
        original_path = self._install_fake_pyrefly(
            tmp_path, payload='{"errors": []}', exit_code=0, log_file=log_file
        )
        try:
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=True)
        tm.that(
            log_file.read_text(encoding="utf-8").splitlines()[0:2],
            eq=["check", "--config"],
        )

    def test_run_pyrefly_reports_command_failures_without_json(
        self, tmp_path: Path
    ) -> None:
        """Verify that a Pyrefly execution failure preserves stderr."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_path = self._install_fake_pyrefly(
            tmp_path, payload=None, exit_code=1, stderr="pyrefly crashed"
        )
        try:
            result = u.Tests.run_gate_check(
                FlextInfraPyreflyGate, tmp_path, proj_dir, reports_dir=reports_dir
            )
        finally:
            os.environ["PATH"] = original_path

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].code, eq="pyrefly-exec")
        tm.that(result.issues[0].message, has="pyrefly crashed")

    def test_run_mypy_no_python_dirs(self, tmp_path: Path) -> None:
        """Verify that Mypy passes projects without Python directories."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path)

        result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)

        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_mypy_with_json_output(self, tmp_path: Path) -> None:
        """Verify that Mypy JSON diagnostics fail the gate with issues."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
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
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)

    def test_run_mypy_skips_empty_lines(self, tmp_path: Path) -> None:
        """Verify that empty Mypy output lines do not hide diagnostics."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
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
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=2)

    def test_run_mypy_limits_check_to_local_python_dirs_and_root_files(
        self, tmp_path: Path
    ) -> None:
        """Verify that Mypy receives only local roots and root files."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        (proj_dir / "scripts").mkdir()
        (proj_dir / "tests").mkdir()
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        (proj_dir / "scripts" / "tool.py").write_text("# code\n", encoding="utf-8")
        (proj_dir / "tests" / "test_main.py").write_text("# code\n", encoding="utf-8")
        (proj_dir / "conftest.py").write_text("# code\n", encoding="utf-8")
        log_file = tmp_path / "mypy-command.txt"
        original_pythonpath = self._install_fake_mypy(
            tmp_path, stdout="", exit_code=0, log_file=log_file
        )
        try:
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(result.result.passed, eq=True)
        command_args = log_file.read_text(encoding="utf-8").splitlines()
        tm.that(command_args[0:3], eq=["src", "conftest.py", "--config-file"])
        tm.that(command_args, lacks="tests")
        tm.that(command_args, lacks="scripts")
        tm.that(Path(command_args[3]).name, eq="pyproject.toml")

    def test_run_mypy_skips_tmp_flow_test_fixture_roots(self, tmp_path: Path) -> None:
        """Verify that Mypy excludes temporary flow-test fixture roots."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        fixture_pkg = (
            proj_dir
            / "tmp_flow_test"
            / "scenario-a"
            / "workspace"
            / "flext-a"
            / "src"
            / "flext_a"
        )
        fixture_pkg.mkdir(parents=True)
        (fixture_pkg / "__init__.py").write_text("", encoding="utf-8")
        log_file = tmp_path / "mypy-command.txt"
        original_pythonpath = self._install_fake_mypy(
            tmp_path, stdout="", exit_code=0, log_file=log_file
        )
        try:
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(result.result.passed, eq=True)
        command_args = log_file.read_text(encoding="utf-8").splitlines()
        tm.that(command_args, has="src")
        tm.that(command_args, lacks="tmp_flow_test")

    def test_run_mypy_reports_command_failures_without_json(
        self, tmp_path: Path
    ) -> None:
        """Verify that a Mypy execution failure preserves stderr."""
        _, proj_dir = u.Tests.create_checker_project(tmp_path, with_src=True)
        (proj_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")
        original_pythonpath = self._install_fake_mypy(
            tmp_path,
            stdout="",
            stderr="mypy timed out waiting for dependency graph",
            exit_code=1,
        )
        try:
            result = u.Tests.run_gate_check(FlextInfraMypyGate, tmp_path, proj_dir)
        finally:
            if original_pythonpath:
                os.environ["PYTHONPATH"] = original_pythonpath
            else:
                os.environ.pop("PYTHONPATH", None)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].code, eq="mypy-exec")
        tm.that(result.issues[0].message, has="mypy timed out")
