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
        target_and_args = self._extract_removable_cast(updated_node)
        if target_and_args is None:
            return updated_node
        target, value_arg = target_and_args
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

    def _extract_removable_cast(
        self,
        node: cst.Call,
    ) -> tuple[str, cst.Arg] | None:
        """Extract (target_type, value_arg) if this is a removable cast() call."""
        func = node.func
        if not isinstance(func, cst.Name) or func.value != "cast":
            return None
        if len(node.args) != c.Infra.CAST_ARITY:
            return None
        type_arg, value_arg = node.args
        if type_arg.keyword is not None or value_arg.keyword is not None:
            return None
        target = self._extract_target_string(type_arg)
        if target is None or target not in self.removable_types:
            return None
        return (target, value_arg)

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
        target_and_args = self._extract_cast_args(node)
        if target_and_args is None or target_and_args[0] != "t.NormalizedValue":
            return None
        return target_and_args[1].value

    @staticmethod
    def _extract_cast_args(node: cst.Call) -> tuple[str, cst.Arg] | None:
        """Extract (target_string, value_arg) from a cast() call, or None."""
        func = node.func
        if not isinstance(func, cst.Name) or func.value != "cast":
            return None
        if len(node.args) != c.Infra.CAST_ARITY:
            return None
        type_arg, value_arg = node.args
        if type_arg.keyword is not None or value_arg.keyword is not None:
            return None
        value = type_arg.value
        if not isinstance(value, cst.SimpleString):
            return None
        evaluated = value.evaluated_value
        if not isinstance(evaluated, str):
            return None
        return (evaluated, value_arg)


__all__ = [
    "FlextInfraRedundantCastRemover",
]
