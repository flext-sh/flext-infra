"""Reporting utilities for standardized .reports/ path management.

Convention::

    .reports/
    ├── {verb}/              # Project-level (check, test, validate, docs, …)
    │   └── {report-files}
    └── workspace/           # Workspace-level
        └── {verb}/
            └── {project}.log

Known verbs: build, check, dependencies, docs, preflight, release, tests,
validate, workspace.

All methods are static — exposed via u.Infra.get_report_dir() through MRO.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t


class FlextInfraUtilitiesReporting:
    """Static reporting utilities for standardized report path management.

    All methods are ``@staticmethod`` — no instantiation required.
    Exposed via ``u.Infra.get_report_dir()`` etc. through MRO.
    """

    @staticmethod
    def get_report_dir(workspace_root: Path | str, scope: str, verb: str) -> Path:
        """Build a standardized report directory path (no I/O).

        Args:
            workspace_root: Workspace or project root.
            scope: ``"project"`` or ``"workspace"``.
            verb: Action verb (check, test, validate, docs, …).

        Returns:
            Absolute Path to the report directory.

        """
        root_path = (
            Path(workspace_root) if isinstance(workspace_root, str) else workspace_root
        )
        base = root_path / c.Infra.Reporting.REPORTS_DIR_NAME
        if scope == c.Infra.ReportKeys.WORKSPACE:
            return (base / c.Infra.ReportKeys.WORKSPACE / verb).resolve()
        return (base / verb).resolve()

    @staticmethod
    def get_report_path(
        workspace_root: Path | str,
        scope: str,
        verb: str,
        filename: str,
    ) -> Path:
        """Build a standardized report file path (no I/O).

        Args:
            workspace_root: Workspace or project root.
            scope: ``"project"`` or ``"workspace"``.
            verb: Action verb (check, test, validate, docs, …).
            filename: Report filename.

        Returns:
            Absolute Path to the report file.

        """
        return (
            FlextInfraUtilitiesReporting.get_report_dir(workspace_root, scope, verb)
            / filename
        )

    @staticmethod
    def _issue_to_sarif_result(issue: m.Infra.Issue) -> m.Infra.SarifResult:
        """Convert a single gate issue to a SARIF result entry."""
        rule_id = issue.code or c.Infra.Defaults.UNKNOWN
        level = (
            c.Infra.ERROR
            if issue.severity == c.Infra.ERROR
            else c.Infra.Severity.WARNING
        )
        return m.Infra.SarifResult(
            rule_id=rule_id,
            level=level,
            message=issue.message,
            locations=[
                m.Infra.SarifLocation(
                    uri=issue.file,
                    start_line=max(issue.line, 1),
                    start_column=max(issue.column, 1),
                ),
            ],
        )

    @staticmethod
    def _build_sarif_run(
        gate: str,
        results: Sequence[m.Infra.ProjectResult],
    ) -> m.Infra.SarifRun:
        """Build a single SARIF run for one gate across all projects."""
        tool_name, tool_url = c.Infra.SARIF_TOOL_INFO.get(gate, (gate, ""))
        sarif_results: list[m.Infra.SarifResult] = []
        rules_seen: t.Infra.StrSet = set()
        rules: list[m.Infra.SarifRule] = []
        for project in results:
            gate_result = project.gates.get(gate)
            if not gate_result:
                continue
            for issue in gate_result.issues:
                rule_id = issue.code or c.Infra.Defaults.UNKNOWN
                if rule_id not in rules_seen:
                    rules_seen.add(rule_id)
                    rules.append(
                        m.Infra.SarifRule(id=rule_id, short_description=rule_id),
                    )
                sarif_results.append(
                    FlextInfraUtilitiesReporting._issue_to_sarif_result(issue),
                )
        return m.Infra.SarifRun(
            tool_name=tool_name,
            information_uri=tool_url,
            rules=tuple(rules),
            results=tuple(sarif_results),
        )

    @staticmethod
    def generate_sarif(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
    ) -> t.Cli.JsonValue:
        """Generate a SARIF 2.1.0 payload from gate results."""
        sarif_runs = tuple(
            FlextInfraUtilitiesReporting._build_sarif_run(gate, results)
            for gate in gates
        )
        sarif_report = m.Infra.SarifReport(runs=sarif_runs)
        sarif_dict: dict[str, t.Cli.JsonValue] = dict(
            sarif_report.model_dump(mode="json", by_alias=True)
        )
        return sarif_dict

    @staticmethod
    def _markdown_summary_table(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
    ) -> t.Infra.Pair[t.StrSequence, int]:
        """Build markdown summary table rows. Returns (lines, failed_count)."""
        header = "| Project |"
        sep = "|---------|"
        for gate in gates:
            header += f" {gate.capitalize()} |"
            sep += "------|"
        header += " Total | Status |"
        sep += "-------|--------|"
        lines: MutableSequence[str] = [header, sep]
        failed_count = 0
        for project in results:
            row = f"| {project.project} |"
            for gate in gates:
                gate_result = project.gates.get(gate)
                row += f" {(len(gate_result.issues) if gate_result else 0)} |"
            status = (
                c.Infra.Status.PASSED
                if project.passed
                else f"**{c.Infra.Status.FAIL}**"
            )
            if not project.passed:
                failed_count += 1
            row += f" {project.total_errors} | {status} |"
            lines.append(row)
        return (lines, failed_count)

    @staticmethod
    def _markdown_project_details(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
    ) -> t.StrSequence:
        """Build per-project error detail sections."""
        lines: MutableSequence[str] = []
        for project in sorted(results, key=lambda p: p.total_errors, reverse=True):
            if project.total_errors == 0:
                continue
            lines.extend([f"## {project.project}", ""])
            for gate in gates:
                gate_result = project.gates.get(gate)
                if not gate_result or not gate_result.issues:
                    continue
                lines.extend([
                    f"### {gate} ({len(gate_result.issues)} errors)",
                    "",
                    "```",
                ])
                lines.extend(
                    issue.formatted
                    for issue in gate_result.issues[: c.Infra.MAX_DISPLAY_ISSUES]
                )
                if len(gate_result.issues) > c.Infra.MAX_DISPLAY_ISSUES:
                    lines.append(
                        f"... and {len(gate_result.issues) - c.Infra.MAX_DISPLAY_ISSUES} more errors",
                    )
                lines.extend(["```", ""])
        return lines

    @staticmethod
    def generate_markdown(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
        timestamp: str,
    ) -> str:
        """Generate a markdown summary report."""
        lines: MutableSequence[str] = [
            "# FLEXT Check Report",
            "",
            f"**Generated**: {timestamp}  ",
            f"**Projects**: {len(results)}  ",
            f"**Gates**: {', '.join(gates)}  ",
            "",
            "## Summary",
            "",
        ]
        table_lines, failed_count = (
            FlextInfraUtilitiesReporting._markdown_summary_table(
                results,
                gates,
            )
        )
        lines.extend(table_lines)
        lines.extend([
            "",
            f"**Total errors**: {sum(p.total_errors for p in results)}  ",
            f"**Failed projects**: {failed_count}/{len(results)}  ",
            "",
        ])
        lines.extend(
            FlextInfraUtilitiesReporting._markdown_project_details(results, gates),
        )
        return "\n".join(lines)


__all__ = ["FlextInfraUtilitiesReporting"]
