"""FLEXT pyrefly quality gate."""

from __future__ import annotations

import re
import sys
import time
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraPyreflyGate(FlextInfraGate):
    """Pyrefly quality gate."""

    gate_id = c.Infra.PYREFLY
    gate_name = "Pyrefly"
    can_fix = False
    tool_name = c.Infra.SARIF_TOOL_INFO[c.Infra.PYREFLY][0]
    tool_url = c.Infra.SARIF_TOOL_INFO[c.Infra.PYREFLY][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        started = time.monotonic()
        json_file = ctx.reports_dir / f"{project_dir.name}-pyrefly.json"
        cmd = [
            sys.executable,
            "-m",
            c.Infra.PYREFLY,
            c.Infra.CHECK,
            ".",
            "--config",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--python-interpreter-path",
            sys.executable,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "-o",
            str(json_file),
            "--summary=none",
        ]
        result = self._run(cmd, project_dir)
        issues: MutableSequence[m.Infra.Issue] = []
        if json_file.exists():
            try:
                raw_text = json_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
                parsed_value = u.Infra.parse(raw_text).unwrap_or(None)
                error_items: Sequence[Mapping[str, t.Infra.InfraValue]] = []
                if u.is_mapping(parsed_value):
                    error_items = u.Infra.deep_list(
                        u.Infra.normalize_str_mapping(parsed_value),
                        "errors",
                    )
                elif isinstance(parsed_value, list):
                    error_items = u.Infra.normalize_mapping_list(parsed_value)
                issues.extend(
                    m.Infra.Issue(
                        file=u.Infra.pick(err, "path", "?"),
                        line=u.Infra.pick(err, "line", 0),
                        column=u.Infra.pick(err, "column", 0),
                        code=u.Infra.pick(err, "name", ""),
                        message=u.Infra.pick(err, "description", ""),
                        severity=u.Infra.pick(err, "severity", c.Infra.ERROR),
                    )
                    for err in error_items
                )
            except (TypeError, ValidationError):
                pass
        if not issues and result.exit_code != 0:
            match = re.search(r"(\d+)\s+errors?", result.stderr + result.stdout)
            if match:
                count = int(match.group(1))
                issues = [
                    m.Infra.Issue(
                        file="?",
                        line=0,
                        column=0,
                        code=c.Infra.PYREFLY,
                        message=f"Pyrefly reported {count} error(s)",
                    ),
                ] * count
        return self._build_gate_result(
            project=project_dir.name,
            passed=result.exit_code == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraPyreflyGate"]
