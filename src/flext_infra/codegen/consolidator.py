"""Extracted facade class for consolidator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, r, s, t, u


class FlextInfraCodegenConsolidator(s[str]):
    """Consolidate inline constants into canonical ``c.*`` references."""

    _ALL_LINT_GATES: ClassVar[Sequence[str]] = tuple(
        entry[0] for entry in c.Infra.LINT_TOOLS
    )

    project_name: str | None = None
    """Single project to consolidate; ``None`` selects every discovered project."""

    @override
    def execute(self) -> p.Result[str]:
        """Execute constants consolidation with normalized command context.

        Returns:
            The consolidated command report text.

        """
        output_lines: MutableSequence[str] = (
            ["[DRY-RUN] Scanning...\n"] if self.dry_run else []
        )
        found = applied = failed = 0
        file_results: MutableSequence[Mapping[str, object]] = []
        projects_result = self._selected_projects()
        if projects_result.failure:
            return r[str].from_failure(projects_result)
        projects = projects_result.value
        with u.Infra.open_project(
            self.repository_root,
            project_roots=tuple(project.path for project in projects) or None,
        ) as rope_project:
            for project in projects:
                project_layout = u.Infra.layout(project.path)
                if project_layout is None or not project_layout.init_path.is_file():
                    continue
                constants_file = project_layout.package_dir / c.Infra.CONSTANTS_PY
                value_map = self._build_value_map_from_constants_file(
                    rope_project, constants_file
                )
                if value_map.failure:
                    return r[str].from_failure(value_map)
                if not value_map.value:
                    continue
                for python_file in (
                    path
                    for path in u.Infra.iter_directory_python_files(
                        project.path,
                        repository_root=project.path,
                    )
                    if "_constants" not in path.parts
                ):
                    outcome = self._consolidate_python_file(
                        rope_project,
                        python_file,
                        value_map.value,
                        project_layout,
                    )
                    found += outcome.found
                    output_lines.extend(outcome.lines)
                    if outcome.record is not None:
                        file_results.append(outcome.record)
                        applied += outcome.applied
                        failed += 0 if outcome.applied else 1
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

    def _consolidate_python_file(
        self,
        rope_project: p.Infra.RopeProject,
        python_file: Path,
        value_map: Mapping[str, str],
        project_layout: p.Infra.RopeProjectLayout,
    ) -> p.Infra.ConsolidationOutcome:
        """Scan and consolidate one Python file against the constants map.

        Returns:
            The scan outcome with dry-run lines or an applied record.

        """
        scanned = self._scan_file(rope_project, python_file, value_map)
        rel_path = python_file.relative_to(self.repository_root)
        if scanned is None:
            return m.Infra.ConsolidationOutcome(
                found=0, lines=(), record=None, applied=0
            )
        if self.dry_run:
            return m.Infra.ConsolidationOutcome(
                found=len(scanned.matches),
                lines=tuple(
                    f"  {rel_path}:{symbol.line}  {symbol.name} = {value} -> {ref}"
                    for symbol, ref, value in scanned.matches
                ),
                record=None,
                applied=0,
            )
        ok, changes, lines = self._apply_and_validate(
            rope_project,
            scanned,
            python_file,
            self.repository_root,
            project_layout.package_name,
        )
        return m.Infra.ConsolidationOutcome(
            found=len(scanned.matches),
            lines=tuple(lines),
            record={
                "file": str(rel_path),
                "status": "applied" if ok else "reverted",
                "changes": list(changes),
            },
            applied=len(changes) if ok else 0,
        )

    def _selected_projects(
        self,
    ) -> p.Result[Sequence[p.Infra.ProjectInfo]]:
        """Select the consolidation targets under the workspace root.

        Returns:
            The discovered consolidation target projects.

        """
        discovered = u.Infra.projects(self.repository_root)
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
        rope_project: t.Infra.RopeProject,
        constants_file: Path,
    ) -> p.Result[Mapping[str, str]]:
        """Map each ``Final`` value of a constants module to its ``c.*`` path.

        ``Final`` identity comes from the typing-aware Rope matches; values and
        class nesting come from the Rope binding index of one module snapshot.
        The outermost class is the ``c`` facade itself, so ``Outer.Inner.NAME``
        maps to ``Inner.NAME``.

        Returns:
            The value map; empty when the constants file does not exist.

        """
        if not constants_file.is_file():
            return r[Mapping[str, str]].ok({})
        resource = u.Infra.resolve_resource_from_path(rope_project, constants_file)
        if resource is None:
            return r[Mapping[str, str]].fail(
                f"constants file is outside the rope project: {constants_file}"
            )
        pymodule = u.Infra.resolve_pymodule(rope_project, resource)
        finals = u.Infra.constant_bindings(pymodule)
        index = pymodule.get_source_binding_index()
        value_map: t.MutableStrMapping = {}
        cls._record_constants(value_map, pymodule, finals, index.assignment_layouts())
        pending: list[tuple[p.Infra.RopeScope, t.StrTuple]] = [
            (scope, ()) for scope in pymodule.get_scope().get_scopes()
        ]
        while pending:
            scope, outer = pending.pop()
            if scope.get_kind() != c.Infra.RopeScopeKind.CLASS:
                continue
            path = (*outer, scope.pyobject.get_name())
            pending.extend((child, path) for child in scope.get_scopes())
            cls._record_constants(
                value_map, pymodule, finals, index.assignment_layouts(scope), path[1:]
            )
        return r[Mapping[str, str]].ok(value_map)

    @staticmethod
    def _record_constants(
        value_map: t.MutableStrMapping,
        pymodule: t.Infra.RopePyModule,
        finals: frozenset[tuple[int, str]],
        layouts: Sequence[p.Infra.RopeSourceAssignmentLayout],
        path: t.StrTuple = (),
    ) -> None:
        """Record the ``Final`` layouts of one scope, with quoted string variants."""
        source = pymodule.source_code
        for layout in layouts:
            if layout.value is None or not layout.targets:
                continue
            name, (start, _) = layout.targets[0]
            raw = source[layout.value[0] : layout.value[1]].strip()
            if not raw or (pymodule.lines.get_line_number(start), name) not in finals:
                continue
            canonical = ".".join((*path, name))
            value_map[raw] = canonical
            if (
                len(raw) >= c.Infra.DETECTION_MIN_QUOTED_LITERAL_LEN
                and raw[0] in {'"', "'"}
                and raw[-1] == raw[0]
            ):
                value_map[f"'{raw[1:-1]}'"] = canonical
                value_map[f'"{raw[1:-1]}"'] = canonical

    def _scan_file(
        self,
        rope_project: t.Infra.RopeProject,
        python_file: Path,
        value_map: Mapping[str, str],
    ) -> p.Infra.ConsolidatorScannedFile | None:
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
        return m.Infra.ConsolidatorScannedFile.model_validate({
            "resource": (resource),
            "source": (source),
            "matches": (matches),
        })

    @staticmethod
    def _match_assignments(
        symbols: Sequence[p.Infra.SymbolInfo],
        # Use the canonical scalar sequence alias directly.
        source_lines: Sequence[str],
        value_to_ref: Mapping[str, str],
    ) -> Sequence[tuple[p.Infra.SymbolInfo, str, str]]:
        """Match assignments.

        Returns:
            The resulting ``Sequence[tuple[p.Infra.SymbolInfo, str, str]]``.

        """
        matches: MutableSequence[tuple[p.Infra.SymbolInfo, str, str]] = []
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
        scanned: p.Infra.ConsolidatorScannedFile,
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

        def apply() -> None:
            u.Infra.rewrite_source_at_offsets(rope_project, resource, edits)
            u.Infra.add_import(rope_project, resource, pkg_name, ["c"])
            source = resource.read()
            prepared = u.Infra.normalize_source(
                workspace, py_file, source, before_source=original_source
            ).unwrap()
            if prepared != source:
                resource.write(prepared)

        ok, report = u.Infra.protected_file_edit(
            py_file,
            request=m.Infra.ProtectedFileEditRequest(
                workspace=workspace,
                before_source=original_source,
                edit_fn=apply,
                gates=cls._ALL_LINT_GATES,
            ),
        )
        if ok:
            return (True, list(descs), [f"  APPLIED {rel}: {item}" for item in descs])
        return (False, list(descs), report)


__all__: list[str] = ["FlextInfraCodegenConsolidator"]
