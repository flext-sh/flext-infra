from __future__ import annotations

from collections.abc import Callable
from typing import override

import libcst as cst

from flext_infra.transformers.import_insertion import (
    FlextInfraTransformerImportInsertion,
)


class TypingAnnotationReplacer(cst.CSTTransformer):
    DUNDER_OBJECT_ALLOWLIST = frozenset(
        {
            "__eq__",
            "__ne__",
            "__hash__",
            "__lt__",
            "__le__",
            "__gt__",
            "__ge__",
            "model_post_init",
        },
    )

    def __init__(
        self,
        *,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._on_change = on_change
        self.modified: bool = False
        self.changes: list[str] = []
        self._t_import_present: bool = False
        self._needs_t_import: bool = False
        self._current_function: str = ""
        self._function_stack: list[str] = []
        self._param_depth: int = 0

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module_name = self._module_name_from_expr(node.module)
        if not module_name.startswith("flext"):
            return
        if isinstance(node.names, cst.ImportStar):
            return
        for import_alias in node.names:
            if not isinstance(import_alias.name, cst.Name):
                continue
            bound_name = import_alias.name.value
            if import_alias.asname is not None and isinstance(
                import_alias.asname.name, cst.Name
            ):
                bound_name = import_alias.asname.name.value
            if bound_name == "t":
                self._t_import_present = True
                return

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._function_stack.append(self._current_function)
        self._current_function = node.name.value

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        del original_node
        result_node = updated_node
        if updated_node.returns is not None:
            replacement = self._replace_expression(updated_node.returns.annotation)
            if replacement is not None:
                result_node = updated_node.with_changes(
                    returns=updated_node.returns.with_changes(annotation=replacement),
                )
                self._mark_modified(
                    "Replaced return annotation: object -> t.ContainerValue"
                )
        self._current_function = (
            self._function_stack.pop() if self._function_stack else ""
        )
        return result_node

    @override
    def visit_Param(self, node: cst.Param) -> None:
        del node
        self._param_depth += 1

    @override
    def leave_Param(
        self,
        original_node: cst.Param,
        updated_node: cst.Param,
    ) -> cst.Param:
        del original_node
        result_node = updated_node
        if self._current_function not in self.DUNDER_OBJECT_ALLOWLIST:
            if updated_node.annotation is not None:
                replacement = self._replace_expression(
                    updated_node.annotation.annotation
                )
                if replacement is not None:
                    result_node = updated_node.with_changes(
                        annotation=updated_node.annotation.with_changes(
                            annotation=replacement
                        ),
                    )
                    self._mark_modified(
                        "Replaced parameter annotation: object -> t.ContainerValue"
                    )
        self._param_depth = max(0, self._param_depth - 1)
        return result_node

    @override
    def leave_AnnAssign(
        self,
        original_node: cst.AnnAssign,
        updated_node: cst.AnnAssign,
    ) -> cst.AnnAssign:
        del original_node
        replacement = self._replace_expression(updated_node.annotation.annotation)
        if replacement is None:
            return updated_node
        self._mark_modified(
            "Replaced assignment annotation: object -> t.ContainerValue"
        )
        return updated_node.with_changes(
            annotation=updated_node.annotation.with_changes(annotation=replacement),
        )

    @override
    def leave_Annotation(
        self,
        original_node: cst.Annotation,
        updated_node: cst.Annotation,
    ) -> cst.Annotation:
        del original_node
        if (
            self._param_depth > 0
            and self._current_function in self.DUNDER_OBJECT_ALLOWLIST
        ):
            return updated_node
        replacement = self._replace_expression(updated_node.annotation)
        if replacement is None:
            return updated_node
        self._mark_modified("Replaced annotation: object -> t.ContainerValue")
        return updated_node.with_changes(annotation=replacement)

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        del original_node
        if not self._needs_t_import or self._t_import_present:
            return updated_node
        new_import = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Name("flext_core"),
                    names=[cst.ImportAlias(name=cst.Name("t"))],
                ),
            ],
        )
        body = list(updated_node.body)
        insert_idx = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
            body,
        )
        new_body = body[:insert_idx] + [new_import] + body[insert_idx:]
        self._record_change("Added import: from flext_core import t")
        self._t_import_present = True
        return updated_node.with_changes(body=new_body)

    @staticmethod
    def _is_object_ref(node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.Name) and node.value == "object":
            return True
        if (
            isinstance(node, cst.Attribute)
            and isinstance(node.value, cst.Name)
            and node.value.value == "builtins"
            and node.attr.value == "object"
        ):
            return True
        return False

    def _replace_expression(
        self, node: cst.BaseExpression
    ) -> cst.BaseExpression | None:
        if self._is_object_ref(node):
            return self._t_container_value()

        if isinstance(node, cst.Subscript) and self._is_supported_base(node.value):
            updated_slices: list[cst.SubscriptElement] = []
            changed = False
            for element in node.slice:
                if not isinstance(element.slice, cst.Index):
                    updated_slices.append(element)
                    continue
                replacement = self._replace_expression(element.slice.value)
                if replacement is None:
                    updated_slices.append(element)
                    continue
                changed = True
                updated_slices.append(
                    element.with_changes(
                        slice=element.slice.with_changes(value=replacement),
                    ),
                )
            if changed:
                return node.with_changes(slice=tuple(updated_slices))

        return None

    def _is_supported_base(self, node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.Name):
            return node.value in {"dict", "Mapping", "list", "Sequence", "TypeAdapter"}
        return isinstance(node, cst.Attribute) and node.attr.value in {
            "dict",
            "Mapping",
            "list",
            "Sequence",
            "TypeAdapter",
        }

    def _module_name_from_expr(self, node: cst.BaseExpression | None) -> str:
        if node is None:
            return ""
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            prefix = self._module_name_from_expr(node.value)
            return f"{prefix}.{node.attr.value}" if prefix else node.attr.value
        return ""

    def _t_container_value(self) -> cst.Attribute:
        return cst.Attribute(value=cst.Name("t"), attr=cst.Name("ContainerValue"))

    def _mark_modified(self, message: str) -> None:
        self.modified = True
        self._needs_t_import = True
        self._record_change(message)

    def _record_change(self, msg: str) -> None:
        self.changes.append(msg)
        if self._on_change is not None:
            self._on_change(msg)


__all__ = ["TypingAnnotationReplacer"]
