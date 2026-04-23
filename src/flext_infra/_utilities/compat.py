"""Compatibility utility surface for infrastructure callers.

Provides stable ``u.Infra.*`` methods that were historically consumed
by services/commands and now delegate to canonical helper implementations.
"""

from __future__ import annotations

import difflib
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path

from flext_cli import u

from flext_infra import (
    c,
    m,
    p,
    r,
    t,
)


class FlextInfraUtilitiesCompatibility:
    """Shared report, diff, and codegen helpers composed into ``u.Infra``."""

    @staticmethod
    def run_ruff_fix(path: Path, *, quiet: bool = False) -> bool:
        """Run Ruff fix + format for one file path; return success status."""
        cwd = path.parent if path.suffix else path
        check_result = u.Cli.capture(
            [c.Infra.RUFF, "check", "--fix", str(path)],
            cwd=cwd,
        )
        if check_result.failure:
            if not quiet:
                u.Cli.error(check_result.error or f"ruff check --fix failed: {path}")
            return False
        format_result = u.Cli.capture(
            [c.Infra.RUFF, "format", str(path)],
            cwd=cwd,
        )
        if format_result.failure and not quiet:
            u.Cli.error(format_result.error or f"ruff format failed: {path}")
        return format_result.success

    @staticmethod
    def generate_module_skeleton(
        *, class_name: str, base_class: str, docstring: str
    ) -> str:
        """Generate one minimal module skeleton used by codegen scaffolding."""
        return (
            f'"""{docstring}"""\n\n'
            "from __future__ import annotations\n\n"
            f"class {class_name}({base_class}):\n"
            f'    """{docstring}"""\n'
            "\n"
            "\n"
            '__all__: list[str] = ["'
            f"{class_name}"
            '"]\n'
        )

    @staticmethod
    def generate_markdown(
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
    def generate_sarif(
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

    @staticmethod
    def failure_summary(
        verb: str,
        failures: Sequence[t.Infra.Triple[str, int, Path]],
    ) -> None:
        """Print compact failure summary for workspace orchestration."""
        if not failures:
            return
        u.Cli.error(f"{verb} failures: {len(failures)} project(s)")
        for project, error_count, log_path in failures:
            u.Cli.error(f"- {project}: {error_count} errors ({log_path})")

    @staticmethod
    def refactor_debug(message: str) -> None:
        """Emit one compact refactor debug line."""
        u.Cli.info(message)

    @staticmethod
    def refactor_header(message: str) -> None:
        """Emit one refactor section header."""
        u.Cli.header(message)

    @staticmethod
    def print_violation_summary(analysis: m.Infra.ViolationAnalysisReport) -> None:
        """Print high-level violation analysis summary."""
        u.Cli.header("Violation Analysis")
        u.Cli.info(f"Files scanned: {analysis.files_scanned}")
        for key, value in sorted(analysis.totals.items()):
            u.Cli.info(f"- {key}: {value}")

    @staticmethod
    def print_diff(original: str, updated: str, file_path: Path) -> None:
        """Print unified diff for one updated file."""
        diff = difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        for line in diff:
            u.Cli.info(line)

    @staticmethod
    def print_summary(results: Sequence[m.Infra.Result], *, dry_run: bool) -> None:
        """Print refactor execution summary."""
        total = len(results)
        success = sum(1 for item in results if item.success)
        failed = total - success
        modified = sum(1 for item in results if item.modified)
        mode = "[DRY-RUN] " if dry_run else ""
        u.Cli.info(f"{mode}Processed: {total} file(s)")
        u.Cli.info(f"Success: {success}  Failed: {failed}  Modified: {modified}")

    @staticmethod
    def write_impact_map(
        results: Sequence[m.Infra.Result],
        output_path: Path,
    ) -> p.Result[bool]:
        """Write refactor impact map JSON to disk."""
        payload = {
            "files": [
                {
                    "path": str(item.file_path),
                    "success": item.success,
                    "modified": item.modified,
                    "error": item.error,
                    "changes": list(item.changes),
                }
                for item in results
            ]
        }
        normalized_payload: t.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_python(
            payload,
        )
        write_result = u.Cli.json_write(output_path, normalized_payload)
        if write_result.failure:
            return r[bool].fail(write_result.error or "impact map write failed")
        return r[bool].ok(True)

    @staticmethod
    def render_census_report(report: m.BaseModel) -> str:
        """Render a human-readable census report for any supported census model."""
        data = report.model_dump(mode="json")
        totals = {
            "classes": data.get("total_classes", 0),
            "methods": data.get("total_methods", 0),
            "usages": data.get("total_usages", 0),
            "unused": data.get("total_unused", 0),
            "files_scanned": data.get("files_scanned", 0),
            "parse_errors": data.get("parse_errors", 0),
        }
        lines = [
            "Utilities Census Report",
            f"Classes: {totals['classes']}",
            f"Methods: {totals['methods']}",
            f"Usages: {totals['usages']}",
            f"Unused: {totals['unused']}",
            f"Files scanned: {totals['files_scanned']}",
            f"Parse errors: {totals['parse_errors']}",
            "",
        ]
        projects = data.get("projects", [])
        if isinstance(projects, list):
            for project in projects:
                if isinstance(project, Mapping):
                    project_name = str(
                        project.get("project", project.get("project_name", ""))
                    )
                    total = int(project.get("total", 0))
                    if project_name:
                        lines.append(f"- {project_name}: {total}")
        return "\n".join(lines)

    @staticmethod
    def render_namespace_enforcement_report(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render workspace namespace-enforcement report as plain text."""
        lines = [
            "Namespace Enforcement Report",
            f"Workspace: {report.workspace}",
            f"Projects: {len(report.projects)}",
            f"Violations: {'YES' if report.has_violations else 'NO'}",
            f"Missing facades: {report.total_facades_missing}",
            f"Loose objects: {report.total_loose_objects}",
            f"Import violations: {report.total_import_violations}",
            f"Namespace source violations: {report.total_namespace_source_violations}",
            f"Internal import violations: {report.total_internal_import_violations}",
            f"Manual protocol violations: {report.total_manual_protocol_violations}",
            f"Cyclic imports: {report.total_cyclic_imports}",
            f"Runtime alias violations: {report.total_runtime_alias_violations}",
            f"Future violations: {report.total_future_violations}",
            f"Manual typing violations: {report.total_manual_typing_violations}",
            f"Compatibility alias violations: {report.total_compatibility_alias_violations}",
            f"Class placement violations: {report.total_class_placement_violations}",
            f"MRO completeness violations: {report.total_mro_completeness_violations}",
            f"Parse failures: {report.total_parse_failures}",
            f"Files scanned: {report.total_files_scanned}",
        ]
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraUtilitiesCompatibility"]
