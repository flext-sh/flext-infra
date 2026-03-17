"""FLEXT mypy quality gate."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, t as t_infra, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext


class FlextInfraMypyGate(FlextInfraGate):
    """Gate for Mypy type checking."""

    gate_id: str = c.Infra.Gates.MYPY
    gate_name: str = "Mypy"
    can_fix: bool = False
    tool_name: str = "Mypy"
    tool_url: str = "https://mypy.readthedocs.io/"

    @override
    @override
    def check(
        self, project_dir: Path, ctx: FlextInfraGateContext
    ) -> m.Infra.Check.GateExecution:
        _ = u
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        mypy_dirs = self._dirs_with_py(project_dir, check_dirs)
        if not mypy_dirs:
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="",
            )
        proj_py = project_dir / c.Infra.Files.PYPROJECT_FILENAME
        cfg = (
            proj_py
            if proj_py.exists()
            and "[tool.mypy]" in proj_py.read_text(encoding=c.Infra.Encoding.DEFAULT)
            else ctx.workspace_root / c.Infra.Files.PYPROJECT_FILENAME
        )
        typings_generated = (
            ctx.workspace_root / c.Infra.Directories.TYPINGS / "generated"
        )
        mypy_env = os.environ.copy()
        if typings_generated.is_dir():
            existing = mypy_env.get("MYPYPATH", "")
            mypy_env["MYPYPATH"] = str(typings_generated) + (
                f":{existing}" if existing else ""
            )
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.Cli.MYPY,
                *mypy_dirs,
                "--config-file",
                str(cfg),
                "--output",
                c.Infra.Cli.OUTPUT_JSON,
            ],
            project_dir,
            env=mypy_env,
        )
        issues: list[m.Infra.Check.Issue] = []
        for raw_line in (result.stdout or "").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                line_data = TypeAdapter(
                    dict[str, t_infra.Infra.InfraValue]
                ).validate_json(stripped)
            except ValidationError:
                continue
            try:
                severity = self._as_str(
                    line_data.get("severity", c.Infra.Toml.ERROR),
                    c.Infra.Toml.ERROR,
                )
                if severity in {"error", "warning", "note"}:
                    issues.append(
                        m.Infra.Check.Issue(
                            file=self._as_str(line_data.get("file", "?"), "?"),
                            line=self._as_int(line_data.get("line", 0)),
                            column=self._as_int(line_data.get("column", 0)),
                            code=self._as_str(line_data.get("code", "")),
                            message=self._as_str(line_data.get("message", "")),
                            severity=severity,
                        ),
                    )
            except ValidationError:
                continue
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )

    @staticmethod
    def _as_int(value: t_infra.Infra.InfraValue, default: int = 0) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    @staticmethod
    def _as_str(value: t_infra.Infra.InfraValue, default: str = "") -> str:
        return value if isinstance(value, str) else default


__all__ = ["FlextInfraMypyGate"]
