"""Census per-module inventory + workspace-report assembly — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, p, u
from flext_infra.refactor._census import (
    FlextInfraRefactorCensusProject,
    FlextInfraRefactorCensusRemoval,
)


class FlextInfraRefactorCensusCollect(
    FlextInfraRefactorCensusRemoval,
    FlextInfraRefactorCensusProject,
):
    """Inventory one module and assemble the WorkspaceReport."""

    @staticmethod
    def project_name_for_module(
        module: p.Infra.RopeModuleIndexEntry,
        convention: p.Infra.RopeModuleConvention,
    ) -> str:
        """Resolve the project owning an inventoried module.

        Returns:
            The convention's project name or the module's project-root name.

        """
        layout = convention.project_layout
        if layout is not None:
            return layout.project_name
        if module.project_root is not None:
            return module.project_root.name
        return ""

    def _scan_module(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        module: p.Infra.RopeModuleIndexEntry,
        scan_config: p.Infra.ScanConfig,
        *,
        findings: p.Infra.ScanFindings,
    ) -> None:
        """Inventory one module, accumulating its selected objects per project.

        A Rope failure on a module escapes with its cause: a census that skips
        the modules it could not read reports a partial workspace as whole.
        """
        convention = rope.convention(module.file_path)
        project = self.project_name_for_module(module, convention)
        if not project:
            return
        findings.report_projects.add(project)
        objects = tuple(
            item
            for item in rope.objects(
                module.file_path,
                include_local_scopes=scan_config.include_local_scopes,
                include_references=scan_config.include_object_references,
            )
            if self._include_object(
                item,
                selected_families=scan_config.selected_families,
                selected_kinds=scan_config.selected_kinds,
            )
        )
        if objects:
            findings.project_objects.setdefault(project, []).extend(objects)

    def _assemble_report(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        *,
        source_preview: p.Infra.SourcePreview,
        findings: p.Infra.ScanFindings,
        scan_config: p.Infra.ScanConfig,
        census_kinds: frozenset[str] | None = None,
    ) -> p.Infra.WorkspaceReport:
        """Aggregate per-project inventories into the workspace census report.

        In dry-run the removal candidates are previewed through the gates and
        only the ones that pass stay candidates.

        Returns:
            The resulting ``m.Infra.WorkspaceReport``.

        """
        duplicates = self.duplicate_groups(tuple(findings.project_objects.values()))
        duplicate_keys = frozenset(
            self._object_key(item)
            for group in duplicates
            if not group.semantic_candidate
            for item in group.definitions[1:]
        )
        project_reports = tuple(
            self._project_report(
                project,
                findings=findings,
                duplicate_keys=duplicate_keys,
                scan_config=scan_config,
                source_project=rope.rope_project,
            )
            for project in sorted(
                findings.report_projects | set(findings.project_objects),
            )
        )
        if self.effective_dry_run:
            project_reports = self._validated_project_reports(
                rope, project_reports, source_preview=source_preview
            )
        sources = {
            Path(resource.real_path): resource.read()
            for resource in rope.rope_project.get_python_files()
        }
        alias_rows, duplicate_rows, shortest_rows = self.extermination_rows(
            sources=sources,
            objects=tuple(
                item
                for entries in findings.project_objects.values()
                for item in entries
            ),
            duplicates=duplicates,
            census_kinds=census_kinds,
        )
        fixable_rows = tuple(
            row for row in (*alias_rows, *duplicate_rows, *shortest_rows) if row.fixable
        )
        fix_plan = m.Infra.CensusFixPlan.model_validate({
            "alias": (tuple(row for row in alias_rows if row.fixable)),
            "duplicate": (tuple(row for row in duplicate_rows if row.fixable)),
            "shortest_form": (tuple(row for row in shortest_rows if row.fixable)),
            "commands": (
                tuple(sorted({self.cure_command(row.cure) for row in fixable_rows}))
            ),
            "expected_rescan": (len(fixable_rows)),
        })
        return m.Infra.WorkspaceReport(
            protocol_placement=u.Infra.protocol_contract_census(
                rope,
                sources=sources,
                objects=tuple(
                    item
                    for entries in findings.project_objects.values()
                    for item in entries
                ),
            ),
            projects=project_reports,
            total_objects=sum(report.objects_total for report in project_reports),
            total_violations=sum(report.violations_total for report in project_reports),
            duplicates=duplicates,
            unused_count=sum(report.unused_count for report in project_reports),
            removal_candidate_count=sum(
                report.removal_candidate_count for report in project_reports
            ),
            removal_candidates=tuple(
                candidate
                for report in project_reports
                for candidate in report.removal_candidates
            ),
            alias_census=alias_rows,
            duplicate_census=duplicate_rows,
            shortest_form_census=shortest_rows,
            census_fix_plan=fix_plan,
        )


__all__: list[str] = ["FlextInfraRefactorCensusCollect"]
