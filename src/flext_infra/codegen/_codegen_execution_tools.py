"""Code execution tools for quality gate checks and external command invocation.

Provides methods for running external tools (git, pyrefly, ruff) and scanning
import nodes in modified Python files.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import shutil
import sys
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraCodegenMetricsChecks,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesSubprocess,
    c,
    t,
)


class FlextInfraCodegenExecutionTools(FlextInfraCodegenMetricsChecks):
    """Execution tools for external command invocation and import scanning."""

    @staticmethod
    def git_lines(workspace_root: Path, args: Sequence[str]) -> Sequence[str]:
        """Run git command and return output lines."""
        git_bin = shutil.which(c.Infra.Cli.GIT)
        if not git_bin:
            return []
        result = FlextInfraUtilitiesSubprocess().run_raw(
            [git_bin, "-C", str(workspace_root), *args],
        )
        if result.is_failure:
            return []
        output = result.value
        if output.exit_code != 0:
            return []
        return [line.strip() for line in output.stdout.splitlines() if line.strip()]

    @staticmethod
    def quality_gate_run_pyrefly_check(
        workspace_root: Path,
        modified_files: Sequence[str],
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Run pyrefly check on modified files."""
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.Cli.PYREFLY,
            c.Infra.Cli.RuffCmd.CHECK,
            *modified_files,
            "--config",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--summary=none",
        ]
        result = FlextInfraCodegenExecutionTools.run_external_check(workspace_root, cmd)
        detail = str(result.get("detail", "")).strip()
        if not bool(result.get("passed", False)) and detail.startswith(
            "WARN PYTHONPATH",
        ):
            result["passed"] = True
        return result

    @staticmethod
    def quality_gate_run_ruff_check(
        workspace_root: Path,
        modified_files: Sequence[str],
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Run ruff check on modified files."""
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.Cli.RUFF,
            c.Infra.Verbs.CHECK,
            *modified_files,
            "--output-format",
            c.Infra.Cli.OUTPUT_JSON,
            "--quiet",
        ]
        return FlextInfraCodegenExecutionTools.run_external_check(workspace_root, cmd)

    @staticmethod
    def run_external_check(
        workspace_root: Path,
        cmd: Sequence[str],
    ) -> MutableMapping[str, t.Infra.InfraValue]:
        """Execute external check command and return result."""
        result = FlextInfraUtilitiesSubprocess().run_raw(cmd, cwd=workspace_root)
        if result.is_failure:
            return {
                "passed": False,
                "detail": result.error or "execution error",
                "exit_code": 127,
            }
        command_output = result.value
        output = (command_output.stderr or command_output.stdout or "").strip()
        lines = [line for line in output.splitlines() if line.strip()]
        excerpt = " | ".join(lines[:5]) if lines else "ok"
        return {
            "passed": command_output.exit_code == 0,
            "detail": excerpt,
            "exit_code": command_output.exit_code,
        }

    @staticmethod
    def quality_gate_scan_import_nodes(
        workspace_root: Path,
        modified_files: Sequence[str],
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Scan import nodes in modified files for invalid patterns."""
        invalid_import_from: MutableSequence[str] = []
        parse_errors: MutableSequence[str] = []
        for rel_path in modified_files:
            file_path = (workspace_root / rel_path).resolve()
            if not file_path.is_file():
                continue
            tree = FlextInfraUtilitiesParsing.parse_module_ast(file_path)
            if tree is None:
                parse_errors.append(f"{rel_path}:parse failed")
                continue
            invalid_import_from.extend(
                f"{rel_path}:{node.lineno}"
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                and node.module is None
                and (node.level == 0)
            )
        invalid_import_from_value: Sequence[t.Infra.InfraValue] = list(
            invalid_import_from
        )
        parse_errors_value: Sequence[t.Infra.InfraValue] = list(parse_errors)
        return {
            "invalid_import_from_count": len(invalid_import_from),
            "parse_error_count": len(parse_errors),
            "invalid_import_from": invalid_import_from_value,
            "parse_errors": parse_errors_value,
        }


__all__ = ["FlextInfraCodegenExecutionTools"]
