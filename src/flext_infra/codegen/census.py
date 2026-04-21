"""Census service for namespace violation counting and reporting.

Read-only service that counts and classifies namespace violations
across all workspace projects using FlextInfraNamespaceValidator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraNamespaceValidator,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


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
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return r[str].fail(f"census failed: {exc}", exception=exc)
        total_violations = sum(report.total for report in reports)
        total_fixable = sum(report.fixable for report in reports)
        if self.output_format == c.Cli.OutputFormats.JSON:
            payload: t.Infra.MutableInfraMapping = {
                c.Infra.RK_PROJECTS: [report.model_dump() for report in reports],
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
        output_format: str = c.Cli.OutputFormats.JSON,
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
        return self._run_project_census(workspace, projects=projects)

    def _run_project_census(
        self,
        workspace: Path,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[m.Infra.CensusReport]:
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
            FlextInfraNamespaceValidator().validate(
                project.path,
                scan_tests=False,
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
