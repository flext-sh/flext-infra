"""Collect code-pattern violations used by infra census reports."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

_DICT_KEY_VALUE_ARITY = 2


class ViolationCensusVisitor(cst.CSTVisitor):
    RUNTIME_ALIASES: frozenset[str] = frozenset({
        "c",
        "m",
        "r",
        "t",
        "u",
        "p",
        "d",
        "e",
        "h",
        "s",
        "x",
    })

    def __init__(self, *, file_path: Path) -> None:
        """Initialize visitor state for one file violation census."""
        self._file_path = file_path
        self._renderer = cst.Module(body=[])
        self.records: list[dict[str, str | int]] = []

    @override
    def visit_Subscript(self, node: cst.Subscript) -> None:
        if self._is_container_invariance(node):
            self._add_record(
                kind="container_invariance",
                detail="Found dict[str, t.Container|t.NormalizedValue] style annotation.",
            )
        if self._is_literal_usage(node):
            self._add_record(
                kind="literal_usage",
                detail="Found Literal[...] usage.",
            )

    @override
    def visit_Call(self, node: cst.Call) -> None:
        if self._is_cast_call(node.func):
            self._add_record(
                kind="redundant_cast",
                detail="Found cast(...) call.",
            )

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module_name = self._get_module_name(node)
        imported_names = self._imported_names(node)

        if module_name.startswith("flext_core."):
            self._add_record(
                kind="direct_submodule_import",
                detail=f"Found direct submodule import: from {module_name} import ...",
            )

        if module_name == "typing" and "Mapping" in imported_names:
            self._add_record(
                kind="legacy_typing_mapping",
                detail="Found from typing import ... Mapping ...",
            )

        if module_name == "flext_core" and not any(
            alias_name in self.RUNTIME_ALIASES for alias_name in imported_names
        ):
            self._add_record(
                kind="runtime_alias_violation",
                detail="Found from flext_core import ... without runtime aliases.",
            )

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        if any(self._is_strenum_base(base_arg.value) for base_arg in node.bases):
            self._add_record(
                kind="strenum_usage",
                detail=f"Class {node.name.value} inherits from StrEnum.",
            )

    @override
    def visit_Assign(self, node: cst.Assign) -> None:
        if self._is_manual_mapping_constant(node):
            self._add_record(
                kind="manual_mapping_constant",
                detail="Found constant assigned to dict literal.",
            )

        if self._is_compatibility_alias(node):
            self._add_record(
                kind="compatibility_alias",
                detail="Found compatibility alias assignment Name = Name.",
            )

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if node.value is None:
            return
        if self._is_type_alias_annotation(node.annotation.annotation):
            self._add_record(
                kind="manual_typing_alias",
                detail="Found TypeAlias-based manual type alias.",
            )

    @override
    def visit_TypeAlias(self, node: cst.TypeAlias) -> None:
        alias_name = self._renderer.code_for_node(node.name)
        self._add_record(
            kind="manual_typing_alias",
            detail=f"Found PEP 695 type alias: {alias_name}.",
        )

    def _add_record(self, *, kind: str, detail: str) -> None:
        self.records.append(
            {
                "file": str(self._file_path),
                "line": 0,
                "kind": kind,
                "detail": detail,
            },
        )

    def _get_module_name(self, node: cst.ImportFrom) -> str:
        if node.module is None:
            return ""
        if isinstance(node.module, cst.Name):
            return node.module.value
        return self._dotted_name(node.module)

    def _imported_names(self, node: cst.ImportFrom) -> list[str]:
        if isinstance(node.names, cst.ImportStar):
            return []
        names: list[str] = []
        for alias in node.names:
            if isinstance(alias.name, cst.Name):
                names.append(alias.name.value)
                continue
            names.append(self._renderer.code_for_node(alias.name).strip())
        return names

    def _is_constant_name(self, name: str) -> bool:
        if not name:
            return False
        if not name[0].isupper():
            return False
        return all(
            character.isupper() or character.isdigit() or character == "_"
            for character in name
        )

    def _is_container_invariance(self, node: cst.Subscript) -> bool:
        if not (isinstance(node.value, cst.Name) and node.value.value == "dict"):
            return False
        if len(node.slice) != _DICT_KEY_VALUE_ARITY:
            return False

        key_expr = self._subscript_value(node.slice[0])
        value_expr = self._subscript_value(node.slice[1])
        if key_expr is None or value_expr is None:
            return False
        if not (isinstance(key_expr, cst.Name) and key_expr.value == "str"):
            return False
        return self._is_container_or_object(value_expr)

    def _is_literal_usage(self, node: cst.Subscript) -> bool:
        if isinstance(node.value, cst.Name):
            return node.value.value == "Literal"
        if isinstance(node.value, cst.Attribute):
            return node.value.attr.value == "Literal"
        return False

    def _is_cast_call(self, func: cst.BaseExpression) -> bool:
        if isinstance(func, cst.Name):
            return func.value == "cast"
        if isinstance(func, cst.Attribute):
            return func.attr.value == "cast"
        return False

    def _is_strenum_base(self, expr: cst.BaseExpression) -> bool:
        if isinstance(expr, cst.Name):
            return expr.value == "StrEnum"
        if isinstance(expr, cst.Attribute):
            return expr.attr.value == "StrEnum"
        return False

    def _is_manual_mapping_constant(self, node: cst.Assign) -> bool:
        if len(node.targets) != 1:
            return False
        target = node.targets[0].target
        return (
            isinstance(target, cst.Name)
            and self._is_constant_name(target.value)
            and isinstance(node.value, cst.Dict)
        )

    def _is_compatibility_alias(self, node: cst.Assign) -> bool:
        if len(node.targets) != 1:
            return False
        target = node.targets[0].target
        value = node.value
        if not (isinstance(target, cst.Name) and isinstance(value, cst.Name)):
            return False
        return self._is_pascal_case(target.value) and self._is_pascal_case(value.value)

    def _is_pascal_case(self, name: str) -> bool:
        if not name or "_" in name:
            return False
        if not name[0].isupper():
            return False
        return any(character.islower() for character in name[1:])

    def _is_type_alias_annotation(self, annotation: cst.BaseExpression) -> bool:
        if isinstance(annotation, cst.Name):
            return annotation.value == "TypeAlias"
        if isinstance(annotation, cst.Attribute):
            return annotation.attr.value == "TypeAlias"
        return False

    def _subscript_value(
        self, element: cst.SubscriptElement
    ) -> cst.BaseExpression | None:
        if isinstance(element.slice, cst.Index):
            return element.slice.value
        return None

    def _is_container_or_object(self, expr: cst.BaseExpression) -> bool:
        if self._is_container_path(expr):
            return True
        if self._is_object_name(expr):
            return True
        if isinstance(expr, cst.BinaryOperation) and isinstance(
            expr.operator, cst.BitOr
        ):
            return self._is_container_or_object(
                expr.left
            ) and self._is_container_or_object(expr.right)
        return False

    def _is_container_path(self, expr: cst.BaseExpression) -> bool:
        if isinstance(expr, cst.Attribute) and isinstance(expr.value, cst.Name):
            return expr.value.value == "t" and expr.attr.value in {
                "Container",
                "t.NormalizedValue",
            }
        return False

    def _is_object_name(self, expr: cst.BaseExpression) -> bool:
        return isinstance(expr, cst.Name) and expr.value == "t.NormalizedValue"

    def _dotted_name(self, expr: cst.BaseExpression) -> str:
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            left = self._dotted_name(expr.value)
            if left:
                return f"{left}.{expr.attr.value}"
            return expr.attr.value
        return ""


__all__ = ["ViolationCensusVisitor"]
