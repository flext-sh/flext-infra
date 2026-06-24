"""Direct constants consolidation command service."""

from __future__ import annotations

from typing import Annotated, override

from flext_infra import (
    FlextInfraRopeWorkspace,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)
from flext_infra.codegen._consolidator_engine import (
    FlextInfraCodegenConsolidatorEngineMixin,
)


class FlextInfraCodegenConsolidator(
    s[str],
    FlextInfraCodegenConsolidatorEngineMixin,
):
    """Consolidate inline constants into canonical ``c.*`` references."""

    project_name: Annotated[
        str | None,
        m.Field(
            alias="project",
            description="Single project to consolidate",
        ),
    ] = None

    @override
    def execute(self) -> p.Result[str]:
        """Execute constants consolidation with normalized command context."""
        output_lines: t.MutableSequenceOf[str] = (
            ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
        )
        found = applied = failed = 0
        file_results: list[dict[str, list[str] | str]] = []

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
                        value_map_result.error or "constants file read failed",
                    )
                value_map = value_map_result.value
                if not value_map:
                    continue

                for python_file in (
                    path
                    for path in u.Infra.iter_matching_files(
                        project_layout.package_dir,
                        includes=[c.Infra.EXT_PYTHON_GLOB],
                    )
                    if "_constants" not in path.parts
                ):
                    scanned = self._scan_file(rope.rope_project, python_file, value_map)
                    if scanned is None:
                        continue
                    resource, source, matches = scanned
                    found += len(matches)
                    rel_path = python_file.relative_to(self.workspace_root)
                    if self.dry_run:
                        output_lines.extend(
                            f"  {rel_path}:{symbol.line}  {symbol.name} = {value} -> {ref}"
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
                    file_results.append({
                        "file": str(rel_path),
                        "status": "applied" if ok else "reverted",
                        "changes": list(changes),
                    })
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
            payload = {
                "total_found": found,
                "total_applied": applied,
                "total_failed": failed,
                "files": list(file_results),
            }
            normalized_payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
            return r[str].ok(
                t.Infra.INFRA_MAPPING_ADAPTER.dump_json(normalized_payload).decode()
            )
        return r[str].ok("\n".join(output_lines))

    def _selected_projects(
        self,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        """Selected projects."""
        _ = rope_workspace
        discovered = u.Infra.projects(self.workspace_root)
        if discovered.failure:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                discovered.error or "project discovery failed",
            )
        selected = tuple(
            project
            for project in discovered.unwrap()
            if self.project_name is None or project.name == self.project_name
        )
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(selected)


__all__: list[str] = ["FlextInfraCodegenConsolidator"]
