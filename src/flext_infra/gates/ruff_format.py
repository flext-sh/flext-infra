"""Ruff format gate implementation."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import override

from flext_infra import c, m
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext


class FlextInfraRuffFormatGate(FlextInfraGate):
    """Gate for Ruff formatter checks and fixes."""

    gate_id = c.Infra.Gates.FORMAT
    gate_name = "Ruff Format"
    can_fix = True
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.Gates.FORMAT][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.Gates.FORMAT][1]

    @override
    @override
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        targets = check_dirs or ["."]
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.Cli.RUFF,
                c.Infra.Cli.RuffCmd.FORMAT,
                "--check",
                *targets,
                "--quiet",
            ],
            project_dir,
        )
        issues: list[m.Infra.Issue] = []
        if self._result_exit_code(result) != 0 and result.stdout.strip():
            seen: set[str] = set()
            for line in result.stdout.strip().splitlines():
                path = line.strip()
                if not path:
                    continue
                match = c.Infra.Check.RUFF_FORMAT_FILE_RE.match(path)
                if match:
                    file_path = match.group(1).strip()
                    if file_path in seen:
                        continue
                    seen.add(file_path)
                    issues.append(
                        m.Infra.Issue(
                            file=file_path,
                            line=0,
                            column=0,
                            code=c.Infra.Gates.FORMAT,
                            message="Would be reformatted",
                        ),
                    )
                elif (
                    path.endswith(c.Infra.Extensions.PYTHON)
                    and " " not in path
                    and (path not in seen)
                ):
                    seen.add(path)
                    issues.append(
                        m.Infra.Issue(
                            file=path,
                            line=0,
                            column=0,
                            code=c.Infra.Gates.FORMAT,
                            message="Would be reformatted",
                        ),
                    )
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )

    @override
    @override
    def fix(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        started = time.monotonic()
        result = self._run(
            [sys.executable, "-m", c.Infra.Cli.RUFF, c.Infra.Cli.RuffCmd.FORMAT, "."],
            project_dir,
        )
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=[],
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraRuffFormatGate"]
