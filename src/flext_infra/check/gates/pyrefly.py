"""FLEXT pyrefly quality gate."""

from __future__ import annotations

import re
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import override

from pydantic import ValidationError

from flext_infra import c, m, t as t_infra, u
from flext_infra.check._base_gate import FlextInfraGate, FlextInfraGateContext
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraPyreflyGate(FlextInfraGate):
    """Gate for Pyrefly checks."""

    """Pyrefly quality gate."""

    gate_id = c.Infra.Gates.PYREFLY
    gate_name = "Pyrefly"
    can_fix = False
    tool_name = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.PYREFLY][0]
    tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO[c.Infra.Gates.PYREFLY][1]

    @override
    @override
    def check(
        self,
        project_dir: Path,
        ctx: FlextInfraGateContext,
    ) -> m.Infra.GateExecution:
        started = time.monotonic()
        check_dirs = self._existing_check_dirs(project_dir)
        targets = check_dirs or [c.Infra.Paths.DEFAULT_SRC_DIR]
        json_file = ctx.reports_dir / f"{project_dir.name}-pyrefly.json"
        cmd = [
            sys.executable,
            "-m",
            c.Infra.Cli.PYREFLY,
            c.Infra.Cli.RuffCmd.CHECK,
            *targets,
            "--config",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--output-format",
            c.Infra.Cli.OUTPUT_JSON,
            "-o",
            str(json_file),
            "--summary=none",
        ]
        result = self._run(cmd, project_dir)
        issues: list[m.Infra.Issue] = []
        if json_file.exists():
            try:
                raw_text = json_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
                parsed = u.Infra.parse(raw_text)
                if parsed.is_success and isinstance(parsed.value, Mapping):
                    parsed_map = self._to_mapping(parsed.value)
                    error_items: list[dict[str, t_infra.Infra.InfraValue]] = (
                        self._to_mapping_list(parsed_map.get("errors", []))
                    )
                elif parsed.is_success and isinstance(parsed.value, list):
                    error_items = self._to_mapping_list(parsed.value)
                else:
                    error_items = []
                issues.extend(
                    m.Infra.Issue(
                        file=self._as_str(item.get("path"), "?"),
                        line=self._as_int(item.get("line"), 0),
                        column=self._as_int(item.get("column"), 0),
                        code=self._as_str(item.get("name"), ""),
                        message=self._as_str(item.get("description"), ""),
                        severity=self._as_str(item.get("severity"), c.Infra.Toml.ERROR),
                    )
                    for err in error_items
                    for item in [dict(err)]
                )
            except (TypeError, ValidationError):
                pass
        if not issues and self._result_exit_code(result) != 0:
            match = re.search(r"(\d+)\s+errors?", result.stderr + result.stdout)
            if match:
                count = int(match.group(1))
                issues = [
                    m.Infra.Issue(
                        file="?",
                        line=0,
                        column=0,
                        code=c.Infra.Gates.PYREFLY,
                        message=f"Pyrefly reported {count} error(s)",
                    ),
                ] * count
        return self._build_gate_result(
            project=project_dir.name,
            passed=self._result_exit_code(result) == 0,
            issues=issues,
            duration=time.monotonic() - started,
            raw_output=result.stderr,
        )


__all__ = ["FlextInfraPyreflyGate"]
