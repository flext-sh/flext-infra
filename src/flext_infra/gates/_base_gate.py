from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Protocol, runtime_checkable

from flext_core import FlextModels
from pydantic import ConfigDict, Field, TypeAdapter, ValidationError

from flext_infra import c, m, t as t_infra, u


class FlextInfraGateContext(FlextModels.FrozenStrictModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    workspace_root: Annotated[Path, Field(description="Workspace root directory")]
    reports_dir: Annotated[Path, Field(description="Reports output directory")]
    fail_fast: Annotated[
        bool,
        Field(default=False, description="Stop on first gate failure"),
    ] = False


@runtime_checkable
class FlextInfraGateProtocol(Protocol):
    @property
    def gate_id(self) -> str: ...
    @property
    def can_fix(self) -> bool: ...
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.GateExecution: ...


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
        ctx: FlextInfraGateContext,
    ) -> m.Infra.GateExecution: ...

    def fix(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
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
        cmd: list[str],
        cwd: Path,
        timeout: int = c.Infra.Timeouts.DEFAULT,
        env: Mapping[str, str] | None = None,
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
        issues: list[m.Infra.Issue],
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

    def _result_exit_code(self, result: m.Infra.CommandOutput) -> int:
        return result.exit_code if hasattr(result, "exit_code") else 1

    def _existing_check_dirs(self, project_dir: Path) -> list[str]:
        dirs = (
            c.Infra.DEFAULT_CHECK_DIRS
            if project_dir.resolve() == self._workspace_root.resolve()
            else c.Infra.CHECK_DIRS_SUBPROJECT
        )
        return [d for d in dirs if (project_dir / d).is_dir()]

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: list[str]) -> list[str]:
        out: list[str] = []
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
        value: t_infra.Infra.InfraValue,
    ) -> dict[str, t_infra.Infra.InfraValue]:
        if not isinstance(value, Mapping):
            return {}
        return TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(value)

    @classmethod
    def _to_mapping_list(
        cls,
        value: t_infra.Infra.InfraValue,
    ) -> list[dict[str, t_infra.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        typed_items = TypeAdapter(list[t_infra.Infra.InfraValue]).validate_python(value)
        normalized: list[dict[str, t_infra.Infra.InfraValue]] = []
        for raw_item in typed_items:
            try:
                typed_item = TypeAdapter(
                    dict[str, t_infra.Infra.InfraValue],
                ).validate_python(raw_item)
            except ValidationError:
                continue
            normalized.append(typed_item)
        return normalized

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

    @staticmethod
    def _nested_mapping(
        data: dict[str, t_infra.Infra.InfraValue],
        *keys: str,
    ) -> dict[str, t_infra.Infra.InfraValue]:
        current: t_infra.Infra.InfraValue = data
        for key in keys:
            if not isinstance(current, Mapping):
                return {}
            typed_current = TypeAdapter(
                dict[str, t_infra.Infra.InfraValue],
            ).validate_python(current)
            if key not in typed_current:
                return {}
            child: t_infra.Infra.InfraValue = typed_current[key]
            if child is None:
                return {}
            current = child
        if not isinstance(current, Mapping):
            return {}
        return TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(current)

    @classmethod
    def _nested_int(
        cls,
        data: dict[str, t_infra.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        target = cls._nested_mapping(data, *keys[:-1])
        raw: t_infra.Infra.InfraValue = target.get(keys[-1])
        if raw is None:
            return default
        return cls._as_int(raw, default)


__all__ = ["FlextInfraGate", "FlextInfraGateContext", "FlextInfraGateProtocol"]
