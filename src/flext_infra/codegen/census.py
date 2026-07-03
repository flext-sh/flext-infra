"""Census service for namespace violation counting and reporting.

Read-only service that counts and classifies namespace violations
across all workspace projects using FlextInfraNamespaceValidator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_core import r, s
from flext_infra import c, m, p
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra.codegen._codegen_constant_visitor import (
    detect_hardcoded_canonicals,
    detect_unused_constants,
    extract_constant_definitions,
    scan_constant_usages,
)
from flext_infra.codegen._codegen_governance import is_rule_fixable
from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator


class FlextInfraCodegenCensus(s[str]):
    """Read-only census service for namespace violation counting."""

    @override
    def execute(self) -> p.Result[str]:
        """Execute the census directly from the validated CLI service model."""
        if self.apply_changes:
            return r[str].fail(
                "census is read-only; use flext-infra codegen auto-fix --apply",
            )
        try:
            reports = self.run()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[str].fail_op("census", exc)
        total_violations = sum(report.total for report in reports)
        total_fixable = sum(report.fixable for report in reports)
        if self.output_format == c.Cli.OutputFormats.JSON:
            payload: t.Infra.MutableInfraMapping = {
                c.Infra.RK_PROJECTS: [report.model_dump() for report in reports],
                "total_violations": total_violations,
                "total_fixable": total_fixable,
            }
            return r[str].ok(t.Infra.INFRA_MAPPING_ADAPTER.dump_json(payload).decode())
        lines: t.MutableSequenceOf[str] = [
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
        output_format: str = c.Cli.OutputFormats.JSON,
        projects: t.SequenceOf[p.Infra.ProjectInfo] | None = None,
    ) -> t.SequenceOf[m.Infra.CensusReport]:
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
        return self._run_project_census(workspace, projects=projects)

    def _run_project_census(
        self,
        workspace: Path,
        *,
        projects: t.SequenceOf[p.Infra.ProjectInfo] | None = None,
    ) -> t.SequenceOf[m.Infra.CensusReport]:
        """Standard path: census all projects in workspace."""
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            projects_result = u.Infra.projects(workspace)
            selected_projects = (
                tuple(projects_result.unwrap()) if projects_result.success else ()
            )
        return [self._census_project(project) for project in selected_projects]

    def _census_project(
        self,
        project: p.Infra.ProjectInfo,
    ) -> m.Infra.CensusReport:
        """Run census on a single project."""
        violations_result = u.Infra.parse_namespace_validation(
            FlextInfraNamespaceValidator().validate_project(
                project.path,
                scan_tests=True,
            ),
        )
        violations = (
            list(violations_result.unwrap()) if violations_result.success else []
        )
        return m.Infra.CensusReport(
            project=project.name,
            violations=list(violations),
            total=len(violations),
            fixable=u.count(violations, lambda v: v.fixable),
        )


__all__: list[str] = ["FlextInfraCodegenCensus"]
