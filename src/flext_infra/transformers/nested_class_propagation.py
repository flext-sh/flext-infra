"""CST transformer for propagating nested class references after nesting."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence
from typing import override

import libcst as cst

from flext_infra import (
    FlextInfraRefactorTransformerPolicyUtilities,
    FlextInfraUtilitiesParsing,
    t,
)


class FlextInfraNestedClassPropagationTransformer(cst.CSTTransformer):
    """Propagate import and name references after classes are nested into namespaces."""

    def __init__(
        self,
        class_renames: t.StrMapping,
        policy_context: t.Infra.PolicyContext | None = None,
        class_families: t.StrMapping | None = None,
    ) -> None:
        """Initialize with class rename mappings and optional policy context."""
        self._class_renames = class_renames
        self._name_renames: MutableMapping[str, str] = dict(class_renames)
        self._policy_context = policy_context
        self._class_families = class_families or {}
        self._skip_names: set[int] = set()

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> bool | None:
        """Mark class name as definition site — skip in leave_Name."""
        self._skip_names.add(id(node.name))
        return None

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        """Mark function name as definition site — skip in leave_Name."""
        self._skip_names.add(id(node.name))
        return None

    @override
    def visit_Param(self, node: cst.Param) -> bool | None:
        """Mark parameter name as definition site — skip in leave_Name."""
        self._skip_names.add(id(node.name))
        return None

    @override
    def visit_ImportAlias(self, node: cst.ImportAlias) -> bool | None:
        """Mark import alias names — leave_ImportFrom handles these."""
        if isinstance(node.name, cst.Name):
            self._skip_names.add(id(node.name))
        return None

    @override
    def visit_AsName(self, node: cst.AsName) -> bool | None:
        """Mark asname target as definition site — skip in leave_Name."""
        if isinstance(node.name, cst.Name):
            self._skip_names.add(id(node.name))
        return None

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        del original_node
        if isinstance(updated_node.names, cst.ImportStar):
            return updated_node
        updated_aliases: MutableSequence[cst.ImportAlias] = []
        changed = False
        for alias in updated_node.names:
            if not isinstance(alias.name, cst.Name):
                updated_aliases.append(alias)
                continue
            rename_to = self._class_renames.get(alias.name.value)
            if rename_to is None or not self._should_propagate(
                alias.name.value, "propagate_imports"
            ):
                updated_aliases.append(alias)
                continue
            rename_parts = rename_to.split(".")
            updated_aliases.append(alias.with_changes(name=cst.Name(rename_parts[0])))
            changed = True
            if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
                local_name = alias.asname.name.value
                self._name_renames[local_name] = (
                    ".".join((local_name, *rename_parts[1:]))
                    if len(rename_parts) > 1
                    else local_name
                )
        return (
            updated_node.with_changes(names=tuple(updated_aliases))
            if changed
            else updated_node
        )

    @override
    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name,
    ) -> cst.BaseExpression:
        if id(original_node) in self._skip_names:
            return updated_node
        rename_to = self._name_renames.get(original_node.value)
        if rename_to is None:
            return updated_node
        if not self._should_propagate(original_node.value, "propagate_name_references"):
            return updated_node
        if self._blocked_by_prefix(original_node.value):
            return updated_node
        return FlextInfraUtilitiesParsing.module_expr_from_dotted(rename_to)

    @override
    def leave_Attribute(
        self,
        original_node: cst.Attribute,
        updated_node: cst.Attribute,
    ) -> cst.BaseExpression:
        rename_to = self._class_renames.get(original_node.attr.value)
        if rename_to is None:
            return updated_node
        if not self._should_propagate(
            original_node.attr.value, "propagate_attribute_references"
        ):
            return updated_node
        if self._blocked_by_prefix(original_node.attr.value):
            return updated_node
        rename_parts = rename_to.split(".")
        if not rename_parts:
            return updated_node
        rightmost = (
            updated_node.value.value
            if isinstance(updated_node.value, cst.Name)
            else (
                updated_node.value.attr.value
                if isinstance(updated_node.value, cst.Attribute)
                else None
            )
        )
        if rightmost == rename_parts[0]:
            suffix_parts = rename_parts[1:]
            if not suffix_parts:
                return updated_node.with_changes(attr=cst.Name(rename_parts[0]))
            return self._chain(updated_node.value, suffix_parts)
        return self._chain(updated_node.value, rename_parts)

    def _chain(self, base: cst.BaseExpression, parts: list[str]) -> cst.BaseExpression:
        expr: cst.BaseExpression = base
        for part in parts:
            expr = cst.Attribute(value=expr, attr=cst.Name(part))
        return expr

    def _should_propagate(self, symbol_name: str, policy_key: str) -> bool:
        policy = FlextInfraRefactorTransformerPolicyUtilities.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )
        if policy is None:
            return True
        if policy_key == "propagate_imports":
            return policy.propagate_imports
        if policy_key == "propagate_name_references":
            return policy.propagate_name_references
        if policy_key == "propagate_attribute_references":
            return policy.propagate_attribute_references
        return False

    def _blocked_by_prefix(self, symbol_name: str) -> bool:
        policy = FlextInfraRefactorTransformerPolicyUtilities.policy_for_symbol(
            policy_context=self._policy_context,
            symbol_families=self._class_families,
            symbol_name=symbol_name,
        )
        if policy is None:
            return False
        return any(symbol_name.startswith(p) for p in policy.blocked_reference_prefixes)


__all__ = ["FlextInfraNestedClassPropagationTransformer"]
