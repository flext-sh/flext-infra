"""Workspace check report rendering: markdown + SARIF + summary — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import operator
from collections.abc import MutableMapping, Sequence
from pathlib import Path

from flext_infra import FlextInfraVersion, c, m, p, r, u


class FlextInfraCheckWorkspaceCheckReports:
    """Render markdown/SARIF reports and print the run summary.

    Composed into FlextInfraWorkspaceChecker via inheritance; pure rendering
    over gate results (no checker state).
    """

    @staticmethod
    def _project_summary(
        summary: m.Infra.CheckReportSummary,
        target: m.Infra.CheckProjectTarget,
    ) -> m.Infra.CheckReportSummary:
        """Bind one exact target to its ordered result before judging completeness.

        Returns:
            The target's requested inventory with only its reached executions.

        """
        position = summary.targets.index(target)
        return summary.model_copy(
            update={
                "targets": (target,),
                "results": summary.results[position : position + 1],
            },
        )

    @classmethod
    def _generate_markdown(
        cls,
        summary: m.Infra.CheckReportSummary,
        timestamp: str,
    ) -> str:
        """Render reached results and missing executions from one typed inventory.

        Returns:
            The resulting ``str``.

        """
        lines: list[str] = [
            "# Workspace Check Report",
            "",
            f"Generated: {timestamp}",
            f"Check phase: {summary.phase}",
            f"Execution: {'COMPLETE' if summary.complete else 'INCOMPLETE'}",
            f"Projects reached: {len(summary.results)}/{len(summary.targets)}",
            "",
            "## Summary",
            "",
            "| Project | Status | Findings |",
            "|---|---:|---:|",
        ]
        for target in summary.targets:
            project_summary = cls._project_summary(summary, target)
            project = (
                project_summary.results[0]
                if len(project_summary.results) == 1
                else None
            )
            status = (
                "INCOMPLETE"
                if not project_summary.complete
                else "PASS"
                if project is not None and project.passed
                else "FAIL"
            )
            findings = (
                str(project.total_findings) if project is not None else "unrecorded"
            )
            lines.append(f"| {target.name} | {status} | {findings} |")
        lines.extend(["", "## Details", ""])
        for target in summary.targets:
            project_summary = cls._project_summary(summary, target)
            project = (
                project_summary.results[0]
                if len(project_summary.results) == 1
                else None
            )
            lines.extend([f"### {target.name}", f"Root: `{target.path}`"])
            if not target.applicable_gates:
                lines.append("- INCOMPLETE: no applicable gate inventory was recorded")
            for gate in target.applicable_gates:
                execution = project.gates.get(gate) if project is not None else None
                if execution is None:
                    lines.append(
                        f"- {gate}: NOT COMPLETED (no completed execution receipt)",
                    )
                    continue
                gate_status = (
                    "INCOMPLETE"
                    if not execution.complete
                    else "PASS"
                    if execution.result.passed
                    else "FAIL"
                )
                lines.append(
                    f"- {gate}: {gate_status} ({len(execution.issues)} issues)",
                )
                lines.extend(f"  - {issue.formatted}" for issue in execution.issues)
                if execution.raw_receipt is not None:
                    lines.extend([
                        (
                            f"  - Native output receipt: "
                            f"[{execution.raw_receipt.name}]"
                            f"({execution.raw_receipt.resolve().as_uri()})"
                        ),
                    ])
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _publish_invocation_summary(
        summary: m.Infra.CheckReportSummary,
        before: m.Cli.AtomicFileState,
    ) -> m.Cli.AtomicFileState:
        """Advance this invocation's exact report target from its read state.

        Returns:
            The state of the report that was just written.

        """
        u.Cli.atomic_write_text_file_guarded(
            before, summary.model_dump_json(round_trip=True) + "\n"
        ).unwrap()
        return u.Cli.atomic_read_binary_file_state(before.path, required=True).unwrap()

    @classmethod
    def _generate_sarif(
        cls,
        results: Sequence[m.Infra.ProjectResult],
        gates: Sequence[str],
        summary: m.Infra.CheckReportSummary,
    ) -> m.Infra.SarifReport:
        """Build the SARIF 2.1.0 report model from workspace gate results.

        Returns:
            The resulting ``m.Infra.SarifReport``.

        """
        rules_by_id: MutableMapping[str, m.Infra.SarifRule] = {}
        sarif_results: list[m.Infra.SarifResult] = []
        for project in results:
            for gate in gates:
                execution = project.gates.get(gate)
                if execution is None:
                    continue
                tool_name, tool_url = c.Infra.SARIF_TOOL_INFO.get(
                    gate, (gate, f"internal://project-check/{gate}")
                )
                for issue in execution.issues:
                    rule_id = issue.code or gate
                    rules_by_id.setdefault(
                        rule_id,
                        m.Infra.SarifRule.model_validate({
                            "id": rule_id,
                            "short_description": f"{tool_name} ({gate}) issue",
                            "help_uri": tool_url,
                        }),
                    )
                    sarif_results.append(cls._sarif_issue(issue, rule_id))
        return m.Infra.SarifReport.model_validate({
            "properties": summary,
            "runs": (
                m.Infra.SarifRun.model_validate({
                    "tool_name": "flext-infra-check",
                    "information_uri": FlextInfraVersion.__url__,
                    "rules": tuple(rules_by_id.values()),
                    "results": tuple(sarif_results),
                }),
            ),
        })

    @staticmethod
    def _sarif_issue(issue: m.Infra.Issue, rule_id: str) -> m.Infra.SarifResult:
        """Render one occurrence while retaining its native severity.

        Returns:
            The resulting ``m.Infra.SarifResult``.

        """
        severity = issue.severity.lower()
        level = (
            c.Infra.GateSeverity.WARNING.value
            if severity in {c.Infra.GateSeverity.WARNING, "warn"}
            else c.Infra.GateSeverity.NOTE.value
            if severity in {c.Infra.GateSeverity.NOTE, "info", "information", "hint"}
            else c.Infra.GateSeverity.ERROR.value
        )
        return m.Infra.SarifResult.model_validate({
            "rule_id": rule_id,
            "level": level,
            "message": issue.message,
            "locations": issue.locations
            or (
                m.Infra.SarifLocation.model_validate({
                    "uri": issue.file,
                    "start_line": issue.line,
                    "start_column": issue.column,
                }),
            ),
            "related_locations": issue.related_locations,
        })

    @classmethod
    def _write_reports(
        cls,
        report_base: Path,
        summary: m.Infra.CheckReportSummary,
    ) -> p.Result[bool]:
        """Publish this invocation's Markdown and SARIF without console repetition.

        Returns:
            Success after both current aggregate reports have been published.

        """
        timestamp = u.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        md_path = report_base / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME
        md_write_result = u.Cli.atomic_write_text_file(
            md_path,
            cls._generate_markdown(summary, timestamp),
        )
        if md_write_result.failure:
            return r[bool].from_failure(md_write_result)
        sarif_path = report_base / c.Infra.CHECK_REPORT_SARIF_FILENAME
        sarif_report = cls._generate_sarif(
            summary.results, summary.requested_gates, summary
        )
        sarif_write_result = u.Cli.atomic_write_text_file(
            sarif_path,
            sarif_report.model_dump_json(indent=2, round_trip=True),
        )
        if sarif_write_result.failure:
            return r[bool].from_failure(sarif_write_result)
        return r[bool].ok(value=True)

    @classmethod
    def _print_summary(
        cls,
        report_base: Path,
        outcome: p.Infra.WorkspaceLoopOutcome,
        summary: m.Infra.CheckReportSummary,
    ) -> None:
        """Print the terminal summary once, without republishing unchanged reports."""
        results = outcome.results
        total_findings = sum(project.total_findings for project in results)
        success = sum(
            project_summary.complete
            and all(project.passed for project in project_summary.results)
            for target in summary.targets
            for project_summary in (cls._project_summary(summary, target),)
        )
        u.Cli.summary(
            m.Infra.SummaryStats(
                verb=c.Infra.VERB_CHECK,
                total=len(results),
                success=success,
                failed=outcome.failed,
                skipped=0,
                elapsed=outcome.total_elapsed,
            ),
        )
        if not summary.complete:
            u.Cli.info(
                "Execution INCOMPLETE: "
                f"{len(results)}/{len(summary.targets)} projects reached; "
                "see the requested gate inventory in the reports",
            )
        u.Cli.info(f"Reports: {report_base / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME}")
        u.Cli.info(f"         {report_base / c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        if total_findings > 0:
            u.Cli.info("Findings by project (see reports for detail):")
            for project in sorted(
                results,
                key=operator.attrgetter("total_findings"),
                reverse=True,
            ):
                if project.total_findings == 0:
                    continue
                breakdown = ", ".join(
                    f"{gate}={project.gates[gate].finding_count}"
                    for gate in summary.requested_gates
                    if gate in project.gates and project.gates[gate].finding_count
                )
                u.Cli.info(
                    f"{project.project:30s} {project.total_findings:6d}  ({breakdown})",
                )


__all__: list[str] = ["FlextInfraCheckWorkspaceCheckReports"]
