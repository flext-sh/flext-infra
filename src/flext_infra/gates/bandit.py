"""FLEXT bandit quality gate."""

from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraBanditGate(FlextInfraGate):
    """Bandit security quality gate."""

    gate_id: ClassVar[str] = c.Infra.SECURITY
    gate_name: ClassVar[str] = "Bandit"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.SECURITY][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.SECURITY][1]

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Get check dirs."""
        _ = ctx
        if not (project_dir / c.Infra.DEFAULT_SRC_DIR).exists():
            return []
        return [c.Infra.DEFAULT_SRC_DIR]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Build check command."""
        _ = project_dir, ctx
        return [
            c.Infra.BANDIT,
            "-r",
            *check_dirs,
            "-f",
            c.Infra.OUTPUT_JSON,
            "-q",
            "-ll",
        ]

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse check output."""
        _ = project_dir, ctx
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        try:
            parsed_result = u.Cli.json_parse(result.stdout or "{}")
            empty_mapping: t.MappingKV[str, t.Infra.InfraValue] = {}
            raw_payload = (
                parsed_result.unwrap() if parsed_result.success else empty_mapping
            )
            bandit_data: t.MappingKV[str, t.Infra.InfraValue] = (
                u.Cli.json_as_mapping(raw_payload)
                if isinstance(raw_payload, Mapping)
                else empty_mapping
            )
            issues.extend(
                m.Infra.Issue(
                    file=u.Cli.json_pick_str(raw_item, "filename", "?"),
                    line=u.Cli.json_pick_int(raw_item, "line_number"),
                    column=0,
                    code=u.Cli.json_pick_str(raw_item, "test_id"),
                    message=u.Cli.json_pick_str(raw_item, "issue_text"),
                    severity=u.Cli.json_pick_str(
                        raw_item,
                        "issue_severity",
                        "MEDIUM",
                    ).lower(),
                )
                for raw_item in u.Cli.json_as_mapping_list(
                    bandit_data.get(c.Infra.BANDIT_RESULTS_KEY, []),
                )
            )
        except c.EXC_VALIDATION_TYPE as err:
            issues.append(
                m.Infra.Issue(
                    file="<bandit-output>",
                    line=0,
                    column=0,
                    code="PARSE_ERROR",
                    message=f"Tool output parsing failed: {type(err).__name__}",
                    severity="ERROR",
                )
            )
            return False, issues
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraBanditGate"]
