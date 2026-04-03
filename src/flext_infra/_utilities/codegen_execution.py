"""Execution utility namespace mapping for codegen operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
import sys
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_core import u
from flext_infra import c, m, t
from flext_infra._utilities.codegen_constant_detection import (
    FlextInfraUtilitiesCodegenConstantDetection,
)
from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess


class FlextInfraUtilitiesCodegenExecution:
    """Consolidated execution and metrics methods for codegen and quality gate."""

    # -------------------------------------------------------------------------
    # COERCION HELPERS
    # -------------------------------------------------------------------------
    @staticmethod
    def as_int(value: t.Infra.InfraValue | None) -> int:
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    @staticmethod
    def dict_or_empty(
        value: t.Infra.InfraValue | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if value is None or not u.is_mapping(value):
            return dict[str, t.Infra.InfraValue]()
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)

    @staticmethod
    def dict_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        result: Sequence[Mapping[str, t.Infra.InfraValue]] = [
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item)
            for item in value
            if u.is_mapping(item)
        ]
        return result

    @staticmethod
    def extract_total_violations(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "total_violations" in payload:
            return FlextInfraUtilitiesCodegenExecution.as_int(
                payload.get("total_violations")
            )
        totals = FlextInfraUtilitiesCodegenExecution.dict_or_empty(
            payload.get("totals")
        )
        if totals:
            return (
                FlextInfraUtilitiesCodegenExecution.as_int(
                    totals.get("ns001_violations")
                )
                + FlextInfraUtilitiesCodegenExecution.as_int(
                    totals.get("layer_violations")
                )
                + FlextInfraUtilitiesCodegenExecution.as_int(
                    totals.get("cross_project_reference_violations"),
                )
            )
        projects = FlextInfraUtilitiesCodegenExecution.dict_list(
            payload.get("projects")
        )
        if projects and all("total" in item for item in projects):
            return sum(
                FlextInfraUtilitiesCodegenExecution.as_int(item.get("total"))
                for item in projects
            )
        return -1

    @staticmethod
    def extract_duplicate_groups(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "duplicate_groups" in payload:
            return FlextInfraUtilitiesCodegenExecution.as_int(
                payload.get("duplicate_groups")
            )
        duplicates = payload.get("duplicates")
        if isinstance(duplicates, list):
            return sum(1 for _ in duplicates)
        return -1

    @staticmethod
    def extract_projects_total(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesCodegenExecution.dict_or_empty(
            payload.get("totals")
        )
        value = totals.get(c.Infra.ReportKeys.PROJECTS)
        if value is not None:
            return FlextInfraUtilitiesCodegenExecution.as_int(value)
        projects = payload.get("projects")
        if isinstance(projects, list):
            return sum(1 for _ in projects)
        return 0

    @staticmethod
    def extract_projects_passed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesCodegenExecution.dict_or_empty(
            payload.get("totals")
        )
        return FlextInfraUtilitiesCodegenExecution.as_int(totals.get("passed"))

    @staticmethod
    def extract_projects_failed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraUtilitiesCodegenExecution.dict_or_empty(
            payload.get("totals")
        )
        return FlextInfraUtilitiesCodegenExecution.as_int(totals.get("failed"))

    # -------------------------------------------------------------------------
    # SUBPROCESS & EXECUTION
    # -------------------------------------------------------------------------
    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        """Get list of modified python files via git status."""
        lines = FlextInfraUtilitiesCodegenExecution.git_lines(
            workspace_root,
            ["status", "--porcelain"],
        )
        modified: MutableSequence[str] = []
        for line in lines:
            if not line:
                continue
            status = line[:2]
            # M, A, R, C, U scenarios
            if any(s in status for s in ("M", "A", "R", "C", "U")):
                path = line[3:].strip()
                if " -> " in path:  # Rename
                    path = path.split(" -> ")[-1]
                if path.endswith(".py"):
                    modified.append(path)
        return modified

    @staticmethod
    def git_lines(workspace_root: Path, args: t.StrSequence) -> t.StrSequence:
        git_bin = shutil.which(c.Infra.GIT)
        if not git_bin:
            return list[str]()

        result = FlextInfraUtilitiesSubprocess().run_raw(
            [git_bin, "-C", str(workspace_root), *args],
        )
        if result.is_failure:
            return list[str]()
        output = result.value
        if output.exit_code != 0:
            return list[str]()
        return [line.strip() for line in output.stdout.splitlines() if line.strip()]

    @staticmethod
    def run_pyrefly_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.PYREFLY,
            c.Infra.CHECK,
            *modified_files,
            "--config",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--summary=none",
        ]
        result = FlextInfraUtilitiesCodegenExecution.run_external_check(
            workspace_root, cmd
        )
        detail = str(result.get("detail", "")).strip()
        if not bool(result.get("passed", False)) and detail.startswith(
            "WARN PYTHONPATH",
        ):
            result["passed"] = True
        return result

    @staticmethod
    def run_ruff_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        cmd = [
            sys.executable,
            "-m",
            c.Infra.RUFF,
            c.Infra.Verbs.CHECK,
            *modified_files,
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "--quiet",
        ]
        return FlextInfraUtilitiesCodegenExecution.run_external_check(
            workspace_root, cmd
        )

    @staticmethod
    def run_external_check(
        workspace_root: Path,
        cmd: t.StrSequence,
    ) -> MutableMapping[str, t.Infra.InfraValue]:
        result = FlextInfraUtilitiesSubprocess().run_raw(cmd, cwd=workspace_root)
        if result.is_failure:
            return {
                "passed": False,
                "detail": result.error or "execution error",
                "exit_code": 127,
            }
        command_output = result.value
        output = (command_output.stderr or command_output.stdout or "").strip()
        lines = [line for line in output.splitlines() if line.strip()]
        excerpt = " | ".join(lines[:5]) if lines else "ok"
        return {
            "passed": command_output.exit_code == 0,
            "detail": excerpt,
            "exit_code": command_output.exit_code,
        }

    _BARE_IMPORT_FROM_RE: re.Pattern[str] = re.compile(
        r"^from\s+import\s",
        re.MULTILINE,
    )

    @staticmethod
    def scan_import_nodes(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        invalid_import_from: MutableSequence[str] = []
        parse_errors: MutableSequence[str] = []
        bare_re = FlextInfraUtilitiesCodegenExecution._BARE_IMPORT_FROM_RE
        for rel_path in modified_files:
            file_path = (workspace_root / rel_path).resolve()
            if not file_path.is_file():
                continue
            try:
                source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                parse_errors.append(f"{rel_path}:parse failed")
                continue
            for lineno, line in enumerate(source.splitlines(), start=1):
                if bare_re.match(line.lstrip()):
                    invalid_import_from.append(f"{rel_path}:{lineno}")
        invalid_import_from_value: Sequence[t.Infra.InfraValue] = list(
            invalid_import_from,
        )
        parse_errors_value: Sequence[t.Infra.InfraValue] = list(parse_errors)
        return {
            "invalid_import_from_count": len(invalid_import_from),
            "parse_error_count": len(parse_errors),
            "invalid_import_from": invalid_import_from_value,
            "parse_errors": parse_errors_value,
        }

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
        if before_payload is None:
            return {
                "total_violations": -1,
                "duplicate_groups": -1,
                "projects_total": 0,
                "projects_passed": 0,
                "projects_failed": 0,
            }
        return {
            "total_violations": FlextInfraUtilitiesCodegenExecution.extract_total_violations(
                before_payload,
            ),
            "duplicate_groups": FlextInfraUtilitiesCodegenExecution.extract_duplicate_groups(
                before_payload,
            ),
            "projects_total": FlextInfraUtilitiesCodegenExecution.extract_projects_total(
                before_payload,
            ),
            "projects_passed": FlextInfraUtilitiesCodegenExecution.extract_projects_passed(
                before_payload,
            ),
            "projects_failed": FlextInfraUtilitiesCodegenExecution.extract_projects_failed(
                before_payload,
            ),
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
                parsed = m.Infra.CensusViolation.model_validate(
                    raw_violation,
                )
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
            "import_parse_violations": FlextInfraUtilitiesCodegenExecution.as_int(
                import_scan.get("invalid_import_from_count"),
            ),
            "import_parse_errors": FlextInfraUtilitiesCodegenExecution.as_int(
                import_scan.get("parse_error_count"),
            ),
            "modified_python_files": modified_python_files_value,
        }

    @staticmethod
    def improvement(
        before_metrics: Mapping[str, t.Infra.InfraValue],
        after_metrics: Mapping[str, t.Infra.InfraValue],
    ) -> Mapping[str, t.Infra.InfraValue]:
        before_violations = FlextInfraUtilitiesCodegenExecution.as_int(
            before_metrics.get("total_violations"),
        )
        before_duplicates = FlextInfraUtilitiesCodegenExecution.as_int(
            before_metrics.get("duplicate_groups"),
        )
        after_violations = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("total_violations"),
        )
        after_duplicates = FlextInfraUtilitiesCodegenExecution.as_int(
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
        violations_total = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("total_violations"),
        )
        violations_delta = FlextInfraUtilitiesCodegenExecution.as_int(
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
        mro_failures = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("mro_failures"),
        )
        cross_ref = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("cross_project_reference_violations"),
        )
        import_parse = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("import_parse_violations"),
        )
        import_parse_errors = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("import_parse_errors"),
        )
        layer_violations = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("layer_violations"),
        )
        duplicate_groups = FlextInfraUtilitiesCodegenExecution.as_int(
            after_metrics.get("duplicate_groups"),
        )
        duplicates_delta = FlextInfraUtilitiesCodegenExecution.as_int(
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
            FlextInfraUtilitiesCodegenExecution.as_int(
                improvement.get("violations_increased"),
            )
            > 0
            or FlextInfraUtilitiesCodegenExecution.as_int(
                improvement.get("duplicates_increased"),
            )
            > 0
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
                project_root / "src" / report.project.replace("-", "_") / "constants.py"
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


__all__ = ["FlextInfraUtilitiesCodegenExecution"]
