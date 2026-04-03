from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraGate(ABC):
    gate_id: str = ""
    gate_name: str = ""
    can_fix: bool = False
    tool_name: str = ""
    tool_url: str = ""

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    @abstractmethod
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution: ...

    def fix(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        return self._build_gate_result(
            project=project_dir.name,
            passed=True,
            issues=[],
            duration=0.0,
            raw_output=f"Gate {self.gate_id} does not support fix",
        )

    def _run(
        self,
        cmd: t.StrSequence,
        cwd: Path,
        timeout: int = c.Infra.Timeouts.DEFAULT,
        env: t.StrMapping | None = None,
    ) -> m.Infra.CommandOutput:
        result = u.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        if result.is_failure:
            return m.Infra.CommandOutput(
                stdout="",
                stderr=result.error or "command execution failed",
                exit_code=1,
            )
        return result.value

    def _build_gate_result(
        self,
        *,
        project: str,
        passed: bool,
        issues: Sequence[m.Infra.Issue],
        duration: float,
        raw_output: str = "",
    ) -> m.Infra.GateExecution:
        model = m.Infra.GateResult(
            gate=self.gate_id,
            project=project,
            passed=passed,
            errors=[issue.formatted for issue in issues],
            duration=round(duration, 3),
        )
        return m.Infra.GateExecution(
            result=model,
            issues=issues,
            raw_output=raw_output,
        )

    def _existing_check_dirs(self, project_dir: Path) -> t.StrSequence:
        has_root_python = any(project_dir.glob(c.Infra.Extensions.PYTHON_GLOB)) or any(
            project_dir.glob("*.pyi"),
        )
        discovered_dirs = u.discover_python_dirs(project_dir)
        if has_root_python or discovered_dirs:
            return ["."]
        return []

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: t.StrSequence) -> t.StrSequence:
        out: MutableSequence[str] = []
        for directory in dirs:
            path = project_dir / directory
            if not path.is_dir():
                continue
            if next(path.rglob(c.Infra.Extensions.PYTHON_GLOB), None) or next(
                path.rglob("*.pyi"),
                None,
            ):
                out.append(directory)
        return out

    def _skip_result(
        self,
        project_dir: Path,
        started: float,
    ) -> m.Infra.GateExecution:
        return self._build_gate_result(
            project=project_dir.name,
            passed=True,
            issues=[],
            duration=time.monotonic() - started,
            raw_output="",
        )


__all__ = ["FlextInfraGate"]
