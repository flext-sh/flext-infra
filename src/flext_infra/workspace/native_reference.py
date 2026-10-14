"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import marshal
import sys
from base64 import b64decode, b64encode
from dis import get_instructions
from gc import get_referents
from importlib.machinery import ExtensionFileLoader, FrozenImporter
from json import dumps
from pathlib import Path
from types import (
    BuiltinFunctionType,
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    GenericAlias,
    GetSetDescriptorType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodType,
    ModuleType,
    UnionType,
    WrapperDescriptorType,
)

from flext_infra import m, p, r, t, u
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)


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
            or vars(type)["__name__"].__get__(value, type(value))
            != binding.imported_name
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
            and type(specification.loader) is not ExtensionFileLoader
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class supplier is not an interpreter extension: {supplier}",
            )
        native_descriptors = (
            descriptor
            for descriptor in cls._class_namespace(value).values()
            if type(descriptor) in {
                MethodDescriptorType, ClassMethodDescriptorType,
                WrapperDescriptorType,
            }
        )
        if not any(
            descriptor.__objclass__ is value
            for descriptor in native_descriptors
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
    def _source_proof(
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
            value, receiver, supplier, attribute = pending.pop()
            identity = (id(value), id(receiver), attribute)
            if identity in visited:
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
                            value, qualified, captured.value,
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
        """Read registered native extension slots without authored accessors."""
        native = type(value)
        slots = cls._class_namespace(native)
        metadata: dict[str, str] = {}
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
            observed = descriptor.__get__(value, native)
            if type(observed) is not str:
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback metadata is not text: {attribute}",
                )
            metadata[attribute] = observed
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
    def _native_wrapper_kind(cls, value: p.AttributeProbe) -> str | None:
        """Identify exact interpreter wrapper types through their registered exports."""
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
        value: p.AttributeProbe,
        kind: str,
    ) -> p.Result[p.AttributeProbe]:
        """Read actual native callable slots, never the mutable __wrapped__ facade."""
        result_type = r[p.AttributeProbe]
        native = type(value)
        namespace = cls._class_namespace(native)
        if kind == "partial":
            slot = namespace.get("func")
            if (
                type(slot) is not MemberDescriptorType
                or slot.__objclass__ is not native
            ):
                return result_type.fail(
                    "native partial lacks its interpreter-owned function slot",
                )
            return result_type.ok(slot.__get__(value, native))
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        for supplier_name in ("gc", "_functools"):
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
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
        if (
            type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or get_referents.__module__ != "gc"
            or get_referents.__name__ != "get_referents"
            or sys.implementation.name != "cpython"
        ):
            return result_type.fail(
                "native wrapper topology has no admitted interpreter traversal",
            )
        storage = namespace.get("__dict__")
        if (
            type(storage) is not GetSetDescriptorType
            or storage.__objclass__ is not native
        ):
            return result_type.fail(
                "native cache wrapper lacks interpreter-owned dictionary storage",
            )
        attributes = storage.__get__(value, native)
        references = get_referents(value)
        # The native traversal exposes the function slot directly, separately
        # from the facade dictionary. Cached callable results can also be direct
        # referents: that shape is ambiguous and must fail instead of choosing a
        # referent by a version-specific traversal position.
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
        function = next(iter(functions.values()))
        if attributes.get("__wrapped__") is not function:
            return result_type.fail(
                "native cache wrapper facade differs from its executable function slot",
            )
        return result_type.ok(function)

    @classmethod
    def _callable_storage(cls, value: p.AttributeProbe) -> bool:
        """Find callback storage without asking the object for its attributes."""
        return any(
            "__call__" in cls._class_namespace(owner)
            for owner in vars(type)["__mro__"].__get__(
                type(value),
                type(type(value)),
            )
        )

    @classmethod
    def _native_cache_state(cls, value: p.AttributeProbe) -> p.Result[str]:
        """Retain observable cache data; reject opaque native links before callbacks."""
        result_type = r[str]
        native = type(value)
        namespace = cls._class_namespace(native)
        attributes = namespace["__dict__"].__get__(value, native)
        references = get_referents(value)
        caches = tuple(
            item for item in references if type(item) is dict and item is not attributes
        )
        if len(caches) != 1:
            return result_type.fail(
                "native cache state has no unique interpreter-owned dictionary",
            )
        link_types = tuple(
            item
            for item in references
            if cls._is_class(item)
            and cls._class_namespace(item).get("__module__") == "functools"
            and vars(type)["__qualname__"].__get__(item, type(item)) == "_lru_list_elem"
        )
        if any(
            type(item) is link_type
            for item in caches[0].values()
            for link_type in link_types
        ):
            return result_type.fail(
                "native cache state contains opaque link slots requiring "
                "admitted execution-owner observation",
            )
        return result_type.ok(cls._value(caches[0], construction=True))

    @staticmethod
    def _is_class(value: p.AttributeProbe) -> bool:
        """Recognize a class through native metaclass storage, never __class__."""
        return any(
            base is type
            for base in vars(type)["__mro__"].__get__(
                type(value),
                type(type(value)),
            )
        )

    @classmethod
    def _symbol(cls, value: p.AttributeProbe) -> str:
        if cls._is_class(value):
            module = vars(type)["__module__"].__get__(value, type(value))
            name = vars(type)["__qualname__"].__get__(value, type(value))
        elif type(value) in {FunctionType, BuiltinFunctionType}:
            module = value.__module__
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
    def _value(
        cls,
        value: p.AttributeProbe | None,
        seen: frozenset[int] = frozenset(),
        *,
        construction: bool = False,
    ) -> str:
        """Encode native value slots without authored repr/hash/equality callbacks."""
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
            return dumps(("cycle", cls._symbol(value)))
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
                tuple(
                    (name, cls._value(descriptor.__get__(value, CodeType), seen))
                    for name, descriptor in sorted(vars(CodeType).items())
                    if type(descriptor) in {MemberDescriptorType, GetSetDescriptorType}
                    and descriptor.__objclass__ is CodeType
                ),
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
                cls._value(value.__code__, seen),
                cls._value(value.__defaults__, seen, construction=construction),
                cls._value(value.__kwdefaults__, seen, construction=construction),
                cls._value(
                    tuple(cell.cell_contents for cell in value.__closure__ or ()),
                    seen,
                    construction=construction,
                ),
            ))
        if native is UnionType:
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
            + cls._symbol(native),
        )

    @staticmethod
    def _relocate_code(
        code: p.Infra.NativeCodeIdentity,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> p.Infra.NativeCodeIdentity:
        """Translate authenticated staging paths using native CodeType.replace."""
        filename = code.co_filename
        if not filename.startswith("<"):
            source = Path(filename)
            for staged, original in paths:
                if source.is_relative_to(staged):
                    filename = str(original / source.relative_to(staged))
                    break
        constants = tuple(
            FlextInfraWorkspaceNativeReference._relocate_code(value, paths)
            if isinstance(value, CodeType)
            else value
            for value in code.co_consts
        )
        return code.replace(co_filename=filename, co_consts=constants)

    @staticmethod
    def _source_path(
        source: Path,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> Path:
        for staged, original in paths:
            if source.is_relative_to(staged):
                return original / source.relative_to(staged)
        return source

    @staticmethod
    def _code_locations(code: p.Infra.NativeCodeIdentity) -> str:
        """Retain physical locations for every nested native compiler code unit."""
        return dumps((
            code.co_qualname,
            code.co_filename,
            code.co_firstlineno,
            b64encode(code.co_linetable).decode("ascii"),
            b64encode(code.co_exceptiontable).decode("ascii"),
            tuple(
                FlextInfraWorkspaceNativeReference._code_locations(value)
                for value in code.co_consts
                if type(value) is CodeType
            ),
        ))

    @classmethod
    def capture(
        cls,
        names: t.StrSequence,
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe the complete native epoch without reconstructing class factories."""
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        origins: dict[str, Path] = {}
        sources: set[t.Triple[str, str, str]] = set()
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
                    for instruction in get_instructions(function.__code__)
                    if instruction.opname == "STORE_GLOBAL"
                )
            evidence.extend(
                m.Infra.NativeBindingEvidence(
                    binding=f"{name}::{key}",
                    kind="boolean",
                    supplier=name,
                    name=key,
                    qualname=key,
                    operands=(("value", cls._value(value)),),
                )
                for key, value in sorted(vars(module).items())
                if type(value) is bool and key not in mutable_globals
            )
            pending.extend(
                (f"{name}::{key}", value, name, "")
                for key, value in sorted(vars(module).items())
                if cls._is_class(value)
                or type(value) in {FunctionType, BuiltinFunctionType, MethodType}
                or type(value) in {property, classmethod, staticmethod}
                or cls._callable_storage(value)
            )
        visited: dict[int, str] = {}
        while pending:
            binding, value, supplier, owner_source = pending.pop()
            if id(value) in visited:
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="alias",
                        supplier=supplier,
                        name="",
                        qualname="",
                        operands=(("target", visited[id(value)]),),
                    ),
                )
                continue
            visited[id(value)] = binding
            if cls._is_class(value):
                namespace = cls._class_namespace(value)
                actual_supplier = vars(type)["__module__"].__get__(
                    value,
                    type(value),
                )
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native source supplier: {binding}",
                    )
                origin = origins.get(actual_supplier)
                if origin is None:
                    observed = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                        actual_supplier,
                    )
                    if observed.failure:
                        # The supplier module sits outside this epoch's
                        # election (pyyaml C loaders, typing origins, ...):
                        # the binding is third-party alias evidence, and the
                        # supplier's own package owns its proof.
                        evidence.append(
                            m.Infra.NativeBindingEvidence(
                                binding=binding,
                                kind="alias",
                                supplier=supplier,
                                name="",
                                qualname="",
                                operands=(("target", actual_supplier),),
                            ),
                        )
                        continue
                    origin = origins[actual_supplier] = cls._source_path(
                        observed.value,
                        paths,
                    )
                source = str(origin)
                qualname = vars(type)["__qualname__"].__get__(value, type(value))
                sources.add((f"{actual_supplier}::{qualname}", source, ""))
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="class",
                        supplier=actual_supplier,
                        name=vars(type)["__name__"].__get__(value, type(value)),
                        qualname=qualname,
                        operands=(
                            ("metaclass", cls._symbol(type(value))),
                            (
                                "bases",
                                dumps(
                                    tuple(
                                        cls._symbol(base)
                                        for base in vars(type)["__bases__"].__get__(
                                            value,
                                            type(value),
                                        )
                                    )
                                ),
                            ),
                            (
                                "annotations",
                                cls._value(
                                    namespace.get("__annotations__"), construction=True
                                ),
                            ),
                            (
                                "dataclass_parameters",
                                cls._value(
                                    namespace.get("__dataclass_params__"),
                                    construction=True,
                                ),
                            ),
                            (
                                "dataclass_fields",
                                cls._value(
                                    namespace.get("__dataclass_fields__"),
                                    construction=True,
                                ),
                            ),
                            ("slots", cls._value(namespace.get("__slots__"))),
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
                        vars(type)["__bases__"].__get__(value, type(value))
                    )
                )
                continue
            if type(value) is MethodType:
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
            if type(value) is property:
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
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"native descriptor owner has no source supplier: {binding}",
                    )
                elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
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
                        kind=type(value).__name__,
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
                if type(
                    storage
                ) is not GetSetDescriptorType or storage.__objclass__ is not type(
                    value
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"native wrapper has no interpreter-owned attributes: "
                        f"{binding}",
                    )
                attributes = storage.__get__(value, type(value))
                operands = [
                    ("function", cls._value(function.value, construction=True)),
                    ("attributes", cls._value(attributes, construction=True)),
                ]
                operational = ()
                if wrapper_kind == "partial":
                    for attribute in ("args", "keywords"):
                        slot = namespace.get(attribute)
                        if type(
                            slot
                        ) is not MemberDescriptorType or slot.__objclass__ is not type(
                            value
                        ):
                            return r[m.Infra.NativeImportObservation].fail(
                                f"native partial lacks its {attribute} slot: {binding}",
                            )
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
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=f"{kind}:{wrapper_kind}",
                        supplier="_functools",
                        name=attributes.get("__name__", ""),
                        qualname=attributes.get("__qualname__", ""),
                        operands=tuple(operands),
                        operational=operational,
                    ),
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
                )
                continue
            if type(value) is not FunctionType:
                if type(value) is not BuiltinFunctionType:
                    extension = cls._extension_callback(value)
                    if extension.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(
                            extension
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
            else:
                actual_supplier = supplier
            origin = origins.get(actual_supplier)
            if origin is None:
                observed = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                    actual_supplier,
                )
                if observed.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(observed)
                origin = origins[actual_supplier] = cls._source_path(
                    observed.value,
                    paths,
                )
            sources.add((
                f"{actual_supplier}::{value.__qualname__}",
                str(origin) if generated else code.co_filename,
                owner_source if generated else "",
            ))
            nonlocals = dict(
                zip(
                    value.__code__.co_freevars,
                    (cell.cell_contents for cell in value.__closure__ or ()),
                    strict=True,
                )
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
                    code=b64encode(marshal.dumps(code)).decode("ascii"),
                    operands=(
                        ("module", cls._value(value.__module__)),
                        ("defaults", cls._value(value.__defaults__)),
                        (
                            "keyword_defaults",
                            dumps(
                                tuple(
                                    (name, cls._value(item))
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
                                    (name, cls._value(item))
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
                modules=tuple(names),
                sources=tuple(sorted(sources)),
                bindings=tuple(sorted(evidence, key=lambda item: item.binding)),
            ),
        )

    @staticmethod
    def compare(
        observed: m.Infra.NativeImportObservation,
        reference: m.Infra.NativeImportObservation,
    ) -> p.Result[bool]:
        """Compare executable code using CPython equality, never serialized hashes."""
        if (
            observed.runtime != reference.runtime
            or observed.runtime_prefix != reference.runtime_prefix
            or observed.modules != reference.modules
            or observed.sources != reference.sources
        ):
            return r[bool].fail("native reference epoch/runtime differs")
        expected = {item.binding: item for item in reference.bindings}
        if set(expected) != {item.binding for item in observed.bindings}:
            return r[bool].fail("producer executable binding inventory differs")
        for item in observed.bindings:
            native = expected[item.binding]
            if item.model_dump(exclude={"code"}) != native.model_dump(exclude={"code"}):
                return r[bool].fail(f"producer native binding differs: {item.binding}")
            if item.code is None or native.code is None:
                if item.code != native.code:
                    return r[bool].fail(
                        f"producer native code presence differs: {item.binding}"
                    )
                continue
            actual_code = marshal.loads(b64decode(item.code, validate=True))
            expected_code = marshal.loads(b64decode(native.code, validate=True))
            if (
                not isinstance(actual_code, CodeType)
                or not isinstance(expected_code, CodeType)
                or actual_code != expected_code
                or actual_code.co_filename != expected_code.co_filename
                or actual_code.co_firstlineno != expected_code.co_firstlineno
                or actual_code.co_linetable != expected_code.co_linetable
                or actual_code.co_exceptiontable != expected_code.co_exceptiontable
                or FlextInfraWorkspaceNativeReference._code_locations(actual_code)
                != FlextInfraWorkspaceNativeReference._code_locations(expected_code)
            ):
                return r[bool].fail(
                    f"producer executed code differs from native import: {item.binding}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def authority_current(
        authority: m.Infra.CodegenSourceAuthority,
        *,
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Validate cold byte/membership authority without granting publication."""
        if not authority.inputs or authority.runtime not in {
            item.path for item in authority.inputs
        }:
            return r[bool].fail(
                "native source authority lacks its physical interpreter"
            )
        output_paths = {item.path for item in outputs}
        if outputs:
            from flext_infra.codegen import (
                FlextInfraMiseArtifactsFiles,
                FlextInfraMiseArtifactsJournalRelocation,
            )

            for expected in outputs:
                state = FlextInfraMiseArtifactsFiles.read_state(
                    expected.path, required=expected.sha256 is not None
                )
                if state.failure:
                    return r[bool].from_failure(state)
                recorded = FlextInfraMiseArtifactsJournalRelocation.source_record(
                    expected.phase, state.value, previous=expected
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
            current = u.Cli.atomic_read_binary_file_receipt(receipt.path, required=True)
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != receipt:
                return r[bool].fail(f"native source authority changed: {receipt.path}")
        from flext_infra.codegen.codegen_preconditions import (
            FlextInfraCodegenPreconditions,
        )

        return FlextInfraCodegenPreconditions.source_trees_current(
            authority.generator_trees,
            outputs,
            modules=authority.generator_modules,
        )

    @staticmethod
    def authored_sources_current(
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
    ) -> p.Result[bool]:
        """Authenticate authored driver code before read-only reference staging.

        Generated descriptors require the isolated reference and are never
        reconstructed here. This proof alone cannot authorize publication.
        """
        states = {item.path: item for item in inputs}
        compiled: dict[str, tuple[CodeType, ...]] = {}
        admitted = 0
        for binding in observed.bindings:
            if binding.code is None:
                continue
            executed = marshal.loads(b64decode(binding.code, validate=True))
            if not isinstance(executed, CodeType):
                return r[bool].fail(f"producer code is not native: {binding.binding}")
            module = sys.modules[binding.supplier]
            frozen = module.__spec__.origin == "frozen"
            if executed.co_filename.startswith("<") and not frozen:
                continue
            key = binding.supplier if frozen else executed.co_filename
            if key not in compiled:
                if frozen:
                    root = FrozenImporter.get_code(module.__spec__.name)
                else:
                    receipt = states.get(Path(executed.co_filename))
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
                        executed.co_filename,
                        "exec",
                        dont_inherit=True,
                        optimize=sys.flags.optimize,
                    )
                pending = [root]
                codes = []
                while pending:
                    code = pending.pop()
                    codes.append(code)
                    pending.extend(
                        item for item in code.co_consts if isinstance(item, CodeType)
                    )
                compiled[key] = tuple(codes)
            if not any(
                code == executed
                and FlextInfraWorkspaceNativeReference._code_locations(code)
                == FlextInfraWorkspaceNativeReference._code_locations(executed)
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
