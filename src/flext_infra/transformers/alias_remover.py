"""Alias remover transformer for legacy compatibility cleanup."""

from __future__ import annotations

from typing import override

import libcst as cst

from flext_infra import t
from flext_infra.transformers._base import FlextInfraChangeTrackingTransformer


class FlextInfraRefactorAliasRemover(FlextInfraChangeTrackingTransformer):
    """Remove module-level ``Name = Name`` aliases with allowlist support."""

    def __init__(
        self,
        allow_aliases: t.Infra.StrSet,
        allow_target_suffixes: t.Infra.VariadicTuple[str],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize alias remover with allow-list configuration."""
        super().__init__(on_change=on_change)
        self._scope_depth = 0
        self._allow_aliases = allow_aliases
        self._allow_target_suffixes = allow_target_suffixes

    @override
    def leave_Assign(
        self,
        original_node: cst.Assign,
        updated_node: cst.Assign,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        if self._scope_depth > 0:
            return updated_node
        if (
            len(original_node.targets) == 1
            and isinstance(original_node.targets[0].target, cst.Name)
            and isinstance(original_node.value, cst.Name)
        ):
            target = original_node.targets[0].target.value
            value = original_node.value.value
            if target in self._allow_aliases:
                return updated_node
            if self._allow_target_suffixes and value.endswith(
                self._allow_target_suffixes,
            ):
                return updated_node
            if target != value and target not in {"__version__", "__all__"}:
                self._record_change(f"Removed alias: {target} = {value}")
                return cst.RemovalSentinel.REMOVE
        return updated_node

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        del original_node
        self._scope_depth -= 1
        return updated_node

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        del original_node
        self._scope_depth -= 1
        return updated_node

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        del node
        self._scope_depth += 1

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        del node
        self._scope_depth += 1
