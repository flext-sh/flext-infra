"""FLEXT bandit quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, t as t_infra, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants

InfraValue = t_infra.Infra.InfraValue


class FlextInfraBanditGate(FlextInfraGate):
    """Gate for Bandit security checks."""

    """Bandit quality gate."""

    gate_id = c.Infra.Gates.SECURITY
    gate_name = "Bandit"
    can_fix = False
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.SECURITY][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.SECURITY][1]

    @staticmethod
    def _to_mapping(value: InfraValue) -> dict[str, InfraValue]:
        if not isinstance(value, Mapping):
            return {}
        return TypeAdapter(dict[str, InfraValue]).validate_python(value)

    @staticmethod
    def _to_mapping_list(value: InfraValue) -> list[dict[str, InfraValue]]:
        if not isinstance(value, list):
            return []
        out: list[dict[str, InfraValue]] = []
        for raw_item in TypeAdapter(list[InfraValue]).validate_python(value):
            try:
                out.append(TypeAdapter(dict[str, InfraValue]).validate_python(raw_item))
            except ValidationError:
                continue
        return out

    @staticmethod
    def _as_int(value: InfraValue, default: int = 0) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if not isinstance(value, str):
            return default
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def _as_str(value: InfraValue, default: str = "") -> str:
        return value if isinstance(value, str) else default

    @override
    @override
    def check(
        self, project_dir: Path, ctx: FlextInfraGateContext
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        started = time.monotonic()
        if not (project_dir / c.Infra.Paths.DEFAULT_SRC_DIR).exists():
            return self._build_gate_result(
                project=project_dir.name,
                passed=True,
                issues=[],
                duration=time.monotonic() - started,
                raw_output="",
            )
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.Cli.BANDIT,
                "-r",
                c.Infra.Paths.DEFAULT_SRC_DIR,
                "-f",
                c.Infra.Cli.OUTPUT_JSON,
                "-q",
                "-ll",
            ],
            project_dir,
        )
        issues: list[m.Infra.Check.Issue] = []
        try:
            parsed = u.Infra.parse(result.stdout or "{}")
            bandit_data = self._to_mapping(parsed.value) if parsed.is_success else {}
            issues.extend(
                m.Infra.Check.Issue(
                    file=self._as_str(raw_item.get("filename", "?"), "?"),
                    line=self._as_int(raw_item.get("line_number", 0)),
                    column=0,
                    code=self._as_str(raw_item.get("test_id", "")),
                    message=self._as_str(raw_item.get("issue_text", "")),
                    severity=self._as_str(
                        raw_item.get("issue_severity", "MEDIUM"), "MEDIUM"
                    ).lower(),
                )
                for raw_item in self._to_mapping_list(bandit_data.get("results", []))
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


__all__ = ["FlextInfraBanditGate"]
