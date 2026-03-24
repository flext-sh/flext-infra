"""Census service for namespace violation counting and reporting.

Read-only service that counts and classifies namespace violations
across all workspace projects using FlextInfraNamespaceValidator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_core import r, s

from flext_infra import (
    FlextInfraNamespaceValidator,
    c,
    m,
    p,
    u,
)


class FlextInfraCodegenCensus(s[bool]):
    """Read-only census service for namespace violation counting."""

    def __init__(
        self,
        workspace_root: Path,
        class_to_analyze: str | None = None,
    ) -> None:
        """Initialize census service with workspace root.

        Args:
            workspace_root: Root directory of workspace
            class_to_analyze: Optional class path to analyze (e.g., 'flext_core.FlextConstants')

        """
        super().__init__(
            config_type=None,
            config_overrides=None,
            initial_context=None,
            subproject=None,
            services=None,
            factories=None,
            resources=None,
            container_overrides=None,
            wire_modules=None,
            wire_packages=None,
            wire_classes=None,
        )
        self._workspace_root: Path = workspace_root
        self._class_to_analyze: str | None = class_to_analyze

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
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() directly")

    def run(
        self,
        workspace_root: Path | None = None,
        *,
        output_format: str = "json",
    ) -> Sequence[m.Infra.CensusReport]:
        """Run census on all projects in workspace.

        Returns:
            List of CensusReport models, one per scanned project.

        """
        _ = output_format
        workspace = (
            workspace_root if workspace_root is not None else self._workspace_root
        )

        # If analyzing a specific class, do ONLY that (fast path)
        if self._class_to_analyze:
            simple_class_name = self._class_to_analyze.rsplit(".", 1)[-1]
            census_data = u.Infra.analyze_class_object_census(
                self._class_to_analyze,
                workspace,
                frozenset({".mypy_cache", "__pycache__", ".git", ".reports"}),
                max_files=1000,  # Limited for speed
            )
            if census_data:
                # Create a pseudo-project report for the analyzed class
                total_objs_val = census_data.get("total_objects", 0)
                total_objs = (
                    int(total_objs_val) if isinstance(total_objs_val, int) else 0
                )
                total_used_val = census_data.get("total_used", 0)
                total_used = (
                    int(total_used_val) if isinstance(total_used_val, int) else 0
                )
                total_unused = total_objs - total_used
                by_type_val = census_data.get("by_type", {})
                by_type: Mapping[str, t.Infra.InfraValue] = (
                    by_type_val if isinstance(by_type_val, dict) else {}
                )
                type_stats: MutableSequence[str] = []
                if isinstance(by_type, dict):
                    for t in sorted(by_type.keys())[:3]:
                        type_info_val = by_type[t]
                        if isinstance(type_info_val, dict):
                            cnt_val = type_info_val.get("total", 0)
                            cnt = int(cnt_val) if isinstance(cnt_val, int) else 0
                            type_stats.append(f"{t}:{cnt}")
                type_detail = f" [{', '.join(type_stats)}]" if type_stats else ""

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
            return []

        # Standard path: analyze all projects
        projects_result = u.Infra.discover_projects(workspace)
        if not projects_result.is_success:
            return []
        reports: MutableSequence[m.Infra.CensusReport] = []
        discovered: Sequence[p.Infra.ProjectInfo] = projects_result.unwrap()
        for project in discovered:
            if project.name in c.Infra.EXCLUDED_PROJECTS:
                continue
            report = self._census_project(project, None)
            reports.append(report)
        return reports

    def _census_project(
        self,
        project: p.Infra.ProjectInfo,
        class_analysis: Mapping[
            str,
            str | Mapping[str, int | Mapping[str, int | Mapping[str, int]]],
        ]
        | None = None,
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

        # Census constants and objects (skip if class_to_analyze is set to speed up)
        src_dir = project.path / c.Infra.Paths.DEFAULT_SRC_DIR
        if src_dir.is_dir() and not self._class_to_analyze:
            # Extract all constant definitions (any class with Final)
            all_defs = u.Infra.extract_all_constant_definitions(
                src_dir.parent,
                frozenset({".mypy_cache", "__pycache__"}),
            )

            # Detect duplicates
            flat_defs: MutableSequence[m.Infra.ConstantDefinition] = []
            for defs in all_defs.values():
                flat_defs.extend(defs)

            duplicates: Sequence[m.Infra.DuplicateConstantGroup] = (
                u.Infra.detect_duplicate_constants(
                    flat_defs,
                )
            )

            # Count usage
            all_usage_map: Mapping[str, Sequence[tuple[str, int]]] = (
                u.Infra.scan_all_constant_usages(
                    src_dir.parent,
                    frozenset({".mypy_cache", "__pycache__"}),
                )
            )

            # Add census info to violations as info (not violations, just counts)
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

        # Census class objects (generic - works for any class)
        if class_analysis and project.name == "flexcore":
            try:
                class_name_str = str(class_analysis.get("class_name", "Unknown"))
                census_data_obj_raw_val = class_analysis.get("census_data")
                if isinstance(census_data_obj_raw_val, dict):
                    census_data_obj: Mapping[
                        str,
                        int | Mapping[str, int | Mapping[str, int]],
                    ] = census_data_obj_raw_val
                else:
                    census_data_obj = {}

                total_objs_val = census_data_obj.get("total_objects", 0)
                total_objs = (
                    int(total_objs_val) if isinstance(total_objs_val, int) else 0
                )
                total_used_val = census_data_obj.get("total_used", 0)
                total_used = (
                    int(total_used_val) if isinstance(total_used_val, int) else 0
                )
                total_unused_val = census_data_obj.get("total_unused", 0)
                total_unused = (
                    int(total_unused_val) if isinstance(total_unused_val, int) else 0
                )

                # Build type breakdown
                type_breakdown = census_data_obj.get("by_type", {})
                type_stats: MutableSequence[str] = []
                if isinstance(type_breakdown, dict):
                    for type_name in sorted(type_breakdown.keys())[:3]:
                        type_info_val = type_breakdown[type_name]
                        if isinstance(type_info_val, dict):
                            cnt_val = type_info_val.get("total", 0)
                            cnt = int(cnt_val) if isinstance(cnt_val, int) else 0
                            type_stats.append(f"{type_name}:{cnt}")
                type_detail = f" [{', '.join(type_stats)}]" if type_stats else ""

                violations.append(
                    m.Infra.CensusViolation(
                        module=f"census:{class_name_str}",
                        rule="CENSUS",
                        line=0,
                        message=(
                            f"{class_name_str}: {total_objs} objects (w/ MRO), "
                            f"{total_used} used, {total_unused} unused{type_detail}"
                        ),
                        fixable=False,
                    ),
                )
            except (ValueError, TypeError, AttributeError):
                pass

        return m.Infra.CensusReport(
            project=project.name,
            violations=violations,
            total=len(violations),
            fixable=sum(1 for v in violations if v.fixable),
        )


__all__ = ["FlextInfraCodegenCensus"]
