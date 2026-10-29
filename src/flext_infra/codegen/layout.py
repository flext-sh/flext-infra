"""Extracted facade class for layout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, override

from flext_infra import m, p, r, u
from flext_infra.codegen._layout import (
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
)
from flext_infra.codegen.execution import FlextInfraCodegenExecution


class FlextInfraCodegenLayout(
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
    FlextInfraCodegenExecution[str],
):
    """Facade for layout."""

    project_name: Annotated[
        str | None,
        m.Field(default=None, description="Single project to conform"),
    ] = None

    @override
    def execute(self) -> p.Result[str]:
        """Run check (default) or apply across the selected projects.

        Returns:
            The layout summary or the first selection, repair or residual failure.

        """
        selected = self._project_dirs()
        if selected.failure:
            return r[str].fail(selected.error or "project selection failed")
        reports: MutableSequence[m.Infra.LayoutProjectReport] = []
        for project_dir in selected.value:
            planned = self.plan_project(project_dir)
            if self.effective_dry_run:
                reports.append(planned)
                continue
            applied = self.apply_project(project_dir, planned)
            if applied.failure:
                return r[str].fail(
                    applied.error or f"layout apply failed: {project_dir.name}",
                )
            residual = self.plan_project(project_dir)
            unresolved = tuple(
                finding.path
                for finding in residual.actionable
                if finding.status == "planned"
            )
            if unresolved:
                return r[str].fail(
                    f"layout apply did not reach a fixed point in "
                    f"{project_dir.name}: {', '.join(unresolved)}",
                )
            reports.append(applied.value)
        output = self._render_output(reports)
        if self.effective_dry_run:
            blocking = [
                finding.message for report in reports for finding in report.actionable
            ]
            if blocking:
                return r[str].fail(f"layout violations: {'; '.join(blocking)}")
        return r[str].ok(output)

    def check_project(self, project_dir: Path) -> m.Infra.LayoutProjectReport:
        """Report layout violations for one project without writing.

        Returns:
            The resulting ``m.Infra.LayoutProjectReport``.

        """
        return self.plan_project(project_dir)

    def _project_dirs(self) -> p.Result[tuple[Path, ...]]:
        """Elect the checked projects from the declared selection.

        Returns:
            The selected project directories or the selection failure.

        """
        if self.project_name is not None:
            candidate = self.repository_root / self.project_name
            if candidate.is_dir():
                return r[tuple[Path, ...]].ok((candidate,))
            return r[tuple[Path, ...]].fail(
                f"project not found in workspace: {self.project_name}",
            )
        discovered = u.Infra.projects(self.repository_root)
        if discovered.success and discovered.value:
            return r[tuple[Path, ...]].ok(
                tuple(project.path for project in discovered.value),
            )
        if self.repository_root.is_dir():
            return r[tuple[Path, ...]].ok((self.repository_root,))
        return r[tuple[Path, ...]].fail("no projects discovered")

    def _render_output(
        self,
        reports: Sequence[m.Infra.LayoutProjectReport],
    ) -> str:
        """Render the text or JSON summary for the collected reports.

        Returns:
            The reports rendered in the selected output format.

        """
        if self.output_format == "json":
            return m.Infra.LayoutRunReport(
                reports=tuple(reports),
            ).model_dump_json()
        lines: MutableSequence[str] = []
        mode = "CHECK" if self.effective_dry_run else "APPLY"
        for report in reports:
            lines.append(f"[{mode}] {report.project}")
            for finding in report.findings:
                lines.append(f"  {finding.rule}: {finding.message}")
            if not report.findings:
                lines.append("  layout canonical: no findings")
        actionable = sum(len(report.actionable) for report in reports)
        applied = sum(report.applied_count for report in reports)
        lines.append(
            f"{len(reports)} project(s), {actionable} actionable finding(s), "
            f"{applied} applied",
        )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraCodegenLayout"]
