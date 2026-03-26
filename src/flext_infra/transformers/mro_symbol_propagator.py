"""CST transformer for propagating MRO-migrated symbol access patterns."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import override

import libcst as cst

from flext_infra import t
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
from flext_infra.transformers._base import FlextInfraChangeTrackingTransformer


class FlextInfraRefactorMROSymbolPropagator(FlextInfraChangeTrackingTransformer):
    """Rewrite imports and references after symbols move into facade namespaces."""

    def __init__(
        self,
        *,
        module_moves: Mapping[str, t.Infra.Pair[str, t.StrMapping]],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize rewrite state for one file."""
        super().__init__(on_change=on_change)
        self._module_moves = module_moves
        self._local_name_rewrites: MutableMapping[str, str] = {}
        self._module_alias_moves: MutableMapping[
            str, t.Infra.Pair[str, t.StrMapping]
        ] = {}
        self._skip_names: t.Infra.IntSet = set()

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool | None:
        if isinstance(node.target, cst.Name):
            self._skip_names.add(id(node.target))
        return True

    @override
    def visit_AsName(self, node: cst.AsName) -> bool | None:
        if isinstance(node.name, cst.Name):
            self._skip_names.add(id(node.name))
        return True

    @override
    def visit_AssignTarget(self, node: cst.AssignTarget) -> bool | None:
        if isinstance(node.target, cst.Name):
            self._skip_names.add(id(node.target))
        return True

    @override
    def visit_Attribute(self, node: cst.Attribute) -> bool | None:
        self._skip_names.add(id(node.attr))
        return True

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
        self._skip_names.add(id(node.name))
        return True

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        self._skip_names.add(id(node.name))
        return True

    @override
    def visit_ImportAlias(self, node: cst.ImportAlias) -> bool | None:
        if isinstance(node.name, cst.Name):
            self._skip_names.add(id(node.name))
        return True

    @override
    def visit_Param(self, node: cst.Param) -> bool | None:
        self._skip_names.add(id(node.name))
        return True

    @override
    def visit_TypeAlias(self, node: cst.TypeAlias) -> bool | None:
        self._skip_names.add(id(node.name))
        return True

    @override
    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> cst.Import:
        for alias in original_node.names:
            module_name = FlextInfraUtilitiesParsing.cst_module_name(alias.name)
            module_move = self._module_moves.get(module_name)
            if module_move is None:
                continue
            if alias.asname is None or not isinstance(alias.asname.name, cst.Name):
                continue
            self._module_alias_moves[alias.asname.name.value] = module_move
        return updated_node

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        module_name = FlextInfraUtilitiesParsing.cst_module_name(original_node.module)
        module_move = self._module_moves.get(module_name)
        if module_move is None or isinstance(updated_node.names, cst.ImportStar):
            return updated_node
        facade_alias, symbol_paths = module_move
        changed = False
        seen_aliases: set[tuple[str, str | None]] = set()
        next_aliases: list[cst.ImportAlias] = []
        for alias in list(updated_node.names):
            if not isinstance(alias.name, cst.Name):
                next_aliases.append(alias)
                continue
            target_path = symbol_paths.get(alias.name.value)
            rewritten = alias
            if target_path is not None:
                local_name = (
                    alias.asname.name.value
                    if alias.asname is not None
                    and isinstance(alias.asname.name, cst.Name)
                    else alias.name.value
                )
                rewrite_base = local_name if alias.asname is not None else facade_alias
                self._local_name_rewrites[local_name] = ".".join(
                    (rewrite_base, *target_path.split(".")),
                )
                rewritten = alias.with_changes(name=cst.Name(facade_alias))
                self._record_change(
                    f"Rewired import: {module_name}.{alias.name.value} -> {facade_alias}.{target_path}",
                )
                changed = True
            rewritten_name = (
                rewritten.name.value if isinstance(rewritten.name, cst.Name) else ""
            )
            rewritten_asname = (
                rewritten.asname.name.value
                if rewritten.asname is not None
                and isinstance(rewritten.asname.name, cst.Name)
                else None
            )
            rewrite_key = (
                rewritten_name,
                rewritten_asname,
            )
            if rewrite_key in seen_aliases:
                continue
            seen_aliases.add(rewrite_key)
            next_aliases.append(rewritten)
        return (
            updated_node.with_changes(names=tuple(next_aliases))
            if changed
            else updated_node
        )

    @override
    def leave_Attribute(
        self,
        original_node: cst.Attribute,
        updated_node: cst.Attribute,
    ) -> cst.BaseExpression:
        direct_module = FlextInfraUtilitiesParsing.cst_module_name(updated_node.value)
        direct_move = self._module_moves.get(direct_module)
        if direct_move is not None:
            replacement = self._replace_module_attribute(
                base_expr=updated_node.value,
                symbol_name=original_node.attr.value,
                module_move=direct_move,
            )
            if replacement is not None:
                return replacement
        if not isinstance(updated_node.value, cst.Name):
            return updated_node
        module_move = self._module_alias_moves.get(updated_node.value.value)
        if module_move is None:
            return updated_node
        replacement = self._replace_module_attribute(
            base_expr=updated_node.value,
            symbol_name=original_node.attr.value,
            module_move=module_move,
        )
        return replacement or updated_node

    @override
    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name,
    ) -> cst.BaseExpression:
        if id(original_node) in self._skip_names:
            return updated_node
        rewrite_target = self._local_name_rewrites.get(original_node.value)
        if rewrite_target is None:
            return updated_node
        self._record_change(
            f"Qualified reference: {original_node.value} -> {rewrite_target}"
        )
        return FlextInfraUtilitiesParsing.module_expr_from_dotted(rewrite_target)

    def _replace_module_attribute(
        self,
        *,
        base_expr: cst.BaseExpression,
        symbol_name: str,
        module_move: t.Infra.Pair[str, t.StrMapping],
    ) -> cst.BaseExpression | None:
        facade_alias, symbol_paths = module_move
        target_path = symbol_paths.get(symbol_name)
        if target_path is None:
            return None
        replacement = FlextInfraUtilitiesParsing.module_expr_from_dotted(
            ".".join(
                (
                    FlextInfraUtilitiesParsing.cst_module_name(base_expr),
                    facade_alias,
                    target_path,
                ),
            ),
        )
        self._record_change(
            f"Qualified module reference: {symbol_name} -> {facade_alias}.{target_path}",
        )
        return replacement


__all__ = ["FlextInfraRefactorMROSymbolPropagator"]
