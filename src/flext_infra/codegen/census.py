"""Census service for namespace violation counting and reporting.

Read-only service that counts and classifies namespace violations
across all workspace projects using FlextInfraNamespaceValidator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_core import r, s
from flext_infra import (
    FlextInfraNamespaceValidator,
    FlextInfraUtilitiesDiscovery,
    c,
    m,
    p,
)
from flext_infra.codegen._codegen_constant_visitor import (
    FlextInfraCodegenConstantDetection,
)
from flext_infra.codegen._codegen_governance import FlextInfraCodegenGovernance


class FlextInfraCodegenCensus(s[bool]):
    """Read-only census service for namespace violation counting."""

    def __init__(
        self, workspace_root: Path, class_to_analyze: str | None = None
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
        return FlextInfraCodegenGovernance.is_rule_fixable(rule, module)

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
    ) -> list[m.Infra.CensusReport]:
        """Run census on all projects in workspace.

        Returns:
            List of CensusReport models, one per scanned project.

        """
        _ = output_format
        workspace = (
            workspace_root if workspace_root is not None else self._workspace_root
        )
        discovery = FlextInfraUtilitiesDiscovery()
        projects_result = discovery.discover_projects(workspace)
        if not projects_result.is_success:
            return []
        reports: list[m.Infra.CensusReport] = []
        discovered: Sequence[p.Infra.ProjectInfo] = projects_result.unwrap()
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
        violations: list[m.Infra.CensusViolation] = []
        if result.is_success:
            report: m.Infra.ValidationReport = result.unwrap()
            for violation_str in report.violations:
                violation = self._parse_violation(violation_str)
                if violation is not None:
                    violations.append(violation)

        # Census constants and objects
        src_dir = project.path / c.Infra.Paths.DEFAULT_SRC_DIR
        if src_dir.is_dir():
            # Extract all constant definitions (any class with Final)
            all_defs = (
                FlextInfraCodegenConstantDetection.extract_all_constant_definitions(
                    src_dir.parent,
                    frozenset({".mypy_cache", "__pycache__"}),
                )
            )

            # Detect duplicates
            flat_defs: list[m.Infra.ConstantDefinition] = []
            for defs in all_defs.values():
                flat_defs.extend(defs)

            duplicates = FlextInfraCodegenConstantDetection.detect_duplicate_constants(
                flat_defs,
            )

            # Count usage
            all_usage_map = FlextInfraCodegenConstantDetection.scan_all_constant_usages(
                src_dir.parent,
                frozenset({".mypy_cache", "__pycache__"}),
            )

            # Add census info to violations as info (not violations, just counts)
            unused = FlextInfraCodegenConstantDetection.detect_unused_constants(
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
                )
            )

        # Census class attributes with MRO (if class_to_analyze provided or default)
        class_to_analyze = self._class_to_analyze or (
            "flext_core.FlextConstants" if project.name == "flext-core" else None
        )
        if class_to_analyze:
            class_attrs = (
                FlextInfraCodegenConstantDetection.extract_class_attributes_with_mro(
                    class_to_analyze,
                )
            )
            if class_attrs:
                # Extract simple class name from full path
                simple_class_name = class_to_analyze.rsplit(".", 1)[-1]
                used_attrs, _ = (
                    FlextInfraCodegenConstantDetection.scan_class_attribute_usages(
                        self._workspace_root,
                        simple_class_name,
                        frozenset({".mypy_cache", "__pycache__"}),
                    )
                )
                unused_attrs = len(class_attrs) - len(used_attrs)
                violations.append(
                    m.Infra.CensusViolation(
                        module=f"census:{simple_class_name}",
                        rule="CENSUS",
                        line=0,
                        message=(
                            f"{simple_class_name}: {len(class_attrs)} attributes (with MRO), "
                            f"{len(used_attrs)} used, {unused_attrs} unused"
                        ),
                        fixable=False,
                    )
                )

        return m.Infra.CensusReport(
            project=project.name,
            violations=violations,
            total=len(violations),
            fixable=sum(1 for v in violations if v.fixable),
        )


__all__ = ["FlextInfraCodegenCensus"]
