"""Collect model definitions and references to identify dead model classes."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst


class ModelDefinitionCollector(cst.CSTVisitor):
    def __init__(self, *, file_path: Path) -> None:
        """Initialize collector state for model definitions in one file."""
        super().__init__()
        self._file_path = file_path
        self.definitions: list[dict[str, str | int]] = []
        self.exported_models: set[str] = set()
        self._all_export_names: set[str] = set()

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        class_name = node.name.value
        if not self._is_model_class(node):
            return
        self.definitions.append(
            {
                "class_name": class_name,
                "file": str(self._file_path),
                "line": 0,
            },
        )
        if class_name in self._all_export_names:
            self.exported_models.add(class_name)

    @override
    def visit_Assign(self, node: cst.Assign) -> None:
        if not self._is_all_assignment(node):
            return
        exported_names = self._extract_all_names(node.value)
        self._all_export_names.update(exported_names)
        defined_names = {
            definition["class_name"]
            for definition in self.definitions
            if isinstance(definition["class_name"], str)
        }
        self.exported_models.update(defined_names.intersection(exported_names))

    def _is_model_class(self, node: cst.ClassDef) -> bool:
        return any(self._has_model_marker(base.value) for base in node.bases)

    def _has_model_marker(self, expression: cst.BaseExpression) -> bool:
        if isinstance(expression, cst.Name):
            name = expression.value
            return "Model" in name or "BaseModel" in name
        if isinstance(expression, cst.Attribute):
            for part in self._attribute_parts(expression):
                if "Model" in part or "BaseModel" in part:
                    return True
        return False

    def _attribute_parts(self, expression: cst.Attribute) -> list[str]:
        parts: list[str] = [expression.attr.value]
        current: cst.BaseExpression = expression.value
        while isinstance(current, cst.Attribute):
            parts.append(current.attr.value)
            current = current.value
        if isinstance(current, cst.Name):
            parts.append(current.value)
        return parts

    def _is_all_assignment(self, node: cst.Assign) -> bool:
        for target in node.targets:
            if isinstance(target.target, cst.Name) and target.target.value == "__all__":
                return True
        return False

    def _extract_all_names(self, expression: cst.BaseExpression) -> set[str]:
        names: set[str] = set()
        if isinstance(expression, cst.List | cst.Tuple | cst.Set):
            for element in expression.elements:
                if isinstance(element.value, cst.SimpleString):
                    evaluated_value = element.value.evaluated_value
                    if isinstance(evaluated_value, str):
                        names.add(evaluated_value)
        return names


class ModelReferenceCollector(cst.CSTVisitor):
    def __init__(self, *, known_models: frozenset[str], file_path: Path) -> None:
        """Initialize collector state for model references in one file."""
        super().__init__()
        self._known_models = known_models
        self._file_path = file_path
        self.referenced_models: set[str] = set()

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        if isinstance(node.names, cst.ImportStar):
            return
        for alias in node.names:
            imported_name = self._terminal_name(alias.name)
            if imported_name in self._known_models:
                self.referenced_models.add(imported_name)

    @override
    def visit_Name(self, node: cst.Name) -> None:
        if node.value in self._known_models:
            self.referenced_models.add(node.value)

    @override
    def visit_Attribute(self, node: cst.Attribute) -> None:
        if node.attr.value in self._known_models:
            self.referenced_models.add(node.attr.value)

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        for base in node.bases:
            base_name = self._terminal_name(base.value)
            if base_name in self._known_models:
                self.referenced_models.add(base_name)

    def _terminal_name(self, expression: cst.BaseExpression) -> str:
        if isinstance(expression, cst.Name):
            return expression.value
        if isinstance(expression, cst.Attribute):
            return expression.attr.value
        return ""


__all__ = ["ModelDefinitionCollector", "ModelReferenceCollector"]
