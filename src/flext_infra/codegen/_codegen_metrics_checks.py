from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraCodegenMetrics,
    c,
    m,
    t,
)


class FlextInfraCodegenMetricsChecks(FlextInfraCodegenMetrics):
    """Quality gate checks and verdict computation."""

    _MIN_DUPLICATE_PROJECT_COUNT: ClassVar[int] = 2

    @staticmethod
    def quality_gate_build_checks(
        *,
        after_metrics: dict[str, t.Infra.InfraValue],
        improvement: dict[str, t.Infra.InfraValue],
        pyrefly_check: dict[str, t.Infra.InfraValue],
        ruff_check: dict[str, t.Infra.InfraValue],
        before_available: bool,
        before_load_error: str,
    ) -> list[dict[str, t.Infra.InfraValue]]:
        checks: list[m.Infra.QualityGateCheck] = []
        violations_total = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("total_violations"),
        )
        violations_delta = FlextInfraCodegenMetricsChecks.as_int(
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
        mro_failures = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("mro_failures"),
        )
        cross_ref = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("cross_project_reference_violations"),
        )
        import_parse = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("import_parse_violations"),
        )
        import_parse_errors = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("import_parse_errors"),
        )
        layer_violations = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("layer_violations"),
        )
        duplicate_groups = FlextInfraCodegenMetricsChecks.as_int(
            after_metrics.get("duplicate_groups"),
        )
        duplicates_delta = FlextInfraCodegenMetricsChecks.as_int(
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
    def quality_gate_compute_verdict(
        checks: Sequence[dict[str, t.Infra.InfraValue]],
        improvement: dict[str, t.Infra.InfraValue],
    ) -> str:
        if all(bool(item.get("passed", False)) for item in checks):
            return "PASS"
        if any(
            bool(not item.get("passed", False) and item.get("critical", False))
            for item in checks
        ):
            return "FAIL"
        if (
            FlextInfraCodegenMetricsChecks.as_int(
                improvement.get("violations_increased"),
            )
            > 0
            or FlextInfraCodegenMetricsChecks.as_int(
                improvement.get("duplicates_increased"),
            )
            > 0
        ):
            return "FAIL"
        return "CONDITIONAL_PASS"

    @staticmethod
    def quality_gate_detect_duplicate_constant_groups(
        workspace_root: Path,
    ) -> list[m.Infra.DuplicateConstantGroup]:
        from flext_infra.codegen.census import FlextInfraCodegenCensus  # noqa: PLC0415

        all_definitions: list[m.Infra.ConstantDefinition] = []
        for report in FlextInfraCodegenCensus(workspace_root=workspace_root).run():
            project_root = workspace_root / report.project
            constants_file = (
                project_root / "src" / report.project.replace("-", "_") / "constants.py"
            )
            if not constants_file.is_file():
                continue
            definitions = (
                FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                    constants_file,
                    report.project,
                )
            )
            all_definitions.extend(definitions)
        name_to_defs: dict[str, list[m.Infra.ConstantDefinition]] = {}
        for definition in all_definitions:
            name_to_defs.setdefault(definition.name, []).append(definition)
        groups: list[m.Infra.DuplicateConstantGroup] = []
        for name, definitions in sorted(name_to_defs.items()):
            projects = {item.project for item in definitions}
            if (
                len(projects)
                < FlextInfraCodegenMetricsChecks._MIN_DUPLICATE_PROJECT_COUNT
            ):
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
    def quality_gate_project_findings(
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> list[dict[str, t.Infra.InfraValue]]:
        findings: list[m.Infra.QualityGateProjectFinding] = [
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
        findings.sort(key=lambda item: item.project)
        return [item.model_dump() for item in findings]


__all__ = ["FlextInfraCodegenMetricsChecks"]
