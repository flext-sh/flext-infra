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
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticDeclarationRetirement,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)


class FlextInfraUtilitiesSemanticDelegations(
    FlextInfraUtilitiesSemanticDeclarationRetirement
):
    """Reject unproven callables before returning any publishable content change."""

    @classmethod
    def materialize_delegations(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        editable: tuple[Path, ...],
        rule_id: str,
    ) -> list[p.Infra.RopeChangeContents]:
        """Discover assignments by native factory identity, never a class-name map.

        Returns:
            Checked native content changes, without publishing any source.

        """
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
            rewrites, required = cls._module_rewrites(project, module, rule_id, sources)
            if rewrites:
                change = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                    resource, sources[path], rewrites
                )
                if required:
                    organized = runtime.module_imports_for_pymodule(
                        project,
                        runtime.build_string_module(
                            project, change.new_contents, resource=resource
                        ),
                    )
                    for information in required:
                        organized.add_import(information)
                    change = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                        resource,
                        sources[path],
                        (
                            m.Infra.SourceRewrite(
                                start=0,
                                end=len(sources[path]),
                                text=organized.get_changed_source(),
                            ),
                        ),
                    )
                changes.append(change)
        return changes

    @classmethod
    def _module_rewrites(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        rule_id: str,
        sources: t.MappingKV[Path, str],
    ) -> tuple[list[p.Infra.SourceRewrite], list[p.Infra.RopeImportInfo]]:
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            msg = "delegation module has no native AST"
            raise TypeError(msg)
        rewrites: list[p.Infra.SourceRewrite] = []
        required: list[p.Infra.RopeImportInfo] = []
        for owner in ast.walk(tree):
            if not isinstance(owner, ast.ClassDef):
                continue
            for statement in owner.body:
                if isinstance(statement, ast.Assign) and isinstance(
                    statement.value, ast.Call
                ):
                    selected = cls._assignment(
                        project, module, (owner, statement), rule_id
                    )
                    if selected is not None:
                        rewrites.append(selected[0])
                        required.extend(selected[1])
            rewrites.extend(cls._ignored_types(project, module, owner, rewrites))
            rewrites.extend(
                cls._wrapper_retirement(project, module, sources, (owner, rewrites))
            )
        return rewrites, required

    @classmethod
    def _wrapper_retirement(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        sources: t.MappingKV[Path, str],
        context: tuple[ast.ClassDef, list[p.Infra.SourceRewrite]],
    ) -> list[p.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        selected: list[p.Infra.SourceRewrite] = []
        for statement in context[0].body:
            if not isinstance(statement, ast.Assign) or not isinstance(
                statement.value, ast.Call
            ):
                continue
            start = runtime.source_offset(module.source_code, statement)
            if not any(rewrite.start == start for rewrite in context[1]):
                continue
            scope = runtime.scope_at(module, start)
            binding = runtime.resolve_symbol(scope, statement.value.func)
            definition = cls._definition(binding)
            if definition is None or binding is None:
                continue
            origin, wrapper = definition
            if origin is not module or not isinstance(wrapper, ast.FunctionDef):
                continue
            rewrite = cls._retire_wrapper(
                project, module, binding, (wrapper, context[1], sources, context[0])
            )
            if rewrite is not None and not any(
                item.start == rewrite.start for item in selected
            ):
                selected.append(rewrite)
        return selected

    @classmethod
    def _retire_wrapper(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        binding: p.Infra.RopePyName,
        context: tuple[
            ast.FunctionDef,
            list[p.Infra.SourceRewrite],
            t.MappingKV[Path, str],
            ast.ClassDef,
        ],
    ) -> p.Infra.SourceRewrite | None:
        wrapper, rewrites, sources, owner = context
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = module.get_resource()
        if resource is None:
            msg = "wrapper retirement has no native resource"
            raise ValueError(msg)
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project, wrapper.name, binding, imports=False, in_hierarchy=False
        )
        if any(
            not occurrence.is_defined()
            and not any(item.start <= occurrence.offset < item.end for item in rewrites)
            for occurrence in finder.find_occurrences(resource=resource)
        ):
            return None
        owner_binding = runtime.resolve_symbol(
            runtime.scope_at(module, runtime.source_offset(module.source_code, owner)),
            ast.Name(id=owner.name, ctx=ast.Load()),
        )
        if owner_binding is None:
            msg = "wrapper retirement lost its native declaring owner"
            raise ValueError(msg)
        owner_finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project, owner.name, owner_binding, imports=False, in_hierarchy=False
        )
        # A carrier outside the class can dynamically select this still-shipped
        # factory. Leave it intact unless the existing retirement proof is admissible.
        if any(
            not occurrence.is_defined()
            and not (
                owner.lineno
                <= module.source_code.count("\n", 0, occurrence.offset) + 1
                <= (owner.end_lineno or owner.lineno)
            )
            for occurrence in owner_finder.find_occurrences(resource=resource)
        ):
            return None
        cls._prove_contract_retirement(
            project,
            sources,
            owners=(binding, None),
            destinations=(),
            span=(
                Path(resource.real_path),
                owner.lineno,
                owner.end_lineno or owner.lineno,
            ),
        )
        first: ast.expr | ast.FunctionDef = wrapper
        if wrapper.decorator_list:
            first = wrapper.decorator_list[0]
        start = runtime.source_offset(module.source_code, first)
        if first is not wrapper:
            start -= len("@")
        segment = ast.get_source_segment(module.source_code, wrapper)
        if segment is None:
            msg = "wrapper retirement has no native declaration span"
            raise ValueError(msg)
        end = runtime.source_offset(module.source_code, wrapper) + len(segment)
        return m.Infra.SourceRewrite(start=start, end=end, text="")

    @classmethod
    def _ignored_types(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        owner: ast.ClassDef,
        rewrites: list[p.Infra.SourceRewrite],
    ) -> list[p.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        descriptors: list[p.Infra.RopePyName] = []
        for statement in owner.body:
            if not isinstance(statement, ast.Assign) or not isinstance(
                statement.value, ast.Call
            ):
                continue
            start = runtime.source_offset(module.source_code, statement)
            if any(rewrite.start == start for rewrite in rewrites):
                descriptor, _arguments = (
                    FlextInfraUtilitiesSemanticDelegations._factory(
                        project, runtime.scope_at(module, start), statement.value
                    )
                )
                if descriptor is not None:
                    descriptors.append(descriptor)
        if not descriptors:
            return []
        return cls._ignored_type_elements(project, module, owner, descriptors)

    @staticmethod
    def _ignored_type_elements(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        owner: ast.ClassDef,
        descriptors: list[p.Infra.RopePyName],
    ) -> list[p.Infra.SourceRewrite]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, owner)
        )
        selected: list[p.Infra.SourceRewrite] = []
        for statement in owner.body:
            if not isinstance(statement, ast.AnnAssign | ast.Assign) or not isinstance(
                statement.value, ast.Call
            ):
                continue
            invocation = statement.value
            if not runtime.same_name(
                runtime.qualified_name(project, "pydantic.ConfigDict"),
                runtime.resolve_symbol(scope, invocation.func),
            ):
                continue
            for keyword in invocation.keywords:
                if keyword.arg != "ignored_types" or not isinstance(
                    keyword.value, ast.Tuple
                ):
                    continue
                remaining = [
                    element
                    for element in keyword.value.elts
                    if not any(
                        runtime.same_name(
                            descriptor, runtime.resolve_symbol(scope, element)
                        )
                        for descriptor in descriptors
                    )
                ]
                if len(remaining) != len(keyword.value.elts):
                    start = runtime.source_offset(module.source_code, keyword.value)
                    segment = ast.get_source_segment(module.source_code, keyword.value)
                    if segment is None:
                        msg = (
                            "ignored descriptor configuration has no native source span"
                        )
                        raise ValueError(msg)
                    selected.append(
                        m.Infra.SourceRewrite(
                            start=start,
                            end=start + len(segment),
                            text=ast.unparse(ast.Tuple(elts=remaining, ctx=ast.Load())),
                        )
                    )
        return selected

    @classmethod
    def _assignment(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        declaration: tuple[ast.ClassDef, ast.Assign],
        rule_id: str,
    ) -> tuple[p.Infra.SourceRewrite, tuple[p.Infra.RopeImportInfo, ...]] | None:
        owner, statement = declaration
        if not isinstance(statement.value, ast.Call):
            return None
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        start = runtime.source_offset(module.source_code, statement)
        scope = runtime.scope_at(module, start)
        try:
            descriptor, arguments = cls._factory(project, scope, statement.value)
            if descriptor is None:
                return None
            cls._require_deferred(module)
            cls._prove_descriptor(project, descriptor)
            text, imports = cls._method(project, scope, owner, statement, arguments)
        except (TypeError, ValueError) as error:
            msg = (
                f"{rule_id}: {module.get_name()}:{statement.lineno}: {error}; "
                "fix the declaring owner before publication"
            )
            raise ValueError(msg) from error
        segment = ast.get_source_segment(module.source_code, statement)
        if segment is None:
            msg = "delegation assignment has no authenticated source span"
            raise ValueError(msg)
        return m.Infra.SourceRewrite(
            start=start,
            end=start + len(segment),
            text=indent(text, " " * statement.col_offset).lstrip(),
        ), imports

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
        location = FlextInfraUtilitiesRopeRuntimeModules.definition_location(binding)
        module = location[0]
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(
            module
        ) or not isinstance(
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
        ancestors: tuple[p.Infra.RopePyName, ...] = (),
    ) -> tuple[p.Infra.RopePyName | None, tuple[ast.expr, ...]]:
        """Elect a terminal native descriptor before enforcing forwarding contracts.

        Returns:
            The descriptor and original arguments, or no elected descriptor.

        Raises:
            ValueError: If an elected wrapper lacks its native scope.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.resolve_symbol(scope, call.func)
        definition = cls._definition(binding)
        if (
            definition is None
            or binding is None
            or any(runtime.same_name(binding, previous) for previous in ancestors)
        ):
            return None, ()
        module, node = definition
        if isinstance(node, ast.ClassDef):
            # Python protocol members, not a project-specific descriptor identifier.
            if cls._descriptor_elected(project, module, node):
                operands = cls._descriptor_arguments(call)
                if len(ancestors) > len(operands):
                    msg = "delegation factory exceeds two proven static wrappers"
                    raise ValueError(msg)
                return binding, operands
            return None, ()
        body = cls._body(node)
        lexical = runtime.scope_at(
            module, runtime.source_offset(module.source_code, node)
        )
        if not (
            isinstance(node, ast.FunctionDef)
            and len(body) == 1
            and isinstance(body[0], ast.Return)
            and isinstance(body[0].value, ast.Call)
            and len(node.decorator_list) == 1
            and runtime.same_name(
                runtime.qualified_name(project, "builtins.staticmethod"),
                runtime.resolve_symbol(lexical, node.decorator_list[0]),
            )
        ):
            return None, ()
        target_scope = FlextInfraUtilitiesRopeRuntimeTypes.require_source_object(
            binding.get_object(), "delegation wrapper"
        ).get_scope()
        descriptor, selected = cls._factory(
            project, target_scope, body[0].value, ancestors=(*ancestors, binding)
        )
        if descriptor is None:
            return None, ()
        return descriptor, cls._factory_arguments(node, call, body[0].value, selected)

    @staticmethod
    def _descriptor_elected(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: ast.ClassDef,
    ) -> bool:
        if not {"__init__", "__get__"}.issubset({
            part.name for part in node.body if isinstance(part, ast.FunctionDef)
        }):
            return False
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        calls = [
            expression
            for part in node.body
            if isinstance(part, ast.FunctionDef) and part.name == "__init__"
            for expression in ast.walk(part)
            if isinstance(expression, ast.Call)
        ]
        return all(
            any(
                runtime.same_name(
                    runtime.qualified_name(project, identity),
                    runtime.resolve_symbol(
                        runtime.scope_at(
                            module,
                            runtime.source_offset(module.source_code, expression),
                        ),
                        expression.func,
                    ),
                )
                for expression in calls
            )
            for identity in ("functools.update_wrapper", "typing.get_type_hints")
        )

    @staticmethod
    def _descriptor_arguments(call: ast.Call) -> tuple[ast.expr, ast.expr]:
        """Read the callback/signature operands of an elected descriptor.

        Returns:
            The two explicit descriptor operands.

        Raises:
            ValueError: If operands are expanded, named or incomplete.

        """
        if call.keywords:
            msg = "delegation constructor requires two explicit arguments"
            raise ValueError(msg)
        try:
            callback, prototype = call.args
        except ValueError as error:
            msg = "delegation constructor requires two explicit arguments"
            raise ValueError(msg) from error
        return callback, prototype

    @staticmethod
    def _factory_arguments(
        node: ast.FunctionDef,
        call: ast.Call,
        returned: ast.Call,
        selected: tuple[ast.expr, ...],
    ) -> tuple[ast.expr, ...]:
        """Bind a proven forwarding layer without executing its factory.

        Returns:
            The original arguments in descriptor operand order.

        Raises:
            ValueError: If the wrapper changes the native argument contract.

        """
        parameters = node.args.posonlyargs + node.args.args
        if len(call.args) > len(parameters) or any(
            isinstance(arg, ast.Starred) for arg in call.args
        ):
            msg = "delegation wrapper has expanded or excess positional arguments"
            raise ValueError(msg)
        if (
            len(parameters) != len(selected)
            or node.args.defaults
            or node.args.kwonlyargs
            or node.args.vararg
            or node.args.kwarg
        ):
            msg = "delegation wrapper has an ambiguous argument contract"
            raise ValueError(msg)
        supplied = dict(zip((item.arg for item in parameters), call.args, strict=False))
        for keyword in call.keywords:
            if (
                keyword.arg is None
                or keyword.arg in supplied
                or keyword.arg in {arg.arg for arg in node.args.posonlyargs}
            ):
                msg = "delegation wrapper has expanded or repeated arguments"
                raise ValueError(msg)
            supplied[keyword.arg] = keyword.value
        if set(supplied) != {item.arg for item in parameters}:
            msg = "delegation wrapper has missing or excess arguments"
            raise ValueError(msg)
        if returned.keywords or not all(
            isinstance(arg, ast.Name) and arg.id in supplied for arg in returned.args
        ):
            msg = "delegation wrapper must return the original arguments unchanged"
            raise ValueError(msg)
        if not all(
            isinstance(arg, ast.Name) and arg.id in supplied for arg in selected
        ):
            msg = "delegation wrappers do not preserve native argument bindings"
            raise ValueError(msg)
        return tuple(supplied[arg.id] for arg in selected if isinstance(arg, ast.Name))

    @classmethod
    def _prove_descriptor(
        cls, project: p.Infra.RopeProject, binding: p.Infra.RopePyName
    ) -> None:
        definition = cls._definition(binding)
        if definition is None:
            msg = "descriptor has no native class declaration"
            raise ValueError(msg)
        module, owner = definition
        if not isinstance(owner, ast.ClassDef):
            msg = "descriptor has no native class declaration"
            raise TypeError(msg)
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
        fields = cls._prove_initializer(project, binding, initializers[0])
        cls._prove_getters(project, module, getters, fields)

    @classmethod
    def _prove_initializer(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        initializer: ast.FunctionDef,
    ) -> tuple[str, str]:
        parameters = tuple(arg.arg for arg in initializer.args.args)
        body = cls._body(initializer)
        receiver_arity = len(("receiver", "callback", "prototype"))
        constructor_statements = len((
            "store",
            "invoke",
            "wrap",
            "annotations",
            "unbound",
        ))
        if (
            len(parameters) != receiver_arity
            or initializer.decorator_list
            or len(body) != constructor_statements
        ):
            msg = "descriptor constructor is not callback/signature-only"
            raise ValueError(msg)
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
        fields = (stored.targets[0].attr, unbound.targets[0].attr)
        native = ast.parse(
            f"{parameters[0]}.{fields[0]} = {parameters[1]}\n"
            f"def {invoke.name}({invoke.args.args[0].arg}, "
            f"*{invoke.args.vararg.arg}, **{invoke.args.kwarg.arg}):\n"
            f"    return {parameters[1]}({invoke.args.args[0].arg})("
            f"*{invoke.args.vararg.arg}, **{invoke.args.kwarg.arg})\n"
            f"wrap({invoke.name}, {parameters[2]})\n"
            f"{invoke.name}.__annotations__ = hints({parameters[2]})\n"
            f"{parameters[0]}.{fields[1]} = {invoke.name}\n"
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
        cls._prove_metadata(project, binding, (wrap.value, annotations.value))
        if isinstance(actual[2], ast.Expr) and isinstance(actual[2].value, ast.Call):
            actual[2].value.func = ast.Name(id="wrap", ctx=ast.Load())
        if isinstance(actual[3], ast.Assign) and isinstance(actual[3].value, ast.Call):
            actual[3].value.func = ast.Name(id="hints", ctx=ast.Load())
        if [ast.dump(node) for node in actual] != [ast.dump(node) for node in native]:
            msg = "descriptor performs effects beyond callback/signature storage"
            raise ValueError(msg)
        return fields

    @staticmethod
    def _prove_metadata(
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        expressions: tuple[ast.Call, ast.Call],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = binding.get_object().get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            msg = "descriptor has no native lexical scope"
            raise ValueError(msg)
        for expression, identity in zip(
            expressions,
            ("functools.update_wrapper", "typing.get_type_hints"),
            strict=True,
        ):
            if not runtime.same_name(
                runtime.qualified_name(project, identity),
                runtime.resolve_symbol(
                    runtime.scope_at(
                        module, runtime.source_offset(module.source_code, expression)
                    ),
                    expression.func,
                ),
            ):
                msg = "descriptor signature metadata has an unproven native origin"
                raise ValueError(msg)

    @classmethod
    def _prove_getters(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        getters: list[ast.FunctionDef],
        fields: tuple[str, str],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        implementations: list[ast.FunctionDef] = []
        for getter in getters:
            if getter.decorator_list:
                lexical = runtime.scope_at(
                    module, runtime.source_offset(module.source_code, getter)
                )
                if not all(
                    runtime.same_name(
                        runtime.qualified_name(project, "typing.overload"),
                        runtime.resolve_symbol(lexical, decorator),
                    )
                    for decorator in getter.decorator_list
                ) or not (
                    len(cls._body(getter)) == 1
                    and ast.dump(cls._body(getter)[0])
                    == ast.dump(ast.Expr(value=ast.Constant(value=Ellipsis)))
                ):
                    msg = "descriptor getter decorator is not an inert overload"
                    raise ValueError(msg)
            else:
                implementations.append(getter)
        receiver_arity = len(("receiver", "instance", "owner"))
        if (
            len(implementations) != 1
            or len(implementations[0].args.args) != receiver_arity
        ):
            msg = "descriptor has no unique native getter"
            raise ValueError(msg)
        getter = implementations[0]
        own, instance, _owner = (arg.arg for arg in getter.args.args)
        expected = ast.parse(
            f"if {instance} is None:\n    return {own}.{fields[1]}\n"
            f"return {own}.{fields[0]}({instance})\n"
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
        scope: p.Infra.RopeScope,
        owner: ast.ClassDef,
        statement: ast.Assign,
        arguments: tuple[ast.expr, ...],
    ) -> tuple[str, tuple[p.Infra.RopeImportInfo, ...]]:
        if (
            len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or len(arguments) != len(("callback", "prototype"))
        ):
            msg = "delegation requires one named class assignment"
            raise ValueError(msg)
        callback, prototype = arguments
        selection = cls._selection(callback)
        binding, native = cls._prototype(project, scope, owner, (prototype, selection))
        rendered = cls._forward(native, statement.targets[0].id, selection)
        required = cls._signature_imports(project, binding, scope, rendered)
        return ast.unparse(ast.fix_missing_locations(rendered)), required

    @staticmethod
    def _selection(callback: ast.expr) -> tuple[str, str, str]:
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
            msg = (
                "callback must select its receiver's current port method "
                "without effects"
            )
            raise ValueError(msg)
        return callback.args.args[0].arg, callback.body.value.attr, callback.body.attr

    @classmethod
    def _prototype(
        cls,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        owner: ast.ClassDef,
        operands: tuple[ast.expr, tuple[str, str, str]],
    ) -> tuple[p.Infra.RopePyName, ast.FunctionDef]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        binding = runtime.resolve_symbol(scope, operands[0])
        definition = cls._definition(binding)
        if definition is None or binding is None:
            msg = "prototype has no native function declaration"
            raise ValueError(msg)
        origin, native = definition
        cls._require_deferred(origin)
        if not isinstance(native, ast.FunctionDef | ast.AsyncFunctionDef):
            msg = "prototype has no native function declaration"
            raise TypeError(msg)
        if isinstance(native, ast.AsyncFunctionDef):
            msg = (
                "async prototype cannot retain call-time port selection with a native "
                "async signature; materialize its declaring owner explicitly"
            )
            raise TypeError(msg)
        tree = origin.get_ast()
        if not isinstance(tree, ast.Module):
            msg = "prototype has no native lexical inventory"
            raise TypeError(msg)
        if any(
            sum(
                isinstance(part, ast.FunctionDef | ast.AsyncFunctionDef)
                and part.name == native.name
                for part in declaration.body
            )
            != 1
            for declaration in ast.walk(tree)
            if isinstance(declaration, ast.Module | ast.ClassDef)
            and native in declaration.body
        ):
            msg = f"prototype {native.name} has overloads or repeated declarations"
            raise ValueError(msg)
        # The existing retirement owner rejects callable defaults before effects.
        cls._native_contract_signature(binding)
        cls._default_identity(origin, scope, native)
        if any(
            not runtime.same_name(
                runtime.qualified_name(project, "typing.override"),
                runtime.resolve_symbol(
                    runtime.scope_at(
                        origin, runtime.source_offset(origin.source_code, native)
                    ),
                    decorator,
                ),
            )
            for decorator in native.decorator_list
        ):
            msg = f"prototype {native.name} has signature-ambiguous decorators"
            raise ValueError(msg)
        if any(
            isinstance(node, ast.Yield | ast.YieldFrom) for node in ast.walk(native)
        ):
            msg = "generator prototypes require a separate proven forwarding contract"
            raise ValueError(msg)
        port = operands[1][1]
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
            port_type.get_object().get_attributes().get(operands[1][2])
            if port_type is not None
            else None
        )
        if not runtime.same_name(binding, actual):
            msg = f"port {port} and prototype select different native operations"
            raise ValueError(msg)
        return binding, native

    @staticmethod
    def _default_identity(
        origin: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        native: ast.FunctionDef,
    ) -> None:
        if scope.pyobject.get_module() is origin:
            return
        if any(
            isinstance(default, ast.Constant)
            and default.value is not None
            and default.value is not True
            and default.value is not False
            and default.value is not Ellipsis
            for default in (*native.args.defaults, *native.args.kw_defaults)
        ):
            msg = (
                "cross-module default identity requires a native shared binding; "
                "copying a literal only proves equality, not object identity"
            )
            raise ValueError(msg)

    @staticmethod
    def _forward(
        native: ast.FunctionDef,
        name: str,
        selection: tuple[str, str, str],
    ) -> ast.FunctionDef:
        rendered = deepcopy(native)
        rendered.name = name
        rendered.decorator_list = []
        positional = rendered.args.posonlyargs + rendered.args.args
        if not positional:
            msg = "prototype has no native receiver parameter"
            raise ValueError(msg)
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
            func=ast.Attribute(
                value=ast.Attribute(
                    value=ast.Name(id=positional[0].arg, ctx=ast.Load()),
                    attr=selection[1],
                    ctx=ast.Load(),
                ),
                attr=selection[2],
                ctx=ast.Load(),
            ),
            args=forwarded,
            keywords=keywords,
        )
        returned = ast.Return(value=invocation)
        rendered.body = (
            [deepcopy(native.body[0])] if ast.get_docstring(native) is not None else []
        ) + [returned]
        return rendered

    @classmethod
    def _signature_imports(
        cls,
        project: p.Infra.RopeProject,
        binding: p.Infra.RopePyName,
        scope: p.Infra.RopeScope,
        rendered: ast.FunctionDef,
    ) -> tuple[p.Infra.RopeImportInfo, ...]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        definition = cls._definition(binding)
        if definition is None:
            msg = "prototype lost its authenticated native source"
            raise ValueError(msg)
        origin = definition[0]
        signature = deepcopy(rendered)
        signature.body = [ast.Pass()]
        generics = {
            parameter.name
            for parameter in signature.type_params
            if isinstance(parameter, ast.TypeVar | ast.TypeVarTuple | ast.ParamSpec)
        }
        native_scope = FlextInfraUtilitiesRopeRuntimeTypes.require_source_object(
            binding.get_object(), "prototype annotation scope"
        ).get_scope()
        required: list[p.Infra.RopeImportInfo] = []
        relocation = FlextInfraUtilitiesSemanticDeclarationRelocation
        imported = {
            alias or name.split(".")[0]: information
            for information in relocation.native_import_infos(project, origin)
            for name, alias in information.names_and_aliases
        }
        for name in cls._signature_names(project, native_scope, signature) - generics:
            original = runtime.expression_name(native_scope, name)
            destination = runtime.expression_name(scope, name)
            if (
                original is not None
                and destination is not None
                and runtime.same_name(original, destination)
            ):
                continue
            information = imported.get(name)
            if (
                original is None
                or destination is not None
                or information is None
                or (
                    isinstance(information, p.Infra.RopeFromImport)
                    and information.level
                )
            ):
                msg = (
                    f"signature binding {name} has no unambiguous native import "
                    f"from {origin.get_name()}"
                )
                raise ValueError(msg)
            aliases = tuple(
                (imported_name, alias)
                for imported_name, alias in information.names_and_aliases
                if (alias or imported_name.split(".")[0]) == name
            )
            required.append(
                runtime.from_import(information.module_name, information.level, aliases)
                if isinstance(information, p.Infra.RopeFromImport)
                else runtime.normal_import(aliases)
            )
        return tuple(required)

    @staticmethod
    def _require_deferred(module: p.Infra.RopePyModule) -> None:
        tree = module.get_ast()
        if not isinstance(tree, ast.Module) or not any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body
        ):
            msg = "delegation requires deferred annotations at both declaring owners"
            raise ValueError(msg)

    @staticmethod
    def _signature_names(
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        signature: ast.FunctionDef,
    ) -> set[str]:
        names: set[str] = set()
        roots: set[str] = set()

        def collect(_scope: p.Infra.RopeScope, expression: str) -> None:
            root = expression.partition(".")[0]
            if root in roots:
                names.add(root)

        expressions = [
            node.annotation
            for node in ast.walk(signature)
            if isinstance(node, ast.arg) and node.annotation is not None
        ]
        if signature.returns is not None:
            expressions.append(signature.returns)
        expressions.extend(
            node.bound
            for node in signature.type_params
            if isinstance(node, ast.TypeVar) and node.bound is not None
        )
        expressions.extend(
            node.default_value
            for node in signature.type_params
            if isinstance(node, ast.TypeVar | ast.TypeVarTuple | ast.ParamSpec)
            and node.default_value is not None
        )
        for expression in expressions:
            if any(isinstance(node, ast.Call) for node in ast.walk(expression)):
                msg = "signature annotations cannot execute authored calls twice"
                raise ValueError(msg)
            roots = {
                node.id for node in ast.walk(expression) if isinstance(node, ast.Name)
            }
            names.update(roots)
            for node in ast.walk(expression):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    quoted = ast.parse(node.value, mode="eval")
                    if any(isinstance(part, ast.Call) for part in ast.walk(quoted)):
                        msg = (
                            "quoted signature annotations cannot execute authored calls"
                        )
                        raise ValueError(msg)
                    roots.update(
                        part.id
                        for part in ast.walk(quoted)
                        if isinstance(part, ast.Name)
                    )
            FlextInfraUtilitiesSemanticFamilyTypeReferences.rewrite_type_source(
                ast.unparse(expression), project, scope, collect
            )
        return names


__all__: list[str] = ["FlextInfraUtilitiesSemanticDelegations"]
