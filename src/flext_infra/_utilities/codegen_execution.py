"""Execution utilities for codegen quality gate: metrics, checks, subprocess.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenConstantAnalysis,
    FlextInfraUtilitiesCodegenConstantDetection,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenExecution:
    """Codegen quality gate: extraction, metrics, checks, subprocess."""

    # ── Metrics ──────────────────────────────────────────────────────

    @staticmethod
    def after_metrics(
        *,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: int,
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
            "modified_python_files": modified_value,
        }

    # ── Subprocess ───────────────────────────────────────────────────

    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        modified: MutableSequence[str] = []
        git_bin = shutil.which(c.Infra.GIT)
        if not git_bin:
            return []
        result = u.Cli.run_raw([
            git_bin,
            "-C",
            str(workspace_root),
            "status",
            "--porcelain",
        ])
        if result.is_failure or result.value.exit_code != 0:
            return []
        for line in (
            ln.strip() for ln in result.value.stdout.splitlines() if ln.strip()
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
    def _run_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
        cmd: t.StrSequence,
    ) -> MutableMapping[str, t.Infra.InfraValue]:
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        result = u.Cli.run_raw(cmd, cwd=workspace_root)
        if result.is_failure:
            return {
                "passed": False,
                "detail": result.error or "execution error",
                "exit_code": 127,
            }
        out = result.value
        output = (out.stderr or out.stdout or "").strip()
        lines = [ln for ln in output.splitlines() if ln.strip()]
        payload: MutableMapping[str, t.Infra.InfraValue] = {
            "passed": out.exit_code == 0,
            "detail": " | ".join(lines[:5]) if lines else "ok",
            "exit_code": out.exit_code,
        }
        return payload

    @staticmethod
    def run_static_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
        tool: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if tool == c.Infra.PYREFLY:
            return FlextInfraUtilitiesCodegenExecution._run_check(
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
        if tool == c.Infra.RUFF:
            return FlextInfraUtilitiesCodegenExecution._run_check(
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
        return {"passed": False, "detail": f"unsupported tool: {tool}", "exit_code": 2}

    # ── Checks & Verdicts ────────────────────────────────────────────

    @staticmethod
    def build_checks(
        *,
        after_metrics: Mapping[str, t.Infra.InfraValue],
        pyrefly_check: Mapping[str, t.Infra.InfraValue],
        ruff_check: Mapping[str, t.Infra.InfraValue],
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        am = after_metrics
        vt = FlextInfraUtilitiesBase.nested_int(am, "total_violations")
        mro = FlextInfraUtilitiesBase.nested_int(am, "mro_failures")
        xref = FlextInfraUtilitiesBase.nested_int(
            am, "cross_project_reference_violations"
        )
        lv = FlextInfraUtilitiesBase.nested_int(am, "layer_violations")
        dg = FlextInfraUtilitiesBase.nested_int(am, "duplicate_groups")

        check_specs = [
            (
                c.Infra.QualityGate.CHECK_NAMESPACE_COMPLIANCE,
                vt == 0,
                f"total={vt}",
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_MRO_VALIDITY,
                mro == 0,
                f"mro_failures={mro}",
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_IMPORT_RESOLUTION,
                xref == 0,
                f"cross_project_reference_violations={xref}",
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_LAYER_COMPLIANCE,
                lv == 0,
                f"layer_violations={lv}",
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_DUPLICATION_REDUCTION,
                dg == 0,
                f"duplicate_groups={dg}",
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_TYPE_SAFETY,
                bool(pyrefly_check.get("passed")),
                str(pyrefly_check.get("detail", "")),
                True,
            ),
            (
                c.Infra.QualityGate.CHECK_LINT_CLEAN,
                bool(ruff_check.get("passed")),
                str(ruff_check.get("detail", "")),
                True,
            ),
        ]
        checks: MutableSequence[m.Infra.QualityGateCheck] = [
            m.Infra.QualityGateCheck(
                name=name,
                passed=passed,
                detail=detail,
                critical=critical,
            )
            for name, passed, detail, critical in check_specs
        ]
        return [item.model_dump() for item in checks]

    @staticmethod
    def compute_verdict(
        checks: Sequence[Mapping[str, t.Infra.InfraValue]],
    ) -> str:
        if all(bool(ck.get("passed", False)) for ck in checks):
            return "PASS"
        return "FAIL"

    @staticmethod
    def detect_duplicate_constant_groups(
        workspace_root: Path,
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        all_defs: list[m.Infra.ConstantDefinition] = []
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
        return [
            group
            for group in FlextInfraUtilitiesCodegenConstantAnalysis.detect_duplicate_constants(
                all_defs,
            )
            if len({definition.project for definition in group.definitions})
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
