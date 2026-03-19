"""CST transformer for MRO reference rewrites."""

from __future__ import annotations

from typing import override

import libcst as cst

from flext_infra import m, u


class FlextInfraRefactorMROReferenceRewriter(cst.CSTTransformer):
    """Rewrite CST references to moved constants using canonical alias `c`."""

    def __init__(
        self,
        *,
        imported_symbols: dict[str, m.Infra.MROImportRewrite],
        module_aliases: dict[str, str],
        module_facades: dict[str, str],
        moved_index: dict[str, dict[str, str]],
    ) -> None:
        """Initialize with symbol mappings for rewriting."""
        self._imported_symbols = imported_symbols
        self._module_aliases = module_aliases
        self._module_facades = module_facades
        self._moved_index = moved_index
        self.replacements = 0

    @override
    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name,
    ) -> cst.BaseExpression:
        """Rewrite bare names that were imported and moved."""
        del original_node
        imported = self._imported_symbols.get(updated_node.value)
        if imported is None:
            return updated_node
        self.replacements += 1
        return u.Infra.module_expr_from_dotted(
            f"{imported.facade_name}.{imported.symbol}",
        )

    @override
    def leave_Attribute(
        self,
        original_node: cst.Attribute,
        updated_node: cst.Attribute,
    ) -> cst.BaseExpression:
        """Rewrite attribute access on module aliases to their moved location."""
        del original_node
        # Walk up to get the root name
        root_name = u.Infra.root_name(updated_node.value)
        if not root_name:
            return updated_node

        # Check if root is a module alias or facade alias
        module_name = self._module_aliases.get(root_name)
        if module_name is None:
            module_name = self._module_facades.get(root_name)
        if module_name is None:
            return updated_node

        symbol_map = self._moved_index.get(module_name)
        if symbol_map is None:
            return updated_node

        new_symbol = symbol_map.get(updated_node.attr.value)
        if new_symbol is None:
            return updated_node

        self.replacements += 1
        return u.Infra.module_expr_from_dotted(new_symbol)


__all__ = ["FlextInfraRefactorMROReferenceRewriter"]
