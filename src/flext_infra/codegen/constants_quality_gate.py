"""Workspace-wide quality gate for constants refactor outcomes."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import FlextInfraCodegenCensus, FlextInfraCodegenLazyInit, c, m, t, u
from flext_infra.base import s


class FlextInfraCodegenConstantsQualityGate(s[bool]):
    """Run final constants migration checks with before/after comparison."""

    before_report: Annotated[
        Path | None,
        Field(default=None, description="Pre-refactor report path"),
    ] = None
    baseline_file: Annotated[
        Path | None,
        Field(default=None, description="Baseline payload path"),
    ] = None

    @override
    def execute(self) -> r[bool]:
        """Execute the quality gate and return its CLI success/failure status."""
        if self.before_report and self.baseline_file:
            return r[bool].fail(
                "--before-report and --baseline-file are mutually exclusive",
            )
        report = self.build_report()
        verdict = u.Infra.pick_str(report, "verdict", "FAIL")
        if self.is_success_verdict(verdict):
            return r[bool].ok(True)
        return r[bool].fail(f"quality gate verdict: {verdict}")

    def build_report(self) -> t.Infra.InfraMapping:
        """Execute quality gate and return structured report payload."""
        before_payload, before_source, before_load_error = u.Infra.load_before_payload(
            self.workspace_root,
            self.before_report,
            self.baseline_file,
        )
        FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": self.workspace_root},
        ).generate_inits()
        census_reports = FlextInfraCodegenCensus.model_validate(
            {"workspace_root": self.workspace_root},
        ).run()
        duplicate_groups = u.Infra.detect_duplicate_constant_groups(
            self.workspace_root,
            census_reports,
        )
        modified_files = u.Infra.modified_python_files(
            self.workspace_root,
        )
        pyrefly_check = u.Infra.run_pyrefly_check(
            self.workspace_root,
            modified_files,
        )
        ruff_check = u.Infra.run_ruff_check(
            self.workspace_root,
            modified_files,
        )
        import_scan = u.Infra.scan_import_nodes(
            self.workspace_root,
            modified_files,
        )
        before_metrics = u.Infra.before_metrics(before_payload)
        after_metrics = u.Infra.after_metrics(
            census_reports=census_reports,
            duplicate_groups=len(duplicate_groups),
            import_scan=import_scan,
            modified_files=modified_files,
        )
        improvement = u.Infra.improvement(
            before_metrics,
            after_metrics,
        )
        checks = u.Infra.build_checks(
            after_metrics=after_metrics,
            improvement=improvement,
            pyrefly_check=pyrefly_check,
            ruff_check=ruff_check,
            before_available=before_payload is not None,
            before_load_error=before_load_error,
        )
        verdict = u.Infra.compute_verdict(checks, improvement)
        checks_infra: Sequence[t.Infra.InfraValue] = tuple(checks)
        projects_infra: Sequence[t.Infra.InfraValue] = tuple(
            u.Infra.project_findings(census_reports),
        )
        report: MutableMapping[str, t.Infra.InfraValue] = {
            "workspace": str(self.workspace_root),
            "generated_at": datetime.now(UTC).isoformat(),
            "verdict": verdict,
            "checks": checks_infra,
            "baseline": {
                "source": before_source,
                "load_error": before_load_error,
                "provided": before_payload is not None,
            },
            "before": before_metrics,
            "after": after_metrics,
            "improvement": improvement,
            "duplicate_constant_groups": tuple(
                group.model_dump() for group in duplicate_groups
            ),
            "projects": projects_infra,
        }
        report["artifacts"] = u.Infra.write_artifacts(
            workspace_root=self.workspace_root,
            report=report,
            render_text=self.render_text(report),
        )
        return report

    @classmethod
    def render_text(cls, report: Mapping[str, t.Infra.InfraValue]) -> str:
        """Render compact human-readable summary."""
        checks = u.Infra.deep_list(report, "checks")
        before = u.Infra.deep_mapping(report, "before")
        after = u.Infra.deep_mapping(report, "after")
        improvement = u.Infra.deep_mapping(report, "improvement")
        duplicate_groups = u.Infra.deep_list(report, "duplicate_constant_groups")
        lines: MutableSequence[str] = [
            f"Workspace: {report.get('workspace', '')}",
            f"Verdict: {report.get('verdict', 'FAIL')}",
            "",
            "Checks:",
        ]
        for check in checks:
            status = "PASS" if u.Infra.pick_bool(check, "passed") else "FAIL"
            lines.append(f"- [{status}] {u.Infra.pick_str(check, 'name', 'unknown')}")
            detail = u.Infra.pick_str(check, "detail")
            if detail:
                lines.append(f"  {detail}")
        lines.extend([
            "",
            "Before/After:",
            f"- violations: {before.get('total_violations', 'n/a')} -> {after.get('total_violations', 'n/a')}",
            f"- duplicates: {before.get('duplicate_groups', 'n/a')} -> {after.get('duplicate_groups', 'n/a')}",
            f"- projects: {after.get('projects_total', 0)} total, {after.get('projects_passed', 0)} passed, {after.get('projects_failed', 0)} failed",
        ])
        if duplicate_groups:
            lines.extend(["", "Duplicate Groups:"])
        for group in duplicate_groups:
            parsed_group = m.Infra.DuplicateConstantGroup.model_validate(group)
            projects = sorted({
                definition.project for definition in parsed_group.definitions
            })
            lines.append(
                "- "
                f"{parsed_group.constant_name}: "
                f"projects={len(projects)}, "
                f"definitions={len(parsed_group.definitions)}, "
                f"values_identical={parsed_group.is_value_identical}",
            )
            if projects:
                lines.append(f"  projects: {', '.join(projects)}")
        lines.extend([
            "",
            "Improvement:",
            f"- violations_delta: {improvement.get('violations_delta', 0)}",
            f"- duplicates_delta: {improvement.get('duplicates_delta', 0)}",
            f"- violations_reduced: {improvement.get('violations_reduced', 0)}",
            f"- duplicates_eliminated: {improvement.get('duplicates_eliminated', 0)}",
        ])
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def is_success_verdict(verdict: str) -> bool:
        """Return True for verdicts that should exit with status 0."""
        return verdict in c.Infra.QualityGate.PASS_VERDICTS


__all__ = ["FlextInfraCodegenConstantsQualityGate"]
