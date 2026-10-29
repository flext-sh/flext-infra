"""Move and compatibility rewrites for namespace refactors.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, t
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesProtectedEditLinting,
    FlextInfraUtilitiesRefactorNamespaceCommon,
    FlextInfraUtilitiesTransformerHeader,
)
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraUtilitiesRefactorNamespaceMoves:
    """Helpers for block moves and compatibility-alias rewrites."""

    @staticmethod
    def rewrite_manual_protocol_violations(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        names_by_file: Mapping[Path, t.Infra.StrSet],
        gates: Sequence[str] | None = None,
    ) -> None:
        """Relocate the named Protocol classes of each file to its protocols owner.

        Raises:
            ValueError: If a consumer path is outside the project.

        """
        for path in py_files:
            if not path.resolve().is_relative_to(project_root.resolve()):
                msg = f"refusing moved-import rewrite outside project: {path}"
                raise ValueError(msg)
        for source_file, protocol_names in names_by_file.items():
            FlextInfraUtilitiesRefactorNamespaceMoves._move_protocol_blocks(
                project_root=project_root,
                source_file=source_file,
                names=protocol_names,
                gates=gates,
            )

    @classmethod
    def rewrite_manual_typing_alias_violations(
        cls,
        *,
        project_root: Path,
        names_by_file: Mapping[Path, t.Infra.StrSet],
        gates: Sequence[str] | None = None,
    ) -> None:
        """Relocate the named typing declarations of each file to its typings owner."""
        for source_file, alias_names in names_by_file.items():
            cls._move_typing_alias_lines(
                project_root=project_root,
                source_file=source_file,
                alias_names=alias_names,
                gates=gates,
            )

    @staticmethod
    def _moved_block_facts(
        lines: Sequence[str],
        names: t.Infra.StrSet,
    ) -> tuple[
        MutableSequence[str],
        MutableSequence[tuple[int, int]],
        MutableSequence[str],
    ]:
        """Collect the block texts, line ranges, and names that exist.

        Returns:
            The resulting ``(blocks, ranges, moved names)`` triple.

        """
        blocks: MutableSequence[str] = []
        ranges: MutableSequence[tuple[int, int]] = []
        moved: MutableSequence[str] = []
        for name in sorted(names):
            found = FlextInfraUtilitiesRefactorNamespaceCommon.find_top_level_block(
                lines=lines,
                header=f"class {name}",
            )
            if found is None:
                continue
            start, end = found
            blocks.append("\n".join(lines[start:end]))
            ranges.append((start, end))
            moved.append(name)
        return blocks, ranges, moved

    @staticmethod
    def _prepared_target(
        target_file: Path,
        source: str,
        blocks: Sequence[str],
    ) -> tuple[str, str | None]:
        """Build the target module text with imports and moved blocks appended.

        Returns:
            The resulting ``(updated target source, expected target source)`` pair.

        """
        expected_target_source = (
            target_file.read_text(encoding=c.DEFAULT_ENCODING)
            if target_file.is_file()
            else None
        )
        target_source = (
            expected_target_source
            if expected_target_source is not None
            else f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        )
        target_lines: Sequence[str] = target_source.splitlines()
        target_lines = FlextInfraUtilitiesRefactorNamespaceCommon.insert_import_lines(
            lines=target_lines,
            imports=(
                FlextInfraUtilitiesRefactorNamespaceMoves._collect_required_import_lines(
                    source=source,
                    blocks=blocks,
                )
            ),
        )
        updated_target = "\n".join(target_lines).rstrip()
        for block in blocks:
            if block.splitlines()[0] not in updated_target:
                updated_target += f"\n\n{block}"
        return updated_target, expected_target_source

    @staticmethod
    def _lines_without_ranges(
        lines: Sequence[str],
        ranges: Sequence[tuple[int, int]],
    ) -> list[str]:
        """Delete every collected line range from the source lines.

        Returns:
            The resulting ``list[str]``.

        """
        filtered_lines = list(lines)
        for start, end in sorted(ranges, reverse=True):
            del filtered_lines[start:end]
        return filtered_lines

    @staticmethod
    def _move_protocol_blocks(
        *,
        project_root: Path,
        source_file: Path,
        names: t.Infra.StrSet,
        gates: Sequence[str] | None,
    ) -> None:
        """Move named protocols and their consumers in one protected transaction."""
        source = source_file.read_text(encoding=c.DEFAULT_ENCODING)
        blocks, ranges, moved = (
            FlextInfraUtilitiesRefactorNamespaceMoves._moved_block_facts(
                source.splitlines(),
                names,
            )
        )
        if not blocks:
            return
        target_file = FlextInfraUtilitiesRefactorNamespaceCommon.canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename=c.Infra.PROTOCOLS_PY,
        )
        updated_target, expected_target_source = (
            FlextInfraUtilitiesRefactorNamespaceMoves._prepared_target(
                target_file,
                source,
                blocks,
            )
        )
        filtered_lines = (
            FlextInfraUtilitiesRefactorNamespaceMoves._lines_without_ranges(
                source.splitlines(),
                ranges,
            )
        )

        candidate_writes: MutableMapping[Path, str] = {
            target_file: updated_target.rstrip() + "\n",
            source_file: "\n".join(filtered_lines).rstrip() + "\n",
        }
        candidate_expected: MutableMapping[Path, str | None] = {
            target_file: expected_target_source,
            source_file: source,
        }
        FlextInfraUtilitiesRefactorNamespaceMoves._plan_declaration_consumers(
            project_root,
            source_file,
            set(moved),
            candidate_writes,
            candidate_expected,
        )
        FlextInfraUtilitiesRefactorNamespaceMoves._write_declaration_move(
            project_root=project_root,
            gates=gates,
            writes=candidate_writes,
            expected_sources=candidate_expected,
        )

    @staticmethod
    def _import_bindings(source: str) -> MutableMapping[str, str]:
        """Map each name a module binds by import to the line that binds it.

        Returns:
            The resulting ``MutableMapping[str, str]``.

        """
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        lines = source.splitlines()
        bindings: MutableMapping[str, str] = {}
        for node in getattr(pymodule.get_ast(), "body", []) or []:
            kind = FlextInfraUtilitiesRopeAnalysis.node_kind(node)
            if kind not in {"Import", "ImportFrom"}:
                continue
            lineno = getattr(node, "lineno", 1)
            end_lineno = getattr(node, "end_lineno", None) or lineno
            import_line = "\n".join(lines[lineno - 1 : end_lineno]).strip()
            for alias in getattr(node, "names", []) or []:
                alias_name = getattr(alias, "name", "")
                alias_as = getattr(alias, "asname", None)
                bound_name = (
                    alias_as or alias_name.split(".", 1)[0]
                    if kind == "Import"
                    else alias_as or alias_name
                )
                if bound_name:
                    bindings[bound_name] = import_line
        return bindings

    @staticmethod
    def _collect_required_import_lines(
        *,
        source: str,
        blocks: Sequence[str],
    ) -> Sequence[str]:
        """Collect required import lines using rope-parsed module bodies.

        Returns:
            The resulting ``Sequence[str]``.

        """
        import_map = FlextInfraUtilitiesRefactorNamespaceMoves._import_bindings(source)
        required_imports: MutableSequence[str] = []
        seen_imports: t.Infra.StrSet = set()
        for block in blocks:
            block_pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(block)
            block_ast = FlextInfraUtilitiesRopeAnalysis.ensure_ast_node(
                block_pymodule.get_ast(),
            )
            for sub in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(block_ast):
                if FlextInfraUtilitiesRopeAnalysis.node_kind(sub) != "Name":
                    continue
                import_line = import_map.get(getattr(sub, "id", ""))
                if import_line is None or import_line in seen_imports:
                    continue
                required_imports.append(import_line)
                seen_imports.add(import_line)
        return required_imports

    @staticmethod
    def _drop_moved_alias_exports(*, source: str, alias_names: t.Infra.StrSet) -> str:
        """Remove moved aliases from a literal module ``__all__`` assignment.

        Returns:
            The resulting ``str``.

        """
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        lines = source.splitlines()
        module_ast = pymodule.get_ast()
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(module_ast):
            return source
        for node in getattr(module_ast, "body", ()) or ():
            if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(node):
                continue
            if c.Infra.DUNDER_ALL not in (
                FlextInfraUtilitiesRopeAnalysis.assignment_target_names(node)
            ):
                continue
            exports = FlextInfraUtilitiesRopeAnalysis.literal_string_sequence(
                getattr(node, "value", None),
            )
            if not exports:
                return source
            kept_exports = tuple(name for name in exports if name not in alias_names)
            if kept_exports == tuple(exports):
                return source
            line_range = FlextInfraUtilitiesRopeAnalysis.line_col_range(node)
            if line_range is None:
                return source
            start_line, _, end_line, _ = line_range
            rendered_exports = ", ".join(f'"{name}"' for name in kept_exports)
            replacement = f"__all__: list[str] = [{rendered_exports}]"
            return "\n".join((*lines[: start_line - 1], replacement, *lines[end_line:]))
        return source

    @staticmethod
    def _class_alias_names(
        project_root: Path,
        source_file: Path,
        source: str,
        alias_names: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        """Name the module-level PEP 613 aliases whose value is a class.

        ``Name: TypeAlias = Owner`` binds the class itself; its PEP 695 rewrite
        binds a ``TypeAliasType`` instead, so every runtime use of ``Name`` as
        the class breaks. A move keeps these in the PEP 613 form (operator
        decision 2026-10-25, "Exceção UP040 por identidade"); only real aliases
        become ``type`` statements. The class is proved by native Rope
        identity, never by spelling.

        Returns:
            The moved names whose ``TypeAlias`` value resolves to a class.

        Raises:
            RuntimeError: If the source is not a resource of the Rope project.

        """
        candidates = [
            (node.target.id, node.value)
            for node in ast.parse(source).body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in alias_names
            and isinstance(node.annotation, ast.Name | ast.Attribute)
            and (
                node.annotation.id
                if isinstance(node.annotation, ast.Name)
                else node.annotation.attr
            )
            == "TypeAlias"
            and isinstance(node.value, ast.Name | ast.Attribute)
        ]
        if not candidates:
            return set()
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_project:
            resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
                rope_project, source_file
            )
            if resource is None:
                msg = f"typing alias source is not a Rope resource: {source_file}"
                raise RuntimeError(msg)
            scope = FlextInfraUtilitiesRopeRuntime.build_string_module(
                rope_project, source, resource=resource
            ).get_scope()
            return {
                name
                for name, value in candidates
                if (
                    resolved := FlextInfraUtilitiesRopeRuntime.resolve_symbol(
                        scope, value
                    )
                )
                is not None
                and FlextInfraUtilitiesRopeRuntime.abstract_class(resolved.get_object())
            }

    @staticmethod
    def _moved_alias_line(
        stripped: str,
        line: str,
        public_alias_names: t.Infra.StrSet,
        class_alias_names: t.Infra.StrSet,
    ) -> str | None:
        """Return the moved statement text for one alias line, else ``None``.

        A PEP 613 alias of a class keeps its form; any other legacy
        ``TypeAlias`` becomes a PEP 695 ``type`` statement.

        Returns:
            The resulting ``str | None``.

        """
        typing_match = c.Infra.TYPING_FACTORY_ASSIGN_RE.match(stripped)
        typing_name = typing_match.group(1) if typing_match is not None else ""
        legacy_alias_match = c.Infra.LEGACY_TYPEALIAS_RE.match(stripped)
        should_move = any(
            stripped.startswith((f"type {name} =", f"{name}: TypeAlias ="))
            or typing_name == name
            for name in public_alias_names
        )
        if not should_move:
            return None
        return (
            f"type {legacy_alias_match.group(1)} = {legacy_alias_match.group(2)}"
            if legacy_alias_match is not None
            and legacy_alias_match.group(1) not in class_alias_names
            else line
        )

    @classmethod
    def _split_alias_lines(
        cls,
        lines: Sequence[str],
        public_alias_names: t.Infra.StrSet,
        class_alias_names: t.Infra.StrSet,
    ) -> tuple[list[str], list[str], int]:
        """Partition source lines into moved alias statements and kept lines.

        Returns:
            The resulting ``(moved lines, kept lines, first moved line
            number)`` triple.

        Raises:
            ValueError: If typing alias move requires an independent statement span.

        """
        module = ast.parse("\n".join(lines))
        moved_lines: list[str] = []
        ranges: list[tuple[int, int]] = []
        for node in module.body:
            first_line = lines[node.lineno - 1]
            moved = (
                first_line
                if isinstance(node, ast.TypeAlias)
                and node.name.id in public_alias_names
                else cls._moved_alias_line(
                    first_line.strip(),
                    first_line,
                    public_alias_names,
                    class_alias_names,
                )
            )
            if moved is None:
                continue
            end_line = node.end_lineno or node.lineno
            if node.col_offset or any(
                other is not node
                and other.lineno <= end_line
                and (other.end_lineno or other.lineno) >= node.lineno
                for other in module.body
            ):
                msg = "typing alias move requires an independent statement span"
                raise ValueError(msg)
            moved_lines.append("\n".join((moved, *lines[node.lineno : end_line])))
            ranges.append((node.lineno - 1, end_line))
        return (
            moved_lines,
            cls._lines_without_ranges(lines, ranges),
            min(start + 1 for start, _end in ranges) if ranges else 0,
        )

    @staticmethod
    def _import_bound_names(import_line: str) -> t.Infra.StrSet:
        """Return the names one import line binds.

        Returns:
            The resulting ``t.Infra.StrSet``.

        """
        return {
            bound
            for _name, bound in FlextInfraUtilitiesRopeSource.parse_import_names(
                import_line.partition(" import ")[2],
            )
        }

    @classmethod
    def _imports_unresolvable(
        cls,
        required_imports: Sequence[str],
        target_bindings: Mapping[str, str],
    ) -> bool:
        """Report imports the destination module cannot legally accept.

        The destination may already bind a required name to a DIFFERENT
        module: `m` is `flext_core`'s facade there and `flext_infra`'s here.
        Adding the second import redefines the name (ruff F811) and dropping
        it silently re-points the moved alias at the wrong facade, so the
        move is not mechanically resolvable and is abandoned instead.
        A facade module may not import a later layer at runtime: the declared
        order is c -> t -> p -> m -> u, and the move target here is always a
        typings module. Carrying `from <pkg> import m` into it is both a
        reverse import and, for the package's own typings module, an import
        cycle -- observed as `ImportError: cannot import name 'm'`.

        Returns:
            The resulting ``bool``.

        """
        later_layers = {"p", "m", "u"}
        for import_line in required_imports:
            for _name, bound in FlextInfraUtilitiesRopeSource.parse_import_names(
                import_line.partition(" import ")[2],
            ):
                if bound in later_layers:
                    return True
                existing = target_bindings.get(bound)
                if existing is not None and existing != import_line:
                    return True
        return False

    @staticmethod
    def _deduplicated_imports(import_lines: Sequence[str]) -> Sequence[str]:
        """Deduplicate import lines by the names they bind, first emitter wins.

        Three collectors contribute imports and they can name the same alias
        from different modules -- `m` is both flext_core's and flext_infra's
        facade. Emitting both redefines the name (ruff F811), so the list is
        deduplicated by the name each line BINDS, not by its text. The source
        module's own imports come first and win, because they are by
        construction the ones the moved declaration resolved against.

        Returns:
            The owned import sequence without a transport copy.

        """
        seen_bindings: t.Infra.StrSet = set()
        candidate_imports: MutableSequence[str] = []
        for import_line in import_lines:
            bound_names = FlextInfraUtilitiesRefactorNamespaceMoves._import_bound_names(
                import_line,
            )
            if bound_names & seen_bindings:
                continue
            seen_bindings |= bound_names
            candidate_imports.append(import_line)
        return candidate_imports

    @classmethod
    def _missing_target_imports(
        cls,
        candidate_imports: Sequence[str],
        target_source: str,
    ) -> list[str]:
        """Filter import lines the destination module does not already have.

        Returns:
            The resulting ``list[str]``.

        """
        target_lines = target_source.splitlines()
        return [
            filtered
            for import_line in candidate_imports
            if import_line not in target_lines
            if (
                filtered := cls._strip_self_bound_aliases(
                    import_line=import_line,
                    target_source=target_source,
                )
            )
        ]

    @staticmethod
    def _prepared_target_text(
        target_lines: Sequence[str],
        moved_lines: Sequence[str],
        missing_imports: Sequence[str],
    ) -> str:
        """Insert missing imports and append every moved alias statement.

        Returns:
            The resulting ``str``.

        """
        lines = FlextInfraUtilitiesRefactorNamespaceCommon.insert_import_lines(
            lines=target_lines,
            imports=missing_imports,
        )
        updated_target = "\n".join(lines).rstrip()
        for moved_line in moved_lines:
            if moved_line not in lines:
                updated_target += f"\n\n{moved_line}"
        return updated_target

    @staticmethod
    def _write_declaration_move(
        *,
        project_root: Path,
        gates: Sequence[str] | None,
        writes: Mapping[Path, str],
        expected_sources: Mapping[Path, str | None],
    ) -> None:
        """Normalize candidates and pass original source expectations by reference.

        Raises:
            RuntimeError: If the protected writer rejects the candidate.

        """
        candidate_writes = {
            path: FlextInfraUtilitiesProtectedEditLinting.normalize_source(
                project_root,
                path,
                source,
                before_source=expected_sources[path],
            ).unwrap()
            for path, source in writes.items()
        }
        ok, reports = FlextInfraUtilitiesProtectedEdit.protected_source_writes(
            candidate_writes,
            request=m.Infra.ProtectedSourceWritesRequest(
                workspace=project_root,
                expected_sources=expected_sources,
                gates=gates,
            ),
        )
        if not ok:
            FlextInfraUtilitiesRefactorNamespaceMoves._restore_rejected_writes(
                written=candidate_writes,
                expected_sources=expected_sources,
            )
            raise RuntimeError("\n".join(reports))

    @staticmethod
    def _restore_rejected_writes(
        *,
        written: Mapping[Path, str],
        expected_sources: Mapping[Path, str | None],
    ) -> None:
        """Put every file a rejected declaration move rewrote back as it was.

        The protected writer retains a rejected candidate so its lint evidence
        survives, but a declaration move is all-or-nothing: a candidate that
        fails validation must not leave the tree half-moved. A destination that
        still holds the rejected candidate is restored to its captured bytes, a
        file the move created is removed, and a destination a concurrent writer
        already advanced past this move is left alone.

        """
        for path, candidate in written.items():
            live = (
                path.read_text(encoding=c.DEFAULT_ENCODING) if path.is_file() else None
            )
            if live != candidate:
                continue
            original = expected_sources.get(path)
            if original is None:
                path.unlink(missing_ok=True)
                continue
            path.write_text(original, encoding=c.DEFAULT_ENCODING)

    @classmethod
    def _move_typing_alias_lines(
        cls,
        *,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
        gates: Sequence[str] | None,
    ) -> None:
        """Move public typing aliases and consumers in one protected transaction."""
        public_alias_names = {name for name in alias_names if not name.startswith("_")}
        if not public_alias_names:
            return
        prepared = cls._prepare_typing_alias_sources(
            project_root, source_file, public_alias_names
        )
        if prepared is None:
            return
        writes, expected_sources = prepared
        cls._plan_declaration_consumers(
            project_root,
            source_file,
            public_alias_names,
            writes,
            expected_sources,
        )
        cls._write_declaration_move(
            project_root=project_root,
            gates=gates,
            writes=writes,
            expected_sources=expected_sources,
        )

    @classmethod
    def _prepare_typing_alias_sources(
        cls,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
    ) -> tuple[MutableMapping[Path, str], MutableMapping[Path, str | None]] | None:
        """Prepare and natively parse final sources before publication.

        Returns:
            Candidate and expected sources, or None when no aliases move.

        Raises:
            RuntimeError: If the destination imports conflict.

        """
        source = source_file.read_text(encoding=c.DEFAULT_ENCODING)
        moved_lines, kept_lines, _first_moved_line = cls._split_alias_lines(
            source.splitlines(),
            alias_names,
            cls._class_alias_names(project_root, source_file, source, alias_names),
        )
        if not moved_lines:
            return None
        kept_source = cls._drop_moved_alias_exports(
            source="\n".join(kept_lines),
            alias_names=alias_names,
        )
        required_imports = cls._collect_required_import_lines(
            source=source,
            blocks=moved_lines,
        )
        target_file = FlextInfraUtilitiesRefactorNamespaceCommon.canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename=c.Infra.TYPINGS_PY,
        )
        expected_target_source = (
            target_file.read_text(encoding=c.DEFAULT_ENCODING)
            if target_file.is_file()
            else None
        )
        target_source = (
            expected_target_source
            if expected_target_source is not None
            else f"{c.Infra.FUTURE_ANNOTATIONS}\n"
        )
        if cls._imports_unresolvable(
            required_imports,
            cls._import_bindings(target_source),
        ):
            msg = f"typing alias move has conflicting imports: {target_file}"
            raise RuntimeError(msg)
        updated_target = cls._prepared_target_text(
            target_source.splitlines(),
            moved_lines,
            cls._missing_target_imports(
                cls._deduplicated_imports((
                    *required_imports,
                    *FlextInfraUtilitiesRefactorNamespaceMoves.collect_missing_runtime_alias_imports(
                        target_source=target_source,
                        blocks=moved_lines,
                    ),
                )),
                target_source,
            ),
        )
        ast.parse(updated_target)
        ast.parse(kept_source)
        return (
            {target_file: updated_target + "\n", source_file: kept_source},
            {target_file: expected_target_source, source_file: source},
        )

    @staticmethod
    def _resolve_declaration_modules(
        rope_project: t.Infra.RopeProject,
        source_file: Path,
        target_file: Path,
        alias_names: t.Infra.StrSet,
        *,
        target_exists: bool,
    ) -> tuple[str, str]:
        """Resolve the declaration owners.

        Returns:
            Source and destination module names.

        Raises:
            RuntimeError: If module identities or destination bindings conflict.

        """
        source_resource = FlextInfraUtilitiesRopeCore.resolve_resource_from_path(
            rope_project,
            source_file,
        )
        if source_resource is None:
            msg = f"typing alias source is not a Rope resource: {source_file}"
            raise RuntimeError(msg)
        source_module, target_module = (
            FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                path, project_root=Path(rope_project.root.real_path)
            )
            for path in (source_file, target_file)
        )
        if not source_module or not target_module or source_module == target_module:
            msg = f"unresolved typing alias modules: {source_file} -> {target_file}"
            raise RuntimeError(msg)
        resolved_source = rope_project.find_module(source_module)
        resolved_target = rope_project.find_module(target_module)
        source_ambiguous = (
            resolved_source is None
            or Path(resolved_source.real_path).resolve() != source_file.resolve()
        )
        target_ambiguous = not source_ambiguous and (
            (
                resolved_target is not None
                and Path(resolved_target.real_path).resolve() != target_file.resolve()
            )
            or (target_exists and resolved_target is None)
        )
        if source_ambiguous or target_ambiguous:
            msg = f"ambiguous typing alias modules: {source_module} -> {target_module}"
            raise RuntimeError(msg)
        if resolved_target is not None:
            target_names = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                rope_project,
                resolved_target,
            ).get_attributes()
            if alias_names.intersection(target_names):
                msg = (
                    f"typing alias destination already binds moved names: {target_file}"
                )
                raise RuntimeError(msg)
        return source_module, target_module

    @classmethod
    def _plan_declaration_consumers(
        cls,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
        writes: MutableMapping[Path, str],
        expected_sources: MutableMapping[Path, str | None],
    ) -> None:
        """Plan consumers before declaration removal.

        Raises:
            RuntimeError: If the destination imports its moved declarations.

        """
        target_file = next(path for path in writes if path != source_file)
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_project:
            source_module, target_module = cls._resolve_declaration_modules(
                rope_project,
                source_file,
                target_file,
                alias_names,
                target_exists=expected_sources[target_file] is not None,
            )
            writes[source_file] = (
                "\n".join(
                    FlextInfraUtilitiesRefactorNamespaceCommon.insert_import_lines(
                        lines=writes[source_file].splitlines(),
                        imports=cls._declaration_source_imports(
                            target_module=target_module,
                            kept_source=writes[source_file],
                            alias_names=alias_names,
                        ),
                    ),
                ).rstrip()
                + "\n"
            )
            for resource in FlextInfraUtilitiesRopeCore.python_resources(rope_project):
                path = Path(resource.real_path).resolve()
                if path == source_file.resolve():
                    continue
                original = resource.read()
                prepared = FlextInfraUtilitiesRopeImports.plan_from_import_aliases(
                    rope_project,
                    resource,
                    source_module=source_module,
                    target_module=target_module,
                    aliases=sorted(alias_names),
                )
                if prepared is None:
                    continue
                if path == target_file.resolve():
                    msg = (
                        "typing alias destination imports its moved declarations: "
                        f"{path}"
                    )
                    raise RuntimeError(msg)
                expected_sources[path] = original
                writes[path] = prepared

    @staticmethod
    def _declaration_source_imports(
        *,
        target_module: str,
        kept_source: str,
        alias_names: t.Infra.StrSet,
    ) -> Sequence[str]:
        """Return imports re-binding moved aliases still referenced by the source."""
        source_pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(
            kept_source,
        )
        source_ast = FlextInfraUtilitiesRopeAnalysis.ensure_ast_node(
            source_pymodule.get_ast(),
        )
        referenced_aliases = sorted({
            getattr(node, "id", "")
            for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(source_ast)
            if FlextInfraUtilitiesRopeAnalysis.node_kind(node) == "Name"
            and getattr(node, "id", "") in alias_names
        })
        referenced_aliases = [name for name in referenced_aliases if name]
        if not referenced_aliases:
            return ()
        import_line = f"from {target_module} import {', '.join(referenced_aliases)}"
        return [import_line] if import_line not in kept_source.splitlines() else ()

    @classmethod
    def _strip_self_bound_aliases(cls, *, import_line: str, target_source: str) -> str:
        """Drop names already bound locally in the move target from an import.

        A facade-root module (``typings.py``, ``constants.py``, ...) binds its
        canonical alias directly (``t = <Project>Types``). Injecting
        ``from <pkg> import t`` there is a self-package import that shadows the
        binding and raises F811. Keep only the names the target does not already
        own; return ``""`` when nothing remains so the whole line is dropped.

        Returns:
            The resulting ``str``.

        """
        prefix, separator, names_part = import_line.partition(" import ")
        if not separator:
            return import_line
        kept = [
            f"{name} as {bound}" if name != bound else name
            for name, bound in FlextInfraUtilitiesRopeSource.parse_import_names(
                names_part,
            )
            if not FlextInfraUtilitiesTransformerHeader.alias_locally_bound(
                target_source,
                bound,
            )
        ]
        if not kept:
            return ""
        return f"{prefix} import {', '.join(kept)}"

    @staticmethod
    def collect_missing_runtime_alias_imports(
        *,
        target_source: str,
        blocks: Sequence[str],
    ) -> Sequence[str]:
        """Collect missing runtime alias imports.

        Returns:
            The resulting ``Sequence[str]``.

        """
        moved_source = "\n".join(blocks)
        moved_pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(
            moved_source,
        )
        moved_ast = FlextInfraUtilitiesRopeAnalysis.ensure_ast_node(
            moved_pymodule.get_ast(),
        )
        runtime_aliases = u.runtime_alias_names(c.Infra.PKG_INFRA_UNDERSCORE)
        moved_ast = moved_pymodule.get_ast()
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(moved_ast):
            return ()
        moved_aliases: set[str] = set()
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(moved_ast):
            if FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "Name":
                continue
            node_id = getattr(node, "id", "")
            if node_id in runtime_aliases:
                moved_aliases.add(node_id)
        if not moved_aliases:
            return ()
        imported_aliases: t.Infra.StrSet = set()
        for match in c.Infra.FROM_IMPORT_RE.finditer(target_source):
            imported_aliases.update(
                bound
                for _, bound in FlextInfraUtilitiesRopeSource.parse_import_names(
                    match.group(2),
                )
            )
        for match in c.Infra.FROM_IMPORT_BLOCK_RE.finditer(target_source):
            imported_aliases.update(
                bound
                for _, bound in FlextInfraUtilitiesRopeSource.parse_import_names(
                    match.group(2),
                )
            )
        missing_aliases = sorted(moved_aliases - imported_aliases)
        if not missing_aliases:
            return ()
        return [
            f"from {c.Infra.PKG_CORE_UNDERSCORE} import {', '.join(missing_aliases)}",
        ]


__all__: list[str] = ["FlextInfraUtilitiesRefactorNamespaceMoves"]
