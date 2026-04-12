"""FLEXT pyrefly quality gate."""

from __future__ import annotations

import sys
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraPyreflyGate(FlextInfraGate):
    """Pyrefly quality gate."""

    gate_id: ClassVar[str] = c.Infra.PYREFLY
    gate_name: ClassVar[str] = "Pyrefly"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.PYREFLY][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.PYREFLY][1]

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Check only local Python roots to avoid scanning dependency trees."""
        _ = ctx
        discovered_dirs = u.Infra.discover_python_dirs(project_dir)
        if discovered_dirs:
            return discovered_dirs
        if any(project_dir.glob(c.Infra.EXT_PYTHON_GLOB)) or any(
            project_dir.glob("*.pyi")
        ):
            return ["."]
        return []

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        json_file = ctx.reports_dir / f"{project_dir.name}-pyrefly.json"
        return [
            c.Infra.PYREFLY,
            c.Infra.CHECK,
            *check_dirs,
            "--config",
            c.Infra.PYPROJECT_FILENAME,
            "--python-interpreter-path",
            sys.executable,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "-o",
            str(json_file),
            "--summary=none",
        ]

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        json_file = ctx.reports_dir / f"{project_dir.name}-pyrefly.json"
        issues: MutableSequence[m.Infra.Issue] = []
        if json_file.exists():
            try:
                raw_text = json_file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
                parsed_value = u.Cli.json_parse(raw_text).unwrap_or(None)
                error_items: Sequence[Mapping[str, t.Infra.InfraValue]] = []
                if isinstance(parsed_value, Mapping):
                    error_items = u.Infra.deep_list(
                        u.Infra.normalize_str_mapping(parsed_value),
                        c.Infra.PYREFLY_ERRORS_KEY,
                    )
                elif isinstance(parsed_value, list):
                    error_items = u.Infra.normalize_mapping_list(parsed_value)
                issues.extend(
                    m.Infra.Issue(
                        file=u.Infra.pick_str(err, "path", "?"),
                        line=u.Infra.pick_int(err, "line"),
                        column=u.Infra.pick_int(err, "column"),
                        code=u.Infra.pick_str(err, "name"),
                        message=u.Infra.pick_str(err, "description"),
                        severity=u.Infra.pick_str(err, "severity", c.Infra.ERROR),
                    )
                    for err in error_items
                )
            except (TypeError, ValidationError):
                pass
        if (not issues) and result.exit_code != 0:
            message = (result.stderr or result.stdout).strip()
            if not message:
                message = (
                    f"pyrefly exited with code {result.exit_code} "
                    "without JSON diagnostics"
                )
            issues.append(
                m.Infra.Issue(
                    file=c.Infra.PYPROJECT_FILENAME,
                    line=1,
                    column=1,
                    code="pyrefly-exec",
                    message=message,
                    severity=c.Infra.ERROR,
                )
            )
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraPyreflyGate"]
