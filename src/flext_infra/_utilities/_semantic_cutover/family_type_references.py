"""Quoted type references resolved in the original Rope lexical scope."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from flext_infra import c, m, p, t

from ..rope_runtime_modules import FlextInfraUtilitiesRopeRuntimeModules
from ..rope_runtime_refactors import FlextInfraUtilitiesRopeRuntimeRefactors


class FlextInfraUtilitiesSemanticFamilyTypeReferences:
    """Select type positions structurally and bind every edit to Rope identity."""

    @classmethod
    def _family_quoted_rewrites(
        cls,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        *,
        owner_name: str,
        wrapper: p.Infra.RopePyName,
        names: t.MappingKV[str, str],
    ) -> t.Pair[bool, t.VariadicTuple[m.Infra.SourceRewrite]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        edits: list[m.Infra.SourceRewrite] = []
        for annotation, declaration_line in cls._annotation_roots(ast.parse(source)):
            start, _end = cls._expression_range(source, annotation)
            scope = runtime.scope_at(module, start, declaration_line=declaration_line)
            for node in cls._type_nodes(annotation, project, scope):
                if not isinstance(node, ast.Constant) or not isinstance(
                    node.value, str
                ):
                    continue
                blocked, updated = cls._quoted_type_source(
                    node.value,
                    project,
                    resource,
                    scope,
                    owner_name=owner_name,
                    wrapper=wrapper,
                    names=names,
                )
                if blocked:
                    return (True, ())
                if updated != node.value:
                    start, end = cls._expression_range(source, node)
                    edits.append(
                        m.Infra.SourceRewrite(start=start, end=end, text=repr(updated))
                    )
        return (False, tuple(edits))

    @classmethod
    def _quoted_type_source(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        scope: p.Infra.RopeScope,
        *,
        owner_name: str,
        wrapper: p.Infra.RopePyName,
        names: t.MappingKV[str, str],
    ) -> t.Pair[bool, str]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        nodes = tuple(
            cls._type_nodes(ast.parse(source, mode="eval").body, project, scope)
        )
        edits: list[m.Infra.SourceRewrite] = []
        for node in nodes:
            start, end = cls._expression_range(source, node)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                blocked, updated = cls._quoted_type_source(
                    node.value,
                    project,
                    resource,
                    scope,
                    owner_name=owner_name,
                    wrapper=wrapper,
                    names=names,
                )
                if blocked:
                    return (True, source)
                if updated != node.value:
                    edits.append(
                        m.Infra.SourceRewrite(start=start, end=end, text=repr(updated))
                    )
            elif isinstance(node, ast.Attribute) and runtime.same_name(
                wrapper, runtime.resolve_symbol(scope, node.value)
            ):
                if node.attr not in names:
                    return (True, source)
                parent = (
                    ast.unparse(node.value.value)
                    if isinstance(node.value, ast.Attribute)
                    else owner_name
                    if scope.get_kind() == c.Infra.RopeScopeKind.FUNCTION
                    else ""
                )
                text = f"{parent}.{names[node.attr]}" if parent else names[node.attr]
                edits.append(m.Infra.SourceRewrite(start=start, end=end, text=text))
            elif (
                isinstance(node, ast.Name)
                and node.id in names
                and runtime.same_name(
                    wrapper.get_object().get_attribute(node.id),
                    runtime.resolve_symbol(scope, node),
                )
            ):
                edits.append(
                    m.Infra.SourceRewrite(start=start, end=end, text=names[node.id])
                )
        for node in nodes:
            start, end = cls._expression_range(source, node)
            if not any(
                edit.start <= start and end <= edit.end for edit in edits
            ) and runtime.same_name(wrapper, runtime.resolve_symbol(scope, node)):
                return (True, source)
        change = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        )
        return (False, change.new_contents)

    @staticmethod
    def _annotation_roots(module: ast.Module) -> Iterator[t.Pair[ast.expr, int | None]]:
        for node in ast.walk(module):
            if isinstance(node, ast.AnnAssign):
                yield (node.annotation, None)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                arguments = (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
                for argument in arguments:
                    annotation = argument.annotation
                    if annotation is not None:
                        yield (annotation, node.lineno)
                for argument in (node.args.vararg, node.args.kwarg):
                    if argument is None:
                        continue
                    annotation = argument.annotation
                    if annotation is not None:
                        yield (annotation, node.lineno)
                if node.returns is not None:
                    yield (node.returns, node.lineno)
            elif isinstance(node, ast.TypeAlias):
                yield (node.value, None)
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    yield (base, node.lineno)
            elif isinstance(node, ast.TypeVar):
                if node.bound is not None:
                    yield (node.bound, None)
                default_value = node.default_value
                if default_value is not None:
                    yield (default_value, None)
            elif isinstance(node, ast.ParamSpec | ast.TypeVarTuple):
                default_value = node.default_value
                if default_value is not None:
                    yield (default_value, None)

    @classmethod
    def _type_nodes(
        cls, node: ast.expr, project: p.Infra.RopeProject, scope: p.Infra.RopeScope
    ) -> Iterator[ast.expr]:
        yield node
        if isinstance(node, ast.Subscript):
            yield from cls._type_nodes(node.value, project, scope)
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            binding = runtime.resolve_symbol(scope, node.value)
            typing = project.get_module("typing")
            if runtime.same_name(typing.get_attribute("Literal"), binding):
                return
            arguments = (
                node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            )
            if runtime.same_name(typing.get_attribute("Annotated"), binding):
                arguments = arguments[:1]
            for argument in arguments:
                yield from cls._type_nodes(argument, project, scope)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            yield from cls._type_nodes(node.left, project, scope)
            yield from cls._type_nodes(node.right, project, scope)
        elif isinstance(node, ast.Tuple | ast.List):
            for element in node.elts:
                yield from cls._type_nodes(element, project, scope)
        elif isinstance(node, ast.Attribute | ast.Starred):
            yield from cls._type_nodes(node.value, project, scope)

    @staticmethod
    def _expression_range(source: str, expression: ast.expr) -> t.Pair[int, int]:
        if expression.end_lineno is None or expression.end_col_offset is None:
            msg = "Parsed type expression has no complete source coordinates"
            raise ValueError(msg)
        lines = source.splitlines(keepends=True)
        start = sum(map(len, lines[: expression.lineno - 1])) + len(
            lines[expression.lineno - 1]
            .encode("utf-8")[: expression.col_offset]
            .decode("utf-8")
        )
        end = sum(map(len, lines[: expression.end_lineno - 1])) + len(
            lines[expression.end_lineno - 1]
            .encode("utf-8")[: expression.end_col_offset]
            .decode("utf-8")
        )
        return (start, end)


__all__: list[str] = ["FlextInfraUtilitiesSemanticFamilyTypeReferences"]
