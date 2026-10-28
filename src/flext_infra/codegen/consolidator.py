"""Extracted facade class for consolidator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, p, r, s, t, u
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraCodegenConsolidator(s[str]):
    """Consolidate inline constants into canonical ``c.*`` references."""

    _ALL_LINT_GATES: ClassVar[Sequence[str]] = tuple(
        entry[0] for entry in c.Infra.LINT_TOOLS
    )

    project_name: str | None = None
    """Single project to consolidate; ``None`` selects every discovered project."""

    def execute(self) -> p.Result[str]:
        """Execute constants consolidation with normalized command context."""
        output_lines: MutableSequence[str] = (
            ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
        )
        found = applied = failed = 0
        file_results: MutableSequence[Mapping[str, object]] = []
        with FlextInfraRopeWorkspace.open_workspace(self.workspace_root) as rope:
            projects_result = self._selected_projects(rope)
            if projects_result.failure:
                return r[str].fail(projects_result.error or "project discovery failed")
            for project in projects_result.unwrap():
                project_layout = u.Infra.layout(project.path)
                if project_layout is None or not project_layout.init_path.is_file():
                    continue
                constants_file = project_layout.package_dir / c.Infra.CONSTANTS_PY
                value_map = self._build_value_map_from_constants_file(constants_file)
                if value_map.failure or not value_map.value:
                    continue
                for python_file in (
                    path
                    for path in u.Infra.iter_directory_python_files(
                        project_layout.package_dir,
                    )
                    if "_constants" not in path.parts
                ):
                    scanned = self._scan_file(
                        rope.rope_project, python_file, value_map.value
                    )
                    if scanned is None:
                        continue
                    found += len(scanned.matches)
                    rel_path = python_file.relative_to(self.workspace_root)
                    if self.dry_run:
                        output_lines.extend(
                            f"  {rel_path}:{symbol.line}"
                            f"  {symbol.name} = {value} -> {ref}"
                            for symbol, ref, value in scanned.matches
                        )
                        continue
                    ok, changes, lines = self._apply_and_validate(
                        rope.rope_project,
                        scanned,
                        python_file,
                        self.workspace_root,
                        project_layout.package_name,
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
            f"Found {found} canonical matches across the selected projects"
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
            normalized = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
            return r[str].ok(
                t.Infra.INFRA_MAPPING_ADAPTER.dump_json(normalized).decode(),
            )
        return r[str].ok("\n".join(output_lines))

    def _selected_projects(
        self,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[Sequence[p.Infra.ProjectInfo]]:
        """Select the consolidation targets under the workspace root."""
        _ = rope_workspace
        discovered = u.Infra.projects(self.workspace_root)
        if discovered.failure:
            return r[Sequence[p.Infra.ProjectInfo]].fail(
                discovered.error or "project discovery failed",
            )
        selected = tuple(
            project
            for project in discovered.unwrap()
            if self.project_name is None or project.name == self.project_name
        )
        return r[Sequence[p.Infra.ProjectInfo]].ok(selected)

    @classmethod
    def _build_value_map_from_constants_file(
        cls,
        constants_file: Path,
    ) -> p.Result[Mapping[str, str]]:
        """Build value map from a constants file.

        Missing file → empty map (nothing to consolidate); an existing-but-unreadable
        file is surfaced as a failure (never silently treated as empty).

        Returns:
            The resulting ``p.Result[Mapping[str, str]]``.

        """
        if not constants_file.is_file():
            return r[Mapping[str, str]].ok({})
        read = u.Cli.files_read_text(constants_file)
        if read.failure:
            return r[Mapping[str, str]].from_failure(read)
        value_map: t.MutableStrMapping = {}
        for name, _, raw, class_path, _ in u.Infra.parse_final_constant_definitions(
            read.value.splitlines(),
        ):
            if not raw:
                continue
            canonical = f"{class_path}.{name}" if class_path else name
            value_map[raw] = canonical
            if (
                len(raw) >= c.Infra.DETECTION_MIN_QUOTED_LITERAL_LEN
                and raw[0] in {'"', "'"}
                and raw[-1] == raw[0]
            ):
                inner = raw[1:-1]
                value_map[f"'{inner}'"] = canonical
                value_map[f'"{inner}"'] = canonical
        return r[Mapping[str, str]].ok(value_map)

    def _scan_file(
        self,
        rope_project: t.Infra.RopeProject,
        python_file: Path,
        value_map: Mapping[str, str],
    ) -> m.Infra.ConsolidatorScannedFile | None:
        """Scan file.

        Returns:
            The resulting ``m.Infra.ConsolidatorScannedFile | None``.

        """
        resource = u.Infra.resolve_resource_from_path(rope_project, python_file)
        if resource is None:
            return None
        symbols = u.Infra.resolve_module_symbols(rope_project, resource)
        assignments = [symbol for symbol in symbols if symbol.kind == "assignment"]
        if not assignments:
            return None
        source = resource.read()
        matches = self._match_assignments(assignments, source.splitlines(), value_map)
        if not matches:
            return None
        return m.Infra.ConsolidatorScannedFile(
            resource=resource,
            source=source,
            matches=matches,
        )

    @staticmethod
    def _match_assignments(
        symbols: Sequence[m.Infra.SymbolInfo],
        # Use the canonical scalar sequence alias directly.
        source_lines: Sequence[str],
        value_to_ref: Mapping[str, str],
    ) -> Sequence[tuple[m.Infra.SymbolInfo, str, str]]:
        """Match assignments.

        Returns:
            The resulting ``Sequence[tuple[m.Infra.SymbolInfo, str, str]]``.

        """
        matches: MutableSequence[tuple[m.Infra.SymbolInfo, str, str]] = []
        for symbol in symbols:
            # Widen the validated constrained int for indexing.
            line_number: int = symbol.line
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
        scanned: m.Infra.ConsolidatorScannedFile,
        py_file: Path,
        workspace: Path,
        pkg_name: str,
    ) -> t.Infra.EditResultWithDescs:
        """Apply and validate.

        Returns:
            The resulting ``t.Infra.EditResultWithDescs``.

        Raises:
            TypeError: If the scanned resource is not a Rope file resource.

        """
        resource = scanned.resource
        if not u.Infra.file_resource(resource):
            msg = f"expected a Rope file resource: {py_file}"
            raise TypeError(msg)
        original_source = scanned.source
        src_lines = original_source.splitlines(keepends=True)
        rel = py_file.relative_to(workspace)
        edits: MutableSequence[tuple[int, int, str]] = []
        descs: MutableSequence[str] = []
        for symbol, ref, value in scanned.matches:
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
            return (True, [], [])

        ok, report = u.Infra.protected_file_edit(
            py_file,
            request=m.Infra.ProtectedFileEditRequest(
                workspace=workspace,
                before_source=original_source,
                edit_fn=lambda: (
                    u.Infra.rewrite_source_at_offsets(
                        rope_project,
                        resource,
                        edits,
                        apply=True,
                    ),
                    u.Infra.add_import(
                        rope_project,
                        resource,
                        pkg_name,
                        ["c"],
                        apply=True,
                    ),
                    None,
                )[-1],
                gates=cls._ALL_LINT_GATES,
            ),
        )
        if ok:
            return (True, list(descs), [f"  APPLIED {rel}: {item}" for item in descs])
        return (False, list(descs), report)


__all__: list[str] = ["FlextInfraCodegenConsolidator"]
