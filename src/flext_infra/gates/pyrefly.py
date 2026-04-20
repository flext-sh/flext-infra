"""FLEXT pyrefly quality gate."""

from __future__ import annotations

import sys
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar, override

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
                parsed_result = u.Cli.json_parse(raw_text)
                parsed_value = parsed_result.unwrap() if parsed_result.success else None
                error_items: Sequence[Mapping[str, t.Infra.InfraValue]] = []
                if isinstance(parsed_value, Mapping):
                    try:
                        error_items = u.Cli.json_deep_mapping_list(
                            u.Cli.json_as_mapping(parsed_value),
                            c.Infra.PYREFLY_ERRORS_KEY,
                        )
                    except (TypeError, c.ValidationError) as err:
                        issues.append(
                            m.Infra.Issue(
                                file="<pyrefly-output>",
                                line=0,
                                column=0,
                                code="PARSE_ERROR",
                                message=f"Tool output parsing failed: {type(err).__name__}",
                                severity="ERROR",
                            )
                        )
                        return False, issues
                elif isinstance(parsed_value, list):
                    try:
                        error_items = u.Cli.json_as_mapping_list(parsed_value)
                    except (TypeError, c.ValidationError) as err:
                        issues.append(
                            m.Infra.Issue(
                                file="<pyrefly-output>",
                                line=0,
                                column=0,
                                code="PARSE_ERROR",
                                message=f"Tool output parsing failed: {type(err).__name__}",
                                severity="ERROR",
                            )
                        )
                        return False, issues
                issues.extend(
                    m.Infra.Issue(
                        file=u.Cli.json_pick_str(err, "path", "?"),
                        line=u.Cli.json_pick_int(err, "line"),
                        column=u.Cli.json_pick_int(err, "column"),
                        code=u.Cli.json_pick_str(err, "name"),
                        message=u.Cli.json_pick_str(err, "description"),
                        severity=u.Cli.json_pick_str(err, "severity", c.Infra.ERROR),
                    )
                    for err in error_items
                )
            except (TypeError, c.ValidationError) as err:
                issues.append(
                    m.Infra.Issue(
                        file="<pyrefly-output>",
                        line=0,
                        column=0,
                        code="PARSE_ERROR",
                        message=(
                            "Tool output parsing failed while collecting diagnostics: "
                            f"{type(err).__name__}"
                        ),
                        severity=c.Infra.ERROR,
                    )
                )
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
