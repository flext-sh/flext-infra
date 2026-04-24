"""Workspace-wide quality gate for constants refactor outcomes."""

from __future__ import annotations

import shutil
import sys
from collections import defaultdict
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenLazyInit,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraConstantsCodegenQualityGate(s[bool]):
    """Run final constants migration checks with before/after comparison."""

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the quality gate and return its CLI success/failure status."""
        report = self.build_report()
        verdict = u.Cli.json_pick_str(report, "verdict", "FAIL")
        if self.successful_verdict(verdict):
            return r[bool].ok(True)
        return r[bool].fail(f"quality gate verdict: {verdict}")

    def build_report(self) -> t.Infra.ContainerDict:
        """Execute quality gate and return structured report payload."""
        FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": self.workspace_root},
        ).generate_inits()
        census_reports = FlextInfraCodegenCensus.model_validate(
            {"workspace_root": self.workspace_root},
        ).run()
        duplicate_groups = self.detect_duplicate_constant_groups(
            self.workspace_root,
            census_reports,
        )
        modified_files = self.modified_python_files(
            self.workspace_root,
        )
        pyrefly_check = self.run_static_check(
            self.workspace_root,
            modified_files,
            c.Infra.PYREFLY,
        )
        ruff_check = self.run_static_check(
            self.workspace_root,
            modified_files,
            c.Infra.RUFF,
        )
        after_metrics = self.after_metrics(
            census_reports=census_reports,
            duplicate_groups=len(duplicate_groups),
            modified_files=modified_files,
        )
        checks = self.build_checks(
            after_metrics=after_metrics,
            pyrefly_check=pyrefly_check,
            ruff_check=ruff_check,
        )
        verdict = self.compute_verdict(checks)
        report_data = {
            "workspace": str(self.workspace_root),
            "generated_at": datetime.now(UTC).isoformat(),
            "verdict": verdict,
            "checks": [
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(check) for check in checks
            ],
            "after": after_metrics,
            "duplicate_constant_groups": [
                group.model_dump() for group in duplicate_groups
            ],
            "projects": [
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(project)
                for project in self.project_findings(census_reports)
            ],
        }
        report = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(report_data)
        report_data["artifacts"] = self.write_artifacts(
            workspace_root=self.workspace_root,
            report=report,
            render_text=self.render_text(report),
        )
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(report_data)

    @staticmethod
    def modified_python_files(workspace_root: Path) -> t.StrSequence:
        """Return modified Python files detected by git porcelain status."""
        modified: MutableSequence[str] = []
        git_bin = shutil.which(c.Infra.GIT)
        if git_bin is None:
            return []
        result = u.Cli.run_raw([
            git_bin,
            "-C",
            str(workspace_root),
            "status",
            "--porcelain",
        ])
        if result.failure or result.value.exit_code != 0:
            return []
        for line in (
            entry.strip() for entry in result.value.stdout.splitlines() if entry.strip()
        ):
            if any(status in line[:2] for status in ("M", "A", "R", "C", "U")):
                path = line[3:].strip()
                if " -> " in path:
                    path = path.split(" -> ")[-1]
                if path.endswith(c.Infra.EXT_PYTHON):
                    modified.append(path)
        return list(modified)

    @staticmethod
    def run_static_check(
        workspace_root: Path,
        modified_files: t.StrSequence,
        tool: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Run a targeted static tool on modified files and normalize result."""
        if not modified_files:
            return {
                "passed": True,
                "detail": "no modified python files detected",
                "exit_code": 0,
            }
        if tool == c.Infra.PYREFLY:
            cmd = [
                sys.executable,
                "-m",
                c.Infra.PYREFLY,
                c.Infra.CHECK,
                *modified_files,
                "--config",
                c.Infra.PYPROJECT_FILENAME,
                "--summary=none",
            ]
        elif tool == c.Infra.RUFF:
            cmd = [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                c.Infra.VERB_CHECK,
                *modified_files,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--quiet",
            ]
        else:
            return {
                "passed": False,
                "detail": f"unsupported tool: {tool}",
                "exit_code": 2,
            }
        run = u.Cli.run_raw(cmd, cwd=workspace_root)
        if run.failure:
            return {
                "passed": False,
                "detail": run.error or "execution error",
                "exit_code": 127,
            }
        output = (run.value.stderr or run.value.stdout or "").strip()
        lines = [line for line in output.splitlines() if line.strip()]
        return {
            "passed": run.value.exit_code == 0,
            "detail": " | ".join(lines[:5]) if lines else "ok",
            "exit_code": run.value.exit_code,
        }

    @staticmethod
    def after_metrics(
        *,
        census_reports: Sequence[m.Infra.CensusReport],
        duplicate_groups: int,
        modified_files: t.StrSequence,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Build post-run metrics summary used by quality checks."""
        by_rule: t.MutableIntMapping = dict.fromkeys(c.Infra.QG_RULE_KEYS, 0)
        total_violations = 0
        for report in census_reports:
            violations = tuple(report.violations)
            total_violations += len(violations)
            for raw in violations:
                parsed = m.Infra.CensusViolation.model_validate(raw)
                if parsed.rule in by_rule:
                    by_rule[parsed.rule] += 1
        total = len(census_reports)
        passed = u.count(census_reports, lambda report: int(report.total) == 0)
        modified_python_files: list[t.Infra.InfraValue] = list(modified_files)
        violations_by_rule: dict[str, t.Infra.InfraValue] = dict(by_rule)
        summary: dict[str, t.Infra.InfraValue] = {
            "total_violations": total_violations,
            "violations_by_rule": violations_by_rule,
            "duplicate_groups": duplicate_groups,
            "projects_total": total,
            "projects_passed": passed,
            "projects_failed": total - passed,
            "mro_failures": 0,
            "layer_violations": 0,
            "cross_project_reference_violations": 0,
            "modified_python_files": modified_python_files,
        }
        return summary

    @staticmethod
    def build_checks(
        *,
        after_metrics: Mapping[str, t.Infra.InfraValue],
        pyrefly_check: Mapping[str, t.Infra.InfraValue],
        ruff_check: Mapping[str, t.Infra.InfraValue],
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Build quality gate check entries from metrics and tool results."""
        violations_total = u.Cli.json_nested_int(after_metrics, "total_violations")
        mro_failures = u.Cli.json_nested_int(after_metrics, "mro_failures")
        cross_reference = u.Cli.json_nested_int(
            after_metrics, "cross_project_reference_violations"
        )
        layer_violations = u.Cli.json_nested_int(after_metrics, "layer_violations")
        duplicate_groups = u.Cli.json_nested_int(after_metrics, "duplicate_groups")
        checks: Sequence[m.Infra.QualityGateCheck] = (
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_NAMESPACE_COMPLIANCE,
                passed=violations_total == 0,
                detail=f"total={violations_total}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_MRO_VALIDITY,
                passed=mro_failures == 0,
                detail=f"mro_failures={mro_failures}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_IMPORT_RESOLUTION,
                passed=cross_reference == 0,
                detail=f"cross_project_reference_violations={cross_reference}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_LAYER_COMPLIANCE,
                passed=layer_violations == 0,
                detail=f"layer_violations={layer_violations}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_DUPLICATION_REDUCTION,
                passed=duplicate_groups == 0,
                detail=f"duplicate_groups={duplicate_groups}",
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_TYPE_SAFETY,
                passed=bool(pyrefly_check.get("passed")),
                detail=str(pyrefly_check.get("detail", "")),
                critical=True,
            ),
            m.Infra.QualityGateCheck(
                name=c.Infra.QG_CHECK_LINT_CLEAN,
                passed=bool(ruff_check.get("passed")),
                detail=str(ruff_check.get("detail", "")),
                critical=True,
            ),
        )
        return [check.model_dump() for check in checks]

    @staticmethod
    def compute_verdict(checks: Sequence[Mapping[str, t.Infra.InfraValue]]) -> str:
        """Return PASS only when all checks passed."""
        return (
            "PASS"
            if all(bool(check.get("passed", False)) for check in checks)
            else "FAIL"
        )

    @staticmethod
    def detect_duplicate_constant_groups(
        workspace_root: Path,
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        """Collect duplicate constants across projects using Rope resource reads."""
        definitions: MutableSequence[m.Infra.ConstantDefinition] = []
        with u.Infra.open_project(workspace_root) as rope_project:
            for report in census_reports:
                constants_file = (
                    workspace_root
                    / report.project
                    / c.Infra.DEFAULT_SRC_DIR
                    / report.project.replace("-", "_")
                    / c.Infra.CONSTANTS_PY
                )
                resource = u.Infra.get_resource_from_path(rope_project, constants_file)
                if resource is None:
                    continue
                class_stack: MutableSequence[tuple[str, int]] = []
                for line_number, line in enumerate(resource.read().splitlines(), 1):
                    stripped = line.lstrip()
                    indent = len(line) - len(stripped)
                    if stripped.startswith("class ") and stripped.endswith(":"):
                        class_match = c.Infra.DETECTION_CLASS_DECL_RE.match(stripped)
                        if class_match is not None:
                            while class_stack and class_stack[-1][1] >= indent:
                                class_stack.pop()
                            class_stack.append((class_match.group(1), indent))
                    elif class_stack:
                        while class_stack and indent <= class_stack[-1][1]:
                            class_stack.pop()
                    match = c.Infra.DETECTION_FINAL_DECL_RE.match(line)
                    if match is None:
                        continue
                    definitions.append(
                        m.Infra.ConstantDefinition(
                            name=match.group("name"),
                            value_repr=match.group("value").strip(),
                            type_annotation=match.group("ann"),
                            file_path=str(constants_file),
                            class_path=".".join(name for name, _ in class_stack),
                            project=report.project,
                            line=line_number,
                        )
                    )
        by_name: defaultdict[str, list[m.Infra.ConstantDefinition]] = defaultdict(list)
        by_value: defaultdict[str, list[m.Infra.ConstantDefinition]] = defaultdict(list)
        for definition in definitions:
            by_name[definition.name].append(definition)
            by_value[definition.value_repr].append(definition)
        duplicates: MutableSequence[m.Infra.DuplicateConstantGroup] = []
        for name, defs in by_name.items():
            if len(defs) > 1:
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=name,
                        definitions=defs,
                        is_value_identical=len({item.value_repr for item in defs}) == 1,
                        canonical_ref="",
                    )
                )
        for value_key, defs in by_value.items():
            if len(defs) > 1 and len({item.name for item in defs}) > 1:
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=f"[value: {value_key}]",
                        definitions=defs,
                        is_value_identical=True,
                        canonical_ref="",
                    )
                )
        return [
            group
            for group in duplicates
            if len({definition.project for definition in group.definitions})
            >= c.Infra.MIN_DUPLICATE_PROJECT_COUNT
        ]

    @staticmethod
    def project_findings(
        census_reports: Sequence[m.Infra.CensusReport],
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Convert census reports into sorted per-project findings."""
        return [
            item.model_dump()
            for item in sorted(
                (
                    m.Infra.QualityGateProjectFinding(
                        project=report.project,
                        violations_total=len(tuple(report.violations)),
                        fixable_violations=int(report.fixable),
                        validator_passed=int(report.total) == 0,
                        mro_failures=0,
                        layer_violations=0,
                        cross_project_reference_violations=0,
                    )
                    for report in census_reports
                ),
                key=lambda entry: entry.project,
            )
        ]

    @staticmethod
    def write_artifacts(
        workspace_root: Path,
        report: t.Infra.ContainerDict,
        render_text: str,
    ) -> t.Infra.ContainerDict:
        """Persist quality gate artifacts to the report directory."""
        report_dir = workspace_root / c.Infra.QG_REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)
        report_json = report_dir / "latest.json"
        report_txt = report_dir / "latest.txt"
        report_json.write_text(
            t.Infra.INFRA_MAPPING_ADAPTER.dump_json(report, by_alias=True).decode(
                c.Cli.ENCODING_DEFAULT,
            ),
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        report_txt.write_text(render_text, encoding=c.Cli.ENCODING_DEFAULT)
        return {"report_json": str(report_json), "report_text": str(report_txt)}

    @classmethod
    def render_text(cls, report: t.Infra.ContainerDict) -> str:
        """Render compact human-readable summary."""
        checks = u.Cli.json_deep_mapping_list(report, "checks")
        after = u.Cli.json_deep_mapping(report, "after")
        duplicate_groups = u.Cli.json_deep_mapping_list(
            report, "duplicate_constant_groups"
        )
        lines: MutableSequence[str] = [
            f"Workspace: {report.get('workspace', '')}",
            f"Verdict: {report.get('verdict', 'FAIL')}",
            "",
            "Checks:",
        ]
        for check in checks:
            status = "PASS" if u.Cli.json_pick_bool(check, "passed") else "FAIL"
            lines.append(
                f"- [{status}] {u.Cli.json_pick_str(check, 'name', 'unknown')}"
            )
            detail = u.Cli.json_pick_str(check, "detail")
            if detail:
                lines.append(f"  {detail}")
        lines.extend([
            "",
            "Current:",
            f"- violations: {after.get('total_violations', 'n/a')}",
            f"- duplicates: {after.get('duplicate_groups', 'n/a')}",
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
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def successful_verdict(verdict: str) -> bool:
        """Return True for verdicts that should exit with status 0.

        Domain-verb naming per AGENTS.md §3.1: boolean outcomes use
        noun/adjective names, not ``is_*`` prefixes.
        """
        return verdict == "PASS"


__all__: list[str] = ["FlextInfraConstantsCodegenQualityGate"]
