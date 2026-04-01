from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_infra import c, m, t, u


class FlextInfraGate(ABC):
    _MAPPING_ADAPTER = t.Infra.INFRA_MAPPING_ADAPTER
    _SEQUENCE_ADAPTER = t.Infra.INFRA_SEQ_ADAPTER

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
        result = u.Infra.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
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
        has_root_python = any(project_dir.glob("*.py")) or any(
            project_dir.glob("*.pyi"),
        )
        discovered_dirs = u.Infra.discover_python_dirs(project_dir)
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

    @staticmethod
    def _to_mapping(
        value: t.Infra.InfraValue,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if not u.is_mapping(value):
            return {}
        return FlextInfraGate._MAPPING_ADAPTER.validate_python(value)

    @classmethod
    def _to_mapping_list(
        cls,
        value: t.Infra.InfraValue,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        typed_items: Sequence[t.Infra.InfraValue] = (
            cls._SEQUENCE_ADAPTER.validate_python(value)
        )
        normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
        for raw_item in typed_items:
            try:
                typed_item: Mapping[str, t.Infra.InfraValue] = (
                    cls._MAPPING_ADAPTER.validate_python(raw_item)
                )
            except ValidationError:
                continue
            normalized.append(typed_item)
        return normalized

    @staticmethod
    def _as_int(value: t.Infra.InfraValue, default: int = 0) -> int:
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
    def _as_str(value: t.Infra.InfraValue, default: str = "") -> str:
        return value if isinstance(value, str) else default

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

    @staticmethod
    def _nested_int(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        current: t.Infra.InfraValue = data
        for key in keys[:-1]:
            if not u.is_mapping(current):
                return default
            current = current.get(key)
            if current is None:
                return default
        if not u.is_mapping(current):
            return default
        raw: t.Infra.InfraValue = current.get(keys[-1])
        if raw is None:
            return default
        return FlextInfraGate._as_int(raw, default)


__all__ = ["FlextInfraGate"]
