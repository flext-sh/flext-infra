"""FLEXT mypy quality gate."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraMypyGate(FlextInfraGate):
    """Gate for Mypy type checking."""

    gate_id: str = c.Infra.MYPY
    gate_name: str = "Mypy"
    can_fix: bool = False
    tool_name: str = "Mypy"
    tool_url: str = "https://mypy.readthedocs.io/"

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        mypy_dirs = self._dirs_with_py(project_dir, check_dirs)
        if not mypy_dirs:
            return self._skip_result(project_dir, started)
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
                c.Infra.MYPY,
                *mypy_dirs,
                "--config-file",
                str(cfg),
                "--output",
                c.Infra.OUTPUT_JSON,
            ],
            project_dir,
            env=mypy_env,
        )
        issues: MutableSequence[m.Infra.Issue] = []
        for raw_line in (result.stdout or "").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                line_data: Mapping[str, t.Infra.InfraValue] = (
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_json(stripped)
                )
            except ValidationError:
                continue
            try:
                severity = u.Infra.as_str(
                    line_data.get("severity", c.Infra.ERROR),
                    c.Infra.ERROR,
                )
                if severity in {"error", "warning", "note"}:
                    issues.append(
                        m.Infra.Issue(
                            file=u.Infra.as_str(line_data.get("file", "?"), "?"),
                            line=u.to_int(line_data.get("line", 0)),
                            column=u.to_int(line_data.get("column", 0)),
                            code=u.Infra.as_str(line_data.get("code", "")),
                            message=u.Infra.as_str(line_data.get("message", "")),
                            severity=severity,
                        ),
                    )
            except ValidationError:
                continue
        return self._build_gate_result(
            project=project_dir.name,
            passed=result.exit_code == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraMypyGate"]
