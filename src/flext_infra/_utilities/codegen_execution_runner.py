"""Subprocess and external tool execution mixin for codegen execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
import sys
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import FlextInfraUtilitiesSubprocess, c, t


class FlextInfraUtilitiesCodegenExecutionRunner:
    """Subprocess execution, git helpers, and import scanning for codegen."""

    # -------------------------------------------------------------------------
    # SUBPROCESS & EXECUTION
    # -------------------------------------------------------------------------
    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        """Get list of modified python files via git status."""
        lines = FlextInfraUtilitiesCodegenExecutionRunner.git_lines(
            workspace_root,
            ["status", "--porcelain"],
        )
        modified: MutableSequence[str] = []
        for line in lines:
            if not line:
                continue
            status = line[:2]
            if any(s in status for s in ("M", "A", "R", "C", "U")):
                path = line[3:].strip()
                if " -> " in path:
                    path = path.split(" -> ")[-1]
                if path.endswith(c.Infra.Extensions.PYTHON):
                    modified.append(path)
        return modified

    @staticmethod
    def git_lines(workspace_root: Path, args: t.StrSequence) -> t.StrSequence:
        git_bin = shutil.which(c.Infra.GIT)
        if not git_bin:
            return list[str]()
        result = FlextInfraUtilitiesSubprocess().run_raw(
            [git_bin, "-C", str(workspace_root), *args],
        )
        if result.is_failure:
            return list[str]()
        output = result.value
        if output.exit_code != 0:
            return list[str]()
        return [line.strip() for line in output.stdout.splitlines() if line.strip()]

    @staticmethod
    def run_pyrefly_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.PYREFLY,
            c.Infra.CHECK,
            *modified_files,
            "--config",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--summary=none",
        ]
        result = FlextInfraUtilitiesCodegenExecutionRunner.run_external_check(
            workspace_root,
            cmd,
        )
        detail = str(result.get("detail", "")).strip()
        if not bool(result.get("passed", False)) and detail.startswith(
            "WARN PYTHONPATH",
        ):
            result["passed"] = True
        return result

    @staticmethod
    def run_ruff_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.RUFF,
            c.Infra.Verbs.CHECK,
            *modified_files,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "--quiet",
        ]
        return FlextInfraUtilitiesCodegenExecutionRunner.run_external_check(
            workspace_root,
            cmd,
        )

    @staticmethod
    def run_external_check(
        workspace_root: Path,
        cmd: t.StrSequence,
    ) -> MutableMapping[str, t.Infra.InfraValue]:
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

    _BARE_IMPORT_FROM_RE: re.Pattern[str] = re.compile(
        r"^from\s+import\s",
        re.MULTILINE,
    )

    @staticmethod
    def scan_import_nodes(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        invalid_import_from: MutableSequence[str] = []
        parse_errors: MutableSequence[str] = []
        bare_re = FlextInfraUtilitiesCodegenExecutionRunner._BARE_IMPORT_FROM_RE
        for rel_path in modified_files:
            file_path = (workspace_root / rel_path).resolve()
            if not file_path.is_file():
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                parse_errors.append(f"{rel_path}:parse failed")
                continue
            for lineno, line in enumerate(source.splitlines(), start=1):
                if bare_re.match(line.lstrip()):
                    invalid_import_from.append(f"{rel_path}:{lineno}")
        invalid_import_from_value: Sequence[t.Infra.InfraValue] = list(
            invalid_import_from,
        )
        parse_errors_value: Sequence[t.Infra.InfraValue] = list(parse_errors)
        return {
            "invalid_import_from_count": len(invalid_import_from),
            "parse_error_count": len(parse_errors),
            "invalid_import_from": invalid_import_from_value,
            "parse_errors": parse_errors_value,
        }


__all__ = ["FlextInfraUtilitiesCodegenExecutionRunner"]
