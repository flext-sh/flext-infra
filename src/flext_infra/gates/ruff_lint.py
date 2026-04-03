"""FLEXT ruff_lint quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import Mapping, MutableSequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, u


class FlextInfraRuffLintGate(FlextInfraGate):
    """Ruff Lint quality gate."""

    gate_id = c.Infra.LINT
    gate_name = "Ruff Lint"
    can_fix = True
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.LINT][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.LINT][1]

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
                c.Infra.RUFF,
                c.Infra.Verbs.CHECK,
                *targets,
                *ctx.ruff_args,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--quiet",
            ],
            project_dir,
        )
        issues: MutableSequence[m.Infra.Issue] = []
        ruff_data = u.Infra.parse(result.stdout or "[]").unwrap_or([])
        try:
            if isinstance(ruff_data, list):
                for entry in ruff_data:
                    if isinstance(entry, Mapping):
                        issues.append(
                            m.Infra.Issue(
                                file=u.Infra.pick(entry, "filename", "?"),
                                line=u.Infra.nested_int(entry, "location", "row"),
                                column=u.Infra.nested_int(entry, "location", "column"),
                                code=u.Infra.pick(entry, "code", ""),
                                message=u.Infra.pick(entry, "message", ""),
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

    @override
    def fix(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        targets = check_dirs or ["."]
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                c.Infra.Verbs.CHECK,
                *targets,
                *ctx.ruff_args,
                "--fix",
                "--quiet",
            ],
            project_dir,
        )
        return self._build_gate_result(
            project=project_dir.name,
            passed=result.exit_code == 0,
            issues=[],
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraRuffLintGate"]
