"""FLEXT infrastructure workspace checker."""

from __future__ import annotations

import shlex
from collections.abc import (
    MutableSequence,
    Sequence,
)
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraGateRegistry,
    FlextInfraWorkspaceCheckGatesMixin,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraWorkspaceChecker(s[bool], FlextInfraWorkspaceCheckGatesMixin):
    """Run workspace quality gates and generate reports."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        *,
        workspace: Path | None = None,
    ) -> None:
        """Initialize workspace checker services and paths."""
        self._workspace_root = u.Infra.resolve_workspace_root_or_cwd(
            workspace_root or workspace,
        )
        self._registry = FlextInfraGateRegistry.default()
        report_dir = u.Cli.resolve_report_dir(
            self._workspace_root,
            c.Infra.PROJECT,
            c.Infra.VERB_CHECK,
        )
        dir_result = u.Cli.ensure_dir(report_dir)
        if dir_result.failure:
            self._default_reports_dir = (
                self._workspace_root / c.Infra.REPORTS_DIR_NAME / c.Infra.VERB_CHECK
            )
        else:
            self._default_reports_dir = report_dir

    @staticmethod
    def parse_tool_args(raw: str | None) -> t.StrSequence:
        """Parse extra gate arguments passed as a shell-style string."""
        if raw is None:
            return list[str]()
        return [item for item in shlex.split(raw) if item]

    @staticmethod
    def resolve_gates(gates: t.StrSequence) -> p.Result[list[str]]:
        """Resolve and validate requested gate names."""
        resolved: MutableSequence[str] = []
        for gate in gates:
            name = gate.strip()
            if not name:
                continue
            mapped = c.Infra.PYREFLY if name == c.Infra.TYPE_ALIAS else name
            if mapped not in c.Infra.ALLOWED_GATES:
                return r[list[str]].fail(f"ERROR: unknown gate '{gate}'")
            if mapped not in resolved:
                resolved.append(mapped)
        return r[list[str]].ok(list(resolved))

    @staticmethod
    def _generate_markdown(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
        timestamp: str,
    ) -> str:
        """Render markdown check report from project gate results."""
        lines: list[str] = [
            "# Workspace Check Report",
            "",
            f"Generated: {timestamp}",
            f"Projects: {len(results)}",
            "",
            "## Summary",
            "",
            "| Project | Status | Errors |",
            "|---|---:|---:|",
        ]
        for project in results:
            status = "PASS" if project.passed else "FAIL"
            lines.append(f"| {project.project} | {status} | {project.total_errors} |")
        lines.extend(["", "## Details", ""])
        for project in results:
            lines.append(f"### {project.project}")
            for gate in gates:
                execution = project.gates.get(gate)
                if execution is None:
                    continue
                gate_status = "PASS" if execution.result.passed else "FAIL"
                lines.append(
                    f"- {gate}: {gate_status} ({len(execution.issues)} issues)",
                )
                lines.extend(f"  - {issue.formatted}" for issue in execution.issues)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _generate_sarif(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
    ) -> t.JsonMapping:
        """Render SARIF 2.1.0 payload from workspace gate results."""
        rules_by_id: dict[str, m.Infra.SarifRule] = {}
        sarif_results: list[m.Infra.SarifResult] = []
        for project in results:
            for gate in gates:
                execution = project.gates.get(gate)
                if execution is None:
                    continue
                for issue in execution.issues:
                    rule_id = issue.code or gate
                    if rule_id not in rules_by_id:
                        rules_by_id[rule_id] = m.Infra.SarifRule(
                            id=rule_id,
                            short_description=f"{gate} issue",
                        )
                    sarif_results.append(
                        m.Infra.SarifResult(
                            rule_id=rule_id,
                            level=(
                                "warning"
                                if issue.severity.lower()
                                == c.Infra.SeverityLevel.WARNING
                                else "error"
                            ),
                            message=issue.message,
                            locations=[
                                m.Infra.SarifLocation(
                                    uri=issue.file,
                                    start_line=issue.line,
                                    start_column=issue.column,
                                )
                            ],
                        )
                    )
        report = m.Infra.SarifReport(
            runs=(
                m.Infra.SarifRun(
                    tool_name="flext-infra-check",
                    information_uri="https://github.com/flext-sh/flext-infra",
                    rules=tuple(rules_by_id.values()),
                    results=tuple(sarif_results),
                ),
            ),
        )
        return report.model_dump(mode="json")

    @override
    def execute(self) -> p.Result[bool]:
        return r[bool].fail("Use execute_command() directly")

    @classmethod
    @override
    def execute_command(
        cls,
        params: m.Infra.RunCommand,
    ) -> p.Result[bool]:
        """Execute quality gates from the canonical check command payload."""
        checker = cls(workspace_root=params.workspace_path)
        project_names = params.project_names or []
        if not project_names:
            return r[bool].fail("no projects specified")
        gates = params.gates
        gate_ctx = m.Infra.GateContext(
            workspace=params.workspace_path,
            reports_dir=params.reports_dir_path,
            apply_fixes=params.fix,
            check_only=params.check_only,
            ruff_args=tuple(cls.parse_tool_args(params.ruff_args)),
            pyright_args=tuple(cls.parse_tool_args(params.pyright_args)),
        )
        run_result = checker.run_projects(
            projects=project_names,
            gates=gates,
            reports_dir=params.reports_dir_path,
            fail_fast=params.fail_fast,
            ctx=gate_ctx,
        )
        if run_result.failure:
            return r[bool].fail(run_result.error or "check failed")
        failed_projects = [
            project for project in run_result.value if not project.passed
        ]
        if failed_projects:
            failed_names = ", ".join(project.project for project in failed_projects)
            return r[bool].fail(f"quality gates failed for: {failed_names}")
        return r[bool].ok(True)

    def format(self, project_dir: Path) -> p.Result[m.Infra.GateResult]:
        """Run format checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.FORMAT, project_dir).result,
        )

    def lint(self, project_dir: Path) -> p.Result[m.Infra.GateResult]:
        """Run lint checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.LINT, project_dir).result,
        )

    def run_project(
        self,
        project: str,
        gates: t.StrSequence,
    ) -> p.Result[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for one project."""
        return self.run_projects([project], list(gates))

    @staticmethod
    def _write_reports_and_summary(
        resolved_gates: t.StrSequence,
        report_base: Path,
        outcome: p.Infra.WorkspaceLoopOutcome,
    ) -> p.Result[Sequence[m.Infra.ProjectResult]]:
        """Write markdown/SARIF reports and print summary to output."""
        results = outcome.results
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        md_path = report_base / "check-report.md"
        md_write_result = u.Cli.atomic_write_text_file(
            md_path,
            FlextInfraWorkspaceChecker._generate_markdown(
                results,
                resolved_gates,
                timestamp,
            ),
        )
        if md_write_result.failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                md_write_result.error or "failed to write markdown report",
            )
        sarif_path = report_base / "check-report.sarif"
        sarif_payload = FlextInfraWorkspaceChecker._generate_sarif(
            results,
            resolved_gates,
        )
        json_write_result = u.Cli.json_write(sarif_path, sarif_payload)
        if json_write_result.failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                json_write_result.error or "failed to write sarif report",
            )
        total_errors = sum(project.total_errors for project in results)
        success = len(results) - outcome.failed
        u.Cli.summary(
            m.Infra.SummaryStats(
                verb=c.Infra.VERB_CHECK,
                total=len(results),
                success=success,
                failed=outcome.failed,
                skipped=outcome.skipped,
                elapsed=outcome.total_elapsed,
            )
        )
        u.Cli.info(f"Reports: {md_path}")
        u.Cli.info(f"         {sarif_path}")
        if total_errors > 0:
            u.Cli.info("Errors by project:")
            for project in sorted(
                results,
                key=lambda item: item.total_errors,
                reverse=True,
            ):
                if project.total_errors == 0:
                    continue
                breakdown = ", ".join(
                    f"{gate}={len(project.gates[gate].issues)}"
                    for gate in resolved_gates
                    if gate in project.gates and project.gates[gate].issues
                )
                u.Cli.error(
                    f"{project.project:30s} {project.total_errors:6d}  ({breakdown})",
                )
        return r[Sequence[m.Infra.ProjectResult]].ok(results)

    def run_projects(
        self,
        projects: t.StrSequence,
        gates: t.StrSequence,
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        ctx: m.Infra.GateContext | None = None,
    ) -> p.Result[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for multiple projects.

        Pass ``ctx`` to supply a pre-built GateContext.
        """
        resolved_gates_result = self.resolve_gates(gates)
        if resolved_gates_result.failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                resolved_gates_result.error or "invalid gates",
            )
        resolved_gates = resolved_gates_result.value
        report_base = reports_dir or self._default_reports_dir
        dir_ensure = u.Cli.ensure_dir(report_base)
        if dir_ensure.failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                dir_ensure.error or "failed to create report directory",
            )
        effective_ctx = ctx or m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=report_base,
        )
        outcome = self._run_project_loop(
            projects,
            resolved_gates,
            effective_ctx,
            fail_fast=fail_fast,
        )
        return self._write_reports_and_summary(
            resolved_gates,
            report_base,
            outcome,
        )


__all__: list[str] = ["FlextInfraWorkspaceChecker"]
