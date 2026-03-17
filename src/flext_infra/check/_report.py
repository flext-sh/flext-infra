"""Report generation service for check results."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import JsonValue

from flext_infra import c, m
from flext_infra.check._constants import FlextInfraCheckConstants


class FlextInfraCheckReporter:
    """Generates SARIF and Markdown reports from gate results."""

    @staticmethod
    def sarif(
        results: Sequence[m.Infra.Check.ProjectResult],
        gates: Sequence[str],
    ) -> JsonValue:
        """Generate a SARIF 2.1.0 payload from gate results."""
        sarif_runs: list[m.Infra.Check.Sarif.Run] = []
        for gate in gates:
            tool_name, tool_url = FlextInfraCheckConstants.SARIF_TOOL_INFO.get(
                gate,
                (gate, ""),
            )
            sarif_results: list[m.Infra.Check.Sarif.Result] = []
            rules_seen: set[str] = set()
            rules: list[m.Infra.Check.Sarif.Rule] = []
            for project in results:
                gate_result = project.gates.get(gate)
                if not gate_result:
                    continue
                for issue in gate_result.issues:
                    rule_id = issue.code or c.Infra.Defaults.UNKNOWN
                    if rule_id not in rules_seen:
                        rules_seen.add(rule_id)
                        rules.append(
                            m.Infra.Check.Sarif.Rule(
                                id=rule_id,
                                short_description=rule_id,
                            ),
                        )
                    sarif_results.append(
                        m.Infra.Check.Sarif.Result(
                            rule_id=rule_id,
                            level=c.Infra.Toml.ERROR
                            if issue.severity == c.Infra.Toml.ERROR
                            else c.Infra.Severity.WARNING,
                            message=issue.message,
                            locations=[
                                m.Infra.Check.Sarif.Location(
                                    uri=issue.file,
                                    start_line=max(issue.line, 1),
                                    start_column=max(issue.column, 1),
                                ),
                            ],
                        ),
                    )
            sarif_runs.append(
                m.Infra.Check.Sarif.Run(
                    tool_name=tool_name,
                    information_uri=tool_url,
                    rules=rules,
                    results=sarif_results,
                ),
            )
        sarif_report = m.Infra.Check.Sarif.Report(runs=sarif_runs)
        sarif_dict: dict[str, JsonValue] = sarif_report.model_dump(by_alias=True)
        return sarif_dict

    @staticmethod
    def markdown(
        results: Sequence[m.Infra.Check.ProjectResult],
        gates: Sequence[str],
        timestamp: str,
    ) -> str:
        """Generate a markdown summary report."""
        lines: list[str] = [
            "# FLEXT Check Report",
            "",
            f"**Generated**: {timestamp}  ",
            f"**Projects**: {len(results)}  ",
            f"**Gates**: {', '.join(gates)}  ",
            "",
            "## Summary",
            "",
        ]
        header = "| Project |"
        sep = "|---------|"
        for gate in gates:
            header += f" {gate.capitalize()} |"
            sep += "------|"
        header += " Total | Status |"
        sep += "-------|--------|"
        lines.extend([header, sep])
        failed_count = 0
        for project in results:
            row = f"| {project.project} |"
            for gate in gates:
                gate_result = project.gates.get(gate)
                row += f" {(len(gate_result.issues) if gate_result else 0)} |"
            status = (
                c.Infra.Status.PASS if project.passed else f"**{c.Infra.Status.FAIL}**"
            )
            if not project.passed:
                failed_count += 1
            row += f" {project.total_errors} | {status} |"
            lines.append(row)
        lines.extend([
            "",
            f"**Total errors**: {sum(p.total_errors for p in results)}  ",
            f"**Failed projects**: {failed_count}/{len(results)}  ",
            "",
        ])
        for project in sorted(
            results,
            key=lambda item: item.total_errors,
            reverse=True,
        ):
            if project.total_errors == 0:
                continue
            lines.extend([f"## {project.project}", ""])
            for gate in gates:
                gate_result = project.gates.get(gate)
                if not gate_result or len(gate_result.issues) == 0:
                    continue
                lines.extend([
                    f"### {gate} ({len(gate_result.issues)} errors)",
                    "",
                    "```",
                ])
                lines.extend(
                    issue.formatted
                    for issue in gate_result.issues[: c.Infra.Check.MAX_DISPLAY_ISSUES]
                )
                if len(gate_result.issues) > c.Infra.Check.MAX_DISPLAY_ISSUES:
                    lines.append(
                        f"... and {len(gate_result.issues) - c.Infra.Check.MAX_DISPLAY_ISSUES} more errors",
                    )
                lines.extend(["```", ""])
        return "\n".join(lines)


__all__ = ["FlextInfraCheckReporter"]
