"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import itertools
import marshal
import sys
from base64 import b64encode
from contextvars import ContextVar
from dis import Instruction, get_instructions
from functools import partial
from gc import get_referents
from importlib.machinery import ExtensionFileLoader, FrozenImporter, ModuleSpec
from inspect import CO_NEWLOCALS, CO_OPTIMIZED
from json import dumps
from math import isnan
from pathlib import Path
from types import (
    BuiltinFunctionType,
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    GenericAlias,
    GetSetDescriptorType,
    MappingProxyType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodType,
    MethodWrapperType,
    ModuleType,
    UnionType,
    WrapperDescriptorType,
)
from typing import TypeGuard

from flext_infra import c, codegen, m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @classmethod
    def _source_witness(
        cls,
        name: str,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[m.Infra.NativeSourceWitness]:
        """Capture each physical supplier once inside the shared semantic graph."""
        if name in witnesses:
            return r[m.Infra.NativeSourceWitness].ok(witnesses[name])
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            return r[m.Infra.NativeSourceWitness].fail(
                f"producer source supplier is not loaded: {name}",
            )
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
        if elected.failure:
            return r[m.Infra.NativeSourceWitness].from_failure(elected)
        specification = vars(module)["__spec__"]
        source = (
            Path(specification.loader_state.filename).absolute()
            if specification.origin == "frozen"
            else elected.value
        )
        captured = u.Cli.atomic_read_binary_file_state(source, required=True)
        if captured.failure:
            return r[m.Infra.NativeSourceWitness].from_failure(captured)
        if captured.value.content is None:
            return r[m.Infra.NativeSourceWitness].fail(
                f"producer captured source is absent: {source}",
            )
        resource = u.Infra.runtime_callable("rope.base.resources", "File")(
            u.Infra.runtime_callable("rope.base.project", "get_no_project")(),
            str(source),
        )
        if not isinstance(resource, p.Infra.RopeFile):
            msg = "Native source resource violates Rope's contract"
            raise TypeError(msg)
        native = u.Infra.build_string_module(
            project,
            captured.value.content.decode("utf-8"),
            resource=resource,
        )
        if not isinstance(native, p.Infra.RopeSourceModule):
            msg = "Native source module has no shared Rope graph"
            raise TypeError(msg)
        root = native.get_scope()
        if not isinstance(root, p.Infra.RopeScope):
            msg = "Native source module has no semantic scope"
            raise TypeError(msg)
        scopes: dict[str, p.Infra.RopeScope] = {}
        pending = [(root, "")]
        while pending:
            scope, qualified = pending.pop()
            previous = scopes.get(qualified)
            if previous is not None:
                if previous.get_kind() == "Function" and scope.get_kind() == "Function":
                    continue
                return r[m.Infra.NativeSourceWitness].fail(
                    f"producer class declaration is ambiguous: {name}::{qualified}",
                )
            scopes[qualified] = scope
            prefix = (
                f"{qualified}.<locals>" if scope.get_kind() == "Function" else qualified
            )
            pending.extend(
                (
                    child,
                    f"{prefix}.{child.pyobject.get_name()}"
                    if prefix
                    else child.pyobject.get_name(),
                )
                for child in scope.get_scopes()
                if child.get_kind() in {"Class", "Function"}
            )
        compiled = (
            FrozenImporter.get_code(specification.name)
            if specification.origin == "frozen"
            else compile(
                captured.value.content,
                str(source),
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
        )
        if not isinstance(compiled, CodeType):
            msg = "Native supplier has no compiler result"
            raise TypeError(msg)
        witness = m.Infra.NativeSourceWitness(
            source=source,
            state=captured.value,
            module=native,
            code=compiled,
            scopes=scopes,
            statements=u.Infra.logical_statements(native.source_code),
            finder=u.Infra.semantic_finder(native),
        )
        witnesses[name] = witness
        return r[m.Infra.NativeSourceWitness].ok(witness)

    @staticmethod
    def _compiled_function(
        witness: m.Infra.NativeSourceWitness,
        code: p.Infra.NativeCodeIdentity,
    ) -> p.Result[bool]:
        """Require an exact executable unit from the captured native compilation."""
        pending = [witness.code]
        while pending:
            candidate = pending.pop()
            if (
                candidate == code
                and candidate.co_filename == code.co_filename
                and candidate.co_firstlineno == code.co_firstlineno
                and candidate.co_linetable == code.co_linetable
                and candidate.co_exceptiontable == code.co_exceptiontable
            ):
                return r[bool].ok(value=True)
            pending.extend(
                item for item in candidate.co_consts if isinstance(item, CodeType)
            )
        return r[bool].fail(
            "producer executable differs from captured native compilation: "
            f"{code.co_qualname}; source={witness.source}",
        )

    @classmethod
    def _native_class_alias(
        cls,
        value: p.AttributeProbe,
        qualified: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Authenticate a source-imported native export with interpreter descriptors."""
        components = qualified.split(".")
        binding = witness.module.get_attributes().get(components[0])
        if binding is None:
            return r[t.Triple[str, str, str]].fail(
                f"native class has no source import binding: {qualified}",
            )
        for component in components[1:]:
            binding = binding.get_object().get_attributes().get(component)
            if binding is None:
                return r[t.Triple[str, str, str]].fail(
                    f"native class import path is absent: {qualified}",
                )
        native = binding.get_object()
        if (
            not isinstance(native, p.Infra.RopeBuiltinClass)
            or native.builtin is not value
            or not isinstance(binding, p.Infra.RopeImportedName)
        ):
            return r[t.Triple[str, str, str]].fail(
                f"class has no identity-matched native source import: {qualified}",
            )
        supplier = binding.imported_module.module_name
        if supplier is None:
            return r[t.Triple[str, str, str]].fail(
                f"native class import has no elected supplier: {qualified}",
            )
        exported = sys.modules.get(supplier)
        if (
            type(exported) is not ModuleType
            or vars(exported).get(binding.imported_name) is not value
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class export differs from its source import: {qualified}",
            )
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(supplier)
        if elected.failure:
            return r[t.Triple[str, str, str]].from_failure(elected)
        specification = vars(exported)["__spec__"]
        if (
            specification.origin not in {"built-in", "frozen"}
            and type(specification.loader).__module__ != "_frozen_importlib_external"
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class supplier is not an interpreter extension: {supplier}",
            )
        native_descriptors = (
            descriptor
            for descriptor in cls._class_namespace(value).values()
            if type(descriptor)
            in {
                MethodDescriptorType,
                ClassMethodDescriptorType,
                WrapperDescriptorType,
            }
        )
        if not any(
            descriptor.__objclass__ is value for descriptor in native_descriptors
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class has no interpreter-owned callable descriptor: {qualified}",
            )
        if any(
            type(descriptor) is FunctionType
            for descriptor in cls._class_namespace(value).values()
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class export carries an authored executable: {qualified}",
            )
        return r[t.Triple[str, str, str]].ok((
            f"{supplier}::{binding.imported_name}",
            str(elected.value),
            str(witness.source),
        ))

    @staticmethod
    def _capture_text(
        witness: m.Infra.NativeSourceWitness,
        match: p.Infra.RopeContractMatch,
        variable: str,
    ) -> str:
        start, end = u.Infra.semantic_capture_region(match, variable)
        return witness.module.source_code[start:end]

    @staticmethod
    def _scope_name(scope: p.Infra.RopeScope) -> str:
        components = []
        current = scope
        while current.parent is not None:
            components.append(current.pyobject.get_name())
            current = current.parent
        return ".".join(reversed(components))

    @classmethod
    def _source_binding(
        cls,
        scope: p.Infra.RopeScope,
        expression: str,
    ) -> p.Result[p.AttributeProbe]:
        """Resolve native lexical identity through callback-free runtime slots."""
        binding = u.Infra.expression_name(scope, expression)
        if binding is None:
            return r[p.AttributeProbe].fail(
                f"producer has no native lexical binding: {expression}",
            )
        native = binding.get_object()
        if isinstance(native, p.Infra.RopeBuiltinClass):
            return r[p.AttributeProbe].ok(native.builtin)
        provider = native.get_module()
        declaration = native.get_scope()
        if provider is None or declaration is None:
            return r[p.AttributeProbe].fail(
                f"producer binding has no physical native declaration: {expression}",
            )
        module_name = provider.get_name()
        value = sys.modules.get(module_name)
        if type(value) is not ModuleType:
            return r[p.AttributeProbe].fail(
                f"producer lexical supplier is not loaded: {module_name}",
            )
        for component in cls._scope_name(declaration).split("."):
            namespace = (
                cls._class_namespace(value)
                if cls._is_class(value)
                else vars(value)
                if type(value) is ModuleType
                else None
            )
            if namespace is None or component not in namespace:
                return r[p.AttributeProbe].fail(
                    f"producer native declaration has no runtime slot: {expression}",
                )
            value = namespace[component]
        if (
            cls._is_class(value)
            and cls._class_namespace(value).get(
                "__module__",
            )
            != module_name
        ):
            return r[p.AttributeProbe].fail(
                f"producer lexical class supplier differs: {expression}",
            )
        return r[p.AttributeProbe].ok(value)

    @classmethod
    def _declared_fields(
        cls,
        witness: m.Infra.NativeSourceWitness,
        scope: p.Infra.RopeScope,
    ) -> t.VariadicTuple[t.Triple[str, str, str | None]]:
        fields = []
        for pattern, name, annotation, default in (
            (
                "${field_name}: ${field_annotation}",
                "field_name",
                "field_annotation",
                None,
            ),
            (
                "${default_name}: ${default_annotation} = ${default_value}",
                "default_name",
                "default_annotation",
                "default_value",
            ),
        ):
            for match in witness.finder.get_matches(pattern):
                start, _end = match.get_region()
                if u.Infra.scope_at(witness.module, start) is not scope:
                    continue
                field_name = cls._capture_text(witness, match, name)
                if field_name.isidentifier():
                    fields.append((
                        start,
                        field_name,
                        cls._capture_text(witness, match, annotation),
                        None
                        if default is None
                        else cls._capture_text(witness, match, default),
                    ))
        return tuple(
            (name, annotation, default)
            for _offset, name, annotation, default in sorted(fields)
        )

    @classmethod
    def _literal(
        cls,
        expression: str,
        witness: m.Infra.NativeSourceWitness,
        scope: p.Infra.RopeScope,
        seen: frozenset[str] = frozenset(),
    ) -> p.Result[p.AttributeProbe | None]:
        """Resolve compiler-closed literals and their physical source aliases."""
        code = compile(expression, str(witness.source), "eval", dont_inherit=True)
        if (
            not code.co_names
            and not code.co_freevars
            and not any(isinstance(item, CodeType) for item in code.co_consts)
        ):
            return r[p.AttributeProbe | None].ok(
                eval(code, {"__builtins__": {}}, {}),
            )
        if not expression.isidentifier() or expression in seen:
            return r[p.AttributeProbe | None].fail(
                f"producer input has no compiler-closed source literal: "
                f"{witness.source}",
            )
        binding = u.Infra.expression_name(scope, expression)
        assignments = []
        for match in witness.finder.get_matches("${input_name} = ${input_value}"):
            if cls._capture_text(witness, match, "input_name") != expression:
                continue
            start, _end = match.get_region()
            if u.Infra.same_name(
                binding,
                u.Infra.expression_name(
                    u.Infra.scope_at(witness.module, start),
                    expression,
                ),
            ):
                assignments.append(match)
        if len(assignments) != 1:
            return r[p.AttributeProbe | None].fail(
                f"producer input has no unique source assignment: {expression}",
            )
        return cls._literal(
            cls._capture_text(witness, assignments[0], "input_value"),
            witness,
            scope,
            seen | {expression},
        )

    @classmethod
    def _native_factory(
        cls,
        module_name: str,
        name: str,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[p.AttributeProbe]:
        witness = cls._source_witness(module_name, project, witnesses)
        if witness.failure:
            return r[p.AttributeProbe].from_failure(witness)
        namespace = vars(sys.modules[module_name])
        factory = namespace.get(name)
        if type(factory) is not FunctionType:
            return r[p.AttributeProbe].fail(
                f"native compiler has no physical function: {module_name}.{name}",
            )
        proof = cls._compiled_function(witness.value, factory.__code__)
        if proof.failure:
            return r[p.AttributeProbe].from_failure(proof)
        for key, value in namespace.items():
            if not cls._is_class(value) or key not in witness.value.scopes:
                continue
            if (
                cls._class_namespace(value).get("__module__") != module_name
                or vars(type)["__qualname__"].__get__(value, type(value)) != key
            ):
                return r[p.AttributeProbe].fail(
                    f"native compiler class binding differs: {module_name}.{key}",
                )
            for descriptor in cls._class_namespace(value).values():
                function = (
                    descriptor.__func__
                    if type(descriptor) in {classmethod, staticmethod}
                    else descriptor
                )
                if type(function) is FunctionType:
                    checked = cls._compiled_function(witness.value, function.__code__)
                    if checked.failure:
                        return r[p.AttributeProbe].from_failure(checked)
        return r[p.AttributeProbe].ok(factory)

    @classmethod
    def _generated_descriptor(
        cls,
        owner: p.AttributeProbe,
        attribute: str,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[p.AttributeProbe]:
        """Invoke proved native compilers without replaying authored class hooks."""
        module_name = cls._class_namespace(owner)["__module__"]
        captured = cls._source_witness(module_name, project, witnesses)
        if captured.failure:
            return r[p.AttributeProbe].from_failure(captured)
        witness = captured.value
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        scope = witness.scopes.get(qualified)
        if scope is None:
            return r[p.AttributeProbe].fail(
                f"generated descriptor has no physical class scope: {qualified}",
            )
        fields = cls._declared_fields(witness, scope)
        namespace = cls._class_namespace(owner)
        if "_fields" in namespace:
            names = tuple(name for name, _annotation, _default in fields)
            if cls._value(namespace["_fields"]) != cls._value(names):
                return r[p.AttributeProbe].fail(
                    f"native tuple field contract differs: {qualified}",
                )
            defaults = []
            for _name, _annotation, expression in fields:
                if expression is None:
                    if defaults:
                        return r[p.AttributeProbe].fail(
                            "native tuple has a required field after a default",
                        )
                    continue
                default = cls._literal(expression, witness, scope)
                if default.failure:
                    return r[p.AttributeProbe].from_failure(default)
                defaults.append(default.value)
            factory = cls._native_factory(
                "collections", "namedtuple", project, witnesses
            )
            if factory.failure:
                return r[p.AttributeProbe].from_failure(factory)
            emitted = factory.value(
                vars(type)["__name__"].__get__(owner, type(owner)),
                names,
                defaults=defaults,
                module=module_name,
            )
        elif "__dataclass_fields__" in namespace:
            factory = cls._native_factory(
                "dataclasses", "make_dataclass", project, witnesses
            )
            if factory.failure:
                return r[p.AttributeProbe].from_failure(factory)
            compiler = sys.modules["dataclasses"]
            header = next(
                item for item in witness.statements if item.line == scope.get_start()
            )
            decorators = []
            preceding = scope.get_start() - 1
            for statement in reversed(witness.statements):
                if statement.end_line > preceding:
                    continue
                if (
                    statement.end_line != preceding
                    or statement.indent != header.indent
                    or not statement.text.lstrip().startswith("@")
                ):
                    break
                decorators.append(statement.text.strip().removeprefix("@"))
                preceding = statement.line - 1
            options = {}
            elected = False
            for expression in decorators:
                resolved = cls._source_binding(
                    scope.parent, expression.partition("(")[0]
                )
                if resolved.failure:
                    return r[p.AttributeProbe].from_failure(resolved)
                if resolved.value is not vars(compiler)["dataclass"]:
                    continue
                if elected:
                    return r[p.AttributeProbe].fail(
                        "native compiler decorator is repeated"
                    )
                elected = True
                if "(" in expression:
                    words = u.Infra.runtime_callable("rope.base.worder", "Worder")(
                        expression
                    )
                    first, last = words.get_word_parens_range(0)
                    positional, keywords = words.get_parameters(first, last - 1)
                    if positional:
                        return r[p.AttributeProbe].fail(
                            "native compiler has positional options"
                        )
                    for key, source in keywords:
                        resolved_option = cls._literal(source, witness, scope.parent)
                        if resolved_option.failure:
                            return r[p.AttributeProbe].from_failure(resolved_option)
                        options[key] = resolved_option.value
            if not elected:
                return r[p.AttributeProbe].fail(
                    "native dataclass has no proved decorator"
                )
            annotations = namespace.get("__annotations__")
            if type(annotations) is not dict:
                return r[p.AttributeProbe].fail(
                    "native dataclass lacks annotation storage"
                )
            specifications = []
            for name, _annotation, expression in fields:
                if name not in annotations:
                    return r[p.AttributeProbe].fail(
                        "native dataclass source field is absent"
                    )
                annotation = annotations[name]
                if cls._is_class(annotation):
                    metaclass = type(annotation)
                    for hook in ("__getattribute__", "__hash__", "__eq__"):
                        actual = next(
                            (
                                cls._class_namespace(base)[hook]
                                for base in vars(type)["__mro__"].__get__(
                                    metaclass, type(metaclass)
                                )
                                if hook in cls._class_namespace(base)
                            ),
                            None,
                        )
                        if actual is not cls._class_namespace(type)[hook]:
                            return r[p.AttributeProbe].fail(
                                "annotation has an authored callback"
                            )
                if expression is None:
                    specifications.append((name, annotation))
                else:
                    default = cls._literal(expression, witness, scope)
                    if default.failure:
                        return r[p.AttributeProbe].from_failure(default)
                    specifications.append((
                        name,
                        annotation,
                        vars(compiler)["field"](default=default.value),
                    ))
            preserved = {}
            for name, descriptor in namespace.items():
                function = (
                    descriptor.__func__
                    if type(descriptor) in {classmethod, staticmethod}
                    else descriptor
                )
                if type(
                    function
                ) is FunctionType and not function.__code__.co_filename.startswith("<"):
                    preserved[name] = descriptor
            preserved["__qualname__"] = qualified
            emitted = factory.value(
                vars(type)["__name__"].__get__(owner, type(owner)),
                specifications,
                namespace=preserved,
                module=module_name,
                **options,
            )
        else:
            return r[p.AttributeProbe].fail(
                f"generated descriptor has no native compiler contract: "
                f"{qualified}.{attribute}",
            )
        descriptor = cls._class_namespace(emitted).get(attribute)
        if descriptor is None:
            return r[p.AttributeProbe].fail(
                "native compiler did not emit the descriptor"
            )
        return r[p.AttributeProbe].ok(descriptor)

    @classmethod
    def source_proof(
        cls,
        names: t.StrSequence,
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        """Authenticate loaded declarations without repeating import side effects."""
        with u.Infra.open_import_project(Path.cwd()) as project:
            witnesses: dict[str, m.Infra.NativeSourceWitness] = {}
            return cls._source_proof(names, project, witnesses)

    @classmethod
    def _executable_operands(
        cls,
        names: t.StrSequence,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        result = r[t.SequenceOf[t.Triple[str, str, str]]]
        sources = set()
        pending = []
        for name in names:
            module = sys.modules.get(name)
            if type(module) is not ModuleType:
                return result.fail(f"producer namespace is not loaded: {name}")
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
            if elected.failure:
                return result.from_failure(elected)
            sources.add((name, str(elected.value), ""))
            pending.extend(
                (value, None, name, key)
                for key, value in vars(module).items()
                if cls._is_class(value)
                or type(value)
                in {
                    FunctionType,
                    BuiltinFunctionType,
                    property,
                    classmethod,
                    staticmethod,
                }
                or cls._native_wrapper_kind(value) is not None
            )
        visited = set()
        generators = {}
        while pending:
            name, item = pending.pop()
            if item is None or id(item) in seen:
                continue
            visited.add(identity)
            if cls._is_class(value):
                namespace = cls._class_namespace(value)
                module_name = vars(type)["__module__"].__get__(
                    value,
                    type(value),
                )
                if type(module_name) is not str:
                    return result.fail(
                        "producer class has no native supplier: "
                        f"binding={supplier}::{attribute}; "
                        f"qualified={vars(type)['__qualname__'].__get__(value, type(value))}",
                    )
                elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                    module_name
                )
                if elected.failure:
                    return result.from_failure(elected)
                qualified = vars(type)["__qualname__"].__get__(value, type(value))
                sources.add((f"{module_name}::{qualified}", str(elected.value), ""))
                specification = vars(sys.modules[module_name])["__spec__"]
                if specification.origin not in {"built-in", "frozen"} and str(
                    elected.value
                ).endswith(".py"):
                    captured = cls._source_witness(module_name, project, witnesses)
                    if captured.failure:
                        return result.from_failure(captured)
                    if qualified not in captured.value.scopes:
                        alias = cls._native_class_alias(
                            value,
                            qualified,
                            captured.value,
                        )
                        if alias.failure:
                            return result.from_failure(alias)
                        sources.add(alias.value)
                        continue
                    pending.extend(
                        (item, value, module_name, name)
                        for name, item in namespace.items()
                        if cls._is_class(item)
                        or type(item)
                        in {
                            FunctionType,
                            BuiltinFunctionType,
                            property,
                            classmethod,
                            staticmethod,
                        }
                        or cls._native_wrapper_kind(item) is not None
                    )
                    pending.extend(
                        (base, None, module_name, "")
                        for base in vars(type)["__bases__"].__get__(value, type(value))
                    )
                continue
            wrapper_kind = cls._native_wrapper_kind(value)
            if wrapper_kind is not None:
                function = cls._native_wrapper_function(value, wrapper_kind)
                if function.failure:
                    return result.from_failure(function)
                pending.append((function.value, receiver, supplier, attribute))
                continue
            if type(value) is property:
                pending.extend(
                    (accessor, receiver, supplier, attribute)
                    for accessor in (value.fget, value.fset, value.fdel)
                    if accessor is not None
                )
                continue
            if type(value) in {classmethod, staticmethod}:
                value = value.__func__
            if type(value) is BuiltinFunctionType:
                continue
            if type(value) is not FunctionType:
                return result.fail(
                    "producer descriptor has no native function identity"
                )
            actual_supplier = value.__globals__.get("__name__")
            if type(actual_supplier) is not str:
                actual_supplier = supplier
            captured = cls._source_witness(actual_supplier, project, witnesses)
            if captured.failure:
                return result.from_failure(captured)
            code = value.__code__
            generated = code.co_filename.startswith(
                "<"
            ) and not code.co_filename.startswith("<frozen ")
            if generated:
                if receiver is None:
                    return result.fail(
                        "generated function has no physical class receiver"
                    )
                key = (id(receiver), attribute)
                if key not in generators:
                    descriptor = cls._generated_descriptor(
                        receiver, attribute, project, witnesses
                    )
                    if descriptor.failure:
                        return result.from_failure(descriptor)
                    generators[key] = descriptor.value
                expected = generators[key]
                if type(expected) in {classmethod, staticmethod}:
                    expected = expected.__func__
                while (
                    type(expected) is FunctionType
                    and expected.__code__.co_qualname != code.co_qualname
                ):
                    expected = vars(expected).get("__wrapped__")
                if type(expected) is not FunctionType or (
                    expected.__code__.replace(co_firstlineno=0)
                    != code.replace(co_firstlineno=0)
                    or cls._value(expected.__defaults__)
                    != cls._value(value.__defaults__)
                    or cls._value(expected.__kwdefaults__)
                    != cls._value(value.__kwdefaults__)
                    or cls._value(
                        tuple(cell.cell_contents for cell in expected.__closure__ or ())
                    )
                    != cls._value(
                        tuple(cell.cell_contents for cell in value.__closure__ or ())
                    )
                ):
                    return result.fail(
                        f"generated executable differs from native compiler: "
                        f"{code.co_qualname}"
                    )
            else:
                proof = cls._compiled_function(captured.value, code)
                if proof.failure:
                    return result.from_failure(proof)
                if receiver is not None:
                    receiver_module = cls._class_namespace(receiver)["__module__"]
                    receiver_source = cls._source_witness(
                        receiver_module, project, witnesses
                    )
                    if receiver_source.failure:
                        return result.from_failure(receiver_source)
                    qualified = vars(type)["__qualname__"].__get__(
                        receiver, type(receiver)
                    )
                    own = receiver_source.value.scopes.get(f"{qualified}.{attribute}")
                    declared = (
                        receiver_source.value
                        .scopes[qualified]
                        .get_names()
                        .get(attribute)
                    )
                    expected_scope = (
                        own
                        if own is not None
                        else (
                            None
                            if declared is None
                            else declared.get_object().get_scope()
                        )
                    )
                    if expected_scope is not None and (
                        cls._scope_name(expected_scope) != code.co_qualname
                        or expected_scope.pyobject.get_module().get_name()
                        != actual_supplier
                    ):
                        return result.fail(
                            f"producer descriptor differs from source owner: "
                            f"{qualified}.{attribute}"
                        )
            wrapped = vars(value).get("__wrapped__")
            cells = tuple(cell.cell_contents for cell in value.__closure__ or ())
            if wrapped is not None:
                if not any(item is wrapped for item in cells):
                    return result.fail(
                        "producer wrapper has no executable closure link"
                    )
                pending.append((wrapped, receiver, actual_supplier, attribute))
            sources.add((
                f"{actual_supplier}::{code.co_qualname}",
                str(captured.value.source) if generated else code.co_filename,
                str(captured.value.source) if generated else "",
            ))
        for witness in witnesses.values():
            current = u.Cli.atomic_read_binary_file_state(witness.source, required=True)
            if current.failure:
                return result.from_failure(current)
            if current.value != witness.state:
                return result.fail(
                    f"producer captured source changed: {witness.source}"
                )
        return result.ok(tuple(sorted(sources)))

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

    @classmethod
    def _extension_callback(
        cls,
        value: p.AttributeProbe,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Read registered native extension slots without authored accessors.

        Returns:
            Supplier, name and qualified name, or the first admission failure.

        """
        native = type(value)
        slots = cls._class_namespace(native)
        metadata: t.DictKV[str, str] = {}
        for attribute in ("__module__", "__name__", "__qualname__"):
            descriptor = slots.get(attribute)
            if type(descriptor) not in {GetSetDescriptorType, MemberDescriptorType}:
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback lacks a native metadata slot: {attribute}",
                )
            if descriptor.__objclass__ is not native:
                return r[t.Triple[str, str, str]].fail(
                    "extension callback metadata belongs to another native type",
                )
            observed = descriptor.__get__(value, descriptor.__objclass__)
            if type(observed) is not str:
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback metadata is not text: {attribute}",
                )
            metadata[attribute] = observed
        return cls._extension_binding(value, native, slots, metadata)

    @classmethod
    def _extension_binding(
        cls,
        value: t.Infra.NativeOperand,
        native: t.Infra.NativeType,
        slots: t.MappingKV[str, t.Infra.NativeOperand],
        metadata: t.StrMapping,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Authenticate an extension supplier and its native globals binding.

        Returns:
            The native callback identity or its supplier admission failure.

        """
        supplier = sys.modules.get(metadata["__module__"])
        if type(supplier) is not ModuleType or supplier.__spec__ is None:
            return r[t.Triple[str, str, str]].fail(
                "extension callback lacks its registered native supplier",
            )
        if not isinstance(supplier.__spec__.loader, ExtensionFileLoader):
            return r[t.Triple[str, str, str]].fail(
                "extension callback supplier is not a native extension",
            )
        namespace = vars(supplier)
        components = metadata["__qualname__"].split(".")
        for component in components[:-1]:
            owner = namespace.get(component)
            if not cls._is_class(owner):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback has no registered lexical owner",
                )
            namespace = cls._class_namespace(owner)
        if namespace.get(components[-1]) is not value:
            return r[t.Triple[str, str, str]].fail(
                "extension callback differs from its registered descriptor",
            )
        return r[t.Triple[str, str, str]].ok((
            metadata["__module__"],
            metadata["__name__"],
            metadata["__qualname__"],
        ))

    @classmethod
    def _extension_state(
        cls,
        value: p.AttributeProbe,
        supplier_name: str,
        qualified: str,
        binding: str,
    ) -> p.Result[t.MappingKV[str, p.AttributeProbe]]:
        """Bind native code and raw exports without invoking opaque getters."""
        result_type = r[t.MappingKV[str, p.AttributeProbe]]
        supplier = sys.modules[supplier_name]
        native = type(value)
        aliases: list[str] = []
        lexical_owners: list[p.AttributeProbe] = []
        pending = [("", vars(supplier), None)]
        visited: set[int] = set()
        while pending:
            prefix, namespace, owner = pending.pop()
            if any(type(name) is not str for name in namespace):
                return result_type.fail("native export namespace has non-text keys")
            for name, descriptor in sorted(namespace.items()):
                registered = (
                    descriptor.__func__
                    if cls._native_type(descriptor, classmethod, staticmethod)
                    else descriptor
                )
                path = f"{prefix}.{name}" if prefix else name
                if registered is value:
                    aliases.append(path)
                    if owner is not None:
                        lexical_owners.append(owner)
                if (
                    cls._is_class(descriptor)
                    and id(descriptor) not in visited
                    and supplier_name
                    in cls._class_identity(descriptor, supplier_name, binding)[1]
                ):
                    visited.add(id(descriptor))
                    pending.append((path, cls._class_namespace(descriptor), descriptor))
        if not aliases:
            native_name = vars(type)["__qualname__"].__get__(native, type(native))
            module_metadata = vars(type)["__module__"].__get__(native, type(native))
            metadata_kind = vars(type)["__qualname__"].__get__(
                type(module_metadata), type(type(module_metadata))
            )
            if type(native_name) is not str or type(metadata_kind) is not str:
                msg = "native diagnostic type identity is not text"
                raise ValueError(msg)
            return result_type.fail(
                "native callback has no registered raw export: "
                f"binding={binding[:320]!r}; supplier={supplier_name[:160]!r}; "
                f"qualname={qualified[:160]!r}; "
                f"native_type={native_name[:160]!r}; "
                f"module_metadata_kind={metadata_kind[:160]!r}"
            )
        storage: dict[str, p.AttributeProbe] = {"aliases": tuple(sorted(aliases))}
        slots = cls._class_namespace(native)
        if "__globals__" not in slots:
            return result_type.ok(storage)
        code_slot = slots.get("__code__")
        if (
            type(code_slot) is not GetSetDescriptorType
            or code_slot.__objclass__ is not native
        ):
            return result_type.fail("native callback has no readonly code witness")
        code = code_slot.__get__(value, native)
        if (
            type(code) is not CodeType
            or code.co_freevars
            or "<locals>" in code.co_qualname
        ):
            return result_type.fail("native callback closure has no complete witness")
        known = [native, vars(supplier), code, *lexical_owners]
        storage["code"] = code
        # Defaults may invoke a lazy helper; the closure getter may report None
        # despite retained native state. Neither getter is an admission witness.
        for attribute in (
            "__module__",
            "__name__",
            "__qualname__",
            "__dict__",
            "__annotations__",
            "__doc__",
        ):
            descriptor = slots.get(attribute)
            if (
                not cls._native_type(
                    descriptor, GetSetDescriptorType, MemberDescriptorType
                )
                or descriptor.__objclass__ is not native
            ):
                return result_type.fail(
                    f"native callback lacks retained storage: {attribute}"
                )
            observed = descriptor.__get__(value, native)
            if (
                attribute in {"__dict__", "__annotations__"}
                and type(observed) is not dict
            ) or (
                attribute not in {"__dict__", "__annotations__"}
                and not cls._native_type(observed, str, type(None))
            ):
                return result_type.fail("native callback storage is not native data")
            known.append(observed)
            storage[attribute] = observed
        referents = cls._native_referents(value)
        if referents.failure:
            return result_type.from_failure(referents)
        if any(
            not any(reference is admitted for admitted in known)
            for reference in referents.value
        ):
            return result_type.fail(
                "native callback closure/default state has no complete witness"
            )
        return result_type.ok(storage)

    @classmethod
    def _native_referents(
        cls, value: p.AttributeProbe
    ) -> p.Result[t.VariadicTuple[p.AttributeProbe]]:
        """Authenticate the interpreter before copying native GC references."""
        result_type = r[t.VariadicTuple[p.AttributeProbe]]
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source("gc")
        if elected.failure:
            return result_type.from_failure(elected)
        supplier = sys.modules.get("gc")
        if (
            elected.value != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
            or type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or get_referents.__self__ is not supplier
            or not cls._native_text(get_referents.__module__, "gc")
            or not cls._native_text(get_referents.__name__, "get_referents")
        ):
            return result_type.fail("native traversal has no elected interpreter owner")
        return result_type.ok(tuple(get_referents(value)))

    @classmethod
    def _native_wrapper_kind(cls, value: t.Infra.NativeOperand) -> str | None:
        """Identify interpreter wrapper types through their registered exports.

        Returns:
            The native wrapper kind, or None for other types.

        """
        supplier = sys.modules.get("_functools")
        if type(supplier) is not ModuleType:
            return None
        namespace = vars(supplier)
        native = type(value)
        if native is namespace.get("_lru_cache_wrapper"):
            return "lru_cache"
        if native is namespace.get("partial"):
            return "partial"
        return None

    @classmethod
    def _native_wrapper_function(
        cls,
        value: t.Infra.NativeOperand,
        kind: str,
    ) -> p.Result[p.AttributeProbe]:
        """Read native callable slots, never the mutable __wrapped__ facade.

        Returns:
            The interpreter-owned callable or its admission failure.

        """
        result_type = r[p.AttributeProbe]
        native = type(value)
        namespace = cls._class_namespace(native)
        if kind == "partial":
            slot = namespace.get("func")
            if (
                not cls._is_native(slot, MemberDescriptorType)
                or slot.__objclass__ is not native
            ):
                return result_type.fail(
                    "native partial lacks its interpreter-owned function slot",
                )
            return result_type.ok(slot.__get__(value, slot.__objclass__))
        authority = cls._native_cache_authority()
        if authority.failure:
            return result_type.from_failure(authority)
        storage = namespace.get("__dict__")
        if (
            not cls._is_native(storage, GetSetDescriptorType)
            or storage.__objclass__ is not native
        ):
            return result_type.fail(
                "native cache wrapper lacks interpreter-owned dictionary storage",
            )
        attributes: t.DictKV[str, t.Infra.NativeOperand] = storage.__get__(
            value, storage.__objclass__
        )
        return cls._native_cache_topology(value, native, attributes)

    @classmethod
    def _native_cache_authority(cls) -> p.Result[bool]:
        """Authenticate the interpreter suppliers of native cache traversal.

        Returns:
            The confirmed traversal authority or its supplier admission failure.

        """
        result_type = r[bool]
        for supplier_name in ("gc", "_functools"):
            elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                supplier_name,
            )
            if elected.failure:
                return result_type.from_failure(elected)
            if elected.value != Path(sys.executable).resolve():
                return result_type.fail(
                    "native cache topology supplier is not the elected interpreter: "
                    f"{supplier_name}={elected.value}",
                )
        supplier = sys.modules.get("gc")
        registered = (
            type(supplier) is ModuleType
            and vars(supplier).get("get_referents") is get_referents
        )
        if (
            not registered
            or type(get_referents) is not BuiltinFunctionType
            or not cls._native_text(get_referents.__module__, "gc")
            or not cls._native_text(get_referents.__name__, "get_referents")
            or sys.implementation.name != "cpython"
        ):
            return result_type.fail(
                "native wrapper topology has no admitted interpreter traversal",
            )
        return result_type.ok(value=True)

    @classmethod
    def _native_cache_topology(
        cls,
        value: t.Infra.NativeOperand,
        native: t.Infra.NativeType,
        attributes: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> p.Result[p.AttributeProbe]:
        """Elect a native cache function from its admitted traversal layout.

        Returns:
            The exact executable slot or its topology admission failure.

        """
        result_type = r[p.AttributeProbe]
        references = get_referents(value)
        # CPython's authenticated lru_cache_tp_traverse visits cached data before
        # cache storage and its executable func slot immediately after storage.
        # __wrapped__ and callable cache results never elect that native slot.
        if not any(item is native for item in references) or not any(
            item is attributes for item in references
        ):
            return result_type.fail(
                "native cache wrapper has an unsupported interpreter traversal layout",
            )
        functions = {
            id(item): item
            for item in references
            if type(item) in {FunctionType, BuiltinFunctionType}
            or cls._native_wrapper_kind(item) is not None
        }
        if len(functions) != 1:
            return result_type.fail(
                "native cache wrapper executable topology is ambiguous",
            )
        function = references[cache_index + 1]
        if not cls._callable_storage(function):
            return result_type.fail(
                "native cache wrapper has no executable function slot"
            )
        if attributes.get("__wrapped__") is not function:
            return result_type.fail(
                "native cache wrapper facade differs from its executable function slot",
            )
        return result_type.ok(function)

    @classmethod
    def _callable_storage(cls, value: t.Infra.NativeOperand) -> bool:
        """Find callback storage without asking the object for its attributes.

        Returns:
            Whether the native method resolution order contains a call slot.

        """
        return any(
            "__call__" in cls._class_namespace(owner)
            for owner in vars(type)["__mro__"].__get__(
                type(value),
                type(type(value)),
            )
        )

    @classmethod
    def _python_callable_implementation(
        cls,
        value: p.AttributeProbe,
    ) -> p.AttributeProbe | None:
        """Elect the effective authored call function without invoking accessors."""
        ancestry = vars(type)["__mro__"].__get__(type(value), type(type(value)))
        for owner in ancestry:
            namespace = cls._class_namespace(owner)
            if "__call__" not in namespace:
                continue
            implementation = namespace["__call__"]
            if cls._native_type(implementation, classmethod, staticmethod):
                implementation = implementation.__func__
            if type(implementation) is not FunctionType:
                return None
            return implementation if cls._python_storage_class(type(value)) else None
        return None

    @classmethod
    def _python_storage_class(cls, native: type) -> bool:
        """Require Python storage to cover every non-object ancestry payload."""
        return cls._python_storage_owners(
            vars(type)["__mro__"].__get__(native, type(native))
        )

    @classmethod
    def _python_storage_owners(cls, owners: t.SequenceOf[p.AttributeProbe]) -> bool:
        """Reject native payloads within the selected raw ancestry owners."""
        for ancestor in owners:
            if ancestor is object:
                continue
            for name, descriptor in cls._class_namespace(ancestor).items():
                if (
                    (
                        cls._native_type(
                            descriptor,
                            MethodDescriptorType,
                            ClassMethodDescriptorType,
                            WrapperDescriptorType,
                        )
                        or (
                            type(descriptor) is GetSetDescriptorType
                            and name not in {"__dict__", "__weakref__"}
                        )
                    )
                    and descriptor.__objclass__ is ancestor
                ) or (
                    type(descriptor) is BuiltinFunctionType
                    and descriptor.__self__ is ancestor
                ):
                    return False
        return True

    @classmethod
    def _native_mapping_proxy_backing(cls, value: p.AttributeProbe) -> p.AttributeProbe:
        """Read the sole exact-dict backing of the CPython mapping proxy."""
        if type(value) is not MappingProxyType or MappingProxyType is not type(
            vars(type)
        ):
            msg = "mapping proxy has no admitted interpreter type"
            raise ValueError(msg)
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source("gc").unwrap()
        supplier = sys.modules.get("gc")
        if (
            elected != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
            or type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or not cls._native_text(get_referents.__module__, "gc")
            or not cls._native_text(get_referents.__name__, "get_referents")
            or get_referents.__self__ is not supplier
        ):
            msg = "mapping proxy storage has no admitted interpreter traversal"
            raise ValueError(msg)
        # CPython's exact proxy traverses only its backing mapping pointer.
        references = get_referents(value)
        if len(references) != 1 or type(references[0]) is not dict:
            msg = "native mapping proxy requires one exact dict backing"
            raise ValueError(msg)
        return references[0]

    @classmethod
    def _instance_storage(
        cls,
        value: p.AttributeProbe,
    ) -> t.SequenceOf[t.Triple[str, bool, p.AttributeProbe | None]]:
        """Read interpreter-owned instance dictionaries and declared member slots."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        result = []
        for index, owner in enumerate(ancestry):
            for name, descriptor in sorted(cls._class_namespace(owner).items()):
                if (
                    not (
                        type(descriptor) is MemberDescriptorType
                        or (
                            name == "__dict__"
                            and type(descriptor) is GetSetDescriptorType
                        )
                    )
                    or descriptor.__objclass__ is not owner
                ):
                    continue
                if index and type(descriptor) is MemberDescriptorType:
                    present, stored = cls._inherited_member_state(
                        value, owner, name, descriptor, ancestry[index - 1]
                    )
                else:
                    # A first-MRO unset slot retains its original native failure.
                    present, stored = True, descriptor.__get__(value, native)
                result.append((f"{cls._symbol(owner)}::{name}", present, stored))
        return tuple(result)

    @classmethod
    def _inherited_member_state(
        cls,
        value: p.AttributeProbe,
        owner: p.AttributeProbe,
        name: str,
        descriptor: p.AttributeProbe,
        predecessor: p.AttributeProbe,
    ) -> t.Pair[bool, p.AttributeProbe | None]:
        """Use native super lookup to retain inherited-slot presence as data."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        index = next(
            position for position, ancestor in enumerate(ancestry) if ancestor is owner
        )
        if (
            not index
            or ancestry[index - 1] is not predecessor
            or name == "__class__"
            or type(descriptor) is not MemberDescriptorType
            or descriptor.__objclass__ is not owner
            or cls._class_namespace(owner).get(name) is not descriptor
        ):
            msg = "native optional slot has no exact inherited descriptor"
            raise ValueError(msg)
        builtins = sys.modules.get("builtins")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            type(builtins) is not ModuleType
            or elected != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
        ):
            msg = "native optional slot has no elected interpreter"
            raise ValueError(msg)
        getter = vars(builtins).get("getattr")
        super_type = vars(builtins).get("super")
        if (
            type(getter) is not BuiltinFunctionType
            or getter.__self__ is not builtins
            or not cls._native_text(getter.__module__, "builtins")
            or not cls._native_text(getter.__name__, "getattr")
            or not cls._is_class(super_type)
            or type(super_type) is not type
        ):
            msg = "native optional slot lookup bindings differ"
            raise ValueError(msg)
        namespace = cls._class_namespace(super_type)
        constructor = namespace.get("__new__")
        accessor = namespace.get("__getattribute__")
        if (
            not cls._native_text(
                vars(type)["__module__"].__get__(super_type, type), "builtins"
            )
            or not cls._native_text(
                vars(type)["__name__"].__get__(super_type, type), "super"
            )
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not super_type
            or type(accessor) is not WrapperDescriptorType
            or accessor.__objclass__ is not super_type
        ):
            msg = "native optional slot lacks the interpreter super implementation"
            raise ValueError(msg)
        root = vars(type)["__base__"].__get__(int, type(int))
        if ancestry[-1] is not root:
            msg = "native optional slot lacks the interpreter object root"
            raise ValueError(msg)
        absent = root()
        stored = getter(super_type(predecessor, value), name, absent)
        current = vars(type)["__mro__"].__get__(type(value), type(type(value)))
        if (
            type(value) is not native
            or len(current) != len(ancestry)
            or any(
                left is not right for left, right in zip(current, ancestry, strict=True)
            )
            or cls._class_namespace(owner).get(name) is not descriptor
        ):
            msg = "native optional slot context changed during observation"
            raise ValueError(msg)
        return (False, None) if stored is absent else (True, stored)

    @classmethod
    def _native_callable_instance(cls, value: p.AttributeProbe) -> bool:
        """Recognize only the declared CPython operator state intrinsics."""
        native = type(value)
        namespace = cls._class_namespace(native)
        descriptor = namespace.get("__call__")
        if (
            not (
                type(descriptor) is MethodDescriptorType
                or type(descriptor) is WrapperDescriptorType
            )
            or descriptor.__objclass__ is not native
            or "__name__" in namespace
        ):
            return False
        module_name = namespace.get("__module__")
        if type(module_name) is not str:
            return False
        supplier = sys.modules.get("_operator")
        return type(supplier) is ModuleType and any(
            vars(supplier).get(name) is native
            and vars(type)["__name__"].__get__(native, type(native)) == name
            and module_name == "operator"
            for name in ("itemgetter", "attrgetter", "methodcaller")
        )

    @classmethod
    def _native_operator_authority(cls) -> p.Result[bool]:
        """Admit the native reducer's complete import and constructor boundary."""
        result_type = r[bool]
        builtins = sys.modules.get("builtins")
        operator = sys.modules.get("operator")
        native_operator = sys.modules.get("_operator")
        functools = sys.modules.get("functools")
        native_functools = sys.modules.get("_functools")
        if sys.implementation.name != "cpython" or not all(
            type(module) is ModuleType
            for module in (
                builtins,
                operator,
                native_operator,
                functools,
                native_functools,
            )
        ):
            return result_type.fail(
                "native operator state requires its loaded CPython suppliers",
            )
        importer = vars(builtins).get("__import__")
        observer = cls._class_namespace(cls)["_native_operator_state"].__func__
        if (
            type(importer) is not BuiltinFunctionType
            or importer.__self__ is not builtins
            or not cls._native_text(importer.__module__, "builtins")
            or not cls._native_text(importer.__name__, "__import__")
            or observer.__builtins__ is not vars(builtins)
        ):
            return result_type.fail(
                "native operator reduction has no admitted interpreter importer",
            )
        if (
            cls._language_singleton(vars(builtins).get("NotImplemented"))
            != "NotImplemented"
            or cls._language_singleton(vars(builtins).get("Ellipsis")) != "Ellipsis"
        ):
            return result_type.fail("language singleton builtin binding differs")
        partial = vars(native_functools).get("partial")
        if not cls._is_class(partial) or type(partial) is not type:
            return result_type.fail("native partial constructor is not registered")
        partial_namespace = cls._class_namespace(partial)
        constructor = partial_namespace.get("__new__")
        if (
            vars(functools).get("partial") is not partial
            or not cls._native_text(partial_namespace.get("__module__"), "functools")
            or vars(type)["__name__"].__get__(partial, type(partial)) != "partial"
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not partial
            or constructor.__name__ != "__new__"
        ):
            return result_type.fail(
                "native operator reduction has no admitted partial constructor",
            )
        for name in ("itemgetter", "attrgetter", "methodcaller"):
            native = vars(native_operator).get(name)
            if not cls._is_class(native) or type(native) is not type:
                return result_type.fail(
                    f"native operator type is not registered: {name}"
                )
            namespace = cls._class_namespace(native)
            reduction = namespace.get("__reduce__")
            if (
                vars(operator).get(name) is not native
                or not cls._native_text(namespace.get("__module__"), "operator")
                or vars(type)["__name__"].__get__(native, type(native)) != name
                or type(reduction) is not MethodDescriptorType
                or reduction.__objclass__ is not native
            ):
                return result_type.fail(
                    f"native operator reduction differs from its registered owner: {name}",
                )
        for name in ("builtins", "_operator", "_functools", "operator", "functools"):
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
            if elected.failure:
                return result_type.from_failure(elected)
            if name.startswith("_") or name == "builtins":
                if elected.value != Path(sys.executable).resolve():
                    return result_type.fail(
                        "native operator supplier is not the elected interpreter: "
                        f"{name}={elected.value}",
                    )
        return result_type.ok(value=True)

    @classmethod
    def _native_operator_state(
        cls, value: p.AttributeProbe
    ) -> p.Result[p.AttributeProbe]:
        """Copy complete constructor state through authenticated native reducers."""
        authority = cls._native_operator_authority()
        if authority.failure:
            return r[p.AttributeProbe].from_failure(authority)
        if not cls._native_callable_instance(value):
            return r[p.AttributeProbe].fail(
                "native callable has no complete admitted constructor state",
            )
        native = type(value)
        descriptor = cls._class_namespace(native)["__reduce__"]
        # Native operator reducers retain C scalar distinctions that GC omits.
        # Their only dynamic constructor is the preflighted native partial.
        return r[p.AttributeProbe].ok(descriptor.__get__(value, native)())

    @classmethod
    def _native_callable_instance(cls, value: t.Infra.NativeOperand) -> bool:
        """Recognize a registered native callable object through its call slot.

        Returns:
            Whether the supplier registers the exact native callable type.

        """
        native = type(value)
        namespace = cls._class_namespace(native)
        descriptor = namespace.get("__call__")
        if (
            not cls._is_descriptor(descriptor)
            or not (
                cls._is_native(descriptor, MethodDescriptorType)
                or cls._is_native(descriptor, WrapperDescriptorType)
            )
            or descriptor.__objclass__ is not native
            or "__name__" in namespace
        ):
            return False
        supplier_name = namespace.get("__module__")
        supplier = (
            sys.modules.get(supplier_name) if type(supplier_name) is str else None
        )
        return type(supplier) is ModuleType and any(
            registered is native for registered in vars(supplier).values()
        )

    @classmethod
    def _python_callable_instance(cls, value: t.Infra.NativeOperand) -> bool:
        """Recognize authored call behavior separately from function metadata.

        Returns:
            Whether an authored function supplies the native call slot.

        """
        return any(
            type(cls._class_namespace(owner).get("__call__")) is FunctionType
            for owner in vars(type)["__mro__"].__get__(type(value), type(type(value)))
        )

    @staticmethod
    def _native_instance_referents(
        value: t.Infra.NativeOperand,
    ) -> t.VariadicTuple[t.Infra.NativeOperand]:
        """Read native argument storage through authenticated CPython traversal.

        Returns:
            Native referents other than the instance's own type.

        Raises:
            ValueError: The interpreter traversal has no admitted supplier.

        """
        supplier = sys.modules.get("gc")
        if (
            type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or get_referents.__module__ != "gc"
            or sys.implementation.name != "cpython"
        ):
            msg = "native callable storage has no admitted interpreter traversal"
            raise ValueError(msg)
        return tuple(item for item in get_referents(value) if item is not type(value))

    @classmethod
    def _native_cache_state(cls, value: t.Infra.NativeOperand) -> p.Result[str]:
        """Retain operational reference identities through authenticated native GC.

        Returns:
            Serialized native referent identities.

        """
        return r[str].ok(
            dumps(
                tuple(
                    (cls._symbol(type(item)), id(item))
                    for item in cls._native_instance_referents(value)
                )
            )
        )

    @classmethod
    def _native_iterator_receiver(cls, value: t.Infra.NativeOperand) -> bool:
        """Prove a bound next slot on a registered native iterator type.

        Returns:
            Whether native ownership proves both iterator slots and the type.

        """
        if not cls._native_builtin(value) or value.__name__ != "__next__":
            return False
        native = type(value.__self__)
        namespace = cls._class_namespace(native)
        for name in ("__iter__", "__next__"):
            slot = namespace.get(name)
            if (
                not cls._is_descriptor(slot)
                or not (
                    cls._is_native(slot, MethodDescriptorType)
                    or cls._is_native(slot, WrapperDescriptorType)
                )
                or slot.__objclass__ is not native
            ):
                return False
        supplier_name = cls._type_attr("__module__", native, type(native))
        supplier = (
            sys.modules.get(supplier_name) if type(supplier_name) is str else None
        )
        return type(supplier) is ModuleType and any(
            registered is native for registered in vars(supplier).values()
        )

    @classmethod
    def _is_class(
        cls,
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[type]:
        """Recognize a class through native metaclass storage, never __class__.

        Returns:
            Whether its native metaclass ancestry contains type.

        """
        return any(base is type for base in cls._native_mro(type(value)))

    @classmethod
    def _native_builtin(
        cls,
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[t.Infra.NativeBuiltinCallable]:
        """Recognize interpreter callable ancestry, including native subtypes.

        Returns:
            Whether native ancestry contains an admitted builtin callable type.

        """
        return any(
            owner is BuiltinFunctionType or owner is MethodWrapperType
            for owner in cls._native_mro(type(value))
        )

    @classmethod
    def _bound_native_symbol(cls, value: t.Infra.NativeBuiltinCallable) -> str:
        """Find an admitted native method's exact defining receiver descriptor.

        Returns:
            The receiver owner's symbolic method identity.

        Raises:
            TypeError: No native descriptor binds the admitted receiver.

        """
        receiver = value.__self__
        class_receiver = cls._is_class(receiver)
        receiver_owner = receiver if cls._is_class(receiver) else type(receiver)
        for owner in cls._native_mro(receiver_owner):
            descriptor = cls._class_namespace(owner).get(value.__name__)
            if cls._is_function_binding(descriptor):
                descriptor = descriptor.__func__
            if descriptor is value:
                return f"{cls._symbol(owner)}.{value.__name__}"
            if (
                cls._is_descriptor(descriptor)
                and any(
                    cls._is_native(descriptor, kind)
                    for kind in (
                        ClassMethodDescriptorType,
                        MethodDescriptorType,
                        WrapperDescriptorType,
                    )
                )
                and descriptor.__objclass__ is owner
            ):
                bound = descriptor.__get__(
                    None if class_receiver else receiver,
                    receiver_owner,
                )
                if type(bound) is type(value) and bound == value:
                    return f"{cls._symbol(owner)}.{value.__name__}"
        msg = (
            "native callable has no defining descriptor for its receiver: "
            f"{cls._symbol(receiver_owner)}.{value.__name__}"
        )
        raise TypeError(msg)

    @staticmethod
    def _native_type(value: p.AttributeProbe | None, *expected: type) -> bool:
        """Compare type identity without invoking an authored metaclass hash."""
        native = type(value)
        return any(native is candidate for candidate in expected)

    @staticmethod
    def _native_text(value: p.AttributeProbe | None, expected: str) -> bool:
        """Reject authored equality before comparing native metadata text."""
        return type(value) is str and value == expected

    @classmethod
    def _symbol(cls, value: p.AttributeProbe) -> str:
        if cls._is_class(value):
            module = vars(type)["__module__"].__get__(value, type(value))
            name = vars(type)["__qualname__"].__get__(value, type(value))
        elif type(value) in {FunctionType, BuiltinFunctionType}:
            module = value.__module__
            name = value.__qualname__
        elif cls._native_builtin(value):
            module_slot: p.Infra.NativeStorageSlot[str | None] = vars(
                BuiltinFunctionType
            )["__module__"]
            module = module_slot.__get__(value, type(value))
            name = value.__qualname__
        elif type(value) is ModuleType:
            module, name = value.__name__, ""
        else:
            module = vars(type)["__module__"].__get__(
                type(value),
                type(type(value)),
            )
            name = vars(type)["__qualname__"].__get__(type(value), type(type(value)))
        return f"{module}::{name}"

    @classmethod
    def _language_singleton(cls, value: p.AttributeProbe | None) -> str | None:
        """Recognize language singletons independently of mutable builtin aliases."""
        if value is ...:
            export, identity = "Ellipsis", ...
        else:
            integer = int
            comparison = cls._class_namespace(integer)["__eq__"]
            if (
                type(comparison) is not WrapperDescriptorType
                or comparison.__objclass__ is not integer
            ):
                msg = "language comparison has no native integer owner"
                raise ValueError(msg)
            identity = comparison.__get__(0, integer)("")
            if value is not identity:
                return None
            export = "NotImplemented"
        builtins = sys.modules.get("builtins")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(builtins) is not ModuleType
            or vars(builtins).get(export) is not identity
        ):
            msg = "language singleton differs from its elected builtin export"
            raise ValueError(msg)
        return export

    @classmethod
    def _typing_singleton(cls, value: p.AttributeProbe) -> str | None:
        """Prove CPython's object-header-only NoDefault intrinsic without calls."""
        owner = sys.modules.get("_typing")
        public = sys.modules.get("typing")
        if type(owner) is not ModuleType or vars(owner).get("NoDefault") is not value:
            return None
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "_typing"
        ).unwrap()
        native = type(value)
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(public) is not ModuleType
            or vars(public).get("NoDefault") is not value
            or type(native) is not type
        ):
            msg = "typing singleton lacks its elected interpreter exports"
            raise ValueError(msg)
        namespace = cls._class_namespace(native)
        constructor = namespace.get("__new__")
        reduction = namespace.get("__reduce__")
        if (
            not cls._native_text(
                vars(type)["__name__"].__get__(native, type(native)), "NoDefaultType"
            )
            or not cls._native_text(
                vars(type)["__module__"].__get__(native, type(native)), "builtins"
            )
            or vars(type)["__base__"].__get__(native, type(native)) is not object
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not native
            or not cls._native_text(constructor.__name__, "__new__")
            or type(reduction) is not MethodDescriptorType
            or reduction.__objclass__ is not native
            or not cls._native_text(reduction.__name__, "__reduce__")
        ):
            msg = "typing singleton differs from its static native type contract"
            raise ValueError(msg)
        for attribute in (
            "__basicsize__",
            "__itemsize__",
            "__dictoffset__",
            "__weakrefoffset__",
        ):
            descriptor = vars(type)[attribute]
            if descriptor.__get__(native, type(native)) != descriptor.__get__(
                object, type
            ):
                msg = "typing singleton has an unproved native payload"
                raise ValueError(msg)
        if any(
            cls._native_type(descriptor, MemberDescriptorType, GetSetDescriptorType)
            for descriptor in namespace.values()
        ):
            msg = "typing singleton has unproved native instance slots"
            raise ValueError(msg)
        return "_typing.NoDefault"

    @classmethod
    def _slice_state(
        cls, value: p.AttributeProbe | None
    ) -> (
        t.Triple[
            p.AttributeProbe | None, p.AttributeProbe | None, p.AttributeProbe | None
        ]
        | None
    ):
        """Read the three retained references of the exact CPython slice type."""
        builtins = sys.modules.get("builtins")
        if type(builtins) is not ModuleType:
            msg = "native slice has no registered builtin supplier"
            raise ValueError(msg)
        native = vars(builtins).get("slice")
        if type(value) is not native:
            return None
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(native) is not type
            or not cls._native_text(
                vars(type)["__name__"].__get__(native, type), "slice"
            )
            or not cls._native_text(
                vars(type)["__module__"].__get__(native, type), "builtins"
            )
        ):
            msg = "native slice differs from its elected interpreter type"
            raise ValueError(msg)
        namespace = cls._class_namespace(native)
        constructor = namespace.get("__new__")
        if (
            "__module__" in namespace
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not native
            or not cls._native_text(constructor.__name__, "__new__")
            or tuple(
                sorted(
                    name
                    for name, descriptor in namespace.items()
                    if cls._native_type(
                        descriptor, MemberDescriptorType, GetSetDescriptorType
                    )
                )
            )
            != ("start", "step", "stop")
        ):
            msg = "native slice has unproved construction or storage"
            raise ValueError(msg)
        result = []
        for name in ("start", "stop", "step"):
            descriptor = namespace[name]
            if (
                type(descriptor) is not MemberDescriptorType
                or descriptor.__objclass__ is not native
                or not cls._native_text(descriptor.__name__, name)
            ):
                msg = "native slice member differs from its declared owner"
                raise ValueError(msg)
            result.append(descriptor.__get__(value, native))
        return result[0], result[1], result[2]

    @classmethod
    def _generic_alias_state(
        cls, value: p.AttributeProbe | None
    ) -> t.SequenceOf[t.Pair[str, p.AttributeProbe | None]] | None:
        """Read retained alias operands without populating its lazy parameters."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        if not any(owner is GenericAlias for owner in ancestry):
            return None
        supplier = sys.modules.get("types")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(supplier) is not ModuleType
            or vars(supplier).get("GenericAlias") is not GenericAlias
            or type(GenericAlias) is not type
            or not cls._native_text(
                vars(type)["__name__"].__get__(GenericAlias, type), "GenericAlias"
            )
            or not cls._native_text(
                vars(type)["__module__"].__get__(GenericAlias, type), "types"
            )
        ):
            msg = "generic alias lacks its elected interpreter type"
            raise ValueError(msg)
        namespace = cls._class_namespace(GenericAlias)
        constructor = namespace.get("__new__")
        if (
            type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not GenericAlias
            or not cls._native_text(constructor.__name__, "__new__")
        ):
            msg = "generic alias has no native constructor owner"
            raise ValueError(msg)
        result = []
        for name in ("__origin__", "__args__", "__unpacked__"):
            descriptor = namespace.get(name)
            if (
                type(descriptor) is not MemberDescriptorType
                or descriptor.__objclass__ is not GenericAlias
                or not cls._native_text(descriptor.__name__, name)
            ):
                msg = "generic alias has an unproved native member"
                raise ValueError(msg)
            result.append((name, descriptor.__get__(value, native)))
        if type(result[1][1]) is not tuple or type(result[2][1]) is not bool:
            msg = "generic alias has non-native argument or expansion storage"
            raise ValueError(msg)
        if native is not GenericAlias:
            owners = tuple(owner for owner in ancestry if owner is not GenericAlias)
            if not cls._python_storage_owners(owners):
                msg = "generic alias subclass has an unproved native payload"
                raise ValueError(msg)
            # Native operand slots and the subclass's Python storage both matter.
            result.append(("storage", cls._instance_storage(value)))
        return tuple(result)

    @classmethod
    def _value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int] = frozenset(),
        *,
        construction: bool = False,
        references: list[t.Pair[str, t.Infra.NativeOperand]] | None = None,
        binding: str = "",
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> str:
        """Serialize one structural observation without recursively escaping JSON.

        Returns:
            The single JSON serialization of the structural observation.

        """
        return dumps(
            cls._value_data(
                value,
                seen,
                construction=construction,
                references=references,
                binding=binding,
                paths=paths,
            )
        )

    @classmethod
    def _value_data(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        *,
        construction: bool,
        references: list[t.Pair[str, t.Infra.NativeOperand]] | None = None,
        binding: str = "",
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> t.JsonValue:
        """Observe native slots as JSON data without authored accessors.

        Returns:
            Structural values read through admitted native storage.

        Raises:
            TypeError: A native descriptor differs from its registered owner.
            ValueError: The operand has no admitted callback-free storage.

        """
        native = type(value)
        if native in {str, int, bool, type(None)}:
            return dumps((native.__name__, value), ensure_ascii=True)
        if native is float:
            return dumps(("float", float.hex(value)))
        if native is bytes:
            return dumps(("bytes", b64encode(value).decode("ascii")))
        if value is Ellipsis:
            return dumps(("ellipsis",))
        if id(value) in seen:
            return ["cycle", cls._symbol(value)]
        seen |= {id(value)}
        if native in {list, set, dict} and not construction:
            return dumps(("mutable", native.__name__))
        if native in {tuple, list, set, frozenset}:
            items = tuple(
                cls._value(item, seen, construction=construction) for item in value
            )
            return dumps((
                native.__name__,
                sorted(items) if native in {set, frozenset} else items,
            ))
        if native is dict:
            return dumps((
                "dict",
                sorted(
                    (
                        cls._value(key, seen, construction=construction),
                        cls._value(item, seen, construction=construction),
                    )
                    for key, item in value.items()
                ),
            ))
        if native is CodeType:
            return dumps((
                "code",
                [
                    [
                        name,
                        observe(
                            descriptor.__get__(value, CodeType), construction=False
                        ),
                    ]
                    for name, descriptor in sorted(vars(CodeType).items())
                    if type(descriptor) in {MemberDescriptorType, GetSetDescriptorType}
                    and descriptor.__objclass__ is CodeType
                ],
            ))
        if native in {
            MemberDescriptorType,
            GetSetDescriptorType,
            ClassMethodDescriptorType,
            MethodDescriptorType,
            WrapperDescriptorType,
        }:
            return dumps((
                "native_descriptor",
                native.__name__,
                cls._symbol(value.__objclass__),
                value.__name__,
            ))
        if native is FunctionType:
            return dumps((
                "function",
                cls._symbol(value),
                observe(value.__code__, construction=False),
                *map(
                    observe,
                    (
                        value.__defaults__,
                        value.__kwdefaults__,
                        tuple(cell.cell_contents for cell in value.__closure__ or ()),
                    ),
                ),
            ))
        if type(value) is UnionType:
            arguments = vars(UnionType)["__args__"].__get__(value, UnionType)
            return dumps(("union", cls._value(arguments, seen)))
        if any(
            owner is GenericAlias
            for owner in vars(type)["__mro__"].__get__(native, type(native))
        ):
            storage = vars(GenericAlias)
            return dumps((
                "generic_alias",
                cls._symbol(native),
                cls._value(storage["__origin__"].__get__(value, native), seen),
                cls._value(storage["__args__"].__get__(value, native), seen),
            ))
        if cls._is_class(value) or native in {BuiltinFunctionType, ModuleType}:
            return dumps(("symbol", cls._symbol(value)))
        if not construction:
            return dumps(("instance", cls._symbol(native)))
        module_name = cls._class_namespace(native).get("__module__")
        module = sys.modules.get(module_name) if type(module_name) is str else None
        if type(module) is ModuleType:
            declared = tuple(
                name
                for name, candidate in vars(module).items()
                if type(name) is str and candidate is value
            )
            if declared:
                return dumps(("registered", module_name, sorted(declared)))
        observed: list[t.Pair[str, str]] = []
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        for owner in ancestry:
            namespace = cls._class_namespace(owner)
            for name, descriptor in sorted(namespace.items()):
                if (
                    type(descriptor) is MemberDescriptorType
                    or (name == "__dict__" and type(descriptor) is GetSetDescriptorType)
                ) and descriptor.__objclass__ is owner:
                    observed.append((
                        f"{cls._symbol(owner)}::{name}",
                        cls._value(
                            descriptor.__get__(value, native), seen, construction=True
                        ),
                    ))
        if observed:
            return dumps(("storage", cls._symbol(native), observed))
        raise ValueError(
            "native import operand has no callback-free storage or registered binding: "
            + cls._symbol(native)
            + (f"; binding={binding}" if binding else ""),
        )

    @classmethod
    def _portable_code_constant(cls, value: t.Infra.NativeOperand) -> bool:
        """Admit exact native scalar constants before the compiler encoder.

        Returns:
            Whether scalar equality is portable between native processes.

        Raises:
            TypeError: A constant has no admitted native encoding.

        """
        native = type(value)
        if (
            value is None
            or value is Ellipsis
            or value is StopIteration
            or any(native is kind for kind in (str, int, bool, bytes))
        ):
            return True
        if cls._is_native(value, float):
            return not isnan(value)
        if cls._is_native(value, complex):
            return not isnan(value.real) and not isnan(value.imag)
        if any(native is kind for kind in (list, set, dict, bytearray, memoryview)):
            return False
        message = (
            "native code constant has no admitted interpreter encoding: "
            + cls._symbol(native)
        )
        raise TypeError(message)

    @classmethod
    def _native_code_constants(
        cls, code: t.Infra.NativeCode
    ) -> t.VariadicTuple[t.Infra.NativeOperand]:
        """Read exact native code storage without authored iteration or buffers.

        Returns:
            The interpreter-owned constant tuple.

        Raises:
            TypeError: Compiler metadata has non-native storage.

        """
        if any(
            type(value) is not str
            for value in (code.co_filename, code.co_name, code.co_qualname)
        ):
            message = "native code metadata requires exact interpreter strings"
            raise TypeError(message)
        if any(
            type(value) is not bytes
            for value in (code.co_linetable, code.co_exceptiontable)
        ):
            message = "native code metadata requires exact interpreter bytes"
            raise TypeError(message)
        names = code.co_names
        if not cls._is_operand_tuple(names) or any(
            type(name) is not str for name in names
        ):
            message = "native code names require exact interpreter string storage"
            raise TypeError(message)
        constants = code.co_consts
        if not cls._is_operand_tuple(constants):
            message = "native code constants require exact interpreter tuple storage"
            raise TypeError(message)
        return constants

    @classmethod
    def _code_nonportable_constants(
        cls, code: t.Infra.NativeCode
    ) -> t.VariadicTuple[t.Pair[t.VariadicTuple[int], str]]:
        """Elect native constants before any relocation or binary encoding.

        Returns:
            Structural paths and native types whose equality is not portable.

        Raises:
            TypeError: A constant has no callback-free native encoding.

        """
        pending: list[t.Pair[t.VariadicTuple[int], t.Infra.NativeOperand]] = [
            ((), code),
        ]
        seen: set[int] = set()
        rejected: list[t.Pair[t.VariadicTuple[int], str]] = []
        while pending:
            position, value = pending.pop()
            children: t.IterableOf[t.Infra.NativeOperand]
            if cls._is_native(value, CodeType):
                children = cls._native_code_constants(value)
            elif (
                type(value) is tuple or type(value) is frozenset
            ) and cls._is_operand_sequence(value):
                children = value
            else:
                if not cls._portable_code_constant(value):
                    rejected.append((position, cls._symbol(type(value))))
                continue
            if id(value) in seen:
                continue
            seen.add(id(value))
            pending.extend(
                ((*position, index), child) for index, child in enumerate(children)
            )
        return tuple(rejected)

    @classmethod
    def _code_evidence(cls, code: t.Infra.NativeCode) -> m.Infra.NativeCodeEvidence:
        """Capture complete compiler bytes without reconstructing executable code.

        Returns:
            Native compiler evidence or explicit nonportable constant markers.

        """
        nonportable = cls._code_nonportable_constants(code)
        return m.Infra.NativeCodeEvidence(
            filename=code.co_filename,
            name=code.co_name,
            firstlineno=code.co_firstlineno,
            witness=(
                None
                if nonportable
                else marshal.dumps(code, c.Infra.NATIVE_CODE_WITNESS_MARSHAL_VERSION)
            ),
            locations=None if nonportable else tuple(cls._code_locations(code)),
            nonportable_constants=nonportable,
        )

    @staticmethod
    def _code_matches(
        observed: m.Infra.NativeCodeEvidence,
        reference: m.Infra.NativeCodeEvidence,
    ) -> bool:
        """Require complete compiler identity, including stack and locals kinds.

        Returns:
            Whether both observations carry the same complete portable witness.

        """
        return (
            observed.witness is not None
            and observed.model_dump() == reference.model_dump()
        )

    @staticmethod
    def _relocate_code(
        code: t.Infra.NativeCode,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> t.Infra.NativeCode:
        """Translate authenticated staging paths using native CodeType.replace.

        Returns:
            Code retaining its identity data with staging paths relocated.

        """
        FlextInfraWorkspaceNativeReference._code_nonportable_constants(code)
        if not paths:
            return code
        filename = code.co_filename
        if not filename.startswith("<"):
            source = Path(filename)
            for staged, original in paths:
                if source.is_relative_to(staged):
                    filename = str(original / source.relative_to(staged))
                    break
        constants = tuple(
            FlextInfraWorkspaceNativeReference._relocate_code(value, paths)
            if FlextInfraWorkspaceNativeReference._is_native(value, CodeType)
            else value
            for value in FlextInfraWorkspaceNativeReference._native_code_constants(code)
        )
        return code.replace(co_filename=filename, co_consts=constants)

    @staticmethod
    def _source_path(
        source: Path,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> Path:
        """Translate a source path through the authenticated staging roots.

        Returns:
            Its original source path, or the unchanged unstaged path.

        """
        for staged, original in paths:
            if source.is_relative_to(staged):
                return original / source.relative_to(staged)
        return source

    @staticmethod
    def _code_locations(code: t.Infra.NativeCode) -> list[t.JsonValue]:
        """Retain physical locations for every nested native compiler code unit.

        Returns:
            Nested code positions and their physical compiler metadata.

        """
        pending: list[t.Pair[t.Infra.NativeCode, t.VariadicTuple[int]]] = [(code, ())]
        locations: list[t.JsonValue] = []
        while pending:
            current, position = pending.pop()
            locations.append([
                list(position),
                current.co_qualname,
                current.co_filename,
                current.co_firstlineno,
                b64encode(current.co_linetable).decode("ascii"),
                b64encode(current.co_exceptiontable).decode("ascii"),
            ])
            pending.extend(
                (value, (*position, index))
                for index, value in enumerate(
                    FlextInfraWorkspaceNativeReference._native_code_constants(current)
                )
                if FlextInfraWorkspaceNativeReference._is_native(value, CodeType)
            )
        return locations

    @staticmethod
    def _code_units(
        root: t.Infra.NativeCode,
    ) -> t.VariadicTuple[t.Infra.NativeCode]:
        """Collect the native compiler's nested code units without executing them.

        Returns:
            The root and every nested native code unit.

        """
        pending = [root]
        units: list[t.Infra.NativeCode] = []
        while pending:
            current = pending.pop()
            units.append(current)
            pending.extend(
                value
                for value in FlextInfraWorkspaceNativeReference._native_code_constants(
                    current
                )
                if FlextInfraWorkspaceNativeReference._is_native(value, CodeType)
            )
        return tuple(units)

    @staticmethod
    def _instructions(
        code: t.Infra.NativeCode,
        cache: t.Infra.NativeInstructionFacts,
    ) -> t.VariadicTuple[Instruction]:
        """Decode each exact immutable code object once within its owning scope.

        Returns:
            Instructions for the exact, strongly retained native code identity.

        """
        captured = cache.get(id(code))
        if captured is not None and captured[0] is code:
            return captured[1]
        instructions = tuple(get_instructions(code))
        cache[id(code)] = (code, instructions)
        return instructions

    @classmethod
    def _compile_class_declarations(
        cls,
        content: bytes,
        filename: str,
        optimize: int,
    ) -> t.Infra.NativeClassDeclarations:
        """Compile immutable class store facts without executing source.

        Returns:
            Qualified class names with their source lines and declared stores.

        """
        root = compile(content, filename, "exec", dont_inherit=True, optimize=optimize)
        indexed: t.DictKV[str, list[t.Pair[int, frozenset[str]]]] = {}
        for unit in cls._code_units(root):
            if unit is not root and not unit.co_flags & (CO_NEWLOCALS | CO_OPTIMIZED):
                stores = frozenset(
                    instruction.argval
                    for instruction in get_instructions(unit)
                    if instruction.opname == "STORE_NAME"
                    and isinstance(instruction.argval, str)
                )
                indexed.setdefault(unit.co_qualname, []).append((
                    unit.co_firstlineno,
                    stores,
                ))
        return MappingProxyType({
            name: tuple(declarations) for name, declarations in indexed.items()
        })

    @classmethod
    def _declared_class_names(
        cls,
        supplier: str,
        path: Path,
        qualname: str,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        compiled: t.DictKV[Path, t.Infra.NativeClassDeclarations],
    ) -> p.Result[t.VariadicTuple[frozenset[str]]]:
        """Separate authored class bindings from a metaclass's operational outputs.

        The physical path is the supplier origin already elected in this capture;
        staging relocation applies only to emitted evidence.

        Returns:
            Zero or one authored store sets, or the source admission failure.

        """
        result = r[t.VariadicTuple[frozenset[str]]]
        if path.suffix != c.Infra.EXT_PYTHON:
            return result.ok(())
        if path not in compiled:
            before = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if before.content is None:
                return result.fail(f"native class declaration source is absent: {path}")
            key = (before.content, str(path), sys.flags.optimize)
            scope = ContextVar[t.Infra.NativeInvocationFacts | None].get(
                cls._compilation_facts
            )
            facts = scope[0] if scope is not None else None
            declarations = facts.get(key) if facts is not None else None
            if declarations is None:
                declarations = cls._compile_class_declarations(*key)
                if facts is not None:
                    facts[key] = declarations
            after = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if before != after:
                return result.fail(f"native class declaration source changed: {path}")
            compiled[path] = declarations
        candidates = compiled[path].get(qualname, ())
        if len(candidates) > 1:
            candidates = tuple(
                declaration
                for declaration in candidates
                if declaration[0] == namespace.get("__firstlineno__")
            )
            if len(candidates) != 1:
                return result.fail(
                    f"native class declaration is ambiguous: {supplier}::{qualname}"
                )
        # Factory-created classes retain their existing complete native
        # payload and generated-code/declaration provenance.
        return result.ok(tuple(names for _, names in candidates[:1]))

    @staticmethod
    def _class_state_writers(
        owner: t.Infra.NativeOperand,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        declarations: frozenset[str],
        instruction_cache: t.Infra.NativeInstructionFacts,
    ) -> t.VariadicTuple[t.Triple[str, p.AttributeProbe, frozenset[str]]]:
        """Prove state writes through the exact native class or global receiver.

        Returns:
            Authenticated writer bindings and the declared fields they modify.

        """
        writers: list[t.Triple[str, p.AttributeProbe, frozenset[str]]] = []
        for name, member in sorted(namespace.items()):
            if not FlextInfraWorkspaceNativeReference._is_function_binding(member):
                continue
            function = member.__func__
            if not FlextInfraWorkspaceNativeReference._is_native(
                function, FunctionType
            ):
                continue
            if not declarations.intersection(function.__code__.co_names):
                continue
            if type(member) is classmethod and not function.__code__.co_argcount:
                continue
            receiver = (
                function.__code__.co_varnames[0]
                if type(member) is classmethod
                else None
            )
            instructions = FlextInfraWorkspaceNativeReference._instructions(
                function.__code__, instruction_cache
            )
            if receiver is not None and any(
                (
                    instruction.opname.startswith("STORE_FAST")
                    or instruction.opname == "DELETE_FAST"
                )
                and (
                    instruction.argval == receiver
                    or (
                        FlextInfraWorkspaceNativeReference._is_operand_tuple(
                            instruction.argval
                        )
                        and receiver in instruction.argval
                    )
                )
                for instruction in instructions
            ):
                continue
            global_receivers = {
                instruction.argval
                for instruction in instructions
                if instruction.opname == "LOAD_GLOBAL"
                and isinstance(instruction.argval, str)
                and function.__globals__.get(instruction.argval) is owner
            }
            rebound_globals = {
                instruction.argval
                for instruction in instructions
                if instruction.opname in {"STORE_GLOBAL", "DELETE_GLOBAL"}
            }
            fields = frozenset(
                instruction.argval
                for previous, instruction in itertools.pairwise(instructions)
                if instruction.opname == "STORE_ATTR"
                and isinstance(instruction.argval, str)
                and instruction.argval in declarations
                and (
                    (
                        receiver is not None
                        and previous.opname == "LOAD_FAST"
                        and previous.argval == receiver
                    )
                    or (
                        receiver is not None
                        and previous.opname == "LOAD_FAST_LOAD_FAST"
                        and FlextInfraWorkspaceNativeReference._is_operand_tuple(
                            previous.argval
                        )
                        and previous.argval[-1] == receiver
                    )
                    or (
                        previous.opname == "LOAD_GLOBAL"
                        and previous.argval in global_receivers - rebound_globals
                    )
                )
            )
            if fields:
                writers.append((name, member, fields))
        return tuple(writers)

    @classmethod
    def _remember_generated_descriptors(
        cls,
        owner: p.AttributeProbe,
        supplier: str,
        owners: t.MutableMappingKV[int, t.Triple[str, str, p.AttributeProbe | None]],
    ) -> None:
        """Keep the actual class receiver while traversing native wrappers."""
        for attribute, descriptor in cls._class_namespace(owner).items():
            value = (
                descriptor.__func__
                if cls._native_type(descriptor, classmethod, staticmethod)
                else descriptor
            )
            if (
                type(value) is FunctionType
                and value.__code__.co_filename.startswith("<")
                and not value.__code__.co_filename.startswith("<frozen ")
            ):
                owners[id(value)] = (supplier, attribute, owner)

    @classmethod
    def capture(
        cls,
        names: t.SequenceOf[str | m.Infra.SourceClassReference],
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe the complete native epoch without reconstructing class factories."""
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        origins: dict[str, Path] = {}
        sources: set[t.Triple[str, str, str]] = set()
        for supplier in (
            "builtins",
            "_operator",
            "_functools",
            "_typing",
            "operator",
            "functools",
            "typing",
            "types",
            "gc",
        ):
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(supplier)
            if elected.failure:
                return r[m.Infra.NativeImportObservation].from_failure(elected)
            sources.add((supplier, str(cls._source_path(elected.value, paths)), ""))
        evidence: list[m.Infra.NativeBindingEvidence] = []
        pending = []
        for name in names:
            module = sys.modules.get(name)
            if type(module) is not ModuleType:
                if name.partition(".")[0] not in {
                    "flext",
                    "flext_core",
                    "flext_infra",
                    "flext_cli",
                    "flext_api",
                }:
                    # Third-party lazy/aliased modules (pygments.lexers, ...)
                    # are their package's construction: this workspace's
                    # epoch proves first-party bindings only.
                    continue
                return r[m.Infra.NativeImportObservation].fail(
                    f"native reference lacks an elected module: {name}",
                )
            origin = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
            if origin.failure:
                return r[m.Infra.NativeImportObservation].from_failure(origin)
            origins[name] = cls._source_path(origin.value, paths)
            sources.add((name, str(origins[name]), ""))
            mutable_globals = set()
            functions = [
                value for value in vars(module).values() if type(value) is FunctionType
            ]
            functions.extend(
                member.__func__
                if type(member) in {classmethod, staticmethod}
                else member
                for value in vars(module).values()
                if cls._is_class(value)
                for member in cls._class_namespace(value).values()
                if type(member) in {FunctionType, classmethod, staticmethod}
            )
            for function in functions:
                if not hasattr(function, "__code__"):
                    # Typing alias pseudo-classes and other callable objects
                    # carry no bytecode: they store no module globals.
                    continue
                mutable_globals.update(
                    instruction.argval
                    for instruction in cls._instructions(
                        function.__code__, instructions
                    )
                    if instruction.opname == "STORE_GLOBAL"
                )
            evidence.extend(
                m.Infra.NativeBindingEvidence(
                    binding=f"{name}::{key}",
                    kind="boolean",
                    supplier=name,
                    name=key,
                    qualname=key,
                    operands=(("value", observe_value(value)),),
                )
                for key, value in sorted(namespace.items())
                if type(value) is bool and key not in mutable_globals
            )
            pending.extend(
                (f"{name}::{key}", value, name, "")
                for key, value in sorted(namespace.items())
                if cls._is_class(value)
                or type(value) in {FunctionType, BuiltinFunctionType, MethodType}
                or type(value) in {property, classmethod, staticmethod}
                or cls._callable_storage(value)
            )
        visited: t.DictKV[int, t.Pair[t.Infra.NativeOperand, str]] = {}
        edges: t.DictKV[str, str] = {}
        absent_edges: set[str] = set()
        while pending or references:
            for registered, owner in references:
                supplier, _, _qualified = cls._symbol(owner).partition("::")
                pending.append((f"{registered}.native_type", owner, supplier, ""))
            references.clear()
            incoming, value, supplier, owner_source = pending.pop()
            captured = visited.get(id(value))
            binding = f"@{len(visited)}" if captured is None else captured[1]
            previous = edges.get(incoming)
            if incoming in absent_edges or (
                previous is not None and previous != binding
            ):
                return r[m.Infra.NativeImportObservation].fail(
                    f"native edge changed target: {incoming}; supplier={supplier}",
                )
            if previous is None:
                edges[incoming] = binding
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=incoming,
                        kind="alias",
                        supplier=supplier,
                        name="",
                        qualname="",
                        operands=(("target", binding),),
                    )
                )
            if captured is not None:
                continue
            visited[id(value)] = (value, binding)
            observe_value = partial(
                cls._value,
                references=references,
                paths=paths,
                binding=f"{incoming}; body={binding}; supplier={supplier}",
            )
            if cls._is_function_binding(value):
                function = value.__func__
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=cls._type_attr("__name__", type(value), type(type(value))),
                        supplier=supplier,
                        name="",
                        qualname="",
                        operands=(("function", cls._symbol(function)),),
                    ),
                )
                pending.append((
                    f"{binding}.function",
                    function,
                    supplier,
                    owner_source,
                ))
                continue
            visited[id(value)] = binding
            if cls._is_class(value):
                namespace = cls._class_namespace(value)
                actual_supplier = cls._type_attr("__module__", value, type(value))
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native source supplier: {binding}",
                    )
                cls._remember_generated_descriptors(
                    value, actual_supplier, generated_owners
                )
                origin = origins.get(actual_supplier)
                if origin is None:
                    observed = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                        actual_supplier,
                    )
                    if observed.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(
                            observed,
                        )
                    origin = origins[actual_supplier] = observed.value
                source = str(cls._source_path(origin, paths))
                qualname = cls._type_attr("__qualname__", value, type(value))
                if type(qualname) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native qualified name: {binding}",
                    )
                sources.add((f"{actual_supplier}::{qualname}", source, ""))
                declarations = cls._declared_class_names(
                    actual_supplier, origin, qualname, namespace, compiled
                )
                if declarations.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(declarations)
                declared = declarations.value
                declaration = {
                    name: item
                    for name, item in sorted(namespace.items())
                    if name != "__annotations__"
                    and (not declared or name in declared[0])
                    and not cls._is_class(item)
                    and not cls._callable_storage(item)
                    and not any(
                        type(item) is kind
                        for kind in (property, classmethod, staticmethod)
                    )
                }
                writers = cls._class_state_writers(
                    value, namespace, frozenset(declaration), instructions
                )
                operational = frozenset(
                    name for _, _, fields in writers for name in fields
                )
                pending.extend(
                    (f"{binding}.{name}", writer, actual_supplier, source)
                    for name, writer, _ in writers
                )
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="class",
                        supplier=actual_supplier,
                        name=cls._type_attr("__name__", value, type(value)),
                        qualname=qualname,
                        operands=(
                            ("metaclass", cls._symbol(type(value))),
                            (
                                "bases",
                                dumps(
                                    tuple(
                                        cls._symbol(base)
                                        for base in cls._type_attr(
                                            "__bases__", value, type(value)
                                        )
                                    )
                                ),
                            ),
                            (
                                "annotations",
                                observe_value(
                                    namespace.get("__annotations__", {}),
                                    construction=True,
                                ),
                            ),
                            ("slots", observe_value(namespace.get("__slots__"))),
                            (
                                "declaration",
                                dumps(
                                    tuple(
                                        (name, observe_value(item))
                                        for name, item in declaration.items()
                                        if name not in operational
                                    )
                                ),
                            ),
                        ),
                        operational=tuple(
                            (name, observe_value(declaration[name]))
                            for name in sorted(operational)
                        ),
                    ),
                )
                pending.extend(
                    (f"{binding}.{key}", item, actual_supplier, source)
                    for key, item in sorted(namespace.items())
                    if cls._is_class(item)
                    or type(item) in {FunctionType, BuiltinFunctionType, MethodType}
                    or type(item) in {property, classmethod, staticmethod}
                    or cls._callable_storage(item)
                )
                pending.append((
                    f"{binding}.metaclass",
                    type(value),
                    actual_supplier,
                    source,
                ))
                pending.extend(
                    (f"{binding}.base.{index}", base, actual_supplier, source)
                    for index, base in enumerate(
                        cls._type_attr("__bases__", value, type(value))
                    )
                )
                continue
            if cls._is_native(value, MethodType):
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="bound_method",
                        supplier=supplier,
                        name=value.__func__.__name__,
                        qualname=value.__func__.__qualname__,
                        operands=(("receiver", cls._symbol(value.__self__)),),
                    )
                )
                pending.append((
                    f"{binding}.function",
                    value.__func__,
                    supplier,
                    owner_source,
                ))
                if cls._is_class(value.__self__):
                    pending.append((
                        f"{binding}.receiver",
                        value.__self__,
                        supplier,
                        owner_source,
                    ))
                continue
            if cls._is_native(value, property):
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="property",
                        supplier=supplier,
                        name="",
                        qualname="",
                        operands=tuple(
                            (name, str(accessor is not None))
                            for name, accessor in (
                                ("get", value.fget),
                                ("set", value.fset),
                                ("delete", value.fdel),
                            )
                        ),
                    ),
                )
                pending.extend(
                    (f"{binding}.{name}", accessor, supplier, owner_source)
                    for name, accessor in (
                        ("get", value.fget),
                        ("set", value.fset),
                        ("delete", value.fdel),
                    )
                    if accessor is not None
                )
                continue
            if type(value) in {
                ClassMethodDescriptorType,
                MethodDescriptorType,
                WrapperDescriptorType,
            }:
                owner = value.__objclass__
                actual_supplier = vars(type)["__module__"].__get__(
                    owner,
                    type(owner),
                )
            if type(value) is MethodWrapperType:
                owner = value.__objclass__
                actual_supplier = cls._type_attr("__module__", owner, type(owner))
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"native descriptor owner has no source supplier: {binding}",
                    )
                elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                    actual_supplier,
                )
                if elected.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(elected)
                sources.add((
                    f"{actual_supplier}::{value.__qualname__}",
                    str(cls._source_path(elected.value, paths)),
                    "",
                ))
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=cls._type_attr("__name__", type(value), type(type(value))),
                        supplier=actual_supplier,
                        name=value.__name__,
                        qualname=value.__qualname__,
                        operands=(("receiver", cls._symbol(owner)),),
                    ),
                )
                pending.append((
                    f"{binding}.receiver",
                    owner,
                    actual_supplier,
                    owner_source,
                ))
                continue
            kind = type(value).__name__
            if type(value) in {classmethod, staticmethod}:
                value = value.__func__
            wrapper_kind = cls._native_wrapper_kind(value)
            if wrapper_kind is not None:
                function = cls._native_wrapper_function(value, wrapper_kind)
                if function.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(function)
                namespace = cls._class_namespace(type(value))
                storage = namespace.get("__dict__")
                if not cls._is_native(
                    storage, GetSetDescriptorType
                ) or storage.__objclass__ is not type(value):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"native wrapper has no interpreter-owned attributes: "
                        f"{binding}",
                    )
                attributes: t.DictKV[str, t.Infra.NativeOperand] = storage.__get__(
                    value, storage.__objclass__
                )
                operands = [
                    ("function", observe_value(function.value, construction=True)),
                    ("attributes", observe_value(attributes, construction=True)),
                ]
                operational = ()
                if wrapper_kind == "partial":
                    for attribute in ("args", "keywords"):
                        slot = namespace.get(attribute)
                        if not cls._is_native(
                            slot, MemberDescriptorType
                        ) or slot.__objclass__ is not type(value):
                            return r[m.Infra.NativeImportObservation].fail(
                                f"native partial lacks its {attribute} slot: {binding}",
                            )
                        slot.__get__(value, type(value))
                        operands.append((
                            attribute,
                            cls._value(
                                slot.__get__(value, type(value)),
                                construction=True,
                            ),
                        ))
                else:
                    cache_state = cls._native_cache_state(value)
                    if cache_state.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(
                            cache_state
                        )
                    operational = (("cache", cache_state.value),)
                evidence.append(
                    m.Infra.NativeBindingEvidence.model_validate({
                        "binding": binding,
                        "kind": f"{kind}:{wrapper_kind}",
                        "supplier": "_functools",
                        "name": attributes.get("__name__", ""),
                        "qualname": attributes.get("__qualname__", ""),
                        "operands": tuple(operands),
                        "operational": operational,
                    }),
                )
                pending.append((
                    f"{binding}.native_function",
                    function.value,
                    supplier,
                    owner_source,
                ))
                pending.extend(
                    (f"{binding}.attributes.{key}", item, supplier, owner_source)
                    for key, item in sorted(attributes.items())
                    if cls._is_class(item)
                    or type(item) in {FunctionType, BuiltinFunctionType}
                    or cls._native_wrapper_kind(item) is not None
                    if not selected or key == "__wrapped__"
                )
                continue
            if type(value) is not FunctionType:
                if type(value) is not BuiltinFunctionType:
                    extension = cls._extension_callback(value)
                    if extension.failure:
                        return r[m.Infra.NativeImportObservation].fail(
                            f"{extension.error}; binding={binding}; "
                            f"binding_supplier={supplier}; "
                            f"native_type={cls._symbol(type(value))}; "
                            f"native_ancestry={
                                tuple(
                                    cls._symbol(owner)
                                    for owner in cls._native_mro(type(value))
                                )
                            }"
                        )
                    actual_supplier, native_name, qualified = extension.value
                    origin = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                        actual_supplier,
                    )
                    if origin.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(origin)
                    sources.add((
                        f"{actual_supplier}::{qualified}",
                        str(cls._source_path(origin.value, paths)),
                        "",
                    ))
                    evidence.append(
                        m.Infra.NativeBindingEvidence(
                            binding=binding,
                            kind=kind,
                            supplier=actual_supplier,
                            name=native_name,
                            qualname=qualified,
                            operands=(("native_type", cls._symbol(type(value))),),
                        ),
                    )
                    continue
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=kind,
                        supplier=value.__module__ or supplier,
                        name=value.__name__,
                        qualname=value.__qualname__,
                    ),
                )
                continue
            raw_code = value.__code__
            code = cls._relocate_code(raw_code, paths)
            generated = code.co_filename.startswith("<")
            actual_supplier = value.__globals__.get("__name__")
            if isinstance(actual_supplier, str):
                module = sys.modules.get(actual_supplier)
                if module is None or (
                    not generated and value.__globals__ is not vars(module)
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer globals have no native supplier: {binding}",
                    )
            origin = origins.get(actual_supplier)
            if origin is None:
                observed = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                    actual_supplier,
                )
                if observed.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(observed)
                origin = origins[actual_supplier] = observed.value
            supplier_module = sys.modules[actual_supplier]
            supplier_namespace = cls._module_namespace(supplier_module)
            supplier_spec = supplier_namespace["__spec__"]
            if not cls._is_native(supplier_spec, ModuleSpec):
                return r[m.Infra.NativeImportObservation].fail(
                    f"producer native supplier has no module spec: {actual_supplier}"
                )
            frozen_source = supplier_spec.origin == "frozen"
            sources.add((
                f"{actual_supplier}::{value.__qualname__}",
                str(cls._source_path(origin, paths))
                if generated or frozen_source
                else code.co_filename,
                owner_source if generated else "",
            ))
            nonlocals: t.DictKV[str, t.Infra.NativeOperand] = (
                {
                    name: cell.cell_contents
                    for name, cell in zip(
                        code.co_freevars, value.__closure__, strict=True
                    )
                }
                if value.__closure__ is not None
                else {}
            )
            globals_used = tuple(
                value.__globals__[name]
                for name in value.__code__.co_names
                if name in value.__globals__
            )
            pending.extend(
                (f"{binding}.global.{name}", item, actual_supplier, owner_source)
                for name in code.co_names
                if (item := value.__globals__.get(name)) is not None
                and (
                    cls._is_class(item)
                    or type(item) in {FunctionType, BuiltinFunctionType, MethodType}
                )
            )
            wrapped = vars(value).get("__wrapped__")
            if wrapped is not None and not any(
                item is wrapped for item in (*nonlocals.values(), *globals_used)
            ):
                return r[m.Infra.NativeImportObservation].fail(
                    f"producer wrapper has no executable link: {binding}",
                )
            if wrapped is not None:
                pending.append((
                    f"{binding}.wrapped",
                    wrapped,
                    actual_supplier,
                    owner_source,
                ))
            evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=binding,
                    kind=kind,
                    supplier=actual_supplier,
                    name=value.__name__,
                    qualname=value.__qualname__,
                    code=cls._code_evidence(code).model_dump_json(),
                    operands=(
                        ("module", observe_value(value.__module__)),
                        (
                            "globals",
                            dumps(
                                tuple(
                                    (
                                        name,
                                        observe_value(
                                            item,
                                            construction=generated,
                                        ),
                                    )
                                    for name, item in sorted(global_bindings.items())
                                    if name not in operational_globals
                                )
                            ),
                        ),
                        ("defaults", observe_value(value.__defaults__)),
                        (
                            "keyword_defaults",
                            dumps(
                                tuple(
                                    (name, observe_value(item))
                                    for name, item in sorted(
                                        (value.__kwdefaults__ or {}).items()
                                    )
                                )
                            ),
                        ),
                        (
                            "closure",
                            dumps(
                                tuple(
                                    (name, observe_value(item))
                                    for name, item in sorted(nonlocals.items())
                                )
                            ),
                        ),
                        ("wrapped", cls._value(wrapped)),
                    ),
                ),
            )
        return r[m.Infra.NativeImportObservation].ok(
            m.Infra.NativeImportObservation(
                runtime=Path(sys.executable).resolve(),
                runtime_prefix=Path(sys.prefix).absolute(),
                modules=nominations,
                sources=tuple(sorted(sources)),
                bindings=tuple(sorted(evidence, key=lambda item: item.binding)),
            ),
        )

    @staticmethod
    def _binding_index(
        snapshot: m.Infra.NativeImportObservation,
    ) -> p.Result[t.DictKV[str, m.Infra.NativeBindingEvidence]]:
        """Index bindings and validate aliases after rejecting duplicates.

        Returns:
            The complete binding index, or its first validation failure.

        """
        result_type = r[t.DictKV[str, m.Infra.NativeBindingEvidence]]
        indexed: t.DictKV[str, m.Infra.NativeBindingEvidence] = {}
        for item in snapshot.bindings:
            if item.binding in indexed:
                return result_type.fail(
                    f"duplicate native binding: {item.binding}; "
                    f"supplier={item.supplier}; qualname={item.qualname}",
                )
            indexed[item.binding] = item
        for item in snapshot.bindings:
            if item.kind != "alias":
                continue
            if len(item.operands) != 1 or item.operands[0][0] != "target":
                return result_type.fail(
                    f"native alias lacks one target: {item.binding}; "
                    f"supplier={item.supplier}; qualname={item.qualname}",
                )
            target = indexed.get(item.operands[0][1])
            if (
                target is None
                or target.kind == "alias"
                or not target.binding.startswith("@")
                or not target.binding[1:].isdecimal()
            ):
                return result_type.fail(
                    f"native alias target is not a native body: "
                    f"{item.binding} -> {item.operands[0][1]}; "
                    f"supplier={item.supplier}; qualname={item.qualname}",
                )
        return result_type.ok(indexed)

    @staticmethod
    def compare(
        observed: m.Infra.NativeImportObservation,
        reference: m.Infra.NativeImportObservation,
    ) -> p.Result[bool]:
        """Compare complete native compiler witnesses without code deserialization.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if (
            observed.runtime != reference.runtime
            or observed.runtime_prefix != reference.runtime_prefix
        ):
            return r[bool].fail(
                f"native reference runtime differs: {observed.runtime} "
                f"!= {reference.runtime}; prefix={observed.runtime_prefix} "
                f"!= {reference.runtime_prefix}"
            )
        if observed.modules != reference.modules:
            return r[bool].fail("native reference elected module epoch differs")
        if observed.sources != reference.sources:
            extra = sorted(set(observed.sources).difference(reference.sources))
            missing = sorted(set(reference.sources).difference(observed.sources))
            return r[bool].fail(
                "native reference source epoch differs: "
                f"extra={extra[:1]} missing={missing[:1]}"
            )
        indexes: list[t.DictKV[str, m.Infra.NativeBindingEvidence]] = []
        for snapshot in (observed, reference):
            indexed = FlextInfraWorkspaceNativeReference._binding_index(snapshot)
            if indexed.failure:
                return r[bool].from_failure(indexed)
            indexes.append(indexed.value)
        actual, expected = indexes
        if expected.keys() != actual.keys():
            only_native = actual.keys() - expected.keys()
            only_imported = expected.keys() - actual.keys()
            identities: list[str] = []
            identity_fields = {"binding", "kind", "supplier", "name", "qualname"}
            for side, current, opposite, differing in (
                ("native", actual, expected, only_native),
                ("imported", expected, actual, only_imported),
            ):
                for binding in sorted(differing, key=lambda name: (len(name), name))[
                    :3
                ]:
                    item = current[binding]
                    parent = binding.rpartition(".")[0]
                    target = dict(item.operands).get("target", "")
                    context = tuple(
                        (
                            role,
                            candidate.model_dump_json(include=identity_fields)
                            if candidate is not None
                            else None,
                        )
                        for role, candidate in (
                            ("binding", item),
                            ("target_body", current.get(target)),
                            ("parent_body", current.get(parent)),
                            ("opposite_parent_body", opposite.get(parent)),
                        )
                    )
                    identities.append(f"side={side}; context={context}")
            return r[bool].fail(
                "producer executable binding inventory differs: "
                f"only_native_count={len(only_native)} "
                f"first={sorted(only_native, key=len)[:3]}; "
                f"only_imported_count={len(only_imported)} "
                f"first={sorted(only_imported, key=len)[:3]}; "
                f"identities={tuple(identities)}"
            )
        for item in observed.bindings:
            native = expected[item.binding]
            live = item.model_dump(exclude={"code", "operational"})
            cold = native.model_dump(exclude={"code", "operational"})
            if live != cold:
                operands = dict(item.operands)
                imported = dict(native.operands)
                return r[bool].fail(
                    f"producer native binding differs: {item.binding}; "
                    f"supplier={item.supplier}; qualname={item.qualname}; "
                    f"fields={
                        tuple(
                            key
                            for key in live
                            if key != 'operands' and live[key] != cold[key]
                        )
                    }; "
                    f"operands={
                        tuple(
                            sorted(
                                key
                                for key in operands.keys() | imported.keys()
                                if operands.get(key) != imported.get(key)
                            )
                        )
                    }; "
                    f"observed_kind={item.kind}; reference_kind={native.kind}; "
                    f"observed_target={operands.get('target')}; "
                    f"reference_target={imported.get('target')}"
                )
            if item.code is None or native.code is None:
                if item.code != native.code:
                    return r[bool].fail(
                        "producer native code presence differs: "
                        f"{item.binding}; "
                        f"supplier={item.supplier}; qualname={item.qualname}",
                    )
                continue
            actual_code = m.Infra.NativeCodeEvidence.model_validate_json(item.code)
            expected_code = m.Infra.NativeCodeEvidence.model_validate_json(native.code)
            if not FlextInfraWorkspaceNativeReference._code_matches(
                actual_code, expected_code
            ):
                live = actual_code.model_dump()
                cold = expected_code.model_dump()
                field = next((key for key in live if live[key] != cold[key]), None)
                witnesses = (actual_code.witness or b"", expected_code.witness or b"")
                pairs = zip(*witnesses, strict=False)
                offset = next(
                    (i for i, (a, b) in enumerate(pairs) if a != b),
                    min(map(len, witnesses)) if witnesses[0] != witnesses[1] else None,
                )
                return r[bool].fail(
                    "producer executed code differs from native import: "
                    f"{item.binding}; "
                    f"supplier={item.supplier}; qualname={item.qualname}; "
                    f"first_code_field={field}; "
                    f"witness_bytes={tuple(map(len, witnesses))}; "
                    f"first_witness_byte={offset}; "
                    f"observed_filename={actual_code.filename!r}; "
                    f"reference_filename={expected_code.filename!r}; "
                    f"observed_name={actual_code.name!r}; "
                    f"reference_name={expected_code.name!r}; "
                    f"observed_firstlineno={actual_code.firstlineno}; "
                    f"reference_firstlineno={expected_code.firstlineno}; "
                    f"observed_aliases={
                        tuple(
                            alias.binding
                            for alias in observed.bindings
                            if alias.kind == 'alias'
                            and alias.operands == (('target', item.binding),)
                        )
                    }; "
                    f"reference_aliases={
                        tuple(
                            alias.binding
                            for alias in reference.bindings
                            if alias.kind == 'alias'
                            and alias.operands == (('target', native.binding),)
                        )
                    }",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def authority_current(
        authority: m.Infra.CodegenSourceAuthority,
        *,
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Validate cold byte/membership authority without granting publication.

        Returns:
            Successful authority validation or the first changed input.

        """
        if not authority.inputs or authority.runtime not in {
            item.path for item in authority.inputs
        }:
            return r[bool].fail(
                "native source authority lacks its physical interpreter"
            )
        output_paths = {item.path for item in outputs}
        if outputs:
            for expected in outputs:
                state = codegen.FlextInfraMiseArtifactsFiles.read_state(
                    expected.path, required=expected.sha256 is not None
                )
                if state.failure:
                    return r[bool].from_failure(state)
                recorded = (
                    codegen.FlextInfraMiseArtifactsJournalRelocation.source_record(
                        expected.phase, state.value, previous=expected
                    )
                )
                if recorded.failure:
                    return r[bool].from_failure(recorded)
                if recorded.value != expected:
                    return r[bool].fail(
                        f"native authorized output changed: {expected.path}"
                    )
        for receipt in authority.inputs:
            if receipt.path in output_paths and receipt.path != authority.runtime:
                continue
            current = u.Cli.atomic_read_binary_file_receipt(
                receipt.path, required=receipt.device is not None
            )
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != receipt:
                return r[bool].fail(f"native source authority changed: {receipt.path}")

        return codegen.FlextInfraCodegenPreconditions.source_trees_current(
            authority.generator_trees,
            tuple(outputs),
            modules=authority.generator_modules,
        )

    @classmethod
    def _generated_binding_current(
        cls,
        binding: m.Infra.NativeBindingEvidence,
        executed: CodeType,
        states: t.MappingKV[Path, m.Cli.AtomicFileReceipt],
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[bool]:
        """Re-derive a generated witness against its pinned physical receipts."""
        result_type = r[bool]
        metadata = dict(binding.operands)
        attribute = metadata.get("generated_attribute")
        receiver_name = metadata.get("generated_receiver")
        if type(attribute) is not str or type(receiver_name) is not str:
            return result_type.fail(
                f"generated binding lacks its physical compiler receipt: {binding.binding}"
            )
        module = sys.modules.get(binding.supplier)
        if type(module) is not ModuleType:
            return result_type.fail("generated compiler supplier is not loaded")
        receiver = None
        if receiver_name:
            receiver = module
            for component in receiver_name.split("."):
                namespace = (
                    vars(receiver)
                    if type(receiver) is ModuleType
                    else cls._class_namespace(receiver)
                    if cls._is_class(receiver)
                    else None
                )
                if namespace is None or component not in namespace:
                    return result_type.fail(
                        "generated class has no registered physical receiver"
                    )
                receiver = namespace[component]
            if not cls._is_class(receiver):
                return result_type.fail("generated receiver is not a native class")
        namespace = vars(module) if receiver is None else cls._class_namespace(receiver)
        value = namespace.get(attribute)
        if cls._native_type(value, classmethod, staticmethod):
            value = value.__func__
        if type(value) is not FunctionType:
            return result_type.fail("generated receipt has no native function")
        proved = cls._generated_proof(
            value, binding.supplier, attribute, receiver, project, witnesses
        )
        if proved.failure:
            return result_type.from_failure(proved)
        _supplier, _attribute, expected = proved.value
        if (
            executed != expected.code
            or cls._code_locations(executed) != cls._code_locations(expected.code)
            or metadata.get("generated_inputs")
            != dumps(tuple(str(state.path) for state in expected.inputs))
        ):
            return result_type.fail(
                f"generated receipt differs from its physical compiler: {binding.binding}"
            )
        for state in expected.inputs:
            receipt = states.get(state.path)
            if receipt is None:
                return result_type.fail(
                    f"generated compiler input is not pinned: {state.path}"
                )
            measured = u.Cli.atomic_read_binary_file_receipt(state.path, required=True)
            if measured.failure:
                return result_type.from_failure(measured)
            if measured.value != receipt:
                return result_type.fail(
                    f"generated compiler receipt changed: {state.path}"
                )
            with u.Cli.atomic_binary_file_reader(receipt) as reader:
                if reader.read_range(0, receipt.size) != state.content:
                    return result_type.fail(
                        f"generated compiler source differs from its receipt: {state.path}"
                    )
        return result_type.ok(value=True)

    @classmethod
    def authored_sources_current(
        cls,
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
    ) -> p.Result[bool]:
        """Authenticate authored driver code before read-only reference staging.

        Generated descriptors require the isolated reference and are never
        reconstructed here. This proof alone cannot authorize publication.
        """
        states = {item.path: item for item in inputs}
        compiled: t.DictKV[str, t.VariadicTuple[t.Infra.NativeCode]] = {}
        admitted = 0
        for binding in observed.bindings:
            if binding.code is None:
                continue
            executed = m.Infra.NativeCodeEvidence.model_validate_json(binding.code)
            module = sys.modules[binding.supplier]
            frozen = module.__spec__.origin == "frozen"
            if executed.co_filename.startswith("<") and not frozen:
                continue
            key = binding.supplier if frozen else executed.filename
            if key not in compiled:
                if frozen:
                    root = FrozenImporter.get_code(module_spec.name)
                    if root is None:
                        return r[bool].fail(
                            f"frozen native supplier has no code: {module_spec.name}"
                        )
                else:
                    receipt = states.get(Path(executed.filename))
                    if receipt is None:
                        return r[bool].fail(
                            f"authored producer source is not pinned: "
                            f"{binding.binding}",
                        )
                    read = u.Cli.atomic_read_binary_file_state(
                        receipt.path, required=True
                    )
                    if read.failure:
                        return r[bool].from_failure(read)
                    state = read.value
                    verified = u.Cli.atomic_read_binary_file_receipt(
                        receipt.path, required=True
                    )
                    if verified.failure:
                        return r[bool].from_failure(verified)
                    if verified.value != receipt or state.content is None:
                        return r[bool].fail(f"authored source changed: {receipt.path}")
                    root = compile(
                        state.content,
                        executed.filename,
                        "exec",
                        dont_inherit=True,
                        optimize=sys.flags.optimize,
                    )
                compiled[key] = FlextInfraWorkspaceNativeReference._code_units(root)
            if executed.witness is None or not any(
                code.co_name == executed.name
                and code.co_firstlineno == executed.firstlineno
                and FlextInfraWorkspaceNativeReference._code_matches(
                    executed,
                    FlextInfraWorkspaceNativeReference._code_evidence(code),
                )
                for code in compiled[key]
            ):
                return r[bool].fail(
                    f"authored producer code differs from pinned native source: "
                    f"{binding.binding}",
                )
            admitted += 1
        if not admitted:
            return r[bool].fail("cold producer authority has no authored driver code")
        return r[bool].ok(value=True)
