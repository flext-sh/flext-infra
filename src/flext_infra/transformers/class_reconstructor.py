"""Class reconstructor transformer for method ordering rules."""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from typing import override

import libcst as cst
from pydantic import TypeAdapter, ValidationError

from flext_infra import FlextInfraChangeTrackingTransformer, c, m, t

_PROPERTY_DECORATORS: frozenset[str] = frozenset(
    {"property", "cached_property", "computed_field"},
)

_DECORATOR_TO_CATEGORY: Sequence[tuple[str, str]] = [
    ("staticmethod", c.Infra.MethodCategory.STATIC),
    ("classmethod", c.Infra.MethodCategory.CLASS),
]


def _categorize_by_name(name: str) -> str:
    """Determine method category from its name when decorators don't match."""
    if name.startswith("__") and name.endswith("__"):
        return c.Infra.MethodCategory.MAGIC
    if name.startswith("__"):
        return c.Infra.MethodCategory.PRIVATE
    if name.startswith("_"):
        return c.Infra.MethodCategory.PROTECTED
    return c.Infra.MethodCategory.PUBLIC


def _check_visibility(name: str, visibility: str | None) -> bool:
    """Return True when the method name satisfies the visibility constraint."""
    if visibility is None:
        return True
    if visibility == "public":
        return not name.startswith("_")
    if visibility == "protected":
        return name.startswith("_") and not name.startswith("__")
    if visibility == "private":
        return name.startswith("__") and not name.endswith("__")
    return True


def _matches_rule(
    method: m.Infra.MethodInfo,
    rule_config: m.Infra.MethodOrderRule,
) -> bool:
    """Return True when *method* satisfies all constraints of *rule_config*."""
    decorators = set(method.decorators)
    exclude_decorators = set(rule_config.exclude_decorators)
    if exclude_decorators and decorators.intersection(exclude_decorators):
        return False
    if not _check_visibility(method.name, rule_config.visibility):
        return False
    rule_decorators = rule_config.decorators
    if rule_decorators and not decorators.intersection(rule_decorators):
        return False
    patterns = rule_config.patterns
    return not patterns or any(re.match(p, method.name) for p in patterns)


def _build_sort_key(
    method: m.Infra.MethodInfo,
    order_config: Sequence[m.Infra.MethodOrderRule],
) -> t.Infra.Triple[int, int, str]:
    """Return a sort key tuple for *method* given the rule sequence."""
    for idx, rule_config in enumerate(order_config):
        if rule_config.category == "class_attributes":
            continue
        if not _matches_rule(method, rule_config):
            continue
        explicit_order = rule_config.order
        if explicit_order:
            if method.name in explicit_order:
                return (idx, explicit_order.index(method.name), method.name)
            if "*" in explicit_order:
                return (idx, explicit_order.index("*") + 1, method.name)
        return (idx, 0, method.name)
    return (len(order_config), 0, method.name)


class FlextInfraRefactorClassReconstructor(FlextInfraChangeTrackingTransformer):
    """Reorder class methods based on declarative ordering configuration."""

    def __init__(
        self,
        order_config: Sequence[t.Infra.ContainerDict],
        on_change: t.Infra.ChangeCallback = None,
    ) -> None:
        """Initialize with rule order config and optional change callback."""
        super().__init__(on_change=on_change)
        try:
            self._order_config: Sequence[m.Infra.MethodOrderRule] = TypeAdapter(
                Sequence[m.Infra.MethodOrderRule],
            ).validate_python(order_config)
        except ValidationError:
            self._order_config = list[m.Infra.MethodOrderRule]()

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        """Sort methods in every contiguous method block of a class body."""
        if not isinstance(updated_node.body, cst.IndentedBlock):
            return updated_node
        body = list(updated_node.body.body)
        if not body:
            return updated_node
        new_body: MutableSequence[cst.BaseStatement] = list(body)
        block_start = 0
        changed_blocks = 0
        reordered_methods_total = 0
        while block_start < len(body):
            if not isinstance(body[block_start], cst.FunctionDef):
                block_start += 1
                continue
            block_end = block_start
            while block_end < len(body) and isinstance(
                body[block_end],
                cst.FunctionDef,
            ):
                block_end += 1
            method_indices = list(range(block_start, block_end))
            methods: MutableSequence[m.Infra.MethodInfo] = []
            for idx in method_indices:
                block_item = body[idx]
                if isinstance(block_item, cst.FunctionDef):
                    methods.append(self._analyze_method(block_item))
            sorted_methods = self._sort_methods(methods)
            original_method_names = [method.name for method in methods]
            sorted_method_names = [method.name for method in sorted_methods]
            if original_method_names != sorted_method_names:
                changed_blocks += 1
                reordered_methods_total += len(methods)
                for idx, method in zip(method_indices, sorted_methods, strict=False):
                    new_body[idx] = method.node
            block_start = block_end
        if changed_blocks == 0:
            return updated_node
        self._record_change(
            f"Reordered {reordered_methods_total} methods in class {original_node.name.value} across {changed_blocks} contiguous block(s)",
        )
        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=new_body),
        )

    def _analyze_method(self, node: cst.FunctionDef) -> m.Infra.MethodInfo:
        name = node.name.value
        decorators: MutableSequence[str] = []
        for dec in node.decorators:
            if isinstance(dec.decorator, cst.Name):
                decorators.append(dec.decorator.value)
            elif isinstance(dec.decorator, cst.Attribute):
                decorators.append(dec.decorator.attr.value)
        category = self._categorize(name, decorators)
        return m.Infra.MethodInfo(
            name=name,
            category=category,
            node=node,
            decorators=decorators,
        )

    def _categorize(self, name: str, decorators: t.StrSequence) -> str:
        if _PROPERTY_DECORATORS.intersection(decorators):
            return c.Infra.MethodCategory.PROPERTY
        for decorator_name, category in _DECORATOR_TO_CATEGORY:
            if decorator_name in decorators:
                return category
        return _categorize_by_name(name)

    def _sort_methods(
        self,
        methods: Sequence[m.Infra.MethodInfo],
    ) -> Sequence[m.Infra.MethodInfo]:
        order_config = self._order_config
        return sorted(
            methods,
            key=lambda method: _build_sort_key(method, order_config),
        )


__all__ = ["FlextInfraRefactorClassReconstructor"]
