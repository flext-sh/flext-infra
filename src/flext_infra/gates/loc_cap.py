"""FLEXT 200-LOC SUPREME LAW (§3.1) module-cap quality gate.

Enforces the per-module logical-LOC ceiling using tokei's code-line count.
Per-class / per-method / per-function caps require AST and are out of scope
for this tool-driven gate (tokei reports at file granularity only).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, t, u
from flext_infra.gates.base_gate import FlextInfraGate


class FlextInfraLocCapGate(FlextInfraGate):
    """Flag any module whose tokei `code` LOC exceeds the 200-line SUPREME LAW."""

    gate_id: ClassVar[str] = "loc-cap"
    gate_name: ClassVar[str] = "200-LOC SUPREME LAW"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["loc-cap"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["loc-cap"][1]

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: p.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Run tokei over the project's Python directories, emitting JSON."""
        _ = project_dir, ctx
        return [c.Infra.TOKEI_BINARY, "--output", "json", *check_dirs]

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: p.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[p.Infra.Issue]]:
        """Parse tokei JSON into one Issue per over-cap module."""
        _ = project_dir, ctx
        issues = self._files_over_cap(result.stdout or "{}", c.Infra.LOC_CAP_MAX)
        return len(issues) == 0, issues

    @classmethod
    def _files_over_cap(cls, tokei_json: str, cap: int) -> tuple[p.Infra.Issue, ...]:
        """Extract over-cap modules from a tokei `--output json` payload.

        Pure function (no subprocess) so the cap logic is unit-testable against
        a literal tokei fixture.

        Returns:
            Tuple of ``Issue`` objects for every module whose code LOC exceeds
            the supplied cap.
        """
        parsed = u.Cli.json_parse(tokei_json or "{}")
        empty: t.JsonValue = {}
        data = parsed.unwrap() if parsed.success else empty
        if not isinstance(data, Mapping):
            return ()
        issues: t.MutableSequenceOf[p.Infra.Issue] = []
        for language, payload in data.items():
            if language != c.Infra.TOKEI_PYTHON_LANG or not isinstance(
                payload, Mapping
            ):
                continue
            reports = payload.get("reports")
            if not isinstance(reports, list):
                continue
            for report in reports:
                if not isinstance(report, Mapping):
                    continue
                code = u.Cli.json_nested_int(report, "stats", "code")
                if code > cap:
                    name = u.Cli.json_pick_str(report, "name", "?")
                    issues.append(
                        m.Infra.Issue(
                            file=name,
                            line=code,
                            column=0,
                            code="LOC_CAP",
                            message=f"{code} code LOC exceeds {cap}-line SUPREME LAW",
                            severity="ERROR",
                        )
                    )
        return tuple(issues)


__all__: list[str] = ["FlextInfraLocCapGate"]
