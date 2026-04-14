"""FLEXT ruff_lint quality gate."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import ValidationError

from flext_infra import FlextInfraGate, c, m, t, u


class FlextInfraRuffLintGate(FlextInfraGate):
    """Ruff Lint quality gate."""

    gate_id: ClassVar[str] = c.Infra.LINT
    gate_name: ClassVar[str] = "Ruff Lint"
    can_fix: ClassVar[bool] = True
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.LINT][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[c.Infra.LINT][1]

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Ruff always runs — never skip."""
        _ = ctx
        return self._existing_check_dirs(project_dir) or ["."]

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        _ = project_dir
        return [
            c.Infra.RUFF,
            c.Infra.VERB_CHECK,
            *check_dirs,
            *ctx.ruff_args,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "--quiet",
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
        parsed_result = u.Cli.json_parse(result.stdout or "[]")
        empty_items: list[object] = []
        ruff_data = parsed_result.unwrap() if parsed_result.success else empty_items
        try:
            if isinstance(ruff_data, list):
                for entry in ruff_data:
                    if isinstance(entry, Mapping):
                        issues.append(
                            m.Infra.Issue(
                                file=u.Infra.pick_str(entry, "filename", "?"),
                                line=u.Infra.nested_int(entry, "location", "row"),
                                column=u.Infra.nested_int(entry, "location", "column"),
                                code=u.Infra.pick_str(entry, "code"),
                                message=u.Infra.pick_str(entry, "message"),
                            ),
                        )
        except (TypeError, ValidationError):
            pass
        return result.exit_code == 0, issues

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> t.StrSequence:
        _ = project_dir
        return [
            c.Infra.RUFF,
            c.Infra.VERB_CHECK,
            *targets,
            *ctx.ruff_args,
            "--fix",
            "--quiet",
        ]


__all__: list[str] = ["FlextInfraRuffLintGate"]
