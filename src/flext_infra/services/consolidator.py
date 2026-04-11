"""Direct constants consolidation command service."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, p, s, t, u


class FlextInfraCodegenConsolidator(s[str]):
    """Consolidate inline constants into canonical ``c.*`` references."""

    project_name: Annotated[
        str | None,
        Field(
            default=None,
            alias="project",
            description="Single project to consolidate",
        ),
    ] = None

    @override
    def execute(self) -> r[str]:
        """Execute constants consolidation with normalized command context."""
        output_lines: MutableSequence[str] = (
            ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
        )
        found = applied = failed = 0
        file_results: MutableSequence[t.Infra.InfraMapping] = []
        projects_result = self._selected_projects()
        if projects_result.is_failure:
            return r[str].fail("Failed to discover projects")
        projects = projects_result.value
        for project in projects:
            package_name = (
                project.package_name
                if isinstance(project, m.Infra.ProjectInfo)
                else u.Infra.package_name(project.path)
            )
            if not package_name:
                continue
            package_dir = project.path / c.Infra.Paths.DEFAULT_SRC_DIR / Path(
                *package_name.split("."),
            )
            if not (package_dir / c.Infra.Files.INIT_PY).is_file():
                continue
            if "c" not in u.Infra.discover_project_aliases(project.path):
                continue
            constants_facade = u.Infra.resolve_constants_facade(package_name)
            if constants_facade is None:
                continue
            value_map = u.Infra.build_value_map(constants_facade)
            rope = u.Infra.init_rope_project(project.path)
            try:
                for python_file in (
                    fp
                    for fp in u.Infra.iter_directory_python_files(package_dir)
                    if "_constants" not in fp.parts
                ):
                    scanned = self._scan_file(rope, python_file, value_map)
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
                    ok, changes, lines = u.Infra.apply_and_validate(
                        rope,
                        resource,
                        python_file,
                        self.workspace_root,
                        package_name,
                        source,
                        matches,
                    )
                    output_lines.extend(lines)
                    file_results.append({
                        "file": str(rel_path),
                        "status": "applied" if ok else "reverted",
                        "changes": tuple(changes),
                    })
                    if ok:
                        applied += len(changes)
                    else:
                        failed += 1
            finally:
                rope.close()
        summary = (
            f"Found {found} canonical matches across {len(projects)} projects"
            if self.dry_run
            else f"Applied {applied} replacements, {failed} files reverted"
        )
        output_lines.extend(("", summary))
        if self.output_format == "json":
            payload: t.Infra.MutableInfraMapping = {
                "total_found": found,
                "total_applied": applied,
                "total_failed": failed,
                "files": file_results,
            }
            return r[str].ok(t.Infra.INFRA_MAPPING_ADAPTER.dump_json(payload).decode())
        return r[str].ok("\n".join(output_lines))

    def _selected_projects(self) -> r[Sequence[p.Infra.ProjectInfo]]:
        projects_result = u.Infra.discover_codegen_projects(self.workspace_root)
        if projects_result.is_failure:
            return r[Sequence[p.Infra.ProjectInfo]].fail(
                projects_result.error or "Failed to discover projects",
            )
        selected = tuple(
            project
            for project in projects_result.value
            if self.project_name is None or project.name == self.project_name
        )
        return r[Sequence[p.Infra.ProjectInfo]].ok(selected)

    def _scan_file(
        self,
        rope_project: t.Infra.RopeProject,
        python_file: Path,
        value_map: t.StrMapping,
    ) -> (
        tuple[
            t.Infra.RopeResource,
            str,
            Sequence[tuple[m.Infra.SymbolInfo, str, str]],
        ]
        | None
    ):
        resource = u.Infra.get_resource_from_path(rope_project, python_file)
        if resource is None:
            return None
        symbols = u.Infra.get_module_symbols(rope_project, resource)
        assignments = [symbol for symbol in symbols if symbol.kind == "assignment"]
        if not assignments:
            return None
        source = resource.read()
        matches = u.Infra.match_assignments(
            assignments,
            source.splitlines(),
            value_map,
        )
        if not matches:
            return None
        return (resource, source, matches)


__all__ = ["FlextInfraCodegenConsolidator"]
