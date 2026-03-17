"""FLEXT pyright quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, t as t_infra, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext


class FlextInfraPyrightGate(FlextInfraGate):
    """Gate for Pyright type checks."""

    """Pyright quality gate."""

    gate_id: str = c.Infra.Gates.PYRIGHT
    gate_name: str = "Pyright"
    can_fix: bool = False
    tool_name: str = "Pyright"
    tool_url: str = "https://github.com/microsoft/pyright"

    @override
    @override
    def check(
        self, project_dir: Path, ctx: FlextInfraGateContext
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        started = time.monotonic()
        check_dirs = self._dirs_with_py(
            project_dir, self._existing_check_dirs(project_dir)
        )
        if not check_dirs:
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="",
            )
        result = self._run(
            [sys.executable, "-m", c.Infra.Cli.PYRIGHT, *check_dirs, "--outputjson"],
            project_dir,
            timeout=c.Infra.Timeouts.LONG,
        )
        issues: list[m.Infra.Check.Issue] = []
        parsed = u.Infra.parse(result.stdout or "{}")
        data = self._to_mapping(parsed.value if parsed.is_success else {})
        try:
            diagnostics = self._to_mapping_list(data.get("generalDiagnostics", []))
            issues.extend(
                m.Infra.Check.Issue(
                    file=str(diag.get("file", "?")),
                    line=self._nested_int(diag, "range", "start", "line") + 1,
                    column=self._nested_int(diag, "range", "start", "character") + 1,
                    code=str(diag.get("rule", "")),
                    message=str(diag.get("message", "")),
                    severity=str(diag.get("severity", c.Infra.Toml.ERROR)),
                )
                for diag in diagnostics
            )
        except (TypeError, ValidationError):
            pass
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )

    @staticmethod
    def _to_mapping(
        value: t_infra.Infra.InfraValue,
    ) -> dict[str, t_infra.Infra.InfraValue]:
        if not isinstance(value, Mapping):
            return {}
        return TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(value)

    @classmethod
    def _to_mapping_list(
        cls, value: t_infra.Infra.InfraValue
    ) -> list[dict[str, t_infra.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        typed = TypeAdapter(list[t_infra.Infra.InfraValue]).validate_python(value)
        normalized: list[dict[str, t_infra.Infra.InfraValue]] = []
        for item in typed:
            try:
                normalized.append(
                    TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(
                        item
                    )
                )
            except ValidationError:
                continue
        return normalized

    @staticmethod
    def _nested_mapping(
        data: dict[str, t_infra.Infra.InfraValue], *keys: str
    ) -> dict[str, t_infra.Infra.InfraValue]:
        current: t_infra.Infra.InfraValue = data
        for key in keys:
            if not isinstance(current, Mapping):
                return {}
            typed = TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(
                current
            )
            if key not in typed:
                return {}
            child: t_infra.Infra.InfraValue = typed[key]
            if child is None:
                return {}
            current = child
        if not isinstance(current, Mapping):
            return {}
        return TypeAdapter(dict[str, t_infra.Infra.InfraValue]).validate_python(current)

    @classmethod
    def _nested_int(
        cls, data: dict[str, t_infra.Infra.InfraValue], *keys: str, default: int = 0
    ) -> int:
        target = cls._nested_mapping(data, *keys[:-1])
        raw: t_infra.Infra.InfraValue = target.get(keys[-1])
        if isinstance(raw, int):
            return raw
        if isinstance(raw, float):
            return int(raw)
        if isinstance(raw, str):
            try:
                return int(raw)
            except ValueError:
                return default
        return default


__all__ = ["FlextInfraPyrightGate"]
