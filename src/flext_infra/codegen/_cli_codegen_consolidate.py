"""Codegen CLI consolidate handler mixin."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra._utilities.codegen_constants import (
    FlextInfraUtilitiesCodegenConstantTransformation as _xform,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.rope import FlextInfraUtilitiesRope
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraCliCodegenConsolidate:
    """Mixin providing the consolidate command handler."""

    @staticmethod
    def _handle_consolidate(params: m.Infra.CodegenConsolidateInput) -> r[str]:
        """Consolidate inline constants into ``c.*`` references."""
        workspace = Path(params.workspace).resolve()
        dry_run = not params.apply
        out: list[str] = ["[DRY-RUN] Scanning...\n"] if dry_run else []
        found = applied = failed = 0
        results: list[dict[str, t.Infra.InfraValue]] = []

        pr = FlextInfraUtilitiesDiscovery.discover_projects(workspace)
        if pr.is_failure:
            return r[str].fail("Failed to discover projects")
        projects = [
            p for p in pr.value if not params.project or p.name == params.project
        ]

        for project in projects:
            pkg_name = project.name.replace("-", "_")
            pkg_dir = (
                workspace / project.name / c.Infra.Paths.DEFAULT_SRC_DIR / pkg_name
            )
            if not pkg_dir.is_dir():
                continue
            aliases = FlextInfraUtilitiesDiscovery.discover_project_aliases(
                workspace / project.name,
            )
            if "c" not in aliases:
                continue
            facade = _xform.resolve_constants_facade(pkg_name)
            if facade is None:
                continue

            vmap = _xform.build_value_map(facade)
            rope = FlextInfraUtilitiesRope.init_rope_project(workspace / project.name)

            for py_file in sorted(pkg_dir.rglob(c.Infra.Extensions.PYTHON_GLOB)):
                if (
                    c.Infra.Dunders.PYCACHE in py_file.parts
                    or "_constants" in py_file.parts
                ):
                    continue
                res = FlextInfraUtilitiesRope.get_resource_from_path(rope, py_file)
                if res is None:
                    continue
                syms = FlextInfraUtilitiesRope.get_module_symbols(rope, res)
                assigns = [s for s in syms if s.kind == "assignment"]
                if not assigns:
                    continue
                source = FlextInfraUtilitiesRope.read_source(res)
                matches = _xform.match_assignments(assigns, source.splitlines(), vmap)
                if not matches:
                    continue

                found += len(matches)
                rel = py_file.relative_to(workspace)

                if dry_run:
                    out.extend(
                        f"  {rel}:{s.line}  {s.name} = {v} -> {ref}"
                        for s, ref, v in matches
                    )
                    continue

                ok, descs, lines = _xform.apply_and_validate(
                    rope,
                    res,
                    py_file,
                    workspace,
                    pkg_name,
                    source,
                    matches,
                )
                out.extend(lines)
                results.append({
                    "file": str(rel),
                    "status": "applied" if ok else "reverted",
                    "changes": descs,
                })
                if ok:
                    applied += len(descs)
                else:
                    failed += 1

        summary = (
            f"Found {found} canonical matches across {len(projects)} projects"
            if dry_run
            else f"Applied {applied} replacements, {failed} files reverted"
        )
        out.extend(("", summary))

        if params.output_format == "json":
            return r[str].ok(
                t.Infra.CONTAINER_MAPPING_ADAPTER.dump_json({
                    "total_found": found,
                    "total_applied": applied,
                    "total_failed": failed,
                    "files": results,
                }).decode(),
            )
        return r[str].ok("\n".join(out))


__all__ = ["FlextInfraCliCodegenConsolidate"]
