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

    def __init__(self, workspace_root: Path) -> None:
        """Initialize census service with workspace root."""
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
        self._census_constants_governance(project=project, violations=violations)
        return m.Infra.CensusReport(
            project=project.name,
            violations=violations,
            total=len(violations),
            fixable=sum(1 for v in violations if v.fixable),
        )

    def _census_constants_governance(
        self,
        *,
        project: p.Infra.ProjectInfo,
        violations: list[m.Infra.CensusViolation],
    ) -> None:
        src_dir = project.path / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return
        package_dir: Path | None = None
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                package_dir = child
                break
        if package_dir is None:
            return
        constants_file = package_dir / "constants.py"
        if not constants_file.exists():
            return

        definitions = FlextInfraCodegenConstantDetection.extract_constant_definitions(
            file_path=constants_file,
            project=project.name,
        )

        hardcoded = FlextInfraCodegenConstantDetection.detect_hardcoded_canonicals(
            definitions,
        )
        violations.extend(
            m.Infra.CensusViolation(
                module=definition.file_path,
                rule="NS-003",
                line=definition.line,
                message=(
                    f"Hardcoded canonical value in '{definition.name}' should use parent MRO reference"
                ),
                fixable=True,
            )
            for definition in hardcoded
        )

        all_used_names: set[str] = set()
        discovery = FlextInfraUtilitiesDiscovery()
        projects_result = discovery.discover_projects(self._workspace_root)
        if projects_result.is_success:
            discovered_projects: Sequence[p.Infra.ProjectInfo] = (
                projects_result.unwrap()
            )
            for discovered_project in discovered_projects:
                discovered_src = discovered_project.path / c.Infra.Paths.DEFAULT_SRC_DIR
                if not discovered_src.is_dir():
                    continue
                for py_file in sorted(discovered_src.rglob("*.py")):
                    used_names, _ = (
                        FlextInfraCodegenConstantDetection.scan_constant_usages(
                            file_path=py_file,
                            project=discovered_project.name,
                        )
                    )
                    all_used_names.update(used_names)

        unused_constants = FlextInfraCodegenConstantDetection.detect_unused_constants(
            definitions=definitions,
            all_used_names=all_used_names,
        )
        violations.extend(
            m.Infra.CensusViolation(
                module=unused.file_path,
                rule="NS-004",
                line=unused.line,
                message=f"Unused constant '{unused.name}' can be removed",
                fixable=True,
            )
            for unused in unused_constants
        )

        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name == "constants.py":
                continue
            _, direct_refs = FlextInfraCodegenConstantDetection.scan_constant_usages(
                file_path=py_file,
                project=project.name,
            )
            violations.extend(
                m.Infra.CensusViolation(
                    module=ref.file_path,
                    rule="NS-005",
                    line=ref.line,
                    message=(f"Direct ref {ref.full_ref} should use {ref.alias_ref}"),
                    fixable=True,
                )
                for ref in direct_refs
            )


__all__ = ["FlextInfraCodegenCensus"]
