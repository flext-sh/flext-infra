"""Rope-owned source proof over one captured semantic and compiler epoch.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from importlib.machinery import ExtensionFileLoader, FrozenImporter
from pathlib import Path
from types import (
    BuiltinFunctionType,
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    GenericAlias,
    GetSetDescriptorType,
    MethodDescriptorType,
    ModuleType,
    UnionType,
    WrapperDescriptorType,
)

from flext_infra import m, p, r, t


class FlextInfraRopeSourceEpoch:
    """Own captured sources and native identities for one read-only invocation."""

    def __init__(
        self,
        project: p.Infra.RopeProject,
        *,
        module_source: p.Infra.NativeModuleSourceResolver,
        observer: p.Infra.NativeSourceObserver,
    ) -> None:
        self.project = project
        self.module_source = module_source
        self.observer = observer
        self.witnesses: dict[str, m.Infra.RopeSourceWitness] = {}
        self.generators: dict[t.Pair[int, str], p.AttributeProbe] = {}

    def witness(self, name: str) -> p.Result[m.Infra.RopeSourceWitness]:
        """Capture each supplier once; source bytes are compiled but never imported."""
        from flext_infra import u

        if name in self.witnesses:
            return r[m.Infra.RopeSourceWitness].ok(self.witnesses[name])
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            return r[m.Infra.RopeSourceWitness].fail(
                f"source supplier is not loaded: {name}",
            )
        elected = self.module_source(name)
        if elected.failure:
            return r[m.Infra.RopeSourceWitness].from_failure(elected)
        specification = vars(module)["__spec__"]
        source = (
            Path(specification.loader_state.filename).absolute()
            if specification.origin == "frozen"
            else elected.value
        )
        read = u.Cli.atomic_read_binary_file_state(source, required=True)
        if read.failure:
            return r[m.Infra.RopeSourceWitness].from_failure(read)
        if read.value.content is None:
            return r[m.Infra.RopeSourceWitness].fail(
                f"captured supplier source is absent: {source}",
            )
        resource = u.Infra.runtime_callable("rope.base.resources", "File")(
            u.Infra.runtime_callable("rope.base.project", "get_no_project")(),
            str(source),
        )
        if not isinstance(resource, p.Infra.RopeFile):
            msg = "Native source resource violates Rope's file contract"
            raise TypeError(msg)
        native = u.Infra.build_string_module(
            self.project,
            read.value.content.decode("utf-8"),
            resource=resource,
        )
        if not isinstance(native, p.Infra.RopeSourceModule):
            msg = "Native source module lost its shared semantic graph"
            raise TypeError(msg)
        root = native.get_scope()
        if not isinstance(root, p.Infra.RopeScope):
            msg = "Native module has no source scope"
            raise TypeError(msg)
        scopes: dict[str, p.Infra.RopeScope] = {}
        pending = [(root, "")]
        while pending:
            scope, qualified = pending.pop()
            previous = scopes.get(qualified)
            if previous is not None:
                if previous.get_kind() == "Function" and scope.get_kind() == "Function":
                    continue
                return r[m.Infra.RopeSourceWitness].fail(
                    f"class declaration is ambiguous: {name}::{qualified}",
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
                read.value.content,
                str(source),
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
        )
        if not isinstance(compiled, CodeType):
            msg = "Native source compiler returned no code object"
            raise TypeError(msg)
        witness = m.Infra.RopeSourceWitness(
            source=source,
            state=read.value,
            module=native,
            code=compiled,
            scopes=scopes,
            statements=u.Infra.logical_statements(native.source_code),
            finder=u.Infra.semantic_finder(native),
        )
        self.witnesses[name] = witness
        return r[m.Infra.RopeSourceWitness].ok(witness)

    @staticmethod
    def compiled(
        witness: m.Infra.RopeSourceWitness,
        executed: p.Infra.NativeCodeIdentity,
    ) -> p.Result[bool]:
        """Compare every native executable coordinate, not merely its filename."""
        pending = [witness.code]
        while pending:
            code = pending.pop()
            if (
                code == executed
                and code.co_filename == executed.co_filename
                and code.co_firstlineno == executed.co_firstlineno
                and code.co_linetable == executed.co_linetable
                and code.co_exceptiontable == executed.co_exceptiontable
            ):
                return r[bool].ok(value=True)
            pending.extend(
                item for item in code.co_consts if isinstance(item, CodeType)
            )
        return r[bool].fail(
            "executable differs from captured native compilation: "
            f"{executed.co_qualname}; source={witness.source}",
        )

    @staticmethod
    def scope_name(scope: p.Infra.RopeScope) -> str:
        components = []
        current = scope
        while current.parent is not None:
            components.append(current.pyobject.get_name())
            current = current.parent
            if current.get_kind() == "Function":
                components.append("<locals>")
        return ".".join(reversed(components))

    @staticmethod
    def capture_text(
        witness: m.Infra.RopeSourceWitness,
        match: p.Infra.RopeContractMatch,
        name: str,
    ) -> str:
        from flext_infra import u

        start, end = u.Infra.semantic_capture_region(match, name)
        return witness.module.source_code[start:end]

    def binding(
        self,
        scope: p.Infra.RopeScope,
        expression: str,
    ) -> p.Result[p.AttributeProbe]:
        """Bridge an elected lexical source identity through static runtime slots."""
        from flext_infra import u

        binding = u.Infra.expression_name(scope, expression)
        if binding is None:
            return r[p.AttributeProbe].fail(
                f"source expression has no native lexical identity: {expression}",
            )
        native = binding.get_object()
        if isinstance(native, p.Infra.RopeBuiltinClass):
            return r[p.AttributeProbe].ok(native.builtin)
        provider = native.get_module()
        scope = native.get_scope()
        if provider is None or scope is None:
            return r[p.AttributeProbe].fail(
                f"source expression has no physical declaration: {expression}",
            )
        module_name = provider.get_name()
        value = sys.modules.get(module_name)
        if type(value) is not ModuleType:
            return r[p.AttributeProbe].fail(
                f"source expression supplier is not loaded: {module_name}",
            )
        for name in self.scope_name(scope).split("."):
            namespace = (
                self.observer._class_namespace(value)
                if self.observer._is_class(value)
                else vars(value)
                if type(value) is ModuleType
                else None
            )
            if namespace is None or name not in namespace:
                return r[p.AttributeProbe].fail(
                    f"source declaration has no static runtime slot: {expression}",
                )
            value = namespace[name]
        if self.observer._is_class(value) and (
            vars(type)["__module__"].__get__(value, type(value)) != module_name
        ):
            return r[p.AttributeProbe].fail(
                f"source class supplier differs from native identity: {expression}",
            )
        return r[p.AttributeProbe].ok(value)

    def literal(
        self,
        expression: str,
        witness: m.Infra.RopeSourceWitness,
        scope: p.Infra.RopeScope,
        seen: frozenset[str] = frozenset(),
    ) -> p.Result[p.AttributeProbe | None]:
        """Resolve compiler-closed literals without access to authored callbacks."""
        from flext_infra import u

        code = compile(expression, str(witness.source), "eval", dont_inherit=True)
        if (
            not code.co_names
            and not code.co_freevars
            and not any(isinstance(item, CodeType) for item in code.co_consts)
        ):
            return r[p.AttributeProbe | None].ok(
                eval(code, {"__builtins__": {}}, {}),
            )
        if expression in seen:
            return r[p.AttributeProbe | None].fail("source literal alias cycle")
        binding = u.Infra.expression_name(scope, expression)
        if binding is None:
            return r[p.AttributeProbe | None].fail(
                f"default operand has no native source binding: {expression}",
            )
        native = binding.get_object()
        if isinstance(native, p.Infra.RopeBuiltinClass):
            return r[p.AttributeProbe | None].ok(native.builtin)
        supplier, _line = binding.get_definition_location()
        if supplier is None:
            return r[p.AttributeProbe | None].fail(
                f"default operand has no physical declaration: {expression}",
            )
        captured = self.witness(supplier.get_name())
        if captured.failure:
            return r[p.AttributeProbe | None].from_failure(captured)
        declared = captured.value
        target = expression.rsplit(".", 1)[-1]
        matches = []
        for pattern in (
            "${literal_name} = ${literal_value}",
            "${literal_name}: ${literal_annotation} = ${literal_value}",
        ):
            for match in declared.finder.get_matches(pattern):
                if self.capture_text(declared, match, "literal_name") != target:
                    continue
                start, _end = match.get_region()
                assignment_scope = u.Infra.scope_at(declared.module, start)
                if u.Infra.same_name(
                    binding,
                    u.Infra.expression_name(assignment_scope, target),
                ):
                    matches.append((match, assignment_scope))
        if len(matches) != 1:
            resolved = self.binding(scope, expression)
            if resolved.failure:
                return r[p.AttributeProbe | None].from_failure(resolved)
            if (
                self.observer._is_class(resolved.value)
                or type(resolved.value) is FunctionType
            ):
                return r[p.AttributeProbe | None].ok(resolved.value)
            return r[p.AttributeProbe | None].fail(
                f"default operand has no unique source value: {expression}",
            )
        match, assignment_scope = matches[0]
        return self.literal(
            self.capture_text(declared, match, "literal_value"),
            declared,
            assignment_scope,
            seen | {expression},
        )

    def fields(
        self,
        witness: m.Infra.RopeSourceWitness,
        scope: p.Infra.RopeScope,
    ) -> t.VariadicTuple[t.Triple[str, str, str | None]]:
        from flext_infra import u

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
                field_name = self.capture_text(witness, match, name)
                if field_name.isidentifier():
                    fields.append((
                        start,
                        field_name,
                        self.capture_text(witness, match, annotation),
                        None
                        if default is None
                        else self.capture_text(witness, match, default),
                    ))
        return tuple(
            (name, annotation, default)
            for _offset, name, annotation, default in sorted(fields)
        )

    def native_alias(
        self,
        value: p.AttributeProbe,
        name: str,
        witness: m.Infra.RopeSourceWitness,
    ) -> p.Result[t.Triple[str, str, str]]:
        binding = witness.module.get_attributes().get(name)
        if not isinstance(binding, p.Infra.RopeImportedName):
            return r[t.Triple[str, str, str]].fail(
                f"native class has no source import declaration: {name}",
            )
        native = binding.get_object()
        if (
            not isinstance(native, p.Infra.RopeBuiltinClass)
            or native.builtin is not value
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class differs from imported semantic identity: {name}",
            )
        supplier = binding.imported_module.module_name
        exported = sys.modules.get(supplier)
        if (
            type(exported) is not ModuleType
            or vars(exported).get(
                binding.imported_name,
            )
            is not value
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class has no registered export identity: {name}",
            )
        elected = self.module_source(supplier)
        if elected.failure:
            return r[t.Triple[str, str, str]].from_failure(elected)
        specification = vars(exported)["__spec__"]
        if specification.origin not in {"built-in", "frozen"} and (
            type(specification.loader) is not ExtensionFileLoader
        ):
            return r[t.Triple[str, str, str]].fail(
                f"native class supplier is not an interpreter extension: {supplier}",
            )
        namespace = self.observer._class_namespace(value)
        if not any(
            descriptor.__objclass__ is value
            for descriptor in namespace.values()
            if any(
                type(descriptor) is kind
                for kind in (
                    MethodDescriptorType,
                    ClassMethodDescriptorType,
                    WrapperDescriptorType,
                )
            )
        ) or any(type(item) is FunctionType for item in namespace.values()):
            return r[t.Triple[str, str, str]].fail(
                f"native class has no interpreter-owned descriptor shape: {name}",
            )
        return r[t.Triple[str, str, str]].ok((
            f"{supplier}::{binding.imported_name}",
            str(elected.value),
            str(witness.source),
        ))

    def native_factory(self, module_name: str, name: str) -> p.Result[p.AttributeProbe]:
        captured = self.witness(module_name)
        if captured.failure:
            return r[p.AttributeProbe].from_failure(captured)
        namespace = vars(sys.modules[module_name])
        factory = namespace.get(name)
        if type(factory) is not FunctionType:
            return r[p.AttributeProbe].fail(
                f"native compiler binding is not a physical function: {module_name}.{name}",
            )
        proof = self.compiled(captured.value, factory.__code__)
        if proof.failure:
            return r[p.AttributeProbe].from_failure(proof)
        for key, value in namespace.items():
            if not self.observer._is_class(value) or key not in captured.value.scopes:
                continue
            if (
                vars(type)["__module__"].__get__(value, type(value)) != module_name
                or vars(type)["__qualname__"].__get__(value, type(value)) != key
            ):
                return r[p.AttributeProbe].fail(
                    f"native compiler construction class differs: {module_name}.{key}",
                )
            for descriptor in self.observer._class_namespace(value).values():
                function = (
                    descriptor.__func__
                    if type(descriptor) is classmethod
                    or type(descriptor) is staticmethod
                    else descriptor
                )
                if type(function) is FunctionType:
                    checked = self.compiled(captured.value, function.__code__)
                    if checked.failure:
                        return r[p.AttributeProbe].from_failure(checked)
        return r[p.AttributeProbe].ok(factory)

    def defaults(
        self,
        function: p.AttributeProbe,
        witness: m.Infra.RopeSourceWitness,
    ) -> p.Result[bool]:
        """Read header operands once with native Rope, using compiled parameter order."""
        if type(function) is not FunctionType:
            return r[bool].fail("source defaults have no native function")
        code = function.__code__
        scope = witness.scopes.get(code.co_qualname)
        if scope is None or scope.parent is None:
            if function.__defaults__ is None and function.__kwdefaults__ is None:
                return r[bool].ok(value=True)
            return r[bool].fail(
                f"source default declaration is unresolved: {code.co_qualname}",
            )
        header = next(
            item for item in witness.statements if item.line == scope.get_start()
        )
        words = u.Infra.runtime_callable("rope.base.worder", "Worder")(
            witness.module.source_code,
        )
        prefix = (
            "async def " if header.text.lstrip().startswith("async def ") else "def "
        )
        offset = header.start_offset + header.indent + len(prefix)
        _name_start, name_end = words.get_word_range(offset)
        suffix = witness.module.source_code[name_end : header.end_offset].lstrip()
        if suffix.startswith("["):
            _type_start, name_end = words.get_word_parens_range(
                offset,
                opening="[",
                closing="]",
            )
        first, last = words.get_word_parens_range(name_end - 1)
        _arguments, default_sources = words.get_parameters(first, last - 1)
        sources = dict(default_sources)
        positional = code.co_varnames[: code.co_argcount]
        keyword_only = code.co_varnames[
            code.co_argcount : code.co_argcount + code.co_kwonlyargcount
        ]
        expected_positional = []
        expected_keywords = {}
        for name in (*positional, *keyword_only):
            source = sources.get(name)
            if source is None:
                continue
            operand = self.literal(source, witness, scope.parent)
            if operand.failure:
                return r[bool].from_failure(operand)
            if name in positional:
                expected_positional.append(operand.value)
            else:
                expected_keywords[name] = operand.value
        actual_positional = function.__defaults__ or ()
        actual_keywords = function.__kwdefaults__ or {}
        if len(expected_positional) != len(actual_positional) or (
            set(expected_keywords) != set(actual_keywords)
        ):
            return r[bool].fail(
                f"source default layout differs: {code.co_qualname}",
            )
        if any(
            self.observer._value(expected, construction=True)
            != self.observer._value(actual, construction=True)
            for expected, actual in (
                *zip(expected_positional, actual_positional, strict=True),
                *(
                    (expected_keywords[name], actual_keywords[name])
                    for name in expected_keywords
                ),
            )
        ):
            return r[bool].fail(
                f"source default operand differs: {code.co_qualname}",
            )
        return r[bool].ok(value=True)

    def pure_annotation(self, value: p.AttributeProbe) -> p.Result[bool]:
        """Reject authored annotation hooks before native compiler operations."""
        pending = [value]
        visited = set()
        while pending:
            item = pending.pop()
            if id(item) in visited:
                continue
            visited.add(id(item))
            if self.observer._is_class(item):
                metaclass = type(item)
                for hook in ("__getattribute__", "__hash__", "__eq__"):
                    actual = next(
                        (
                            self.observer._class_namespace(base)[hook]
                            for base in vars(type)["__mro__"].__get__(
                                metaclass, type(metaclass)
                            )
                            if hook in self.observer._class_namespace(base)
                        ),
                        None,
                    )
                    expected = next(
                        (
                            self.observer._class_namespace(base)[hook]
                            for base in vars(type)["__mro__"].__get__(type, type)
                            if hook in self.observer._class_namespace(base)
                        ),
                        None,
                    )
                    if actual is not expected:
                        return r[bool].fail(
                            f"annotation operand declares an authored {hook} callback",
                        )
                continue
            native = type(item)
            if native is UnionType:
                pending.extend(vars(UnionType)["__args__"].__get__(item, UnionType))
            elif any(
                base is GenericAlias
                for base in vars(type)["__mro__"].__get__(native, type(native))
            ):
                pending.extend(vars(GenericAlias)["__args__"].__get__(item, native))
            else:
                storage = next(
                    (
                        self.observer._class_namespace(base)["__dict__"]
                        for base in vars(type)["__mro__"].__get__(native, type(native))
                        if "__dict__" in self.observer._class_namespace(base)
                        and type(self.observer._class_namespace(base)["__dict__"])
                        is GetSetDescriptorType
                    ),
                    None,
                )
                if storage is not None:
                    namespace = storage.__get__(item, native)
                    if type(namespace) is dict:
                        arguments = namespace.get("__args__")
                        if type(arguments) is tuple:
                            pending.extend(arguments)
        return r[bool].ok(value=True)

    def generated(
        self,
        owner: p.AttributeProbe,
        attribute: str,
    ) -> p.Result[p.AttributeProbe]:
        """Materialize only proved native compilers, never an authored class body."""
        from flext_infra import u

        module_name = vars(type)["__module__"].__get__(owner, type(owner))
        captured = self.witness(module_name)
        if captured.failure:
            return r[p.AttributeProbe].from_failure(captured)
        witness = captured.value
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        scope = witness.scopes.get(qualified)
        if scope is None:
            return r[p.AttributeProbe].fail(
                f"generated method has no physical class declaration: {qualified}",
            )
        namespace = self.observer._class_namespace(owner)
        fields = self.fields(witness, scope)
        if "_fields" in namespace:
            names = tuple(name for name, _annotation, _default in fields)
            if self.observer._value(namespace["_fields"], construction=True) != (
                self.observer._value(names, construction=True)
            ):
                return r[p.AttributeProbe].fail("native tuple field layout differs")
            defaults = []
            for _name, _annotation, expression in fields:
                if expression is None:
                    if defaults:
                        return r[p.AttributeProbe].fail(
                            "native tuple required field follows a default",
                        )
                    continue
                default = self.literal(expression, witness, scope)
                if default.failure:
                    return r[p.AttributeProbe].from_failure(default)
                defaults.append(default.value)
            factory = self.native_factory("collections", "namedtuple")
            if factory.failure:
                return r[p.AttributeProbe].from_failure(factory)
            emitted = factory.value(
                vars(type)["__name__"].__get__(owner, type(owner)),
                names,
                defaults=defaults,
                module=module_name,
            )
        elif "__dataclass_fields__" in namespace:
            factory = self.native_factory("dataclasses", "make_dataclass")
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
                decorator = self.binding(scope.parent, expression.partition("(")[0])
                if decorator.failure:
                    return r[p.AttributeProbe].from_failure(decorator)
                if decorator.value is not vars(compiler)["dataclass"]:
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
                        option = self.literal(source, witness, scope.parent)
                        if option.failure:
                            return r[p.AttributeProbe].from_failure(option)
                        options[key] = option.value
            if not elected:
                return r[p.AttributeProbe].fail(
                    "dataclass has no source compiler identity"
                )
            annotations = namespace.get("__annotations__")
            if type(annotations) is not dict:
                return r[p.AttributeProbe].fail(
                    "dataclass has no native annotation storage"
                )
            specifications = []
            for name, _annotation, expression in fields:
                if name not in annotations:
                    return r[p.AttributeProbe].fail("dataclass source field is absent")
                admitted = self.pure_annotation(annotations[name])
                if admitted.failure:
                    return r[p.AttributeProbe].from_failure(admitted)
                if expression is None:
                    specifications.append((name, annotations[name]))
                    continue
                default = self.literal(expression, witness, scope)
                if default.failure:
                    return r[p.AttributeProbe].from_failure(default)
                specifications.append((
                    name,
                    annotations[name],
                    vars(compiler)["field"](default=default.value),
                ))
            preserved = {}
            for name, descriptor in namespace.items():
                function = (
                    descriptor.__func__
                    if type(descriptor) is classmethod
                    or type(descriptor) is staticmethod
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
                f"generated method has no proved native compiler: {qualified}.{attribute}",
            )
        descriptor = self.observer._class_namespace(emitted).get(attribute)
        if descriptor is None:
            return r[p.AttributeProbe].fail(
                "native compiler emitted no matching method"
            )
        return r[p.AttributeProbe].ok(descriptor)

    def verify(
        self, names: t.StrSequence
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        from flext_infra import u

        result = r[t.SequenceOf[t.Triple[str, str, str]]]
        sources = set()
        pending = []
        for name in names:
            module = sys.modules.get(name)
            if type(module) is not ModuleType:
                return result.fail(f"source namespace is not loaded: {name}")
            elected = self.module_source(name)
            if elected.failure:
                return result.from_failure(elected)
            sources.add((name, str(elected.value), ""))
            pending.extend(
                (value, None, name, key)
                for key, value in vars(module).items()
                if self.observer._is_class(value)
                or any(
                    type(value) is kind
                    for kind in (
                        FunctionType,
                        BuiltinFunctionType,
                        property,
                        classmethod,
                        staticmethod,
                    )
                )
                or self.observer._native_wrapper_kind(value) is not None
            )
        visited = set()
        while pending:
            value, receiver, supplier, attribute = pending.pop()
            key = (id(value), id(receiver), attribute)
            if key in visited:
                continue
            visited.add(key)
            if self.observer._is_class(value):
                namespace = self.observer._class_namespace(value)
                module_name = vars(type)["__module__"].__get__(value, type(value))
                if type(module_name) is not str:
                    return result.fail("class supplier is not native text")
                elected = self.module_source(module_name)
                if elected.failure:
                    return result.from_failure(elected)
                qualified = vars(type)["__qualname__"].__get__(value, type(value))
                sources.add((f"{module_name}::{qualified}", str(elected.value), ""))
                specification = vars(sys.modules[module_name])["__spec__"]
                if specification.origin not in {"built-in", "frozen"} and str(
                    elected.value
                ).endswith(".py"):
                    captured = self.witness(module_name)
                    if captured.failure:
                        return result.from_failure(captured)
                    if qualified not in captured.value.scopes:
                        alias = self.native_alias(value, qualified, captured.value)
                        if alias.failure:
                            return result.from_failure(alias)
                        sources.add(alias.value)
                        continue
                    pending.extend(
                        (item, value, module_name, name)
                        for name, item in namespace.items()
                        if self.observer._is_class(item)
                        or any(
                            type(item) is kind
                            for kind in (
                                FunctionType,
                                BuiltinFunctionType,
                                property,
                                classmethod,
                                staticmethod,
                            )
                        )
                        or self.observer._native_wrapper_kind(item) is not None
                    )
                    pending.extend(
                        (base, None, module_name, "")
                        for base in vars(type)["__bases__"].__get__(value, type(value))
                    )
                continue
            kind = self.observer._native_wrapper_kind(value)
            if kind is not None:
                function = self.observer._native_wrapper_function(value, kind)
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
            if type(value) is classmethod or type(value) is staticmethod:
                value = value.__func__
            if type(value) is BuiltinFunctionType:
                continue
            if type(value) is not FunctionType:
                return result.fail("source descriptor is not a native function")
            module_name = value.__globals__.get("__name__")
            if type(module_name) is not str:
                module_name = supplier
            captured = self.witness(module_name)
            if captured.failure:
                return result.from_failure(captured)
            code = value.__code__
            generated = code.co_filename.startswith(
                "<"
            ) and not code.co_filename.startswith("<frozen ")
            if generated:
                if receiver is None:
                    return result.fail("generated function has no declaration receiver")
                generator_key = (id(receiver), attribute)
                if generator_key not in self.generators:
                    generated_method = self.generated(receiver, attribute)
                    if generated_method.failure:
                        return result.from_failure(generated_method)
                    self.generators[generator_key] = generated_method.value
                expected = self.generators[generator_key]
                if type(expected) is classmethod or type(expected) is staticmethod:
                    expected = expected.__func__
                while (
                    type(expected) is FunctionType
                    and expected.__code__.co_qualname != code.co_qualname
                ):
                    expected = vars(expected).get("__wrapped__")
                if type(expected) is not FunctionType or (
                    expected.__code__.replace(co_firstlineno=0)
                    != code.replace(co_firstlineno=0)
                    or self.observer._value(expected.__defaults__, construction=True)
                    != self.observer._value(value.__defaults__, construction=True)
                    or self.observer._value(expected.__kwdefaults__, construction=True)
                    != self.observer._value(value.__kwdefaults__, construction=True)
                    or self.observer._value(
                        tuple(
                            cell.cell_contents for cell in expected.__closure__ or ()
                        ),
                        construction=True,
                    )
                    != self.observer._value(
                        tuple(cell.cell_contents for cell in value.__closure__ or ()),
                        construction=True,
                    )
                ):
                    return result.fail(
                        f"generated executable differs from native compiler: {code.co_qualname}"
                    )
            else:
                authenticated = self.compiled(captured.value, code)
                if authenticated.failure:
                    return result.from_failure(authenticated)
                defaults = self.defaults(value, captured.value)
                if defaults.failure:
                    return result.from_failure(defaults)
                if receiver is not None:
                    receiver_module = vars(type)["__module__"].__get__(
                        receiver, type(receiver)
                    )
                    receiver_source = self.witness(receiver_module)
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
                        self.scope_name(expected_scope) != code.co_qualname
                        or expected_scope.pyobject.get_module().get_name()
                        != module_name
                    ):
                        return result.fail(
                            f"descriptor differs from its source owner: {qualified}.{attribute}"
                        )
            wrapped = vars(value).get("__wrapped__")
            if wrapped is not None:
                if not any(
                    cell.cell_contents is wrapped for cell in value.__closure__ or ()
                ):
                    return result.fail("wrapper has no native executable closure link")
                pending.append((wrapped, receiver, module_name, attribute))
            sources.add((
                f"{module_name}::{code.co_qualname}",
                str(captured.value.source) if generated else code.co_filename,
                str(captured.value.source) if generated else "",
            ))
        for witness in self.witnesses.values():
            current = u.Cli.atomic_read_binary_file_state(witness.source, required=True)
            if current.failure:
                return result.from_failure(current)
            if current.value != witness.state:
                return result.fail(
                    f"source changed during semantic observation: {witness.source}"
                )
        return result.ok(tuple(sorted(sources)))


class FlextInfraUtilitiesRopeRuntimeSourceProof:
    """Compose native source proof into the existing Rope runtime utilities."""

    @staticmethod
    def source_proof(
        names: t.StrSequence,
        *,
        module_source: p.Infra.NativeModuleSourceResolver,
        observer: p.Infra.NativeSourceObserver,
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        from flext_infra import u

        with u.Infra.open_import_project(Path.cwd()) as project:
            return FlextInfraRopeSourceEpoch(
                project,
                module_source=module_source,
                observer=observer,
            ).verify(names)


__all__ = ["FlextInfraUtilitiesRopeRuntimeSourceProof"]
