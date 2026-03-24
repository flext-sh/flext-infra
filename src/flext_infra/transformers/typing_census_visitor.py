"""Collect typing-annotation violations for reporting and remediation."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst

_PAIR_LENGTH = 2


class TypingAnnotationCensusVisitor(cst.CSTVisitor):
    """Collect census of typing annotation usage for reporting and migration planning."""

    DUNDER_OBJECT_ALLOWLIST = frozenset({
        "__eq__",
        "__ne__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "model_post_init",
    })

    def __init__(self, *, file_path: Path, project_name: str) -> None:
        """Initialize census state for a single source file."""
        self._file_path = file_path
        self._project_name = project_name
        self._current_class: str = ""
        self._current_function: str = ""
        self._current_function_is_typeguard: bool = False
        self._renderer = cst.Module(body=[])
        self.violations: MutableSequence[Mapping[str, str | int]] = []

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Track current class context while traversing class nodes."""
        self._current_class = node.name.value

    @override
    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        """Clear class context after finishing class traversal."""
        del original_node
        self._current_class = ""

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Track function context and inspect return annotations."""
        self._current_function = node.name.value
        self._current_function_is_typeguard = self._has_typeguard_return(node)
        return_annotation = (
            node.returns.annotation if node.returns is not None else None
        )
        self._check_annotation(return_annotation, context="return", line=0)

    @override
    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        """Clear function context after leaving a function definition."""
        del original_node
        self._current_function = ""
        self._current_function_is_typeguard = False

    @override
    def visit_Param(self, node: cst.Param) -> None:
        """Inspect parameter annotations except allowlisted guard contexts."""
        if self._current_function in self.DUNDER_OBJECT_ALLOWLIST:
            return
        if self._current_function_is_typeguard:
            return
        annotation = node.annotation.annotation if node.annotation is not None else None
        self._check_annotation(annotation, context="param", line=0)

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        """Inspect annotated assignment nodes for forbidden typing patterns."""
        context = (
            "field"
            if self._current_class and not self._current_function
            else "variable"
        )
        self._check_annotation(node.annotation.annotation, context=context, line=0)

    def _check_annotation(
        self,
        annotation: cst.BaseExpression | None,
        context: str,
        line: int,
        *,
        within_container: bool = False,
    ) -> None:
        if annotation is None:
            return

        if self._is_object_name(annotation) and not within_container:
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="bare_object",
                context=context,
                suggested_replacement="t.ContainerValue",
            )
            return

        if not isinstance(annotation, cst.Subscript):
            return

        base_name = self._get_subscript_name(annotation)
        values = self._get_subscript_values(annotation)

        if base_name == "dict" and self._is_str_object_pair(values):
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="container_object",
                context=context,
                suggested_replacement="Mapping[str, t.ContainerValue]",
            )

        if base_name == "Mapping" and self._is_str_object_pair(values):
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="mapping_object",
                context=context,
                suggested_replacement="Mapping[str, t.ContainerValue]",
            )

        if base_name == "list" and len(values) == 1 and self._is_object_name(values[0]):
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="list_object",
                context=context,
                suggested_replacement="Sequence[t.ContainerValue]",
            )

        if (
            base_name == "Sequence"
            and len(values) == 1
            and self._is_object_name(values[0])
        ):
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="sequence_object",
                context=context,
                suggested_replacement="Sequence[t.ContainerValue]",
            )

        if (
            base_name == "TypeAdapter"
            and len(values) == 1
            and self._is_typeadapter_object(
                values[0],
            )
        ):
            self._record_violation(
                line=line,
                column=0,
                annotation_text=self._renderer.code_for_node(annotation),
                violation_kind="typeadapter_object",
                context=context,
                suggested_replacement="TypeAdapter[t.ContainerValue]",
            )

        for value in values:
            self._check_annotation(
                value,
                context,
                line,
                within_container=True,
            )

    def _is_object_name(self, node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.Name) and node.value == "t.NormalizedValue":
            return True
        return bool(
            isinstance(node, cst.Attribute)
            and isinstance(node.value, cst.Name)
            and node.value.value == "builtins"
            and node.attr.value == "t.NormalizedValue",
        )

    def _has_typeguard_return(self, node: cst.FunctionDef) -> bool:
        if node.returns is None:
            return False
        ann = node.returns.annotation
        if isinstance(ann, cst.Subscript):
            base = ann.value
            if isinstance(base, cst.Name) and base.value in {
                "TypeGuard",
                "TypeIs",
            }:
                return True
        fn_name = node.name.value
        is_guard_name = fn_name.startswith(("is_", "_is_"))
        return bool(is_guard_name and isinstance(ann, cst.Name) and ann.value == "bool")

    def _get_subscript_name(self, node: cst.Subscript) -> str:
        if isinstance(node.value, cst.Name):
            return node.value.value
        if isinstance(node.value, cst.Attribute):
            return node.value.attr.value
        return ""

    def _record_violation(
        self,
        *,
        line: int,
        column: int,
        annotation_text: str,
        violation_kind: str,
        context: str,
        suggested_replacement: str,
    ) -> None:
        self.violations.append(
            {
                "file_path": str(self._file_path),
                "project": self._project_name,
                "class_name": self._current_class,
                "function_name": self._current_function,
                "line": line,
                "column": column,
                "annotation": annotation_text,
                "violation_kind": violation_kind,
                "context": context,
                "suggested_replacement": suggested_replacement,
            },
        )

    def _get_subscript_values(
        self,
        node: cst.Subscript,
    ) -> Sequence[cst.BaseExpression]:
        values: MutableSequence[cst.BaseExpression] = []
        for element in node.slice:
            if isinstance(element.slice, cst.Index):
                values.append(element.slice.value)
                continue
            if isinstance(element.slice, cst.Slice):
                if element.slice.lower is not None:
                    values.append(element.slice.lower)
                if element.slice.upper is not None:
                    values.append(element.slice.upper)
                if element.slice.step is not None:
                    values.append(element.slice.step)
        return values

    def _is_typeadapter_object(self, node: cst.BaseExpression) -> bool:
        if self._is_object_name(node):
            return True
        if not isinstance(node, cst.Subscript):
            return False
        base_name = self._get_subscript_name(node)
        values = self._get_subscript_values(node)
        return base_name == "dict" and self._is_str_object_pair(values)

    def _is_str_object_pair(self, values: Sequence[cst.BaseExpression]) -> bool:
        if len(values) != _PAIR_LENGTH:
            return False
        key_node = values[0]
        value_node = values[1]
        return (
            isinstance(key_node, cst.Name)
            and key_node.value == "str"
            and self._is_object_name(value_node)
        )


__all__ = ["TypingAnnotationCensusVisitor"]
