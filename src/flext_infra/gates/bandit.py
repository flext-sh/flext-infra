"""FLEXT bandit quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, u


class FlextInfraBanditGate(FlextInfraGate):
    """Bandit security quality gate."""

    gate_id = c.Infra.SECURITY
    gate_name = "Bandit"
    can_fix = False
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.SECURITY][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.SECURITY][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        started = time.monotonic()
        if not (project_dir / c.Infra.Paths.DEFAULT_SRC_DIR).exists():
            return self._skip_result(project_dir, started)
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.BANDIT,
                "-r",
                c.Infra.Paths.DEFAULT_SRC_DIR,
                "-f",
                c.Infra.OUTPUT_JSON,
                "-q",
                "-ll",
            ],
            project_dir,
        )
        issues: MutableSequence[m.Infra.Issue] = []
        try:
            bandit_data = (
                u.Infra
                .parse(result.stdout or "{}")
                .map(
                    u.Infra.normalize_str_mapping,
                )
                .unwrap_or({})
            )
            issues.extend(
                m.Infra.Issue(
                    file=u.Infra.pick_str(raw_item, "filename", "?"),
                    line=u.Infra.pick_int(raw_item, "line_number"),
                    column=0,
                    code=u.Infra.pick_str(raw_item, "test_id"),
                    message=u.Infra.pick_str(raw_item, "issue_text"),
                    severity=u.Infra.pick_str(
                        raw_item, "issue_severity", "MEDIUM"
                    ).lower(),
                )
                for raw_item in u.Infra.normalize_mapping_list(
                    bandit_data.get("results", [])
                )
            )
        except (TypeError, ValidationError):
            pass
        return self._build_gate_result(
            project=project_dir.name,
            passed=result.exit_code == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraBanditGate"]
