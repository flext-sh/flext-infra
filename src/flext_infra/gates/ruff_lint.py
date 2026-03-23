"""FLEXT ruff_lint quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraRuffLintGate(FlextInfraGate):
    """Gate for Ruff lint checks."""

    """Ruff Lint quality gate."""
    gate_id = c.Infra.Gates.LINT
    gate_name = "Ruff Lint"
    can_fix = False
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.Gates.LINT][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.Gates.LINT][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
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
        issues: MutableSequence[m.Infra.Issue] = []
        ruff_parse_result = u.Infra.parse(result.stdout or "[]")
        ruff_data: t.Infra.InfraValue = (
            ruff_parse_result.value if ruff_parse_result.is_success else []
        )
        try:
            if isinstance(ruff_data, list):
                issues.extend(
                    m.Infra.Issue(
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
