from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_infra import c, t
from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration
from flext_infra.codegen._models import FlextInfraCodegenModels


class FlextInfraCodegenMetrics(FlextInfraCodegenGeneration):
    """Metrics extraction and computation for quality gate analysis."""

    @staticmethod
    def quality_gate_load_before_payload(
        workspace_root: Path,
        before_report: Path | None,
        baseline_file: Path | None,
    ) -> tuple[dict[str, t.Infra.InfraValue] | None, str, str]:
        baseline_path = before_report or baseline_file
        if baseline_path is None:
            return (None, "", "")
        resolved = (
            baseline_path
            if baseline_path.is_absolute()
            else workspace_root / baseline_path
        ).resolve()
        if not resolved.is_file():
            return (None, str(resolved), f"baseline file not found: {resolved}")
        try:
            text = resolved.read_text(encoding=c.Infra.Encoding.DEFAULT)
            payload = FlextInfraCodegenMetrics.container_mapping_adapter.validate_json(
                text,
            )
        except (OSError, UnicodeDecodeError, ValueError):
            return (None, str(resolved), "baseline parse failed")
        try:
            raw = FlextInfraCodegenMetrics.container_mapping_adapter.validate_python(
                payload,
            )
        except ValidationError:
            return (None, str(resolved), "baseline payload is not a JSON object")
        return (raw, str(resolved), "")

    @staticmethod
    def quality_gate_before_metrics(
        before_payload: dict[str, t.Infra.InfraValue] | None,
    ) -> dict[str, t.Infra.InfraValue]:
        if before_payload is None:
            return {
                "total_violations": -1,
                "duplicate_groups": -1,
                "projects_total": 0,
                "projects_passed": 0,
                "projects_failed": 0,
            }
        return {
            "total_violations": FlextInfraCodegenMetrics.extract_total_violations(
                before_payload,
            ),
            "duplicate_groups": FlextInfraCodegenMetrics.extract_duplicate_groups(
                before_payload,
            ),
            "projects_total": FlextInfraCodegenMetrics.extract_projects_total(
                before_payload,
            ),
            "projects_passed": FlextInfraCodegenMetrics.extract_projects_passed(
                before_payload,
            ),
            "projects_failed": FlextInfraCodegenMetrics.extract_projects_failed(
                before_payload,
            ),
        }

    @staticmethod
    def quality_gate_after_metrics(
        *,
        census_reports: Sequence[FlextInfraCodegenModels.CensusReport],
        duplicate_groups: int,
        import_scan: dict[str, t.Infra.InfraValue],
        modified_files: list[str],
    ) -> dict[str, t.Infra.InfraValue]:
        by_rule: dict[str, int] = dict.fromkeys(
            c.Infra.Codegen.QualityGate.RULE_KEYS, 0,
        )
        total_violations = 0
        for report in census_reports:
            violations = tuple(report.violations)
            total_violations += len(violations)
            for raw_violation in violations:
                parsed = FlextInfraCodegenModels.CensusViolation.model_validate(
                    raw_violation,
                )
                if parsed.rule in by_rule:
                    by_rule[parsed.rule] += 1
        projects_total = len(census_reports)
        projects_passed = sum(1 for item in census_reports if int(item.total) == 0)
        projects_failed = projects_total - projects_passed
        violations_by_rule: dict[str, t.Infra.InfraValue] = dict(by_rule)
        modified_python_files_value: list[t.Infra.InfraValue] = list(modified_files)
        return {
            "total_violations": total_violations,
            "violations_by_rule": violations_by_rule,
            "duplicate_groups": duplicate_groups,
            "projects_total": projects_total,
            "projects_passed": projects_passed,
            "projects_failed": projects_failed,
            "mro_failures": 0,
            "layer_violations": 0,
            "cross_project_reference_violations": 0,
            "import_parse_violations": FlextInfraCodegenMetrics.as_int(
                import_scan.get("invalid_import_from_count"),
            ),
            "import_parse_errors": FlextInfraCodegenMetrics.as_int(
                import_scan.get("parse_error_count"),
            ),
            "modified_python_files": modified_python_files_value,
        }

    @staticmethod
    def quality_gate_improvement(
        before_metrics: dict[str, t.Infra.InfraValue],
        after_metrics: dict[str, t.Infra.InfraValue],
    ) -> dict[str, t.Infra.InfraValue]:
        before_violations = FlextInfraCodegenMetrics.as_int(
            before_metrics.get("total_violations"),
        )
        before_duplicates = FlextInfraCodegenMetrics.as_int(
            before_metrics.get("duplicate_groups"),
        )
        after_violations = FlextInfraCodegenMetrics.as_int(
            after_metrics.get("total_violations"),
        )
        after_duplicates = FlextInfraCodegenMetrics.as_int(
            after_metrics.get("duplicate_groups"),
        )
        violations_delta = (
            0 if before_violations < 0 else after_violations - before_violations
        )
        duplicates_delta = (
            0 if before_duplicates < 0 else after_duplicates - before_duplicates
        )
        return {
            "violations_delta": violations_delta,
            "duplicates_delta": duplicates_delta,
            "violations_reduced": max(0, -violations_delta),
            "duplicates_eliminated": max(0, -duplicates_delta),
            "violations_increased": max(0, violations_delta),
            "duplicates_increased": max(0, duplicates_delta),
        }


__all__ = ["FlextInfraCodegenMetrics"]
