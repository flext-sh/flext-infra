"""FLEXT bandit quality gate."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import c, m, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraBanditGate(FlextInfraGate):
    """Gate for Bandit security checks."""

    """Bandit quality gate."""

    gate_id = c.Infra.Gates.SECURITY
    gate_name = "Bandit"
    can_fix = False
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.SECURITY][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.SECURITY][1]

    @override
    def check(
        self, project_dir: Path, ctx: FlextInfraGateContext,
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
                        raw_item.get("issue_severity", "MEDIUM"), "MEDIUM",
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
