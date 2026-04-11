"""Move and compatibility rewrites for namespace refactors."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactorNamespaceCommon,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorNamespaceMoves(
    FlextInfraUtilitiesRefactorNamespaceCommon
):
    """Helpers for block moves and compatibility-alias rewrites."""

    @classmethod
    def rewrite_import_violations(
        cls,
        *,
        py_files: Sequence[Path],
        project_package: str,
    ) -> None:
        if not py_files:
            return
        with FlextInfraUtilitiesRope.open_project(
            cls._shared_workspace_root(py_files=py_files),
        ) as rope_project:
            for file_path in py_files:
                if file_path.name == c.Infra.Files.INIT_PY:
                    continue
                project_root = (
                    FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
                        file_path,
                    )
                )
                if project_root is not None and (
                    FlextInfraUtilitiesDiscovery.contextual_runtime_alias_sources(
                        project_root=project_root,
                        file_path=file_path,
                    )
                ):
                    continue
                try:
                    source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                except OSError:
                    continue
                if FlextInfraUtilitiesParsing.looks_like_facade_file(
                    file_path=file_path,
                    source=source,
                ):
                    continue
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if resource is None:
                    continue
                rewritten = FlextInfraUtilitiesRope.collapse_submodule_alias_imports(
                    rope_project,
                    resource,
                    package_name=project_package,
                    aliases=tuple(sorted(c.Infra.RUNTIME_ALIAS_NAMES)),
                    apply=True,
                )
                if rewritten is None:
                    continue
                _ = FlextInfraUtilitiesRope.organize_imports(
                    rope_project,
                    resource,
                    apply=True,
                )
                FlextInfraUtilitiesFormatting.run_ruff_fix(file_path)

    @classmethod
    def rewrite_runtime_alias_violations(
        cls,
        *,
        py_files: Sequence[Path],
    ) -> None:
        if not py_files:
            return
        workspace_root = cls._shared_workspace_root(py_files=py_files)
        with FlextInfraUtilitiesRope.open_project(
            workspace_root,
        ) as rope_project:
            for file_path in py_files:
                expected = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(file_path.name)
                if expected is None:
                    continue
                alias_name, expected_suffix = expected
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if resource is None:
                    continue
                class_candidates = [
                    info.name
                    for info in FlextInfraUtilitiesRope.get_class_info(
                        rope_project,
                        resource,
                    )
                    if info.name.endswith(expected_suffix)
                ]
                if len(class_candidates) != 1:
                    continue
                target_class = class_candidates[0]
                lines = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                ).splitlines()
                kept = [
                    line
                    for line in lines
                    if not line.strip().startswith(f"{alias_name} = ")
                ]
                rewritten = (
                    "\n".join(kept).rstrip() + f"\n\n{alias_name} = {target_class}\n"
                )
                original_source = file_path.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                if rewritten == original_source:
                    continue
                _ = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                    file_path,
                    workspace=workspace_root,
                    updated_source=rewritten,
                    keep_backup=True,
                )

    @staticmethod
    def rewrite_manual_protocol_violations(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        violations: Sequence[m.Infra.ManualProtocolViolation],
    ) -> None:
        grouped: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped[Path(violation.file)].add(violation.name)
        protocol_moves: MutableSequence[
            t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]
        ] = []
        for source_file, protocol_names in grouped.items():
            move = FlextInfraUtilitiesRefactorNamespaceMoves._move_named_blocks(
                project_root=project_root,
                source_file=source_file,
                target_filename=c.Infra.Files.PROTOCOLS_PY,
                names=protocol_names,
                header_prefix="class ",
            )
            if move is not None:
                protocol_moves.append(move)
        if protocol_moves:
            FlextInfraUtilitiesRefactorNamespaceMoves._rewrite_moved_imports(
                project_root=project_root,
                py_files=py_files,
                moves=protocol_moves,
            )

    @staticmethod
    def rewrite_manual_typing_alias_violations(
        *,
        project_root: Path,
        violations: Sequence[m.Infra.ManualTypingAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        _ = parse_failures
        grouped: Mapping[Path, t.Infra.StrSet] = defaultdict(set)
        for violation in violations:
            grouped[Path(violation.file)].add(violation.name)
        for source_file, alias_names in grouped.items():
            FlextInfraUtilitiesRefactorNamespaceMoves._move_typing_alias_lines(
                project_root=project_root,
                source_file=source_file,
                alias_names=alias_names,
            )

    @staticmethod
    def rewrite_compatibility_alias_violations(
        *,
        violations: Sequence[m.Infra.CompatibilityAliasViolation],
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
    ) -> None:
        _ = parse_failures
        grouped: Mapping[Path, t.MutableStrMapping] = defaultdict(dict)
        for violation in violations:
            grouped[Path(violation.file)][violation.alias_name] = violation.target_name
        for file_path, alias_map in grouped.items():
            FlextInfraUtilitiesRefactorNamespaceMoves._rewrite_compat_aliases_in_file(
                file_path=file_path,
                alias_map=alias_map,
            )

    @staticmethod
    def _rewrite_compat_aliases_in_file(
        *,
        file_path: Path,
        alias_map: t.StrMapping,
    ) -> None:
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        kept_source = "\n".join(
            line
            for line in source.splitlines()
            if FlextInfraUtilitiesRefactorNamespaceMoves._compat_assignment_target(
                line,
                alias_map=alias_map,
            )
            is None
        )
        rewritten = FlextInfraUtilitiesRefactorNamespaceMoves._apply_token_replacements(
            source=kept_source,
            alias_map=alias_map,
        )
        if rewritten != source:
            _ = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                file_path,
                workspace=file_path.parent,
                updated_source=rewritten,
                keep_backup=True,
            )

    @staticmethod
    def _move_named_blocks(
        *,
        project_root: Path,
        source_file: Path,
        target_filename: str,
        names: t.Infra.StrSet,
        header_prefix: str,
    ) -> t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]] | None:
        source = source_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        blocks: MutableSequence[str] = []
        ranges: MutableSequence[t.Infra.IntPair] = []
        moved: MutableSequence[str] = []
        for name in sorted(names):
            found = FlextInfraUtilitiesRefactorNamespaceMoves._find_top_level_block(
                lines=lines,
                header=f"{header_prefix}{name}",
            )
            if found is None:
                continue
            start, end = found
            blocks.append("\n".join(lines[start:end]))
            ranges.append((start, end))
            moved.append(name)
        if not blocks:
            return None
        target_file = FlextInfraUtilitiesRefactorNamespaceMoves._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename=target_filename,
        )
        required_imports = (
            FlextInfraUtilitiesRefactorNamespaceMoves._collect_required_import_lines(
                source=source,
                blocks=blocks,
            )
        )
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else f"{c.Infra.SourceCode.FUTURE_ANNOTATIONS}\n"
        )
        target_lines = target_source.splitlines()
        target_lines = FlextInfraUtilitiesRefactorNamespaceMoves._insert_import_lines(
            lines=target_lines,
            imports=required_imports,
        )
        updated_target = "\n".join(target_lines).rstrip()
        for block in blocks:
            if block.splitlines()[0] not in updated_target:
                updated_target += f"\n\n{block}"
        filtered_lines = list(lines)
        for start, end in sorted(ranges, reverse=True):
            del filtered_lines[start:end]

        def _post_write() -> None:
            FlextInfraUtilitiesFormatting.run_ruff_fix(source_file, quiet=True)
            FlextInfraUtilitiesFormatting.run_ruff_fix(target_file, quiet=True)

        ok, _ = FlextInfraUtilitiesProtectedEdit.protected_source_writes(
            {
                target_file: updated_target.rstrip() + "\n",
                source_file: "\n".join(filtered_lines).rstrip() + "\n",
            },
            workspace=project_root,
            keep_backup=True,
            post_write=_post_write,
        )
        if not ok:
            return None
        return (source_file, target_file, tuple(moved))

    @staticmethod
    def _collect_required_import_lines(
        *,
        source: str,
        blocks: Sequence[str],
    ) -> t.StrSequence:
        source_ast = ast.parse(source)
        source_lines = source.splitlines()
        import_map: dict[str, str] = {}
        for node in source_ast.body:
            if isinstance(node, ast.Import):
                import_line = "\n".join(
                    source_lines[node.lineno - 1 : node.end_lineno],
                ).strip()
                for alias in node.names:
                    bound_name = alias.asname or alias.name.split(".", 1)[0]
                    import_map[bound_name] = import_line
            if isinstance(node, ast.ImportFrom):
                import_line = "\n".join(
                    source_lines[node.lineno - 1 : node.end_lineno],
                ).strip()
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    import_map[bound_name] = import_line
        required_imports: MutableSequence[str] = []
        seen_imports: t.Infra.StrSet = set()
        for block in blocks:
            block_ast = ast.parse(block)
            for node in ast.walk(block_ast):
                if not isinstance(node, ast.Name):
                    continue
                import_line = import_map.get(node.id)
                if import_line is None or import_line in seen_imports:
                    continue
                required_imports.append(import_line)
                seen_imports.add(import_line)
        return required_imports

    @staticmethod
    def _move_typing_alias_lines(
        *,
        project_root: Path,
        source_file: Path,
        alias_names: t.Infra.StrSet,
    ) -> None:
        source = source_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        moved_lines: MutableSequence[str] = []
        kept_lines: MutableSequence[str] = []
        for line in lines:
            stripped = line.strip()
            typing_match = c.Infra.TYPING_FACTORY_ASSIGN_RE.match(stripped)
            typing_name = typing_match.group(1) if typing_match is not None else ""
            should_move = any(
                stripped.startswith((f"type {name} =", f"{name}: TypeAlias ="))
                or typing_name == name
                for name in alias_names
            )
            if should_move:
                moved_lines.append(line)
            else:
                kept_lines.append(line)
        if not moved_lines:
            return
        required_imports = (
            FlextInfraUtilitiesRefactorNamespaceMoves._collect_required_import_lines(
                source=source,
                blocks=moved_lines,
            )
        )
        target_file = FlextInfraUtilitiesRefactorNamespaceMoves._canonical_target_file(
            project_root=project_root,
            source_file=source_file,
            filename=c.Infra.Files.TYPINGS_PY,
        )
        target_source = (
            target_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target_file.exists()
            else f"{c.Infra.SourceCode.FUTURE_ANNOTATIONS}\n"
        )
        target_lines = target_source.splitlines()
        missing_imports = [
            import_line
            for import_line in required_imports
            if import_line not in target_lines
        ]
        target_lines = FlextInfraUtilitiesRefactorNamespaceMoves._insert_import_lines(
            lines=target_lines,
            imports=missing_imports,
        )
        updated_target = "\n".join(target_lines).rstrip()
        for moved_line in moved_lines:
            if moved_line not in target_lines:
                updated_target += f"\n\n{moved_line}"

        def _post_write() -> None:
            FlextInfraUtilitiesFormatting.run_ruff_fix(source_file, quiet=True)
            FlextInfraUtilitiesFormatting.run_ruff_fix(target_file, quiet=True)

        ok, _ = FlextInfraUtilitiesProtectedEdit.protected_source_writes(
            {
                target_file: updated_target + "\n",
                source_file: "\n".join(kept_lines).rstrip() + "\n",
            },
            workspace=project_root,
            keep_backup=True,
            post_write=_post_write,
        )
        _ = ok

    @staticmethod
    def _rewrite_moved_imports(
        *,
        project_root: Path,
        py_files: Sequence[Path],
        moves: Sequence[t.Infra.Triple[Path, Path, t.Infra.VariadicTuple[str]]],
    ) -> None:
        with FlextInfraUtilitiesRope.open_project(project_root) as rope_project:
            mappings: MutableSequence[
                t.Infra.Triple[str, str, t.Infra.VariadicTuple[str]]
            ] = []
            for source, target, names in moves:
                source_resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project, source
                )
                target_resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project, target
                )
                if source_resource is None or target_resource is None:
                    continue
                try:
                    source_module = FlextInfraUtilitiesRope.get_pymodule(
                        rope_project, source_resource
                    ).get_name()
                    target_module = FlextInfraUtilitiesRope.get_pymodule(
                        rope_project, target_resource
                    ).get_name()
                except (
                    *FlextInfraUtilitiesRope.RUNTIME_ERRORS,
                    *FlextInfraUtilitiesRope.SYNTAX_ERRORS,
                    TypeError,
                ):
                    continue
                if source_module and target_module:
                    mappings.append((source_module, target_module, names))
            for py_file in py_files:
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project, py_file
                )
                if resource is None:
                    continue
                original_source = py_file.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                changed = False
                for source_module, target_module, names in mappings:
                    updated = FlextInfraUtilitiesRope.relocate_from_import_aliases(
                        rope_project,
                        resource,
                        source_module=source_module,
                        target_module=target_module,
                        aliases=names,
                        apply=True,
                    )
                    changed = changed or updated is not None
                if changed:
                    _ = FlextInfraUtilitiesRope.organize_imports(
                        rope_project,
                        resource,
                        apply=True,
                    )
                    backup_path = py_file.with_suffix(
                        py_file.suffix + c.Infra.SafeExecution.BAK_SUFFIX,
                    )
                    if not backup_path.exists():
                        backup_path.write_text(
                            original_source,
                            encoding=c.Infra.Encoding.DEFAULT,
                        )


__all__ = ["FlextInfraUtilitiesRefactorNamespaceMoves"]
