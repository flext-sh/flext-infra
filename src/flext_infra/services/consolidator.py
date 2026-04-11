"""Direct constants consolidation command service."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, override

from pydantic import Field

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCodegenConsolidator(s[str]):
    """Consolidate inline constants into canonical ``c.*`` references."""

    _ALL_LINT_GATES: ClassVar[tuple[str, ...]] = tuple(
        tool for tool, _ in c.Infra.LINT_TOOLS
    )

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
        file_results = []

        projects_result = self._selected_projects()
        if projects_result.failure:
            return r[str].fail("Failed to discover projects")

        for project in projects_result.value:
            project_path = project.path
            package_name = project.package_name or u.Infra.package_name(project_path)
            if not package_name:
                continue
            package_dir = (
                project_path
                / c.Infra.DEFAULT_SRC_DIR
                / Path(
                    *package_name.split("."),
                )
            )
            if not (package_dir / c.Infra.INIT_PY).is_file():
                continue

            constants_file = package_dir / c.Infra.CONSTANTS_PY
            value_map = self._build_value_map_from_constants_file(constants_file)
            if not value_map:
                continue

            rope = u.Infra.init_rope_project(project_path)
            try:
                for python_file in (
                    path
                    for path in u.Infra.iter_directory_python_files(package_dir)
                    if "_constants" not in path.parts
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
                    ok, changes, lines = self._apply_and_validate(
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
                        "changes": list(changes),
                    })
                    if ok:
                        applied += len(changes)
                    else:
                        failed += 1
            finally:
                rope.close()

        summary = (
            f"Found {found} canonical matches across {len(projects_result.value)} projects"
            if self.dry_run
            else f"Applied {applied} replacements, {failed} files reverted"
        )
        output_lines.extend(("", summary))
        if self.output_format == "json":
            payload = {
                "total_found": found,
                "total_applied": applied,
                "total_failed": failed,
                "files": list(file_results),
            }
            return r[str].ok(t.Infra.INFRA_MAPPING_ADAPTER.dump_json(payload).decode())
        return r[str].ok("\n".join(output_lines))

    def _selected_projects(self) -> r[Sequence[p.Infra.ProjectInfo]]:
        projects_result = u.Infra.discover_codegen_projects(self.workspace_root)
        if projects_result.failure:
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
        value_map: Mapping[str, str],
    ) -> (
        tuple[
            t.Infra.RopeResource,
            str,
            Sequence[tuple[m.Infra.Rope.SymbolInfo, str, str]],
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
        matches = self._match_assignments(
            assignments,
            source.splitlines(),
            value_map,
        )
        if not matches:
            return None
        return (resource, source, matches)

    @staticmethod
    def _match_assignments(
        symbols: Sequence[m.Infra.Rope.SymbolInfo],
        source_lines: Sequence[str],
        value_to_ref: Mapping[str, str],
    ) -> Sequence[tuple[m.Infra.Rope.SymbolInfo, str, str]]:
        matches: MutableSequence[tuple[m.Infra.Rope.SymbolInfo, str, str]] = []
        for symbol in symbols:
            line_number = symbol.line
            if line_number < 1 or line_number > len(source_lines):
                continue
            line: str = source_lines[line_number - 1]
            eq = line.find("=")
            if eq < 0:
                continue
            raw = line[eq + 1 :].strip()
            if raw in c.Infra.DETECTION_TRIVIAL_VALUES:
                continue
            canonical = value_to_ref.get(raw)
            if canonical is None or canonical == symbol.name:
                continue
            canonical_key = canonical.lower().replace("_", "")
            symbol_key = symbol.name.lower().replace("_", "")
            if canonical_key == symbol_key or symbol_key in canonical_key:
                matches.append((symbol, f"c.{canonical}", raw))
        return tuple(matches)

    @classmethod
    def _apply_and_validate(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        py_file: Path,
        workspace: Path,
        pkg_name: str,
        backup: str,
        matches: Sequence[tuple[m.Infra.Rope.SymbolInfo, str, str]],
    ) -> t.Infra.EditResultWithDescs:
        src_lines = backup.splitlines(keepends=True)
        rel = py_file.relative_to(workspace)
        edits: MutableSequence[tuple[int, int, str]] = []
        descs: MutableSequence[str] = []
        for symbol, ref, value in matches:
            line_number = symbol.line
            if line_number < 1 or line_number > len(src_lines):
                continue
            line = src_lines[line_number - 1]
            eq = line.find("=")
            if eq < 0:
                continue
            base = sum(len(src_lines[i]) for i in range(line_number - 1))
            edits.append((
                base + eq + 1,
                base + eq + 1 + len(line[eq + 1 :].rstrip()),
                f" {ref}",
            ))
            descs.append(f"{symbol.name} = {value} -> {ref}")
        if not edits:
            empty_changes: list[str] = []
            empty_report: list[str] = []
            return (True, empty_changes, empty_report)

        def _do_edit() -> None:
            u.Infra.rewrite_source_at_offsets(
                rope_project,
                resource,
                edits,
                apply=True,
            )
            u.Infra.add_import(
                rope_project,
                resource,
                pkg_name,
                ["c"],
                apply=True,
            )

        def _restore_edit() -> None:
            resource.write(backup)

        ok, report = u.Infra.protected_file_edit(
            py_file,
            workspace=workspace,
            before_source=backup,
            edit_fn=_do_edit,
            restore_fn=_restore_edit,
            keep_backup=True,
            gates=cls._ALL_LINT_GATES,
        )
        if ok:
            return (True, list(descs), [f"  APPLIED {rel}: {item}" for item in descs])
        return (False, list(descs), report)

    @classmethod
    def _build_value_map_from_constants_file(
        cls, constants_file: Path
    ) -> Mapping[str, str]:
        min_quoted_length = 2
        value_map: MutableMapping[str, str] = {}
        try:
            source = constants_file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except (OSError, UnicodeDecodeError):
            return value_map

        class_stack: MutableSequence[tuple[str, int]] = []
        for line in source.splitlines():
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if stripped.startswith("class ") and stripped.endswith(":"):
                class_match = c.Infra.DETECTION_CLASS_DECL_RE.match(stripped)
                if class_match is not None:
                    while class_stack and class_stack[-1][1] >= indent:
                        class_stack.pop()
                    class_stack.append((class_match.group(1), indent))
            elif class_stack:
                while class_stack and indent <= class_stack[-1][1]:
                    class_stack.pop()

            match = c.Infra.DETECTION_FINAL_DECL_RE.match(line)
            if match is None:
                continue
            name = match.group("name")
            raw = match.group("value").strip()
            if not raw:
                continue
            class_path = ".".join(item[0] for item in class_stack)
            canonical = f"{class_path}.{name}" if class_path else name
            value_map[raw] = canonical
            if (
                len(raw) >= min_quoted_length
                and raw[0] in {'"', "'"}
                and raw[-1] == raw[0]
            ):
                inner = raw[1:-1]
                value_map[f"'{inner}'"] = canonical
                value_map[f'"{inner}"'] = canonical
        return value_map


__all__ = ["FlextInfraCodegenConsolidator"]
