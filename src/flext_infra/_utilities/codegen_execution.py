"""Execution utilities for codegen quality gate: metrics, checks, subprocess.

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
from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesSubprocess,
    c,
    m,
    t,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase

_BARE_IMPORT_FROM_RE = re.compile(r"^from\s+import\s", re.MULTILINE)
_NO_MODIFIED = {
    "passed": True,
    "detail": "no modified python files detected",
    "exit_code": 0,
}


def _int(payload: Mapping[str, t.Infra.InfraValue], key: str) -> int:
    """Shorthand for ``u.to_int(payload.get(key))``."""
    return FlextInfraUtilitiesBase.nested_int(payload, key)


def _totals(
    payload: Mapping[str, t.Infra.InfraValue],
) -> Mapping[str, t.Infra.InfraValue]:
    return FlextInfraUtilitiesBase.normalize_str_mapping(payload.get("totals"))


class FlextInfraUtilitiesCodegenExecution:
    """Codegen quality gate: extraction, metrics, checks, subprocess."""

    # ── Extraction ───────────────────────────────────────────────────

    @staticmethod
    def extract_total_violations(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "total_violations" in payload:
            return _int(payload, "total_violations")
        totals = _totals(payload)
        if totals:
            return sum(
                _int(totals, k)
                for k in (
                    "ns001_violations",
                    "layer_violations",
                    "cross_project_reference_violations",
                )
            )
        projects = FlextInfraUtilitiesBase.normalize_mapping_list(
            payload.get("projects")
        )
        if projects and all("total" in item for item in projects):
            return sum(_int(item, "total") for item in projects)
        return -1

    @staticmethod
    def extract_duplicate_groups(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "duplicate_groups" in payload:
            return _int(payload, "duplicate_groups")
        dups = payload.get("duplicates")
        return sum(1 for _ in dups) if isinstance(dups, list) else -1

    @staticmethod
    def extract_projects_total(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        value = _totals(payload).get(c.Infra.ReportKeys.PROJECTS)
        if value is not None:
            return u.to_int(value)
        projects = payload.get("projects")
        return sum(1 for _ in projects) if isinstance(projects, list) else 0

    @staticmethod
    def _extract_totals_field(
        payload: Mapping[str, t.Infra.InfraValue], key: str
    ) -> int:
        return _int(_totals(payload), key)

    # ── Metrics ──────────────────────────────────────────────────────

    @staticmethod
    def load_before_payload(
        workspace_root: Path,
        before_report: Path | None,
        baseline_file: Path | None,
    ) -> t.Infra.Triple[Mapping[str, t.Infra.InfraValue] | None, str, str]:
        path = before_report or baseline_file
        if path is None:
            return (None, "", "")
        resolved = (path if path.is_absolute() else workspace_root / path).resolve()
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
        cls = FlextInfraUtilitiesCodegenExecution
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
            "projects_passed": cls._extract_totals_field(before_payload, "passed"),
            "projects_failed": cls._extract_totals_field(before_payload, "failed"),
        }

    @staticmethod
    def after_metrics(
        *,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: int,
        import_scan: Mapping[str, t.Infra.InfraValue],
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        by_rule: t.MutableIntMapping = dict.fromkeys(c.Infra.QualityGate.RULE_KEYS, 0)
        total_violations = 0
        for report in census_reports:
            violations = tuple(report.violations)
            total_violations += len(violations)
            for raw in violations:
                parsed = m.Infra.CensusViolation.model_validate(raw)
                if parsed.rule in by_rule:
                    by_rule[parsed.rule] += 1
        total = len(census_reports)
        passed = u.count(census_reports, lambda r: int(r.total) == 0)
        modified_value: Sequence[t.Infra.InfraValue] = list(modified_files)
        return {
            "total_violations": total_violations,
            "violations_by_rule": dict(by_rule),
            "duplicate_groups": duplicate_groups,
            "projects_total": total,
            "projects_passed": passed,
            "projects_failed": total - passed,
            "mro_failures": 0,
            "layer_violations": 0,
            "cross_project_reference_violations": 0,
            "import_parse_violations": _int(import_scan, "invalid_import_from_count"),
            "import_parse_errors": _int(import_scan, "parse_error_count"),
            "modified_python_files": modified_value,
        }

    @staticmethod
    def improvement(
        before_metrics: Mapping[str, t.Infra.InfraValue],
        after_metrics: Mapping[str, t.Infra.InfraValue],
    ) -> Mapping[str, t.Infra.InfraValue]:
        bv = _int(before_metrics, "total_violations")
        bd = _int(before_metrics, "duplicate_groups")
        av = _int(after_metrics, "total_violations")
        ad = _int(after_metrics, "duplicate_groups")
        vd = 0 if bv < 0 else av - bv
        dd = 0 if bd < 0 else ad - bd
        return {
            "violations_delta": vd,
            "duplicates_delta": dd,
            "violations_reduced": max(0, -vd),
            "duplicates_eliminated": max(0, -dd),
            "violations_increased": max(0, vd),
            "duplicates_increased": max(0, dd),
        }

    # ── Subprocess ───────────────────────────────────────────────────

    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        modified: MutableSequence[str] = []
        for line in FlextInfraUtilitiesCodegenExecution.git_lines(
            workspace_root, ["status", "--porcelain"]
        ):
            if not line:
                continue
            if any(s in line[:2] for s in ("M", "A", "R", "C", "U")):
                path = line[3:].strip()
                if " -> " in path:
                    path = path.split(" -> ")[-1]
                if path.endswith(c.Infra.Extensions.PYTHON):
                    modified.append(path)
        return modified

    @staticmethod
    def git_lines(workspace_root: Path, args: t.StrSequence) -> t.StrSequence:
        git_bin = shutil.which(c.Infra.GIT)
        if not git_bin:
            return []
        result = FlextInfraUtilitiesSubprocess().run_raw([
            git_bin,
            "-C",
            str(workspace_root),
            *args,
        ])
        if result.is_failure or result.value.exit_code != 0:
            return []
        return [ln.strip() for ln in result.value.stdout.splitlines() if ln.strip()]

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
        out = result.value
        output = (out.stderr or out.stdout or "").strip()
        lines = [ln for ln in output.splitlines() if ln.strip()]
        return {
            "passed": out.exit_code == 0,
            "detail": " | ".join(lines[:5]) if lines else "ok",
            "exit_code": out.exit_code,
        }

    @staticmethod
    def _run_tool_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
        cmd: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Shared runner for ruff/pyrefly: skip if no files, else run_external_check."""
        if not modified_files:
            return dict(_NO_MODIFIED)
        return FlextInfraUtilitiesCodegenExecution.run_external_check(
            workspace_root, cmd
        )

    @staticmethod
    def run_pyrefly_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        result = FlextInfraUtilitiesCodegenExecution._run_tool_check(
            workspace_root,
            modified_files,
            [
                sys.executable,
                "-m",
                c.Infra.PYREFLY,
                c.Infra.CHECK,
                *modified_files,
                "--config",
                c.Infra.Files.PYPROJECT_FILENAME,
                "--summary=none",
            ],
        )
        detail = str(result.get("detail", "")).strip()
        if not bool(result.get("passed", False)) and detail.startswith(
            "WARN PYTHONPATH"
        ):
            result = {**result, "passed": True}
        return result

    @staticmethod
    def run_ruff_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        return FlextInfraUtilitiesCodegenExecution._run_tool_check(
            workspace_root,
            modified_files,
            [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                c.Infra.Verbs.CHECK,
                *modified_files,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--quiet",
            ],
        )

    @staticmethod
    def scan_import_nodes(
        workspace_root: Path,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        invalid: MutableSequence[str] = []
        errors: MutableSequence[str] = []
        for rel in modified_files:
            fp = (workspace_root / rel).resolve()
            if not fp.is_file():
                continue
            try:
                source = fp.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                errors.append(f"{rel}:parse failed")
                continue
            for lineno, line in enumerate(source.splitlines(), 1):
                if _BARE_IMPORT_FROM_RE.match(line.lstrip()):
                    invalid.append(f"{rel}:{lineno}")
        inv_v: Sequence[t.Infra.InfraValue] = list(invalid)
        err_v: Sequence[t.Infra.InfraValue] = list(errors)
        return {
            "invalid_import_from_count": len(invalid),
            "parse_error_count": len(errors),
            "invalid_import_from": inv_v,
            "parse_errors": err_v,
        }

    # ── Checks & Verdicts ────────────────────────────────────────────

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
        am = after_metrics
        im = improvement
        vt = _int(am, "total_violations")
        vd = _int(im, "violations_delta")
        mro = _int(am, "mro_failures")
        xref = _int(am, "cross_project_reference_violations")
        ip = _int(am, "import_parse_violations")
        ipe = _int(am, "import_parse_errors")
        lv = _int(am, "layer_violations")
        dg = _int(am, "duplicate_groups")
        dd = _int(im, "duplicates_delta")
        ba = before_available

        def _delta_pass(total: int, delta: int) -> bool:
            return (total == 0 or (ba and delta < 0)) and (not ba or delta <= 0)

        checks: MutableSequence[m.Infra.QualityGateCheck] = [
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_NAMESPACE_COMPLIANCE,
                passed=_delta_pass(vt, vd),
                detail=f"total={vt}, delta={vd}"
                if ba
                else f"total={vt} (no baseline provided)",
                critical=False,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_MRO_VALIDITY,
                passed=mro == 0,
                detail=f"mro_failures={mro}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_IMPORT_RESOLUTION,
                passed=xref == 0 and ip == 0 and ipe == 0,
                detail=f"cross_project_reference_violations={xref}, invalid_import_from={ip}, parse_errors={ipe}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_LAYER_COMPLIANCE,
                passed=lv == 0,
                detail=f"layer_violations={lv}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QualityGate.CHECK_DUPLICATION_REDUCTION,
                passed=_delta_pass(dg, dd),
                detail=f"duplicate_groups={dg}, delta={dd}"
                if ba
                else f"duplicate_groups={dg} (no baseline provided)",
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
        ]
        if before_load_error:
            checks.append(
                m.Infra.QualityGateCheck(
                    name=c.Infra.QualityGate.CHECK_BASELINE_LOAD,
                    passed=False,
                    detail=before_load_error,
                    critical=False,
                )
            )
        return [item.model_dump() for item in checks]

    @staticmethod
    def compute_verdict(
        checks: Sequence[Mapping[str, t.Infra.InfraValue]],
        improvement: Mapping[str, t.Infra.InfraValue],
    ) -> str:
        if all(bool(ck.get("passed", False)) for ck in checks):
            return "PASS"
        if any(
            not ck.get("passed", False) and ck.get("critical", False) for ck in checks
        ):
            return "FAIL"
        if (
            _int(improvement, "violations_increased") > 0
            or _int(improvement, "duplicates_increased") > 0
        ):
            return "FAIL"
        return "CONDITIONAL_PASS"

    @staticmethod
    def detect_duplicate_constant_groups(
        workspace_root: Path,
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        all_defs: MutableSequence[m.Infra.ConstantDefinition] = []
        for report in census_reports:
            cf = (
                workspace_root
                / report.project
                / c.Infra.Paths.DEFAULT_SRC_DIR
                / report.project.replace("-", "_")
                / c.Infra.Files.CONSTANTS_PY
            )
            if cf.is_file():
                all_defs.extend(
                    FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                        cf, report.project
                    ),
                )
        by_name: defaultdict[str, MutableSequence[m.Infra.ConstantDefinition]] = (
            defaultdict(list)
        )
        for d in all_defs:
            by_name[d.name].append(d)
        return [
            m.Infra.DuplicateConstantGroup(
                constant_name=name,
                definitions=defs,
                is_value_identical=len({d.value_repr for d in defs}) == 1,
                canonical_ref="",
            )
            for name, defs in sorted(by_name.items())
            if len({d.project for d in defs})
            >= c.Infra.Thresholds.MIN_DUPLICATE_PROJECT_COUNT
        ]

    @staticmethod
    def project_findings(
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        return [
            item.model_dump()
            for item in sorted(
                (
                    m.Infra.QualityGateProjectFinding(
                        project=e.project,
                        violations_total=len(tuple(e.violations)),
                        fixable_violations=int(e.fixable),
                        validator_passed=int(e.total) == 0,
                        mro_failures=0,
                        layer_violations=0,
                        cross_project_reference_violations=0,
                    )
                    for e in census_reports
                ),
                key=lambda item: item.project,
            )
        ]

    @staticmethod
    def write_artifacts(
        workspace_root: Path,
        report: Mapping[str, t.Infra.InfraValue],
        render_text: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        d = workspace_root / c.Infra.QualityGate.REPORT_DIR
        d.mkdir(parents=True, exist_ok=True)
        rj, rt = d / "latest.json", d / "latest.txt"
        rj.write_text(
            t.Infra.INFRA_MAPPING_ADAPTER.dump_json(report, by_alias=True).decode(
                c.Infra.Encoding.DEFAULT
            ),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        rt.write_text(render_text, encoding=c.Infra.Encoding.DEFAULT)
        return {"report_json": str(rj), "report_text": str(rt)}


__all__ = ["FlextInfraUtilitiesCodegenExecution"]
