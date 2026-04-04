"""FLEXT pyright quality gate."""

from __future__ import annotations

import sys
import time
from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, u


class FlextInfraPyrightGate(FlextInfraGate):
    """Pyright quality gate."""

    gate_id: str = c.Infra.PYRIGHT
    gate_name: str = "Pyright"
    can_fix: bool = False
    tool_name: str = "Pyright"
    tool_url: str = "https://github.com/microsoft/pyright"

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        _ = ctx
        started = time.monotonic()
        check_dirs = self._dirs_with_py(
            project_dir,
            self._existing_check_dirs(project_dir),
        )
        if not check_dirs:
            return self._skip_result(project_dir, started)
        result = self._run(
            [
                sys.executable,
                "-m",
                c.Infra.PYRIGHT,
                *check_dirs,
                *ctx.pyright_args,
                "--outputjson",
            ],
            project_dir,
            timeout=c.Infra.Timeouts.LONG,
        )
        issues: MutableSequence[m.Infra.Issue] = []
        data = (
            u.Infra
            .parse(result.stdout or "{}")
            .map(
                u.Infra.normalize_str_mapping,
            )
            .unwrap_or({})
        )
        try:
            diagnostics = u.Infra.deep_list(data, "generalDiagnostics")
            issues.extend(
                m.Infra.Issue(
                    file=u.Infra.pick_str(diag, "file", "?"),
                    line=u.Infra.nested_int(diag, "range", "start", "line") + 1,
                    column=u.Infra.nested_int(diag, "range", "start", "character") + 1,
                    code=u.Infra.pick_str(diag, "rule"),
                    message=u.Infra.pick_str(diag, "message"),
                    severity=u.Infra.pick_str(diag, "severity", c.Infra.ERROR),
                )
                for diag in diagnostics
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


__all__ = ["FlextInfraPyrightGate"]
