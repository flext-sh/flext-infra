"""FLEXT bandit quality gate."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


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
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = project_dir, ctx
        issues: MutableSequence[m.Infra.Issue] = []
        try:
            parsed_result = u.Cli.json_parse(result.stdout or "{}")
            empty_mapping: Mapping[str, t.Infra.InfraValue] = {}
            raw_payload = (
                parsed_result.unwrap() if parsed_result.success else empty_mapping
            )
            bandit_data: Mapping[str, t.Infra.InfraValue] = (
                u.Infra.normalize_str_mapping(raw_payload)
                if isinstance(raw_payload, Mapping)
                else empty_mapping
            )
            issues.extend(
                m.Infra.Issue(
                    file=u.Infra.pick_str(raw_item, "filename", "?"),
                    line=u.Infra.pick_int(raw_item, "line_number"),
                    column=0,
                    code=u.Infra.pick_str(raw_item, "test_id"),
                    message=u.Infra.pick_str(raw_item, "issue_text"),
                    severity=u.Infra.pick_str(
                        raw_item,
                        "issue_severity",
                        "MEDIUM",
                    ).lower(),
                )
                for raw_item in u.Infra.normalize_mapping_list(
                    bandit_data.get(c.Infra.BANDIT_RESULTS_KEY, []),
                )
            )
        except (TypeError, ValidationError):
            pass
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraBanditGate"]
