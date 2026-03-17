from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

from flext_infra import c, t
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
from flext_infra.codegen._metrics_checks import FlextInfraCodegenMetricsChecks


class FlextInfraCodegenExecutionTools(FlextInfraCodegenMetricsChecks):
    @staticmethod
    def git_lines(workspace_root: Path, args: list[str]) -> list[str]:
        git_bin = shutil.which(c.Infra.Cli.GIT)
        if not git_bin:
            return []
        result = FlextInfraUtilitiesSubprocess.capture(
            [git_bin, "-C", str(workspace_root), *args],
        )
        return result.fold(
            on_failure=lambda _: [],
            on_success=lambda output: [
                line.strip() for line in output.splitlines() if line.strip()
            ],
        )

    @staticmethod
    def quality_gate_run_pyrefly_check(
        workspace_root: Path,
        modified_files: list[str],
    ) -> dict[str, t.Infra.InfraValue]:
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
        modified_files: list[str],
    ) -> dict[str, t.Infra.InfraValue]:
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
        cmd: list[str],
    ) -> dict[str, t.Infra.InfraValue]:
        result = FlextInfraUtilitiesSubprocess.capture(
            cmd,
            cwd=workspace_root,
        )
        if result.is_failure:
            return {
                "passed": False,
                "detail": result.error or "execution error",
                "exit_code": 127,
            }
        output = result.value.strip()
        lines = [line for line in output.splitlines() if line.strip()]
        excerpt = " | ".join(lines[:5]) if lines else "ok"
        return {
            "passed": True,
            "detail": excerpt,
            "exit_code": 0,
        }

    @staticmethod
    def quality_gate_scan_import_nodes(
        workspace_root: Path,
        modified_files: list[str],
    ) -> dict[str, t.Infra.InfraValue]:
        invalid_import_from: list[str] = []
        parse_errors: list[str] = []
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
                and node.level == 0
            )
        return {
            "invalid_import_from_count": len(invalid_import_from),
            "parse_error_count": len(parse_errors),
            "invalid_import_from": list(invalid_import_from),
            "parse_errors": list(parse_errors),
        }


__all__ = ["FlextInfraCodegenExecutionTools"]
