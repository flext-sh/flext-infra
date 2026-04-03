"""Checks, verdicts, and artifact writing mixin for codegen execution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import u
from flext_infra import FlextInfraUtilitiesCodegenConstantDetection, c, m, t


class FlextInfraUtilitiesCodegenExecutionChecks:
    """Quality gate checks, verdicts, duplicate detection, and artifact writing."""

    # -------------------------------------------------------------------------
    # CHECKS & VERDICTS
    # -------------------------------------------------------------------------
    @staticmethod
    def build_checks(
        *,
        after_metrics: Mapping[str, t.Infra.InfraValue],
        improvement: Mapping[str, t.Infra.InfraValue],
        pyrefly_check: Mapping[str, t.Infra.InfraValue],
        ruff_check: Mapping[str, t.Infra.InfraValue],
        before_available: bool,
        before_load_error: str,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        checks: MutableSequence[m.Infra.QualityGateCheck] = []
        violations_total = u.to_int(
            after_metrics.get("total_violations"),
        )
        violations_delta = u.to_int(
            improvement.get("violations_delta"),
        )
        checks.append(
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_NAMESPACE_COMPLIANCE,
                passed=(
                    violations_total == 0 or (before_available and violations_delta < 0)
                )
                and (not before_available or violations_delta <= 0),
                detail=(
                    f"total={violations_total}, delta={violations_delta}"
                    if before_available
                    else f"total={violations_total} (no baseline provided)"
                ),
                critical=False,
            ),
        )
        mro_failures = u.to_int(after_metrics.get("mro_failures"))
        cross_ref = u.to_int(
            after_metrics.get("cross_project_reference_violations"),
        )
        import_parse = u.to_int(
            after_metrics.get("import_parse_violations"),
        )
        import_parse_errors = u.to_int(
            after_metrics.get("import_parse_errors"),
        )
        layer_violations = u.to_int(
            after_metrics.get("layer_violations"),
        )
        duplicate_groups = u.to_int(
            after_metrics.get("duplicate_groups"),
        )
        duplicates_delta = u.to_int(
            improvement.get("duplicates_delta"),
        )
        checks.extend([
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_MRO_VALIDITY,
                passed=mro_failures == 0,
                detail=f"mro_failures={mro_failures}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_IMPORT_RESOLUTION,
                passed=cross_ref == 0
                and import_parse == 0
                and (import_parse_errors == 0),
                detail=(
                    f"cross_project_reference_violations={cross_ref}, "
                    f"invalid_import_from={import_parse}, parse_errors={import_parse_errors}"
                ),
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_LAYER_COMPLIANCE,
                passed=layer_violations == 0,
                detail=f"layer_violations={layer_violations}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_DUPLICATION_REDUCTION,
                passed=(
                    duplicate_groups == 0 or (before_available and duplicates_delta < 0)
                )
                and (not before_available or duplicates_delta <= 0),
                detail=(
                    f"duplicate_groups={duplicate_groups}, delta={duplicates_delta}"
                    if before_available
                    else f"duplicate_groups={duplicate_groups} (no baseline provided)"
                ),
                critical=False,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_TYPE_SAFETY,
                passed=bool(pyrefly_check.get("passed")),
                detail=str(pyrefly_check.get("detail", "")),
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_LINT_CLEAN,
                passed=bool(ruff_check.get("passed")),
                detail=str(ruff_check.get("detail", "")),
                critical=True,
            ),
        ])
        if before_load_error:
            checks.append(
                m.Infra.QualityGateCheck(
                    name=c.Infra.QualityGate.CHECK_BASELINE_LOAD,
                    passed=False,
                    detail=before_load_error,
                    critical=False,
                ),
            )
        return [item.model_dump() for item in checks]

    @staticmethod
    def compute_verdict(
        checks: Sequence[Mapping[str, t.Infra.InfraValue]],
        improvement: Mapping[str, t.Infra.InfraValue],
    ) -> str:
        if all(bool(item.get("passed", False)) for item in checks):
            return "PASS"
        if any(
            bool(not item.get("passed", False) and item.get("critical", False))
            for item in checks
        ):
            return "FAIL"
        if (
            u.to_int(improvement.get("violations_increased")) > 0
            or u.to_int(improvement.get("duplicates_increased")) > 0
        ):
            return "FAIL"
        return "CONDITIONAL_PASS"

    @staticmethod
    def detect_duplicate_constant_groups(
        workspace_root: Path,
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        all_definitions: MutableSequence[m.Infra.ConstantDefinition] = []
        for report in census_reports:
            project_root = workspace_root / report.project
            constants_file = (
                project_root
                / c.Infra.Paths.DEFAULT_SRC_DIR
                / report.project.replace("-", "_")
                / c.Infra.Files.CONSTANTS_PY
            )
            if not constants_file.is_file():
                continue
            definitions = FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                constants_file,
                report.project,
            )
            all_definitions.extend(definitions)
        name_to_defs: defaultdict[
            str,
            MutableSequence[m.Infra.ConstantDefinition],
        ] = defaultdict(list)
        for definition in all_definitions:
            name_to_defs[definition.name].append(definition)
        groups: MutableSequence[m.Infra.DuplicateConstantGroup] = []
        for name, definitions in sorted(name_to_defs.items()):
            projects = {item.project for item in definitions}
            if len(projects) < c.Infra.Thresholds.MIN_DUPLICATE_PROJECT_COUNT:
                continue
            values = {item.value_repr for item in definitions}
            groups.append(
                m.Infra.DuplicateConstantGroup(
                    constant_name=name,
                    definitions=definitions,
                    is_value_identical=len(values) == 1,
                    canonical_ref="",
                ),
            )
        return groups

    @staticmethod
    def project_findings(
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        findings: MutableSequence[m.Infra.QualityGateProjectFinding] = [
            m.Infra.QualityGateProjectFinding(
                project=entry.project,
                violations_total=len(tuple(entry.violations)),
                fixable_violations=int(entry.fixable),
                validator_passed=int(entry.total) == 0,
                mro_failures=0,
                layer_violations=0,
                cross_project_reference_violations=0,
            )
            for entry in census_reports
        ]
        return [
            item.model_dump()
            for item in sorted(findings, key=lambda item: item.project)
        ]

    @staticmethod
    def write_artifacts(
        workspace_root: Path,
        report: Mapping[str, t.Infra.InfraValue],
        render_text: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        directory = workspace_root / c.Infra.QualityGate.REPORT_DIR
        directory.mkdir(parents=True, exist_ok=True)
        report_json = directory / "latest.json"
        report_text = directory / "latest.txt"
        report_json.write_text(
            t.Infra.INFRA_MAPPING_ADAPTER.dump_json(report, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT,
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        report_text.write_text(render_text, encoding=c.Infra.Encoding.DEFAULT)
        return {
            "report_json": str(report_json),
            "report_text": str(report_text),
        }


__all__ = ["FlextInfraUtilitiesCodegenExecutionChecks"]
