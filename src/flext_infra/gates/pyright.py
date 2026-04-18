"""FLEXT pyright quality gate."""

from __future__ import annotations

import sys
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraPyrightGate(FlextInfraGate):
    """Pyright quality gate."""

    gate_id: ClassVar[str] = c.Infra.PYRIGHT
    gate_name: ClassVar[str] = "Pyright"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.PYRIGHT][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.PYRIGHT][1]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        _ = project_dir
        return [
            sys.executable,
            "-m",
            c.Infra.PYRIGHT,
            *check_dirs,
            *ctx.pyright_args,
            "--outputjson",
        ]

    @override
    def _check_timeout(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> int:
        _ = project_dir, ctx
        return c.Infra.TIMEOUT_LONG

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        _ = project_dir, ctx
        issues: MutableSequence[m.Infra.Issue] = []
        empty: Mapping[str, t.Infra.InfraValue] = {}
        parsed_result = u.Cli.json_parse(result.stdout or "{}")
        parsed = parsed_result.unwrap() if parsed_result.success else empty
        data = (
            u.Infra.normalize_str_mapping(parsed)
            if isinstance(parsed, Mapping)
            else empty
        )
        try:
            diagnostics = u.Infra.deep_list(
                data,
                c.Infra.PYRIGHT_DIAGNOSTICS_KEY,
            )
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
        except (TypeError, c.ValidationError) as err:
            issues.append(
                m.Infra.Issue(
                    file="<pyright-output>",
                    line=0,
                    column=0,
                    code="PARSE_ERROR",
                    message=f"Tool output parsing failed: {type(err).__name__}",
                    severity="ERROR",
                )
            )
            return False, issues
        return result.exit_code == 0, issues


__all__: list[str] = ["FlextInfraPyrightGate"]
