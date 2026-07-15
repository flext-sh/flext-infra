"""Direct constants consolidation command service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra import c, config, m, p, t, u
from flext_infra.base import s
from flext_infra.codegen._consolidator_steps import (
    FlextInfraCodegenConsolidatorStepsMixin,
)
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


class FlextInfraCodegenConsolidator(s[str], FlextInfraCodegenConsolidatorStepsMixin):
    """Consolidate inline constants into canonical ``c.*`` references."""

    project_name: Annotated[
        str | None,
        m.Field(alias="project", description="Single project to consolidate"),
    ] = None

    @override
    def execute(self) -> p.Result[str]:
        """Execute constants consolidation with normalized command context."""
        output_lines: t.MutableSequenceOf[str] = (
            ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
        )
        found = applied = failed = 0
        file_results: t.MutableSequenceOf[m.Infra.ConsolidatorFileResult] = []

        with FlextInfraRopeWorkspace.open_workspace(self.workspace_root) as rope:
            projects_result = self._selected_projects(rope)
            if projects_result.failure:
                return r[str].fail("Failed to discover projects")
            selected_projects = projects_result.unwrap()

            for project in selected_projects:
                project_layout = u.Infra.layout(project.path)
                if project_layout is None or not project_layout.init_path.is_file():
                    continue

                constants_file = project_layout.package_dir / c.Infra.CONSTANTS_PY
                value_map_result = self._build_value_map_from_constants_file(
                    constants_file
                )
                if value_map_result.failure:
                    return r[str].fail(
                        value_map_result.error or "constants file read failed"
                    )
                value_map = value_map_result.value
                if not value_map:
                    continue

                project_files = self._project_python_files(project.path)
                if project_files.failure:
                    return r[str].fail(
                        project_files.error or "project python file discovery failed"
                    )
                for python_file in project_files.value:
                    scanned = self._scan_file(rope.rope_project, python_file, value_map)
                    if scanned is None:
                        continue
                    resource, source, matches = scanned
                    found += len(matches)
                    rel_path = python_file.relative_to(self.workspace_root)
                    if self.dry_run:
                        output_lines.extend(
                            (
                                f"  {rel_path}:{symbol.line}  "
                                f"{symbol.name} = {value} -> {ref}"
                            )
                            for symbol, ref, value in matches
                        )
                        continue
                    ok, changes, lines = self._apply_and_validate(
                        rope.rope_project,
                        resource,
                        python_file,
                        self.workspace_root,
                        project_layout.package_name,
                        source,
                        matches,
                    )
                    output_lines.extend(lines)
                    file_results.append(
                        m.Infra.ConsolidatorFileResult(
                            file=str(rel_path),
                            status="applied" if ok else "reverted",
                            changes=tuple(changes),
                        )
                    )
                    if ok:
                        applied += len(changes)
                    else:
                        failed += 1

        summary = (
            f"Found {found} canonical matches across {len(selected_projects)} projects"
            if self.dry_run
            else f"Applied {applied} replacements, {failed} files reverted"
        )
        output_lines.extend(("", summary))
        if self.output_format == c.Cli.OutputFormats.JSON:
            report = m.Infra.ConsolidatorReport(
                total_found=found,
                total_applied=applied,
                total_failed=failed,
                files=tuple(file_results),
            )
            return r[str].ok(report.model_dump_json())
        return r[str].ok("\n".join(output_lines))

    def _project_python_files(self, project_root: Path) -> p.Result[t.SequenceOf[Path]]:
        """Return governed Python files for one project consolidation pass."""
        constants_directory = c.Infra.FAMILY_DIRECTORIES["c"]
        try:
            files = {
                path
                for root_name in config.Infra.rope_index.roots
                for path in u.Infra.iter_directory_python_files(
                    project_root / root_name
                )
                if constants_directory not in path.parts
            }
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("project python file discovery", exc)
        return r[t.SequenceOf[Path]].ok(tuple(sorted(files)))

    def _selected_projects(
        self, rope_workspace: p.Infra.RopeWorkspaceDsl
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        """Return the selected projects."""
        _ = rope_workspace
        discovered = u.Infra.projects(self.workspace_root)
        if discovered.failure:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                discovered.error or "project discovery failed"
            )
        selected = tuple(
            project
            for project in discovered.unwrap()
            if self.project_name is None or project.name == self.project_name
        )
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(selected)


__all__: list[str] = ["FlextInfraCodegenConsolidator"]
