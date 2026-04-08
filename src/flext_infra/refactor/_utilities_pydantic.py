"""AST-driven centralizer for Pydantic models and dict-like contracts.

Centralizes the ``FlextInfraRefactorPydanticCentralizer`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesFormatting,
    FlextInfraUtilitiesImportNormalizer,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorPydantic:
    """Centralize model contracts into ``models.py``/``_models.py`` files.

    Usage via namespace::

        from flext_infra import u

        stats = u.Infra.centralize_workspace(
            workspace_root,
            apply=True,
            normalize_remaining=False,
        )
    """

    _PYDANTIC_SCOPE_DIRS: t.StrSequence = (
        c.Infra.Paths.DEFAULT_SRC_DIR,
        c.Infra.Directories.TESTS,
        c.Infra.Directories.SCRIPTS,
        c.Infra.Directories.EXAMPLES,
    )
    _PYDANTIC_SKIP_DIRS: frozenset[str] = c.Infra.Excluded.COMMON_EXCLUDED_DIRS
    _PYDANTIC_PROTECTED_FILENAMES: t.StrSequence = (
        "settings.py",
        c.Infra.Files.INIT_PY,
    )
    _PYDANTIC_AUTO_APPLY_CLASS_KINDS: t.StrSequence = (
        "typed_dict",
        "typed_dict_factory",
    )

    @staticmethod
    def _is_target_python(file_path: Path) -> bool:
        if file_path.suffix != c.Infra.Extensions.PYTHON:
            return False
        if any(
            part in FlextInfraUtilitiesRefactorPydantic._PYDANTIC_SKIP_DIRS
            for part in file_path.parts
        ):
            return False
        if (
            file_path.name
            in FlextInfraUtilitiesRefactorPydantic._PYDANTIC_PROTECTED_FILENAMES
        ):
            return False
        parts = set(file_path.parts)
        return bool(
            parts.intersection(
                FlextInfraUtilitiesRefactorPydantic._PYDANTIC_SCOPE_DIRS,
            ),
        )

    @staticmethod
    def _is_allowed_model_path(file_path: Path) -> bool:
        posix = file_path.as_posix()
        return posix.endswith(("/models.py", "/_models.py")) or "/models/" in posix

    @staticmethod
    def _ensure_dest_header(dest_path: Path) -> str:
        if dest_path.exists():
            return dest_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        return (
            '"""Auto-generated centralized models."""\n\n'
            "from __future__ import annotations\n"
        )

    @staticmethod
    def _append_unique_blocks(
        existing: str,
        blocks: t.StrSequence,
        names: t.StrSequence,
    ) -> str:
        updated = existing
        for name, block in zip(names, blocks, strict=True):
            if f"class {name}(" in updated or f"class {name}:" in updated:
                continue
            updated = updated.rstrip() + "\n\n" + block.rstrip() + "\n"
        return updated

    @staticmethod
    def _import_supplies_name(node: ast.Import | ast.ImportFrom, name: str) -> bool:
        if isinstance(node, ast.Import):
            return any(
                (alias.asname or alias.name.split(".", maxsplit=1)[0]) == name
                for alias in node.names
            )
        return any((alias.asname or alias.name) == name for alias in node.names)

    @staticmethod
    def _alias_import_lines(
        file_path: Path,
        alias_moves: Sequence[m.Infra.AliasMove],
    ) -> t.StrSequence:
        needed_names = {
            node.id
            for move in alias_moves
            for node in ast.walk(ast.parse(move.alias_expr, mode="eval"))
            if isinstance(node, ast.Name)
        }
        if not needed_names:
            return []
        source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        module = ast.parse(source)
        lines = source.splitlines()
        imports: list[str] = []
        for node in module.body:
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if not any(
                FlextInfraUtilitiesRefactorPydantic._import_supplies_name(node, name)
                for name in needed_names
            ):
                continue
            import_line = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            if import_line not in imports:
                imports.append(import_line)
        return imports

    @staticmethod
    def _normalize_disallowed_bases(
        file_path: Path,
        *,
        apply: bool,
    ) -> bool:
        _ = file_path
        _ = apply
        return False

    @staticmethod
    def _process_single_file(
        file_path: Path,
        *,
        apply: bool,
        failure_stats: m.Infra.CentralizerFailureStats,
    ) -> m.Infra.CentralizerFileResult | None:
        """Process a single file for model centralization.

        Returns None if the file has no moves, or a result with move details.
        """
        cls = FlextInfraUtilitiesRefactorPydantic
        found_models, found_aliases = (
            FlextInfraUtilitiesRefactorPydanticAnalysis.scan_file_violations(file_path)
        )
        collected_moves = (
            FlextInfraUtilitiesRefactorPydanticAnalysis.collect_moves_safe(
                file_path,
                failure_stats=failure_stats,
            )
        )
        if collected_moves is None:
            return m.Infra.CentralizerFileResult(
                found_models=found_models,
                found_aliases=found_aliases,
            )
        class_moves, alias_moves = collected_moves
        if not class_moves and not alias_moves:
            return m.Infra.CentralizerFileResult(
                found_models=found_models,
                found_aliases=found_aliases,
            )
        apply_class_moves = class_moves
        apply_alias_moves = alias_moves
        if apply:
            apply_class_moves = [
                move
                for move in class_moves
                if move.kind in cls._PYDANTIC_AUTO_APPLY_CLASS_KINDS
            ]
            apply_alias_moves = alias_moves
            if not apply_class_moves and not apply_alias_moves:
                return m.Infra.CentralizerFileResult(
                    found_models=found_models,
                    found_aliases=found_aliases,
                    skipped_non_necessary=True,
                )
        return m.Infra.CentralizerFileResult(
            found_models=found_models,
            found_aliases=found_aliases,
            apply_class_moves=list(apply_class_moves),
            apply_alias_moves=list(apply_alias_moves),
        )

    @staticmethod
    def _apply_moves(
        file_path: Path,
        result: m.Infra.CentralizerFileResult,
    ) -> t.Infra.Triple[Path, str, str]:
        """Build updated destination and source content for a file's moves."""
        cls = FlextInfraUtilitiesRefactorPydantic
        apply_class_moves = result.apply_class_moves
        apply_alias_moves = result.apply_alias_moves
        dest_path = file_path.parent / "_models.py"
        class_blocks = [mv.source for mv in apply_class_moves]
        class_names = [mv.name for mv in apply_class_moves]
        alias_blocks = [
            f"class {a.name}(RootModel[{a.alias_expr}]):\n    pass\n"
            for a in apply_alias_moves
        ]
        alias_names = [a.name for a in apply_alias_moves]
        dest_imports = [
            *(["from pydantic import RootModel"] if apply_alias_moves else []),
            *cls._alias_import_lines(file_path, apply_alias_moves),
        ]
        existing_dest = cls._ensure_dest_header(dest_path)
        updated_dest = (
            FlextInfraUtilitiesRefactorPydanticAnalysis.insert_import_statements(
                existing_dest,
                dest_imports,
            )
        )
        updated_dest = cls._append_unique_blocks(
            updated_dest, class_blocks, class_names
        )
        updated_dest = cls._append_unique_blocks(
            updated_dest, alias_blocks, alias_names
        )
        moved_names = [mv.name for mv in apply_class_moves] + [
            a.name for a in apply_alias_moves
        ]
        package_dir, package_name = FlextInfraUtilitiesDiscovery.package_context(
            file_path,
        )
        import_module = FlextInfraUtilitiesImportNormalizer.file_to_module(
            file_path=dest_path,
            package_dir=package_dir,
            package_name=package_name,
        )
        updated_source = FlextInfraUtilitiesRefactorPydanticAnalysis.rewrite_source(
            file_path,
            apply_class_moves,
            apply_alias_moves,
            import_statement=f"from {import_module} import {', '.join(sorted(set(moved_names)))}",
        )
        return (dest_path, updated_dest, updated_source)

    @staticmethod
    def _apply_protected_updates(
        *,
        workspace_root: Path,
        source_file: Path,
        dest_path: Path,
        updated_dest: str,
        updated_source: str,
    ) -> bool:
        package_dir, package_name = FlextInfraUtilitiesDiscovery.package_context(
            source_file,
        )
        lint_workspace = package_dir.parent if package_name else workspace_root

        def _post_write() -> None:
            FlextInfraUtilitiesFormatting.run_ruff_fix(source_file, quiet=True)
            FlextInfraUtilitiesFormatting.run_ruff_fix(dest_path, quiet=True)

        ok, _ = FlextInfraUtilitiesProtectedEdit.protected_source_writes(
            {
                dest_path: updated_dest,
                source_file: updated_source,
            },
            workspace=lint_workspace,
            keep_backup=True,
            post_write=_post_write,
        )
        return ok

    @staticmethod
    def _normalize_pass(
        python_files: Sequence[Path],
        *,
        apply: bool,
    ) -> int:
        """Run normalization pass over files, returning count of normalized files."""
        cls = FlextInfraUtilitiesRefactorPydantic
        normalized_files = 0
        for file_path in python_files:
            if not cls._is_target_python(file_path):
                continue
            if cls._is_allowed_model_path(file_path):
                continue
            try:
                changed = cls._normalize_disallowed_bases(file_path, apply=apply)
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            if changed:
                normalized_files += 1
        return normalized_files

    @staticmethod
    def centralize_workspace(
        workspace_root: Path,
        *,
        apply: bool,
        normalize_remaining: bool,
    ) -> t.IntMapping:
        """Centralize model contracts and normalize namespace scaffolds."""
        cls = FlextInfraUtilitiesRefactorPydantic
        moved_classes = 0
        moved_aliases = 0
        normalized_files = 0
        touched_files = 0
        scanned_files = 0
        detected_model_violations = 0
        detected_alias_violations = 0
        failed_apply_writes = 0
        created_model_files = 0
        created_typings_files = 0
        skipped_nonpackage_apply = 0
        skipped_non_necessary_apply = 0
        failure_stats = m.Infra.CentralizerFailureStats()
        files_result = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root=workspace_root,
        )
        if files_result.is_failure:
            return {
                "scanned_files": scanned_files,
                "touched_files": touched_files,
                "moved_classes": moved_classes,
                "moved_aliases": moved_aliases,
                "normalized_files": normalized_files,
                "detected_model_violations": detected_model_violations,
                "detected_alias_violations": detected_alias_violations,
                "failed_apply_writes": failed_apply_writes,
                "created_model_files": created_model_files,
                "created_typings_files": created_typings_files,
                "skipped_nonpackage_apply": skipped_nonpackage_apply,
                "skipped_non_necessary_apply": skipped_non_necessary_apply,
                "parse_syntax_errors": failure_stats.parse_syntax_errors,
                "parse_encoding_errors": failure_stats.parse_encoding_errors,
                "parse_io_errors": failure_stats.parse_io_errors + 1,
            }
        python_files = files_result.value
        for file_path in python_files:
            if not cls._is_target_python(file_path):
                continue
            if cls._is_allowed_model_path(file_path):
                continue
            scanned_files += 1
            result = cls._process_single_file(
                file_path,
                apply=apply,
                failure_stats=failure_stats,
            )
            if result is None:
                continue
            detected_model_violations += result.found_models
            detected_alias_violations += result.found_aliases
            if result.skipped_non_necessary:
                skipped_non_necessary_apply += 1
                continue
            if not result.apply_class_moves and not result.apply_alias_moves:
                continue
            dest_path = file_path.parent / "_models.py"
            dest_exists = dest_path.exists()
            dest_path, updated_dest, updated_source = cls._apply_moves(
                file_path, result
            )
            if apply:
                if not (file_path.parent / c.Infra.Files.INIT_PY).exists():
                    skipped_nonpackage_apply += 1
                    continue
                if not cls._apply_protected_updates(
                    workspace_root=workspace_root,
                    source_file=file_path,
                    dest_path=dest_path,
                    updated_dest=updated_dest,
                    updated_source=updated_source,
                ):
                    failed_apply_writes += 1
                    continue
            if not dest_exists:
                created_model_files += 1
            moved_classes += len(result.apply_class_moves)
            moved_aliases += len(result.apply_alias_moves)
            touched_files += 1
        if normalize_remaining:
            normalized_files = cls._normalize_pass(python_files, apply=apply)
        return {
            "scanned_files": scanned_files,
            "touched_files": touched_files,
            "moved_classes": moved_classes,
            "moved_aliases": moved_aliases,
            "normalized_files": normalized_files,
            "detected_model_violations": detected_model_violations,
            "detected_alias_violations": detected_alias_violations,
            "failed_apply_writes": failed_apply_writes,
            "created_model_files": created_model_files,
            "created_typings_files": created_typings_files,
            "skipped_nonpackage_apply": skipped_nonpackage_apply,
            "skipped_non_necessary_apply": skipped_non_necessary_apply,
            "parse_syntax_errors": failure_stats.parse_syntax_errors,
            "parse_encoding_errors": failure_stats.parse_encoding_errors,
            "parse_io_errors": failure_stats.parse_io_errors,
        }


__all__ = ["FlextInfraUtilitiesRefactorPydantic"]
