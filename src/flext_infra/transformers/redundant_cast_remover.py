"""Redundant cast() call remover transformer."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst

from flext_infra import c, t


class FlextInfraRedundantCastRemover(cst.CSTTransformer):
    """Remove redundant cast() calls for specified types."""

    def __init__(self, removable_types: t.Infra.StrSet) -> None:
        """Initialize with the set of type names whose casts are removable."""
        self.removable_types = removable_types
        self.changes: MutableSequence[str] = []

    @override
    def leave_Call(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.BaseExpression:
        del original_node
        func = updated_node.func
        if not isinstance(func, cst.Name) or func.value != "cast":
            return updated_node
        if len(updated_node.args) != c.Infra.CAST_ARITY:
            return updated_node
        type_arg, value_arg = updated_node.args
        if type_arg.keyword is not None or value_arg.keyword is not None:
            return updated_node
        target = self._extract_target_string(type_arg)
        if target is None:
            return updated_node
        if target not in self.removable_types:
            return updated_node
        if target == "type":
            unwrapped = self._unwrap_nested_object_cast(value_arg.value)
            if unwrapped is None:
                return updated_node
            self.changes.append(
                "Removed redundant cast chain for type/t.NormalizedValue",
            )
            return unwrapped
        self.changes.append(f"Removed redundant cast for {target}")
        return value_arg.value

    def _extract_target_string(self, node: cst.Arg) -> str | None:
        value = node.value
        if not isinstance(value, cst.SimpleString):
            return None
        evaluated = value.evaluated_value
        if not isinstance(evaluated, str):
            return None
        return evaluated

    def _unwrap_nested_object_cast(
        self,
        node: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "cast":
            return None
        if len(node.args) != c.Infra.CAST_ARITY:
            return None
        type_arg, value_arg = node.args
        if type_arg.keyword is not None or value_arg.keyword is not None:
            return None
        target = self._extract_target_string(type_arg)
        if target != "t.NormalizedValue":
            return None
        return value_arg.value


__all__ = [
    "FlextInfraRedundantCastRemover",
]
