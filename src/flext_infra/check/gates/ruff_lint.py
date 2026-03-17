"""FLEXT ruff_lint quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import c, m, t as t_infra, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraRuffLintGate(FlextInfraGate):
    """Gate for Ruff lint checks."""

    """Ruff Lint quality gate."""
    gate_id = c.Infra.Gates.LINT
    gate_name = "Ruff Lint"
    can_fix = False
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.LINT][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.LINT][1]

    @classmethod
    def _nested_int(
        cls,
        data: dict[str, t_infra.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        current: t_infra.Infra.InfraValue = data
        for key in keys:
            if not isinstance(current, Mapping):
                return default
            value = current.get(key)
            if value is None:
                return default
            current = value
        if isinstance(current, int):
            return current
        if isinstance(current, float):
            return int(current)
        if isinstance(current, str):
            try:
                return int(current)
            except ValueError:
                return default
        return default

    @override
    @override
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.Check.GateExecution:
        _ = ctx
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        targets = check_dirs or ["."]
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.Toml.RUFF,
                c.Infra.Verbs.CHECK,
                *targets,
                "--output-format",
                c.Infra.Cli.OUTPUT_JSON,
                "--quiet",
            ],
            project_dir,
        )
        issues: list[m.Infra.Check.Issue] = []
        ruff_parse_result = u.Infra.parse(result.stdout or "[]")
        ruff_data: t_infra.Infra.InfraValue = (
            ruff_parse_result.value if ruff_parse_result.is_success else []
        )
        try:
            if isinstance(ruff_data, list):
                issues.extend(
                    m.Infra.Check.Issue(
                        file=str(entry.get("filename", "?")),
                        line=self._nested_int(dict(entry.items()), "location", "row"),
                        column=self._nested_int(
                            dict(entry.items()),
                            "location",
                            "column",
                        ),
                        code=str(entry.get("code", "")),
                        message=str(entry.get("message", "")),
                    )
                    for entry in ruff_data
                    if isinstance(entry, Mapping)
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


__all__ = ["FlextInfraRuffLintGate"]
