"""Direct constants consolidation command service."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, t, u
from flext_infra.base import s


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
        projects_result = u.Infra.discover_projects(
            self.workspace_root,
        )
        if projects_result.is_failure:
            return r[str].fail("Failed to discover projects")
        projects = [
            project
            for project in projects_result.value
            if self.project_name is None or project.name == self.project_name
        ]
        for project in projects:
            package_name = project.name.replace("-", "_")
            package_dir = (
                self.workspace_root
                / project.name
                / c.Infra.Paths.DEFAULT_SRC_DIR
                / package_name
            )
            if not package_dir.is_dir():
                continue
            aliases = u.Infra.discover_project_aliases(
                self.workspace_root / project.name,
            )
            if "c" not in aliases:
                continue
            constants_facade = u.Infra.resolve_constants_facade(package_name)
            if constants_facade is None:
                continue
            value_map = u.Infra.build_value_map(constants_facade)
            rope = u.Infra.init_rope_project(
                self.workspace_root / project.name,
            )
            for python_file in sorted(
                package_dir.rglob(c.Infra.Extensions.PYTHON_GLOB)
            ):
                if (
                    c.Infra.Dunders.PYCACHE in python_file.parts
                    or "_constants" in python_file.parts
                ):
                    continue
                resource = u.Infra.get_resource_from_path(
                    rope,
                    python_file,
                )
                if resource is None:
                    continue
                symbols = u.Infra.get_module_symbols(rope, resource)
                assignments = [
                    symbol for symbol in symbols if symbol.kind == "assignment"
                ]
                if not assignments:
                    continue
                source = u.Infra.read_source(resource)
                matches = u.Infra.match_assignments(
                    assignments,
                    source.splitlines(),
                    value_map,
                )
                if not matches:
                    continue
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


__all__ = ["FlextInfraCodegenConsolidator"]
