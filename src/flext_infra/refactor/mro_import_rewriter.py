"""AST import and reference rewriting for MRO migrations."""

from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import libcst as cst

from flext_infra import (
    FlextInfraRefactorMROReferenceRewriter,
    c,
    m,
    t,
    u,
)


class FlextInfraRefactorMROImportRewriter:
    """Rewrite import statements across workspace after MRO class relocations."""

    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        moved_index: Mapping[str, t.StrMapping],
        module_facade_aliases: t.StrMapping,
        apply: bool,
    ) -> Sequence[m.Infra.MRORewriteResult]:
        """Rewrite all eligible Python files inside a workspace."""
        results: MutableSequence[m.Infra.MRORewriteResult] = []
        py_files = u.Infra.iter_python_files(workspace_root=workspace_root).fold(
            on_failure=lambda _: [],
            on_success=lambda v: list(v),
        )
        for file_path in py_files:
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
        moved_index: Mapping[str, t.StrMapping],
        module_facade_aliases: t.StrMapping,
        apply: bool,
    ) -> m.Infra.MRORewriteResult | None:
        """Rewrite one file and return replacement statistics."""
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return None
        cst_tree = u.Infra.parse_cst_from_source(source)
        if cst_tree is None:
            return None
        ast_tree = u.Infra.parse_ast_from_source(source)
        if ast_tree is None:
            return None
        imported_symbols: MutableMapping[str, m.Infra.MROImportRewrite] = {}
        module_aliases: MutableMapping[str, str] = {}
        facade_aliases: MutableMapping[str, str] = {}
        module_facade_alias: MutableMapping[str, str] = {}
        facade_imports_needed: t.Infra.StrSet = set()
        facade_import_objects: MutableMapping[str, m.Infra.MROImportRewrite] = {}
        for stmt in ast_tree.body:
            if isinstance(stmt, ast.ImportFrom):
                module_name = stmt.module
                if module_name is None or module_name not in moved_index:
                    continue
                if any(alias.name == "*" for alias in stmt.names):
                    continue
                kept_names: MutableSequence[ast.alias] = []
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
                stmt.names = list(kept_names)
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
        rewritten_cst: cst.Module = cst_tree.visit(rewriter)
        if rewriter.replacements == 0 and not facade_imports_needed:
            return None
        rendered = rewritten_cst.code
        if apply and rendered != source:
            _ = file_path.write_text(f"{rendered}\n", encoding=c.Infra.Encoding.DEFAULT)
        return m.Infra.MRORewriteResult(
            file=str(file_path),
            replacements=rewriter.replacements,
        )


__all__ = ["FlextInfraRefactorMROImportRewriter"]
