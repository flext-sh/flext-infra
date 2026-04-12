"""Validate silent failure sentinels across governed Python projects."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import (
    FlextInfraSilentFailureDetector,
    m,
    p,
    s,
    u,
)


class FlextInfraSilentFailureValidator(s[bool]):
    """Validate that failure paths do not collapse into sentinel returns."""

    project_filter: Annotated[
        str | None,
        Field(default=None, description="Project filter (comma-separated)"),
    ] = None

    include_tests: Annotated[
        bool,
        Field(default=True, description="Scan test trees in addition to source trees"),
    ] = True

    def _selected_projects(
        self,
        projects: Sequence[p.Infra.ProjectInfo],
    ) -> Sequence[p.Infra.ProjectInfo]:
        if self.project_filter is None:
            return projects
        selected = {
            item.strip() for item in self.project_filter.split(",") if item.strip()
        }
        return [project for project in projects if project.name in selected]

    def build_report(self) -> r[m.Infra.ValidationReport]:
        """Build one validation report for the selected workspace projects."""
        projects_result = u.Infra.discover_codegen_projects(self.workspace_root)
        if projects_result.failure:
            return r[m.Infra.ValidationReport].fail(
                projects_result.error or "project discovery failed",
            )
        issues: MutableSequence[str] = []
        projects = self._selected_projects(projects_result.value)
        for project in projects:
            iter_result = u.Infra.iter_python_files(
                project.path,
                project_roots=[project.path],
                include_tests=self.include_tests,
            )
            if iter_result.failure:
                return r[m.Infra.ValidationReport].fail(
                    iter_result.error
                    or f"python file iteration failed for {project.name}",
                )
            rope_project = u.Infra.init_rope_project(project.path)
            try:
                for file_path in iter_result.value:
                    issues.extend(
                        issue.formatted
                        for issue in FlextInfraSilentFailureDetector.detect_file(
                            m.Infra.DetectorContext(
                                file_path=file_path,
                                project_root=project.path,
                                rope_project=rope_project,
                            )
                        )
                    )
            finally:
                rope_project.close()
        passed = len(issues) == 0
        summary = (
            "silent failure validation passed"
            if passed
            else f"silent failure validation found {len(issues)} issue(s)"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=list(issues),
                summary=summary,
            ),
        )

    @override
    def execute(self) -> r[bool]:
        """Execute silent-failure validation and collapse the report to `r[bool]`."""
        report_result = self.build_report()
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "silent failure validation failed"
            )
        report = report_result.value
        if report.passed:
            return r[bool].ok(True)
        details = "\n".join([report.summary, *report.violations[:20]])
        return r[bool].fail(details)


__all__: list[str] = ["FlextInfraSilentFailureValidator"]
