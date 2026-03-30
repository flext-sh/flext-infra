"""Dict-to-Mapping annotation transformer."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import override

import libcst as cst

from flext_infra import t

_MUTATING_METHODS = frozenset({
    "clear",
    "copy",
    "pop",
    "popitem",
    "setdefault",
    "update",
})


class _MutableParamVisitor(cst.CSTVisitor):
    """Detect dict parameters that are mutated in function bodies."""

    def __init__(self, param_names: t.Infra.StrSet) -> None:
        self._param_names = param_names
        self.mutated: t.Infra.StrSet = set()

    def _check_subscript_target(self, target: cst.BaseAssignTargetExpression) -> None:
        """Mark param as mutated if assigned via subscript (e.g. d[key] = ...)."""
        if (
            isinstance(target, cst.Subscript)
            and isinstance(target.value, cst.Name)
            and target.value.value in self._param_names
        ):
            self.mutated.add(target.value.value)

    @override
    def visit_AssignTarget(self, node: cst.AssignTarget) -> None:
        self._check_subscript_target(node.target)

    @override
    def visit_AugAssign(self, node: cst.AugAssign) -> None:
        self._check_subscript_target(node.target)

    @override
    def visit_Call(self, node: cst.Call) -> None:
        func = node.func
        if not isinstance(func, cst.Attribute) or not isinstance(func.value, cst.Name):
            return
        if (
            func.value.value in self._param_names
            and func.attr.value in _MUTATING_METHODS
        ):
            self.mutated.add(func.value.value)


class FlextInfraDictToMappingTransformer(cst.CSTTransformer):
    """Transform dict annotations to Mapping for immutable parameters."""

    def __init__(self, *, include_return_annotations: bool) -> None:
        """Initialize with return-annotation rewriting toggle."""
        self.changes: MutableSequence[str] = []
        self._has_mapping_import = False
        self._include_return_annotations = include_return_annotations

    @staticmethod
    def _collect_mutated_params(function_node: cst.FunctionDef) -> t.Infra.StrSet:
        param_names: t.Infra.StrSet = set()
        parameters = function_node.params
        param_names.update(param.name.value for param in parameters.posonly_params)
        param_names.update(param.name.value for param in parameters.params)
        param_names.update(param.name.value for param in parameters.kwonly_params)
        if isinstance(parameters.star_arg, cst.Param):
            param_names.add(parameters.star_arg.name.value)
        if parameters.star_kwarg is not None:
            param_names.add(parameters.star_kwarg.name.value)
        mutating_methods = {"clear", "copy", "pop", "popitem", "setdefault", "update"}

        class MutableParamVisitor(cst.CSTVisitor):
            def __init__(self) -> None:
                self.mutated: t.Infra.StrSet = set()

            @override
            def visit_AssignTarget(self, node: cst.AssignTarget) -> None:
                target = node.target
                if isinstance(target, cst.Subscript):
                    value = target.value
                    if isinstance(value, cst.Name) and value.value in param_names:
                        self.mutated.add(value.value)

            @override
            def visit_AugAssign(self, node: cst.AugAssign) -> None:
                target = node.target
                if isinstance(target, cst.Subscript):
                    value = target.value
                    if isinstance(value, cst.Name) and value.value in param_names:
                        self.mutated.add(value.value)

            @override
            def visit_Call(self, node: cst.Call) -> None:
                func = node.func
                if not isinstance(func, cst.Attribute):
                    return
                if not isinstance(func.value, cst.Name):
                    return
                if func.value.value not in param_names:
                    return
                if func.attr.value in mutating_methods:
                    self.mutated.add(func.value.value)

        visitor = MutableParamVisitor()
        function_node.visit(visitor)
        return visitor.mutated

    @staticmethod
    def _is_overload_function(function_node: cst.FunctionDef) -> bool:
        for decorator in function_node.decorators:
            expr = decorator.decorator
            if isinstance(expr, cst.Name) and expr.value == "overload":
                return True
            if isinstance(expr, cst.Attribute) and expr.attr.value == "overload":
                return True
        return False

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.BaseStatement:
        if self._is_overload_function(original_node):
            return updated_node
        mutated_names = self._collect_mutated_params(original_node)
        parameters = updated_node.params
        star_arg_updated = parameters.star_arg
        if isinstance(star_arg_updated, cst.Param):
            star_arg_updated = self._rewrite_param_if_safe(
                star_arg_updated,
                mutated_names,
            )
        star_kwarg_updated = parameters.star_kwarg
        if star_kwarg_updated is not None:
            star_kwarg_updated = self._rewrite_param_if_safe(
                star_kwarg_updated,
                mutated_names,
            )
        rewritten_params = parameters.with_changes(
            posonly_params=[
                self._rewrite_param_if_safe(param, mutated_names)
                for param in parameters.posonly_params
            ],
            params=[
                self._rewrite_param_if_safe(param, mutated_names)
                for param in parameters.params
            ],
            kwonly_params=[
                self._rewrite_param_if_safe(param, mutated_names)
                for param in parameters.kwonly_params
            ],
            star_arg=star_arg_updated,
            star_kwarg=star_kwarg_updated,
        )
        working_node = updated_node.with_changes(params=rewritten_params)
        if not self._include_return_annotations:
            return working_node
        returns = working_node.returns
        if returns is None:
            return working_node
        rewritten = self._rewrite_annotation_expr(returns.annotation)
        if rewritten is returns.annotation:
            return working_node
        return working_node.with_changes(
            returns=returns.with_changes(annotation=rewritten),
        )

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        del original_node
        if not self.changes or self._has_mapping_import:
            return updated_node
        import_line: cst.SimpleStatementLine = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Attribute(
                        value=cst.Name("collections"),
                        attr=cst.Name("abc"),
                    ),
                    names=[cst.ImportAlias(name=cst.Name("Mapping"))],
                ),
            ],
        )
        body = list(updated_node.body)
        insert_at = 0
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and body[0].body
            and isinstance(body[0].body[0], cst.Expr)
        ):
            expr = body[0].body[0].value
            if isinstance(expr, cst.SimpleString):
                insert_at = 1
                if len(body) > 1 and isinstance(body[1], cst.EmptyLine):
                    insert_at = 2
        while insert_at < len(body):
            stmt = body[insert_at]
            if not isinstance(stmt, cst.SimpleStatementLine):
                break
            if not stmt.body or not isinstance(stmt.body[0], cst.ImportFrom):
                break
            future_import = stmt.body[0]
            module = future_import.module
            if not isinstance(module, cst.Name) or module.value != "__future__":
                break
            insert_at += 1
        body.insert(insert_at, import_line)
        return updated_node.with_changes(body=body)

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module = node.module
        if not isinstance(module, cst.Attribute) and (not isinstance(module, cst.Name)):
            return
        module_name = cst.Module(body=[]).code_for_node(module)
        if module_name != "collections.abc":
            return
        names = node.names
        if isinstance(names, cst.ImportStar):
            self._has_mapping_import = True
            return
        for alias in names:
            if isinstance(alias.name, cst.Name) and alias.name.value == "Mapping":
                self._has_mapping_import = True

    def _rewrite_annotation_expr(
        self,
        annotation: cst.BaseExpression,
    ) -> cst.BaseExpression:
        if not isinstance(annotation, cst.Subscript):
            return annotation
        if not isinstance(annotation.value, cst.Name):
            return annotation
        if annotation.value.value != "dict":
            return annotation
        replacement: cst.BaseExpression = annotation.with_changes(
            value=cst.Name("Mapping"),
        )
        self.changes.append("Converted annotation Mapping[...] to Mapping[...]")
        return replacement

    def _rewrite_param_if_safe(
        self,
        param: cst.Param,
        mutated_names: t.Infra.StrSet,
    ) -> cst.Param:
        if param.name.value in mutated_names:
            return param
        annotation = param.annotation
        if annotation is None:
            return param
        rewritten = self._rewrite_annotation_expr(annotation.annotation)
        if rewritten is annotation.annotation:
            return param
        return param.with_changes(
            annotation=annotation.with_changes(annotation=rewritten),
        )


__all__ = [
    "FlextInfraDictToMappingTransformer",
]
