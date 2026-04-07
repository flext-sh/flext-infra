"""Census service for namespace violation counting and reporting.

Read-only service that counts and classifies namespace violations
across all workspace projects using FlextInfraNamespaceValidator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import (
    FlextInfraCommandContext,
    FlextInfraNamespaceValidator,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraCodegenCensus(FlextInfraCommandContext[str]):
    """Read-only census service for namespace violation counting."""

    class_to_analyze: Annotated[
        str | None,
        Field(
            default=None,
            description="Full class path to analyze (e.g. flext_core.FlextConstants)",
        ),
    ] = None

    @staticmethod
    def _is_fixable(*, rule: str, module: str, message: str) -> bool:
        _ = message
        return u.Infra.is_rule_fixable(rule, module)

    @staticmethod
    def _parse_violation(violation_str: str) -> m.Infra.CensusViolation | None:
        """Parse a violation string into a CensusViolation model."""
        match = c.Infra.VIOLATION_PATTERN.match(violation_str)
        if match is None:
            return None
        rule = match.group("rule")
        fixable = FlextInfraCodegenCensus._is_fixable(
            rule=rule,
            module=match.group("module"),
            message=match.group("message"),
        )
        return m.Infra.CensusViolation(
            module=match.group("module"),
            rule=rule,
            line=int(match.group("line")),
            message=match.group("message"),
            fixable=fixable,
        )

    @override
    def execute(self) -> r[str]:
        """Execute the census directly from the validated CLI service model."""
        reports = self.run()
        total_violations = sum(report.total for report in reports)
        total_fixable = sum(report.fixable for report in reports)
        if self.output_format == "json":
            payload: t.Infra.MutableInfraMapping = {
                c.Infra.ReportKeys.PROJECTS: [
                    report.model_dump() for report in reports
                ],
                "total_violations": total_violations,
                "total_fixable": total_fixable,
            }
            return r[str].ok(t.Infra.INFRA_MAPPING_ADAPTER.dump_json(payload).decode())
        lines: MutableSequence[str] = [
            (
                f"  {report.project}: {report.total} violations"
                f" ({report.fixable} fixable)"
            )
            for report in reports
            if report.total > 0
        ]
        lines.append(
            (
                f"Total: {total_violations} violations ({total_fixable} fixable)"
                f" across {len(reports)} projects"
            ),
        )
        return r[str].ok("\n".join(lines))

    def run(
        self,
        workspace_root: Path | None = None,
        *,
        output_format: str = "json",
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.CensusReport]:
        """Run census on all projects in workspace.

        Args:
            workspace_root: Override workspace root (defaults to self.workspace_root).
            output_format: Unused, kept for API compat.
            projects: Pre-discovered projects to skip redundant discovery.

        Returns:
            List of CensusReport models, one per scanned project.

        """
        _ = output_format
        workspace = workspace_root or self.workspace_root
        if self.class_to_analyze:
            return self._run_class_analysis(workspace)
        return self._run_project_census(workspace, projects=projects)

    def _run_class_analysis(
        self,
        workspace: Path,
    ) -> Sequence[m.Infra.CensusReport]:
        """Fast path: analyze a single class and return a pseudo-project report."""
        class_name = self.class_to_analyze or ""
        simple_class_name = class_name.rsplit(".", 1)[-1]
        census_data = u.Infra.analyze_class_object_census(
            class_name,
            workspace,
            frozenset({
                ".mypy_cache",
                c.Infra.Dunders.PYCACHE,
                c.Infra.Git.DIR,
                ".reports",
            }),
            max_files=1000,
        )
        if not census_data:
            return []
        total_objs_val = census_data.get("total_objects", 0)
        total_objs = int(total_objs_val) if isinstance(total_objs_val, int) else 0
        total_used_val = census_data.get("total_used", 0)
        total_used = int(total_used_val) if isinstance(total_used_val, int) else 0
        total_unused = total_objs - total_used
        type_detail = self._format_type_stats(census_data)
        return [
            m.Infra.CensusReport(
                project=f"class-analysis:{simple_class_name}",
                violations=[
                    m.Infra.CensusViolation(
                        module=f"census:{simple_class_name}",
                        rule="CENSUS",
                        line=0,
                        message=(
                            f"{simple_class_name}: {total_objs} objects "
                            f"(w/ MRO), {total_used} used, "
                            f"{total_unused} unused{type_detail}"
                        ),
                        fixable=False,
                    ),
                ],
                total=1,
                fixable=0,
            ),
        ]

    @staticmethod
    def _format_type_stats(
        census_data: Mapping[str, t.Infra.InfraValue],
    ) -> str:
        """Format top-3 type stats from census data into a bracket-delimited string."""
        by_type_val = census_data.get("by_type", {})
        by_type: Mapping[str, t.Infra.InfraValue] = (
            by_type_val if u.is_mapping(by_type_val) else {}
        )
        type_stats: MutableSequence[str] = []
        if by_type:
            for type_key in sorted(by_type.keys())[:3]:
                type_info_val = by_type[type_key]
                type_info = u.Cli.toml_as_mapping(type_info_val)
                if type_info is None:
                    continue
                cnt_val = type_info.get("total", 0)
                cnt = int(cnt_val) if isinstance(cnt_val, int) else 0
                type_stats.append(f"{type_key}:{cnt}")
        return f" [{', '.join(type_stats)}]" if type_stats else ""

    def _run_project_census(
        self,
        workspace: Path,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.CensusReport]:
        """Standard path: census all projects in workspace."""
        if projects is None:
            projects_result = u.Infra.discover_projects(workspace)
            if not projects_result.is_success:
                return []
            discovered: Sequence[p.Infra.ProjectInfo] = projects_result.unwrap()
        else:
            discovered = projects
        reports: MutableSequence[m.Infra.CensusReport] = []
        for project in discovered:
            if project.name in c.Infra.EXCLUDED_PROJECTS:
                continue
            report = self._census_project(project)
            reports.append(report)
        return reports

    def _census_project(
        self,
        project: p.Infra.ProjectInfo,
    ) -> m.Infra.CensusReport:
        """Run census on a single project."""
        validator = FlextInfraNamespaceValidator()
        result = validator.validate(project.path, scan_tests=False)
        violations: MutableSequence[m.Infra.CensusViolation] = []
        if result.is_success:
            report: m.Infra.ValidationReport = result.unwrap()
            for violation_str in report.violations:
                violation = self._parse_violation(violation_str)
                if violation is not None:
                    violations.append(violation)
        src_dir = project.path / c.Infra.Paths.DEFAULT_SRC_DIR
        if src_dir.is_dir() and not self.class_to_analyze:
            self._census_constants(src_dir, violations)
        return m.Infra.CensusReport(
            project=project.name,
            violations=list(violations),
            total=len(violations),
            fixable=u.count(violations, lambda v: v.fixable),
        )

    @staticmethod
    def _census_constants(
        src_dir: Path,
        violations: MutableSequence[m.Infra.CensusViolation],
    ) -> None:
        """Analyze constant definitions, duplicates, and usage for a project."""
        skip_dirs = frozenset({".mypy_cache", c.Infra.Dunders.PYCACHE})
        all_defs = u.Infra.extract_all_constant_definitions(
            src_dir.parent,
            skip_dirs,
        )
        flat_defs: MutableSequence[m.Infra.ConstantDefinition] = []
        for defs in all_defs.values():
            flat_defs.extend(defs)
        duplicates: Sequence[m.Infra.DuplicateConstantGroup] = (
            u.Infra.detect_duplicate_constants(flat_defs)
        )
        all_usage_map: Mapping[str, Sequence[t.Infra.StrIntPair]] = (
            u.Infra.scan_all_constant_usages(src_dir.parent, skip_dirs)
        )
        unused = u.Infra.detect_unused_constants(
            flat_defs,
            set(all_usage_map.keys()),
        )
        violations.append(
            m.Infra.CensusViolation(
                module="census:constants",
                rule="CENSUS",
                line=0,
                message=(
                    f"Constants: {len(flat_defs)} defined, "
                    f"{len(flat_defs) - len(unused)} used, "
                    f"{len(duplicates)} duplicate groups"
                ),
                fixable=False,
            ),
        )


__all__ = ["FlextInfraCodegenCensus"]
