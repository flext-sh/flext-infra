"""Materialize identity-proven dynamic service delegations in native Rope plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from textwrap import indent

from flext_infra import m, p, t
from flext_infra._utilities._semantic_cutover.declaration_retirement import (
    FlextInfraUtilitiesSemanticDeclarationRetirement,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities.rope_runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesSemanticDelegations:
    """Reject unproven callables before returning any publishable content change."""

    @classmethod
    def materialize_delegations(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        editable: tuple[Path, ...],
        rule_id: str,
    ) -> list[p.Infra.RopeChangeContents]:
        """Discover assignments by native factory identity, never a class-name map."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        changes: list[p.Infra.RopeChangeContents] = []
        for path in editable:
            resource = project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            )
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project,
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    resource, path
                ),
            )
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                msg = "delegation module has no native AST"
                raise TypeError(msg)
            rewrites: list[p.Infra.SourceRewrite] = []
            for owner in ast.walk(tree):
                if not isinstance(owner, ast.ClassDef):
                    continue
                for statement in owner.body:
                    if not (
                        isinstance(statement, ast.Assign)
                        and isinstance(statement.value, ast.Call)
                    ):
                        continue
                    scope = runtime.scope_at(
                        module, runtime.source_offset(module.source_code, statement)
                    )
                    invocation = statement.value
                    descriptor, arguments = cls._factory(
                        project, scope, invocation, depth=0
                    )
                    if descriptor is None:
                        continue
                    location = f"{rule_id}: {module.get_name()}:{statement.lineno}"
                    try:
                        cls._prove_descriptor(project, descriptor)
                        text = cls._method(
                            project, module, scope, owner, statement, arguments
                        )
                    except (TypeError, ValueError) as error:
                        msg = f"{location}: {error}; fix the declaring owner before publication"
                        raise ValueError(msg) from error
                    start = runtime.source_offset(module.source_code, statement)
                    segment = ast.get_source_segment(module.source_code, statement)
                    if segment is None:
                        msg = "delegation assignment has no authenticated source span"
                        raise ValueError(msg)
                    end = start + len(segment)
                    rewrites.append(
                        m.Infra.SourceRewrite(
                            start=start,
                            end=end,
                            text=indent(text, " " * statement.col_offset).lstrip(),
                        )
                    )
            if rewrites:
                changes.append(
                    FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                        resource, sources[path], rewrites
                    )
                )
        return changes

    @staticmethod
    def _body(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> list[ast.stmt]:
        body = node.body
        return body[1:] if ast.get_docstring(node) is not None else body

    @staticmethod
    def _definition(
        binding: p.Infra.RopePyName | None,
    ) -> (
        tuple[
            p.Infra.RopePyModule, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ]
        | None
    ):
        if binding is None:
            return None
        value = binding.get_object()
        if not isinstance(value, p.Infra.RopeSourceDefinition):
            return None
        node = value.get_ast()
        module = value.get_module()
        if module is None or not isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            return None
        return module, node

    @classmethod
    def _factory(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        call: ast.Call,
        *,
        depth: int,
    ) -> tuple[p.Infra.RopePyName | None, tuple[ast.expr, ...]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.resolve_symbol(scope, call.func)
        definition = cls._definition(binding)
        if definition is None:
            return None, ()
        module, node = definition
        if isinstance(node, ast.ClassDef):
            # Python protocol members, not a project-specific descriptor identifier.
            if {"__init__", "__get__"}.issubset({
                part.name for part in node.body if isinstance(part, ast.FunctionDef)
            }):
                if call.keywords or len(call.args) != 2:
                    msg = "delegation constructor requires two explicit arguments"
                    raise ValueError(msg)
                return binding, tuple(call.args)
            return None, ()
        if isinstance(node, ast.AsyncFunctionDef):
            return None, ()
        body = cls._body(node)
        if not (
            len(body) == 1
            and isinstance(body[0], ast.Return)
            and isinstance(body[0].value, ast.Call)
        ):
            return None, ()
        if depth >= 2:
            msg = "delegation factory exceeds two proven static wrappers"
            raise ValueError(msg)
        lexical = runtime.scope_at(
            module, runtime.source_offset(module.source_code, node)
        )
        if len(node.decorator_list) != 1 or not runtime.same_name(
            runtime.resolve_symbol(lexical, node.decorator_list[0]),
            runtime.qualified_name(project, "builtins.staticmethod"),
        ):
            return None, ()
        parameters = node.args.posonlyargs + node.args.args
        if (
            len(parameters) != 2
            or node.args.defaults
            or node.args.kwonlyargs
            or node.args.vararg
            or node.args.kwarg
        ):
            msg = "delegation wrapper has an ambiguous argument contract"
            raise ValueError(msg)
        supplied = dict(zip((item.arg for item in parameters), call.args, strict=False))
        for keyword in call.keywords:
            if keyword.arg is None or keyword.arg in supplied:
                msg = "delegation wrapper has expanded or repeated arguments"
                raise ValueError(msg)
            supplied[keyword.arg] = keyword.value
        if set(supplied) != {item.arg for item in parameters}:
            msg = "delegation wrapper has missing or excess arguments"
            raise ValueError(msg)
        returned = body[0].value
        if returned.keywords or not all(
            isinstance(arg, ast.Name) and arg.id in supplied for arg in returned.args
        ):
            msg = "delegation wrapper must return the original arguments unchanged"
            raise ValueError(msg)
        target_scope = binding.get_object().get_scope() if binding is not None else None
        if target_scope is None:
            msg = "delegation wrapper has no native scope"
            raise ValueError(msg)
        descriptor, selected = cls._factory(
            project, target_scope, returned, depth=depth + 1
        )
        if descriptor is None:
            return None, ()
        if not all(
            isinstance(arg, ast.Name) and arg.id in supplied for arg in selected
        ):
            msg = "delegation wrappers do not preserve native argument bindings"
            raise ValueError(msg)
        return descriptor, tuple(
            supplied[arg.id] for arg in selected if isinstance(arg, ast.Name)
        )

    @classmethod
    def _prove_descriptor(
        cls, project: p.Infra.RopeProject, binding: p.Infra.RopePyName
    ) -> None:
        definition = cls._definition(binding)
        if definition is None or not isinstance(definition[1], ast.ClassDef):
            msg = "descriptor has no native class declaration"
            raise ValueError(msg)
        module, owner = definition
        if owner.bases or owner.keywords or owner.decorator_list:
            msg = "descriptor inheritance or decorators change binding semantics"
            raise ValueError(msg)
        members = cls._body(owner)
        if not all(isinstance(node, ast.FunctionDef) for node in members):
            msg = "descriptor has additional class effects"
            raise ValueError(msg)
        initializers = [
            node
            for node in members
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        ]
        getters = [
            node
            for node in members
            if isinstance(node, ast.FunctionDef) and node.name == "__get__"
        ]
        if len(initializers) != 1 or len(initializers) + len(getters) != len(members):
            msg = "descriptor has additional behavior"
            raise ValueError(msg)
        initializer = initializers[0]
        parameters = initializer.args.args
        body = cls._body(initializer)
        if len(parameters) != 3 or initializer.decorator_list or len(body) != 5:
            msg = "descriptor constructor is not callback/signature-only"
            raise ValueError(msg)
        receiver, callback, prototype = (arg.arg for arg in parameters)
        stored, invoke, wrap, annotations, unbound = body
        if not (
            isinstance(stored, ast.Assign)
            and len(stored.targets) == 1
            and isinstance(stored.targets[0], ast.Attribute)
            and isinstance(invoke, ast.FunctionDef)
            and len(invoke.args.args) == 1
            and invoke.args.vararg
            and invoke.args.kwarg
            and isinstance(wrap, ast.Expr)
            and isinstance(wrap.value, ast.Call)
            and isinstance(annotations, ast.Assign)
            and isinstance(annotations.value, ast.Call)
            and isinstance(unbound, ast.Assign)
            and len(unbound.targets) == 1
            and isinstance(unbound.targets[0], ast.Attribute)
        ):
            msg = "descriptor does not retain the original callback and signature"
            raise ValueError(msg)
        callback_field = stored.targets[0].attr
        unbound_field = unbound.targets[0].attr
        native = ast.parse(
            f"{receiver}.{callback_field} = {callback}\n"
            f"def {invoke.name}({invoke.args.args[0].arg}, *{invoke.args.vararg.arg}, **{invoke.args.kwarg.arg}):\n"
            f"    return {callback}({invoke.args.args[0].arg})(*{invoke.args.vararg.arg}, **{invoke.args.kwarg.arg})\n"
            f"wrap({invoke.name}, {prototype})\n"
            f"{invoke.name}.__annotations__ = hints({prototype})\n"
            f"{receiver}.{unbound_field} = {invoke.name}\n"
        ).body
        actual = deepcopy(body)
        actual_invoke = actual[1]
        if not isinstance(actual_invoke, ast.FunctionDef):
            msg = "descriptor invocation is not a native function"
            raise TypeError(msg)
        if (
            invoke.decorator_list
            or invoke.type_params
            or invoke.args.defaults
            or invoke.args.kwonlyargs
        ):
            msg = "descriptor invocation has additional signature effects"
            raise ValueError(msg)
        actual_invoke.returns = None
        for argument in (
            *actual_invoke.args.args,
            actual_invoke.args.vararg,
            actual_invoke.args.kwarg,
        ):
            if argument is not None:
                argument.annotation = None
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = binding.get_object().get_scope()
        if scope is None:
            msg = "descriptor has no native lexical scope"
            raise ValueError(msg)
        for expression, identity in (
            (wrap.value, "functools.update_wrapper"),
            (annotations.value, "typing.get_type_hints"),
        ):
            if not runtime.same_name(
                runtime.resolve_symbol(scope, expression.func),
                runtime.qualified_name(project, identity),
            ):
                msg = "descriptor signature metadata has an unproven native origin"
                raise ValueError(msg)
        if isinstance(actual[2], ast.Expr) and isinstance(actual[2].value, ast.Call):
            actual[2].value.func = ast.Name(id="wrap", ctx=ast.Load())
        if isinstance(actual[3], ast.Assign) and isinstance(actual[3].value, ast.Call):
            actual[3].value.func = ast.Name(id="hints", ctx=ast.Load())
        if [ast.dump(node) for node in actual] != [ast.dump(node) for node in native]:
            msg = "descriptor performs effects beyond callback/signature storage"
            raise ValueError(msg)
        implementations = []
        for getter in getters:
            if getter.decorator_list:
                lexical = runtime.scope_at(
                    module, runtime.source_offset(module.source_code, getter)
                )
                if not all(
                    runtime.same_name(
                        runtime.resolve_symbol(lexical, decorator),
                        runtime.qualified_name(project, "typing.overload"),
                    )
                    for decorator in getter.decorator_list
                ) or not (
                    len(cls._body(getter)) == 1
                    and isinstance(cls._body(getter)[0], ast.Expr)
                    and isinstance(cls._body(getter)[0].value, ast.Constant)
                    and cls._body(getter)[0].value.value is Ellipsis
                ):
                    msg = "descriptor getter decorator is not an inert overload"
                    raise ValueError(msg)
            else:
                implementations.append(getter)
        if len(implementations) != 1 or len(implementations[0].args.args) != 3:
            msg = "descriptor has no unique native getter"
            raise ValueError(msg)
        getter = implementations[0]
        own, instance, _owner = (arg.arg for arg in getter.args.args)
        expected = ast.parse(
            f"if {instance} is None:\n    return {own}.{unbound_field}\n"
            f"return {own}.{callback_field}({instance})\n"
        ).body
        if [ast.dump(node) for node in cls._body(getter)] != [
            ast.dump(node) for node in expected
        ]:
            msg = "descriptor captures a service snapshot or changes receiver binding"
            raise ValueError(msg)

    @classmethod
    def _method(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        owner: ast.ClassDef,
        statement: ast.Assign,
        arguments: tuple[ast.expr, ...],
    ) -> str:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if (
            len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or len(arguments) != 2
        ):
            msg = "delegation requires one named class assignment"
            raise ValueError(msg)
        callback, prototype = arguments
        if not (
            isinstance(callback, ast.Lambda)
            and len(callback.args.args) == 1
            and not callback.args.posonlyargs
            and not callback.args.kwonlyargs
            and not callback.args.defaults
            and not callback.args.vararg
            and not callback.args.kwarg
            and isinstance(callback.body, ast.Attribute)
            and isinstance(callback.body.value, ast.Attribute)
            and isinstance(callback.body.value.value, ast.Name)
            and callback.body.value.value.id == callback.args.args[0].arg
        ):
            msg = "callback must select its receiver's current port method without effects"
            raise ValueError(msg)
        binding = runtime.resolve_symbol(scope, prototype)
        definition = cls._definition(binding)
        if definition is None or not isinstance(
            definition[1], ast.FunctionDef | ast.AsyncFunctionDef
        ):
            msg = "prototype has no native function declaration"
            raise ValueError(msg)
        origin, native = definition
        # The existing retirement owner rejects callable defaults before effects.
        FlextInfraUtilitiesSemanticDeclarationRetirement._native_contract_signature(
            binding
        )
        if native.decorator_list:
            msg = f"prototype {native.name} has signature-ambiguous decorators"
            raise ValueError(msg)
        if any(
            isinstance(node, ast.Yield | ast.YieldFrom) for node in ast.walk(native)
        ):
            msg = "generator prototypes require a separate proven forwarding contract"
            raise ValueError(msg)
        port = callback.body.value.attr
        annotations = [
            node.annotation
            for node in owner.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == port
        ]
        if len(annotations) != 1:
            msg = f"port {port} has no unique native annotation"
            raise ValueError(msg)
        port_type = runtime.annotation_origin(project, annotations[0], scope)
        actual = (
            port_type.get_object().get_attributes().get(callback.body.attr)
            if port_type is not None
            else None
        )
        if binding is None or not runtime.same_name(binding, actual):
            msg = f"port {port} and prototype select different native operations"
            raise ValueError(msg)
        rendered = deepcopy(native)
        rendered.name = statement.targets[0].id
        rendered.decorator_list = []
        positional = rendered.args.posonlyargs + rendered.args.args
        if not positional or positional[0].arg != callback.args.args[0].arg:
            msg = "prototype and callback receiver names differ"
            raise ValueError(msg)
        positional[0].annotation = None
        if rendered.args.defaults and len(rendered.args.defaults) == len(positional):
            msg = "prototype receiver cannot have a default"
            raise ValueError(msg)
        forwarded: list[ast.expr] = [
            ast.Name(id=arg.arg, ctx=ast.Load()) for arg in positional[1:]
        ]
        if rendered.args.vararg:
            forwarded.append(
                ast.Starred(
                    value=ast.Name(id=rendered.args.vararg.arg, ctx=ast.Load()),
                    ctx=ast.Load(),
                )
            )
        keywords = [
            ast.keyword(arg=arg.arg, value=ast.Name(id=arg.arg, ctx=ast.Load()))
            for arg in rendered.args.kwonlyargs
        ]
        if rendered.args.kwarg:
            keywords.append(
                ast.keyword(
                    arg=None, value=ast.Name(id=rendered.args.kwarg.arg, ctx=ast.Load())
                )
            )
        invocation = ast.Call(
            func=deepcopy(callback.body), args=forwarded, keywords=keywords
        )
        returned = ast.Return(
            value=ast.Await(value=invocation)
            if isinstance(native, ast.AsyncFunctionDef)
            else invocation
        )
        rendered.body = (
            [deepcopy(native.body[0])] if ast.get_docstring(native) is not None else []
        ) + [returned]
        # Admit only names already bound to the same native declaration at destination.
        # Import transplantation is deliberately not approximated by copying source text.
        signature = deepcopy(rendered)
        signature.body = [ast.Pass()]
        generics = {parameter.name for parameter in signature.type_params}
        native_scope = binding.get_object().get_scope()
        if native_scope is None:
            msg = "prototype has no native annotation scope"
            raise ValueError(msg)
        for node in ast.walk(signature):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id not in generics
            ):
                original = runtime.expression_name(native_scope, node.id)
                destination = runtime.expression_name(scope, node.id)
                if (
                    original is None
                    or destination is None
                    or not runtime.same_name(original, destination)
                ):
                    msg = f"signature binding {node.id} requires native import transplantation from {origin.get_name()}"
                    raise ValueError(msg)
        return ast.unparse(ast.fix_missing_locations(rendered))


__all__: list[str] = ["FlextInfraUtilitiesSemanticDelegations"]
