"""Data-driven skill validation service.

Validates workspace skills against rules.yml-based policy gates,
supporting AST-grep and custom rule types with baseline comparison.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import (
    Mapping,
    MutableSequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, r, s, t, u


class FlextInfraSkillValidator(s[bool]):
    """Validates workspace skills using rules.yml policy gates.

    Supports AST-grep rules, custom validator scripts, and baseline
    comparison with per-group and total strategies.
    """

    skill: Annotated[str, m.Field(description="Skill folder name")]
    mode: Annotated[
        c.Infra.OperationMode,
        m.Field(
            description="Validation mode (baseline or strict)",
        ),
    ] = c.Infra.OperationMode.BASELINE

    @staticmethod
    def _render_template(workspace_root: Path, template: str, skill: str) -> Path:
        """Render a skill path template."""
        rendered = template.replace("{skill}", skill)
        candidate = Path(rendered)
        if candidate.is_absolute():
            return candidate
        return (workspace_root / candidate).resolve()

    def _evaluate_single_rule(
        self,
        rule_obj: Mapping[str, t.Infra.InfraValue],
        skill_dir: Path,
        root: Path,
        mode: c.Infra.OperationMode,
        include_globs: t.StrSequence,
        exclude_globs: t.StrSequence,
        counts: t.MutableIntMapping,
        violations: MutableSequence[str],
    ) -> None:
        """Evaluate one rule entry and accumulate counts/violations."""
        rule_id = u.Cli.json_get_str_key(rule_obj, c.Infra.RK_ID)
        rule_type = u.Cli.json_get_str_key(rule_obj, "type")
        group = (
            u.Cli.json_get_str_key(rule_obj, c.Infra.GROUP, default=rule_id) or rule_id
        )
        if rule_type == "ast-grep":
            count = self._run_ast_grep_count(
                rule_obj,
                skill_dir,
                root,
                include_globs,
                exclude_globs,
            )
        elif rule_type == "custom":
            count = self._run_custom_count(rule_obj, skill_dir, root, mode)
        else:
            return
        counts[group] = counts.get(group, 0) + count
        if count > 0:
            label = (
                "ast-grep matches" if rule_type == "ast-grep" else "custom violations"
            )
            violations.append(f"[{rule_id}] {count} {label}")

    def _apply_baseline_comparison(
        self,
        rules: Mapping[str, t.Infra.InfraValue],
        root: Path,
        skill_name: str,
        counts: t.IntMapping,
        total: int,
    ) -> bool:
        """Compare counts against the baseline file and return pass/fail."""
        baseline_obj = u.Cli.json_deep_mapping(
            rules,
            c.Infra.OperationMode.BASELINE.value,
        )
        if not baseline_obj:
            return True
        strategy = str(baseline_obj.get("strategy", c.Infra.RK_TOTAL))
        baseline_path = self._render_template(
            root,
            str(baseline_obj.get(c.Infra.RK_FILE, c.Infra.BASELINE_DEFAULT)),
            skill_name,
        )
        if not baseline_path.exists():
            return True
        bl_data_result = u.Cli.json_read(baseline_path)
        if bl_data_result.failure:
            return True
        bl_data = u.Cli.json_as_mapping(bl_data_result.value)
        bl_counts_raw_map = u.Cli.json_deep_mapping(bl_data, "counts")
        bl_counts: t.MutableIntMapping = {}
        for key_obj, val_obj in bl_counts_raw_map.items():
            if isinstance(val_obj, int):
                bl_counts[str(key_obj)] = int(val_obj)
        if strategy == c.Infra.RK_TOTAL:
            return total <= sum(bl_counts.values())
        return all(
            counts.get(g, 0) <= bl_counts.get(g, 0)
            for g in set(counts) | set(bl_counts)
        )

    def build_report(
        self,
        workspace_root: Path,
        skill_name: str,
        *,
        mode: c.Infra.OperationMode = c.Infra.OperationMode.BASELINE,
        _project_filter: t.StrSequence | None = None,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate a single skill across workspace projects.

        Args:
            workspace_root: Root directory of the workspace.
            skill_name: Name of the skill folder to validate.
            mode: Validation mode ("baseline" or "strict").

        Returns:
            r with ValidationReport.

        """
        try:
            root = workspace_root.resolve()
            skills_dir = root / c.Infra.SKILLS_DIR
            rules_path = skills_dir / skill_name / "rules.yml"
            if not rules_path.exists():
                return r[m.Infra.ValidationReport].ok(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=[f"rules.yml not found for skill '{skill_name}'"],
                        summary=f"no rules.yml for {skill_name}",
                    ),
                )
            rules = u.Cli.yaml_load_mapping(rules_path)
            scan_targets_raw = rules.get("scan_targets", {})
            scan_targets = u.Cli.json_as_mapping(scan_targets_raw)
            if not scan_targets and scan_targets_raw not in ({}, None):
                return r[m.Infra.ValidationReport].fail(
                    f"scan_targets must be a mapping: {rules_path}",
                )
            include_globs = u.Infra.string_list(
                scan_targets.get("include", ["**/*.py"]),
            ) or ["**/*"]
            exclude_globs = u.Infra.string_list(
                scan_targets.get(c.Infra.EXCLUDE, []),
            )
            rules_list_obj = rules.get(c.Infra.RK_RULES, [])
            if not isinstance(rules_list_obj, list):
                return r[m.Infra.ValidationReport].fail("rules must be a list")
            rules_list: t.JsonList = t.Cli.JSON_LIST_ADAPTER.validate_python(
                rules_list_obj,
            )
            counts: t.MutableIntMapping = {}
            violations: MutableSequence[str] = []
            skill_dir = skills_dir / skill_name
            for rule_obj_raw in rules_list:
                rule_obj = u.Cli.json_as_mapping(rule_obj_raw)
                if not rule_obj:
                    continue
                self._evaluate_single_rule(
                    rule_obj,
                    skill_dir,
                    root,
                    mode,
                    include_globs,
                    exclude_globs,
                    counts,
                    violations,
                )
            total = sum(counts.values())
            passed = total == 0 if mode == c.Infra.OperationMode.STRICT else True
            if mode != c.Infra.OperationMode.STRICT:
                passed = self._apply_baseline_comparison(
                    rules,
                    root,
                    skill_name,
                    counts,
                    total,
                )
            summary = (
                f"{skill_name}: {total} violations, {('PASS' if passed else 'FAIL')}"
            )
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=passed,
                    violations=violations,
                    summary=summary,
                ),
            )
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            return r[m.Infra.ValidationReport].fail(
                f"skill validation failed: {exc}",
            )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the skill-validation CLI flow."""
        report_result = self.build_report(
            self.workspace_root,
            self.skill,
            mode=self.mode,
        )
        if report_result.failure:
            return r[bool].fail(report_result.error or "skill validation failed")
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)

    def _run_ast_grep_count(
        self,
        rule: Mapping[str, t.Infra.InfraValue],
        skill_dir: Path,
        project_path: Path,
        include_globs: t.StrSequence,
        exclude_globs: t.StrSequence,
    ) -> int:
        """Run an ast-grep rule and return match count."""
        rule_file_raw = u.Cli.json_get_str_key(rule, c.Infra.RK_FILE)
        if not rule_file_raw:
            return 0
        rule_file = Path(rule_file_raw)
        if not rule_file.is_absolute():
            rule_file = (skill_dir / rule_file_raw).resolve()
        if not rule_file.exists():
            return 0
        cmd = [
            c.Infra.SG,
            c.Infra.SCAN,
            "--rule",
            str(rule_file),
            "--json=stream",
        ]
        for pat in include_globs:
            cmd.extend(["--globs", pat])
        for pat in exclude_globs:
            cmd.extend(["--globs", f"!{pat}"])
        cmd.append(str(project_path))
        result_wrapper = u.Cli.run_raw(
            cmd, cwd=project_path, timeout=c.Infra.TIMEOUT_DEFAULT
        )
        if result_wrapper.failure:
            return 0
        result: m.Cli.CommandOutput = result_wrapper.value
        if result.exit_code not in {0, 1}:
            return 0
        count = 0
        for raw_line in (result.stdout or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parsed_line_result = u.Cli.json_parse(line)
            if parsed_line_result.success:
                count += 1
        return count

    @staticmethod
    def _parse_violation_count(stdout: str) -> int:
        """Parse violation count from JSON-line stdout of a custom script."""
        count = 0
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            payload_result = u.Cli.json_parse(line)
            if payload_result.success and isinstance(payload_result.value, Mapping):
                payload = payload_result.value
                maybe = payload.get("violation_count", payload.get("count", 0))
                if isinstance(maybe, int):
                    count += maybe
        return count

    def _run_custom_count(
        self,
        rule: Mapping[str, t.Infra.InfraValue],
        skill_dir: Path,
        project_path: Path,
        mode: c.Infra.OperationMode,
    ) -> int:
        """Run a custom rule script and return violation count."""
        script_raw = u.Cli.json_get_str_key(rule, "script")
        if not script_raw:
            return 0
        script = Path(script_raw)
        if not script.is_absolute():
            script = (skill_dir / script_raw).resolve()
        if not script.exists():
            return 0
        cmd: MutableSequence[str] = (
            [sys.executable, str(script)]
            if script.suffix == c.Infra.EXT_PYTHON
            else [str(script)]
        )
        cmd.extend(["--workspace", str(project_path)])
        if bool(rule.get("pass_mode")):
            cmd.extend(["--mode", mode.value])
        result_wrapper = u.Cli.run_raw(
            cmd, cwd=project_path, timeout=c.Infra.TIMEOUT_DEFAULT
        )
        if result_wrapper.failure:
            return 0
        result: m.Cli.CommandOutput = result_wrapper.value
        count = self._parse_violation_count(result.stdout or "")
        if result.exit_code == 1:
            count = max(count, 1)
        return count


__all__: list[str] = ["FlextInfraSkillValidator"]
