"""AST import and reference rewriting for MRO migrations."""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, u
from flext_infra.codegen.transforms import FlextInfraCodegenTransforms
from flext_infra.transformers.mro_reference_rewriter import (
    FlextInfraRefactorMROReferenceRewriter,
)


class FlextInfraRefactorMROImportRewriter:
    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        moved_index: dict[str, dict[str, str]],
        module_facade_aliases: dict[str, str],
        apply: bool,
    ) -> list[m.Infra.MRORewriteResult]:
        """Rewrite all eligible Python files inside a workspace."""
        results: list[m.Infra.MRORewriteResult] = []
        for file_path in cls._iter_workspace_python_files(
            workspace_root=workspace_root,
        ):
            rewritten = cls.rewrite_file(
                file_path=file_path,
                moved_index=moved_index,
                module_facade_aliases=module_facade_aliases,
                apply=apply,
            )
            if rewritten is not None and rewritten.replacements > 0:
                results.append(rewritten)
        return results

    @staticmethod
    def rewrite_file(
        *,
        file_path: Path,
        moved_index: dict[str, dict[str, str]],
        module_facade_aliases: dict[str, str],
        apply: bool,
    ) -> m.Infra.MRORewriteResult | None:
        """Rewrite one file and return replacement statistics."""
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return None
        tree = u.Infra.parse_ast_from_source(source)
        if tree is None:
            return None
        imported_symbols: dict[str, m.Infra.MROImportRewrite] = {}
        module_aliases: dict[str, str] = {}
        facade_aliases: dict[str, str] = {}
        module_facade_alias: dict[str, str] = {}
        facade_imports_needed: set[str] = set()
        facade_import_objects: dict[str, m.Infra.MROImportRewrite] = {}
        for stmt in tree.body:
            if isinstance(stmt, ast.ImportFrom):
                module_name = stmt.module
                if module_name is None or module_name not in moved_index:
                    continue
                if any(alias.name == "*" for alias in stmt.names):
                    continue
                kept_names: list[ast.alias] = []
                for alias in stmt.names:
                    default_facade_alias = module_facade_aliases.get(
                        module_name,
                        c.Infra.DEFAULT_FACADE_ALIAS,
                    )
                    if alias.name == default_facade_alias:
                        facade_local_name = default_facade_alias
                        facade_aliases[facade_local_name] = module_name
                        module_facade_alias[module_name] = facade_local_name
                        facade_import = m.Infra.MROImportRewrite(
                            module=module_name,
                            import_name=default_facade_alias,
                            as_name=None,
                            symbol="",
                            facade_name=facade_local_name,
                        )
                        facade_key = f"{facade_import.module}:{facade_import.import_name}:{facade_import.as_name or ''}"
                        facade_imports_needed.add(facade_key)
                        facade_import_objects[facade_key] = facade_import
                        if alias.asname is None or alias.asname == default_facade_alias:
                            kept_names.append(ast.alias(name=default_facade_alias))
                        continue
                    symbol_map = moved_index[module_name]
                    new_symbol = symbol_map.get(alias.name)
                    if new_symbol is None:
                        kept_names.append(alias)
                        continue
                    imported_symbols[alias.asname or alias.name] = (
                        m.Infra.MROImportRewrite(
                            module=module_name,
                            import_name=default_facade_alias,
                            as_name=None,
                            symbol=new_symbol,
                            facade_name=module_facade_alias.get(
                                module_name,
                                default_facade_alias,
                            ),
                        )
                    )
                    facade_import = m.Infra.MROImportRewrite(
                        module=module_name,
                        import_name=default_facade_alias,
                        as_name=None
                        if module_name not in module_facade_alias
                        else (
                            None
                            if module_facade_alias[module_name] == default_facade_alias
                            else module_facade_alias[module_name]
                        ),
                        symbol="",
                        facade_name=module_facade_alias.get(
                            module_name,
                            default_facade_alias,
                        ),
                    )
                    facade_key = f"{facade_import.module}:{facade_import.import_name}:{facade_import.as_name or ''}"
                    facade_imports_needed.add(facade_key)
                    facade_import_objects[facade_key] = facade_import
                stmt.names = kept_names
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    if alias.name in moved_index:
                        module_aliases[alias.asname or alias.name] = alias.name
        rewriter = FlextInfraRefactorMROReferenceRewriter(
            imported_symbols=imported_symbols,
            module_aliases=module_aliases,
            module_facades=facade_aliases,
            moved_index=moved_index,
        )
        rewritten = rewriter.visit(tree)
        if not isinstance(rewritten, ast.Module):
            return None
        rewritten.body = [
            stmt
            for stmt in rewritten.body
            if not (
                isinstance(stmt, ast.ImportFrom)
                and stmt.module in moved_index
                and (len(stmt.names) == 0)
            )
        ]
        existing_imports: set[str] = set()
        for stmt in rewritten.body:
            if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
                for alias in stmt.names:
                    if alias.name != "*":
                        key = f"{stmt.module}:{alias.name}:{alias.asname or ''}"
                        existing_imports.add(key)
        imports_to_add = sorted(facade_imports_needed - existing_imports)
        if len(imports_to_add) > 0:
            insert_at = FlextInfraCodegenTransforms.find_insert_position(rewritten)
            for offset, facade_key in enumerate(imports_to_add):
                facade_import = facade_import_objects[facade_key]
                rewritten.body.insert(
                    insert_at + offset,
                    ast.ImportFrom(
                        module=facade_import.module,
                        names=[
                            ast.alias(
                                name=facade_import.import_name,
                                asname=facade_import.as_name,
                            ),
                        ],
                        level=0,
                    ),
                )
        if rewriter.replacements == 0 and len(imports_to_add) == 0:
            return None
        rendered = ast.unparse(ast.fix_missing_locations(rewritten))
        if apply and rendered != source:
            _ = file_path.write_text(f"{rendered}\n", encoding=c.Infra.Encoding.DEFAULT)
        return m.Infra.MRORewriteResult(
            file=str(file_path),
            replacements=rewriter.replacements,
        )

    @staticmethod
    def _iter_workspace_python_files(*, workspace_root: Path) -> list[Path]:
        result = u.Infra.iter_python_files(workspace_root=workspace_root)
        return result.fold(
            on_failure=lambda _: [],
            on_success=lambda v: v,
        )


__all__ = ["FlextInfraRefactorMROImportRewriter"]
