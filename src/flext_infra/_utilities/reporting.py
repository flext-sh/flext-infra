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

import sys
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesOutputFailureSummary,
    FlextInfraUtilitiesOutputReporting,
    FlextInfraUtilitiesTerminal,
    c,
    m,
    p,
    t,
)


class FlextInfraUtilitiesReporting(
    FlextInfraUtilitiesOutputReporting,
    FlextInfraUtilitiesOutputFailureSummary,
):
    """Static reporting utilities for standardized report path management.

    All methods are ``@staticmethod`` — no instantiation required.
    Exposed via ``u.Infra.get_report_dir()`` etc. through MRO.
    """

    _stream: ClassVar[p.Infra.OutputStream] = sys.stderr
    _use_color: ClassVar[bool] = False
    _use_unicode: ClassVar[bool] = False

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

    @classmethod
    def setup(
        cls,
        *,
        color: bool | None = None,
        unicode: bool | None = None,
        stream: p.Infra.OutputStream | None = None,
    ) -> None:
        """Initialize reporting output capabilities."""
        cls._use_color = (
            FlextInfraUtilitiesTerminal.terminal_should_use_color()
            if color is None
            else color
        )
        cls._use_unicode = (
            FlextInfraUtilitiesTerminal.terminal_should_use_unicode()
            if unicode is None
            else unicode
        )
        if stream is not None:
            cls._stream = stream

    @classmethod
    def _fmt(cls, level: str, color: str, message: str) -> None:
        reset = c.Infra.RESET if cls._use_color else ""
        prefix = color if cls._use_color else ""
        cls._stream.write(f"{prefix}{level}{reset}: {message}\n")
        cls._stream.flush()

    @classmethod
    def info(cls, msg: str) -> None:
        cls._fmt("INFO", c.Infra.BLUE, msg)

    @classmethod
    def error(cls, msg: str, detail: str | None = None) -> None:
        cls._fmt("ERROR", c.Infra.RED, msg)
        if detail:
            cls._stream.write(f"  {detail}\n")
            cls._stream.flush()

    @classmethod
    def warning(cls, msg: str) -> None:
        cls._fmt("WARN", c.Infra.YELLOW, msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls._fmt("DEBUG", c.Infra.GREEN, msg)

    @classmethod
    def header(cls, title: str) -> None:
        sep = "═" if cls._use_unicode else "="
        line = sep * 60
        start = c.Infra.BOLD if cls._use_color else ""
        reset = c.Infra.RESET if cls._use_color else ""
        cls._stream.write(f"\n{start}{line}\n  {title}\n{line}{reset}\n")
        cls._stream.flush()

    @classmethod
    def progress(cls, idx: int, total: int, proj: str, verb: str) -> None:
        width = len(str(total))
        cls._stream.write(f"[{idx:0{width}d}/{total:0{width}d}] {proj} {verb} ...\n")
        cls._stream.flush()

    @classmethod
    def status(cls, verb: str, proj: str, *, result: bool, elapsed: float) -> None:
        symbol = (
            (c.Infra.OK if result and cls._use_unicode else "[OK]")
            if result
            else (c.Infra.FAIL if cls._use_unicode else "[FAIL]")
        )
        color = (c.Infra.GREEN if result else c.Infra.RED) if cls._use_color else ""
        reset = c.Infra.RESET if cls._use_color else ""
        cls._stream.write(
            f"  {color}{symbol}{reset} {verb:<8} {proj:<24} {elapsed:.2f}s\n",
        )
        cls._stream.flush()

    @classmethod
    def write(cls, text: str) -> None:
        """Write raw text to the configured output stream."""
        cls._stream.write(text)
        cls._stream.flush()

    @classmethod
    def summary(cls, stats: m.Infra.SummaryStats) -> None:
        hdr = (
            f"── {stats.verb} summary ──"
            if cls._use_unicode
            else f"-- {stats.verb} summary --"
        )
        cls._stream.write(
            f"\n{hdr}\nTotal: {stats.total}  Success: {stats.success}  "
            f"Failed: {stats.failed}  Skipped: {stats.skipped}  "
            f"({stats.elapsed:.2f}s)\n",
        )
        cls._stream.flush()

    @classmethod
    def gate_result(
        cls,
        gate: str,
        count: int,
        *,
        passed: bool,
        elapsed: float,
    ) -> None:
        symbol = (
            (c.Infra.OK if passed and cls._use_unicode else "[OK]")
            if passed
            else (c.Infra.FAIL if cls._use_unicode else "[FAIL]")
        )
        cls._stream.write(
            f"    {symbol} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n",
        )
        cls._stream.flush()

    @classmethod
    def project_failure(cls, info: m.Infra.ProjectFailureInfo) -> None:
        """Render one failed project summary with a truncated error excerpt."""
        color = c.Infra.RED if cls._use_color else ""
        reset = c.Infra.RESET if cls._use_color else ""
        fail_sym = c.Infra.FAIL if cls._use_unicode else "[FAIL]"
        count_label = f"  [{info.error_count} errors]" if info.error_count > 0 else ""
        cls._stream.write(
            f"  {color}{fail_sym}{reset} {info.project} completed in {int(info.elapsed)}s"
            f"{count_label}  ({info.log_path})\n",
        )
        for line in info.errors[: info.max_show]:
            cls._stream.write(f"      {line}\n")
        remaining = info.error_count - info.max_show
        if remaining > 0:
            cls._stream.write(f"      ... and {remaining} more (see log)\n")
        cls._stream.flush()

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


FlextInfraUtilitiesReporting.setup()

__all__ = ["FlextInfraUtilitiesReporting"]
