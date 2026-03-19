from __future__ import annotations

from pathlib import Path

import libcst as cst

__all__ = ["TypingAnnotationCensusVisitor"]


class TypingAnnotationCensusVisitor(cst.CSTVisitor):
    DUNDER_OBJECT_ALLOWLIST = frozenset({
        "__eq__",
        "__ne__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
    })

    def __init__(self, *, file_path: Path, project_name: str) -> None:
        self._file_path = file_path
        self._project_name = project_name
        self._current_class: str = ""
        self._current_function: str = ""
        self._renderer = cst.Module(body=[])
        self.violations: list[dict[str, str | int]] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._current_class = node.name.value

    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        del original_node
        self._current_class = ""

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._current_function = node.name.value
        return_annotation = (
            node.returns.annotation if node.returns is not None else None
        )
        self._check_annotation(return_annotation, context="return", line=0)

    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        del original_node
        self._current_function = ""

    def visit_Param(self, node: cst.Param) -> None:
        if self._current_function in self.DUNDER_OBJECT_ALLOWLIST:
            return
        annotation = node.annotation.annotation if node.annotation is not None else None
        self._check_annotation(annotation, context="param", line=0)

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
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
                suggested_replacement="dict[str, t.ContainerValue]",
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
                suggested_replacement="list[t.ContainerValue]",
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
        return isinstance(node, cst.Name) and node.value == "object"

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

    def _get_subscript_values(self, node: cst.Subscript) -> list[cst.BaseExpression]:
        values: list[cst.BaseExpression] = []
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

    def _is_str_object_pair(self, values: list[cst.BaseExpression]) -> bool:
        if len(values) != 2:
            return False
        key_node = values[0]
        value_node = values[1]
        return (
            isinstance(key_node, cst.Name)
            and key_node.value == "str"
            and self._is_object_name(value_node)
        )
