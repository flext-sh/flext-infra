"""Extraction and metrics mixin for codegen execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_core import u
from flext_infra import c, m, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraUtilitiesCodegenExecutionMetrics:
    """Extraction helpers and metrics computation for codegen quality gate."""

    # -------------------------------------------------------------------------
    # EXTRACTION HELPERS
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_total_violations(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "total_violations" in payload:
            return u.to_int(payload.get("total_violations"))
        totals = FlextInfraUtilitiesBase.normalize_str_mapping(payload.get("totals"))
        if totals:
            return (
                u.to_int(totals.get("ns001_violations"))
                + u.to_int(totals.get("layer_violations"))
                + u.to_int(
                    totals.get("cross_project_reference_violations"),
                )
            )
        projects = FlextInfraUtilitiesBase.normalize_mapping_list(
            payload.get("projects")
        )
        if projects and all("total" in item for item in projects):
            return sum(u.to_int(item.get("total")) for item in projects)
        return -1

    @staticmethod
    def extract_duplicate_groups(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "duplicate_groups" in payload:
            return u.to_int(payload.get("duplicate_groups"))
        duplicates = payload.get("duplicates")
        if isinstance(duplicates, list):
            return sum(1 for _ in duplicates)
        return -1

    @staticmethod
    def extract_projects_total(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesBase.normalize_str_mapping(payload.get("totals"))
        value = totals.get(c.Infra.ReportKeys.PROJECTS)
        if value is not None:
            return u.to_int(value)
        projects = payload.get("projects")
        if isinstance(projects, list):
            return sum(1 for _ in projects)
        return 0

    @staticmethod
    def extract_projects_passed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesBase.normalize_str_mapping(payload.get("totals"))
        return u.to_int(totals.get("passed"))

    @staticmethod
    def extract_projects_failed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesBase.normalize_str_mapping(payload.get("totals"))
        return u.to_int(totals.get("failed"))

    # -------------------------------------------------------------------------
    # METRICS
    # -------------------------------------------------------------------------
    @staticmethod
    def load_before_payload(
        workspace_root: Path,
        before_report: Path | None,
        baseline_file: Path | None,
    ) -> t.Infra.Triple[Mapping[str, t.Infra.InfraValue] | None, str, str]:
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
            payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_json(text)
        except (OSError, UnicodeDecodeError, ValueError):
            return (None, str(resolved), "baseline parse failed")
        try:
            raw = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
        except ValidationError:
            return (
                None,
                str(resolved),
                "baseline payload is not a JSON t.NormalizedValue",
            )
        return (raw, str(resolved), "")

    @staticmethod
    def before_metrics(
        before_payload: Mapping[str, t.Infra.InfraValue] | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        cls = FlextInfraUtilitiesCodegenExecutionMetrics
        if before_payload is None:
            return {
                "total_violations": -1,
                "duplicate_groups": -1,
                "projects_total": 0,
                "projects_passed": 0,
                "projects_failed": 0,
            }
        return {
            "total_violations": cls.extract_total_violations(before_payload),
            "duplicate_groups": cls.extract_duplicate_groups(before_payload),
            "projects_total": cls.extract_projects_total(before_payload),
            "projects_passed": cls.extract_projects_passed(before_payload),
            "projects_failed": cls.extract_projects_failed(before_payload),
        }

    @staticmethod
    def after_metrics(
        *,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: int,
        import_scan: Mapping[str, t.Infra.InfraValue],
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        by_rule: t.MutableIntMapping = dict.fromkeys(
            c.Infra.QualityGate.RULE_KEYS,
            0,
        )
        total_violations = 0
        for report in census_reports:
            violations = tuple(report.violations)
            total_violations += len(violations)
            for raw_violation in violations:
                parsed = m.Infra.CensusViolation.model_validate(raw_violation)
                if parsed.rule in by_rule:
                    by_rule[parsed.rule] += 1
        projects_total = len(census_reports)
        projects_passed = u.count(census_reports, lambda item: int(item.total) == 0)
        projects_failed = projects_total - projects_passed
        violations_by_rule: Mapping[str, t.Infra.InfraValue] = dict(by_rule)
        modified_python_files_value: Sequence[t.Infra.InfraValue] = list(modified_files)
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
            "import_parse_violations": u.to_int(
                import_scan.get("invalid_import_from_count"),
            ),
            "import_parse_errors": u.to_int(
                import_scan.get("parse_error_count"),
            ),
            "modified_python_files": modified_python_files_value,
        }

    @staticmethod
    def improvement(
        before_metrics: Mapping[str, t.Infra.InfraValue],
        after_metrics: Mapping[str, t.Infra.InfraValue],
    ) -> Mapping[str, t.Infra.InfraValue]:
        before_violations = u.to_int(
            before_metrics.get("total_violations"),
        )
        before_duplicates = u.to_int(
            before_metrics.get("duplicate_groups"),
        )
        after_violations = u.to_int(
            after_metrics.get("total_violations"),
        )
        after_duplicates = u.to_int(
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


__all__ = ["FlextInfraUtilitiesCodegenExecutionMetrics"]
