"""FLEXT module-cap SUPREME LAW (§3.1) quality gate.

Enforces the per-module logical-LOC ceiling using scc's code-line count.
Per-class / per-method / per-function caps require AST and are out of scope
for this tool-driven gate (scc reports at file granularity only).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraLocCapGate(FlextInfraGate):
    """Flag any module whose scc `Code` LOC exceeds ``c.Infra.LOC_CAP_MAX``."""

    gate_id: ClassVar[str] = "loc-cap"
    gate_name: ClassVar[str] = "MODULE-LOC SUPREME LAW"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["loc-cap"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["loc-cap"][1]

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Run scc over the project's Python directories, emitting per-file JSON."""
        _ = project_dir, ctx
        return [c.Infra.SCC_BINARY, "--format", "json", "--by-file", *check_dirs]

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse scc JSON into one Issue per over-cap module."""
        _ = project_dir, ctx
        if result.exit_code != 0:
            return (
                False,
                (
                    m.Infra.Issue(
                        file="<scc>",
                        line=0,
                        column=0,
                        code="LOC_CAP_EXEC",
                        message=result.stderr or "scc execution failed",
                        severity="ERROR",
                    ),
                ),
            )
        issues = self._files_over_cap(result.stdout or "[]", c.Infra.LOC_CAP_MAX)
        return len(issues) == 0, issues

    @classmethod
    def _files_over_cap(cls, scc_json: str, cap: int) -> tuple[m.Infra.Issue, ...]:
        """Extract over-cap modules from an `scc --format json --by-file` payload.

        Pure function (no subprocess) so the cap logic is unit-testable against
        a literal scc fixture.
        """
        parsed = u.Cli.json_parse(scc_json or "[]")
        empty: t.JsonValue = []
        data = parsed.unwrap() if parsed.success else empty
        if not isinstance(data, list):
            return ()
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        for language_entry in data:
            if not isinstance(language_entry, Mapping):
                continue
            if language_entry.get("Name") != c.Infra.SCC_PYTHON_LANG:
                continue
            files = language_entry.get("Files")
            if not isinstance(files, list):
                continue
            for file_entry in files:
                if not isinstance(file_entry, Mapping):
                    continue
                code = u.Cli.json_pick_int(file_entry, "Code")
                if code > cap:
                    name = u.Cli.json_pick_str(file_entry, "Location", "?")
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
