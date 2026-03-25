from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

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
        dirs = (
            c.Infra.DEFAULT_CHECK_DIRS
            if project_dir.resolve() == self._workspace_root.resolve()
            else c.Infra.CHECK_DIRS_SUBPROJECT
        )
        return [d for d in dirs if (project_dir / d).is_dir()]

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
        if not isinstance(value, Mapping):
            return {}
        return TypeAdapter(Mapping[str, t.Infra.InfraValue]).validate_python(
            value,
        )

    @classmethod
    def _to_mapping_list(
        cls,
        value: t.Infra.InfraValue,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        typed_items: Sequence[t.Infra.InfraValue] = TypeAdapter(
            Sequence[t.Infra.InfraValue]
        ).validate_python(
            value,
        )
        normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
        for raw_item in typed_items:
            try:
                typed_item: Mapping[str, t.Infra.InfraValue] = TypeAdapter(
                    Mapping[str, t.Infra.InfraValue],
                ).validate_python(raw_item)
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

    @staticmethod
    def _result_exit_code(result: m.Infra.CommandOutput) -> int:
        """Extract exit code from command output."""
        return result.exit_code

    @staticmethod
    def _nested_mapping(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        current: t.Infra.InfraValue = data
        for key in keys:
            if not isinstance(current, Mapping):
                return {}
            typed_current: Mapping[str, t.Infra.InfraValue] = TypeAdapter(
                Mapping[str, t.Infra.InfraValue],
            ).validate_python(current)
            if key not in typed_current:
                return {}
            child: t.Infra.InfraValue = typed_current[key]
            if child is None:
                return {}
            current = child
        if not isinstance(current, Mapping):
            return {}
        return TypeAdapter(Mapping[str, t.Infra.InfraValue]).validate_python(
            current,
        )

    @classmethod
    def _nested_int(
        cls,
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        target = cls._nested_mapping(data, *keys[:-1])
        raw: t.Infra.InfraValue = target.get(keys[-1])
        if raw is None:
            return default
        return cls._as_int(raw, default)


__all__ = ["FlextInfraGate"]
