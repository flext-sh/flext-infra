"""Workspace-wide symbol propagation transformer for refactor API renames."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst

from flext_infra import (
    FlextInfraChangeTrackingTransformer,
    FlextInfraUtilitiesParsing,
    t,
)


class FlextInfraRefactorSymbolPropagator(FlextInfraChangeTrackingTransformer):
    """Propagate import/symbol renames safely using CST import tracking."""

    def __init__(
        self,
        *,
        target_modules: t.Infra.StrSet,
        module_renames: t.StrMapping,
        import_symbol_renames: t.StrMapping,
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize symbol propagation configuration and change collector."""
        super().__init__(on_change=on_change)
        self._target_modules = target_modules
        self._module_renames = module_renames
        self._import_symbol_renames = import_symbol_renames
        self._local_name_renames: t.MutableStrMapping = {}

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        module_name = FlextInfraUtilitiesParsing.cst_module_name(original_node.module)
        next_node = updated_node
        if module_name in self._module_renames:
            next_module = FlextInfraUtilitiesParsing.module_expr_from_dotted(
                self._module_renames[module_name],
            )
            next_node = next_node.with_changes(module=next_module)
            self._record_change(
                f"Renamed import module: {module_name} -> {self._module_renames[module_name]}"
            )
            module_name = self._module_renames[module_name]
        if module_name not in self._target_modules or isinstance(
            next_node.names, cst.ImportStar
        ):
            return next_node
        next_aliases: MutableSequence[cst.ImportAlias] = []
        changed = False
        for alias in list(next_node.names):
            if not isinstance(alias.name, cst.Name):
                next_aliases.append(alias)
                continue
            imported_name = alias.name.value
            renamed_symbol = self._import_symbol_renames.get(imported_name)
            if renamed_symbol is None:
                next_aliases.append(alias)
                continue
            changed = True
            next_aliases.append(alias.with_changes(name=cst.Name(renamed_symbol)))
            if alias.asname is None:
                self._local_name_renames[imported_name] = renamed_symbol
            self._record_change(
                f"Renamed imported symbol: {imported_name} -> {renamed_symbol}"
            )
        return (
            next_node.with_changes(names=tuple(next_aliases)) if changed else next_node
        )

    @override
    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name,
    ) -> cst.BaseExpression:
        rename_to = self._local_name_renames.get(original_node.value)
        if rename_to is None or updated_node.value == rename_to:
            return updated_node
        self._record_change(
            f"Propagated local symbol rename: {updated_node.value} -> {rename_to}"
        )
        return cst.Name(rename_to)


__all__ = ["FlextInfraRefactorSymbolPropagator"]
