"""Closed source-template witnesses for module-level generated functions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import sys
from pathlib import Path
from types import (
    BuiltinFunctionType,
    CodeType,
    FunctionType,
    GetSetDescriptorType,
    MemberDescriptorType,
    MethodDescriptorType,
    ModuleType,
    WrapperDescriptorType,
)
from typing import TypeIs

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)


class FlextInfraWorkspaceGeneratedFunction:
    """Interpret a closed compiler's data without invoking its Python callbacks."""

    def __init__(self, witness: m.Infra.NativeSourceWitness) -> None:
        """Keep all observations local to the current immutable source witness."""
        self._witness = witness
        self._inputs: dict[Path, m.Cli.AtomicFileState] = {
            witness.source: witness.state,
        }
        self._trees: dict[Path, ast.Module] = {
            witness.source: ast.parse(
                witness.module.source_code,
                filename=str(witness.source),
            ),
        }
        self._codes: dict[Path, p.Infra.NativeCodeIdentity] = {
            witness.source: witness.code,
        }
        self._emitted: dict[int, m.Infra.NativeGeneratedFunctionProof] = {}
        self._dictionaries: set[int] = set()
        self._patterns: dict[int, str] = {}

    @classmethod
    def compile(
        cls,
        value: FunctionType,
        supplier: str,
        attribute: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Derive one emitted function from a unique physical literal invocation.

        No compiler factory, generated source, descriptor hook, or module hook
        executes here. Unsupported grammar raises its original ``ValueError``.

        Returns:
            Expected code, globals, annotations and consulted physical inputs.

        Raises:
            TypeError: If the observed export is not a native Python function.
            ValueError: If a source binding or closed compiler grammar is unproved.

        """
        engine = cls(witness)
        namespace = engine._module(supplier)
        if type(value) is not FunctionType:
            msg = "generated function is not its registered source export"
            raise TypeError(msg)
        if vars(namespace).get(attribute) is not value:
            msg = "generated function is not its registered source export"
            raise ValueError(msg)
        matches = engine._physical_invocations(
            "${export} = ${factory}(${first}, ${second})",
            ("export", "factory", "first", "second"),
            (attribute,),
        )
        if len(matches) != 1:
            msg = "generated function has no unique physical literal factory call"
            raise ValueError(msg)
        invocation = matches[0]
        factory_name = invocation["factory"]
        if not factory_name.isidentifier():
            msg = "generated function factory is not a direct source binding"
            raise ValueError(msg)
        factory = vars(namespace).get(factory_name)
        if type(factory) is not FunctionType or factory.__globals__ is not vars(
            namespace
        ):
            msg = "generated function factory has a foreign execution namespace"
            raise ValueError(msg)
        function, tree, globals_ = engine._function(factory)
        if Path(factory.__code__.co_filename) != witness.source:
            msg = "generated function factory is outside its physical declaration"
            raise ValueError(msg)
        local = engine._compiler_arguments(function, invocation)
        returned = engine._statements(function.body, local, globals_, tree)
        if (
            type(returned) is not CodeType
            or id(returned) not in engine._emitted
            or len(engine._emitted) != 1
        ):
            msg = "closed compiler did not return its sole emitted function"
            raise ValueError(msg)
        proof = engine._emitted[id(returned)]
        if returned.co_name != attribute or value.__name__ != attribute:
            msg = "generated function name differs from its physical export"
            raise ValueError(msg)
        engine._inputs_current("generated compiler source changed")
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            proof.model_copy(update={"inputs": tuple(engine._inputs.values())}),
        )

    def _inputs_current(self, changed_message: str) -> None:
        """Revalidate every consulted full physical snapshot before returning proof.

        Raises:
            ValueError: If any source bytes, mode or identity changed.

        """
        for state in self._inputs.values():
            current = u.Cli.atomic_read_binary_file_state(
                state.path,
                required=True,
            ).unwrap()
            if current != state:
                msg = f"{changed_message}: {state.path}"
                raise ValueError(msg)

    def _physical_invocations(
        self,
        pattern: str,
        names: t.StrSequence,
        exports: t.StrSequence,
    ) -> t.VariadicTuple[t.MappingKV[str, str]]:
        """Read exact module-level factory operands through the retained Rope witness.

        Returns:
            Captured physical operands for the requested registered exports.

        """
        captured: list[t.MappingKV[str, str]] = []
        for match in self._witness.finder.get_matches(pattern, {}):
            first, _last = match.get_region()
            scope = u.Infra.scope_at(self._witness.module, first)
            if scope.get_kind() != "Module":
                continue
            operands: t.DictKV[str, str] = {}
            for name in names:
                start, end = u.Infra.semantic_capture_region(match, name)
                operands[name] = self._witness.module.source_code[start:end]
            if operands["export"] in exports:
                captured.append(operands)
        return tuple(captured)

    @staticmethod
    def _compiler_arguments(
        function: ast.FunctionDef,
        invocation: t.MappingKV[str, str],
    ) -> t.DictKV[str, p.AttributeProbe]:
        """Bind the factory's two physical string literals without evaluating them.

        Returns:
            The literal locals of the closed compiler.

        Raises:
            ValueError: If parameters or invocation operands are unsupported.

        """
        match (*function.args.posonlyargs, *function.args.args):
            case (first, second):
                arguments = (first, second)
            case _:
                msg = (
                    "generated function compiler requires two closed literal parameters"
                )
                raise ValueError(msg)
        if (
            function.args.kwonlyargs
            or function.args.vararg is not None
            or function.args.kwarg is not None
            or function.args.defaults
            or function.args.kw_defaults
        ):
            msg = "generated function compiler requires two closed literal parameters"
            raise ValueError(msg)
        literals = tuple(
            ast.parse(invocation[name], mode="eval").body
            for name in ("first", "second")
        )
        local: t.DictKV[str, p.AttributeProbe] = {}
        for argument, literal in zip(arguments, literals, strict=True):
            if not isinstance(literal, ast.Constant) or type(literal.value) is not str:
                msg = (
                    "generated function compiler arguments are not exact "
                    "string literals"
                )
                raise ValueError(msg)
            local[argument.arg] = literal.value
        return local

    @staticmethod
    def function_chain(
        value: t.Infra.NativeOperand | None,
    ) -> t.VariadicTuple[FunctionType]:
        """Read a slot function and its raw wrapped functions without hooks.

        Returns:
            The slot function followed by every raw ``__wrapped__`` function.

        Raises:
            ValueError: If the raw wrapper chain is cyclic.

        """
        if type(value) is classmethod or type(value) is staticmethod:
            value = value.__func__
        functions: list[FunctionType] = []
        seen: set[int] = set()
        while type(value) is FunctionType:
            if id(value) in seen:
                msg = "generated receiver function wrapper chain is cyclic"
                raise ValueError(msg)
            seen.add(id(value))
            functions.append(value)
            value = vars(value).get("__wrapped__")
        return tuple(functions)

    def _dataclass_emission(
        self,
        value: FunctionType,
        owner: p.AttributeProbe,
        attribute: str,
        receivers: t.Pair[p.AttributeProbe, p.AttributeProbe],
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Select the SDK emission at the observed slot position as the proof.

        Returns:
            The emitted function's code, metadata and consulted physical inputs.

        Raises:
            ValueError: If options or the emitted wrapper chain differ.

        """
        fresh, emitted_owner = receivers
        sdk = vars(self._module("dataclasses"))
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        emitted_namespace = vars(type)["__dict__"].__get__(
            emitted_owner, type(emitted_owner)
        )
        params = namespace.get("__dataclass_params__")
        emitted_params = emitted_namespace.get("__dataclass_params__")
        if (
            type(params) is not sdk.get("_DataclassParams")
            or type(emitted_params) is not sdk.get("_DataclassParams")
            or repr(emitted_params) != repr(params)
        ):
            msg = "native dataclass options differ from the physical declaration"
            raise ValueError(msg)
        observed = self.function_chain(namespace.get(attribute))
        emitted = self.function_chain(emitted_namespace.get(attribute))
        positions = [index for index, item in enumerate(observed) if item is value]
        if len(positions) != 1 or len(observed) != len(emitted):
            msg = "native dataclass emission differs from the observed receiver slot"
            raise ValueError(msg)
        function = emitted[positions[0]]
        closure = tuple(
            owner
            if cell.cell_contents is emitted_owner or cell.cell_contents is fresh
            else cell.cell_contents
            for cell in function.__closure__ or ()
        )
        self._inputs_current("native dataclass compiler input changed")
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=function.__code__,
                globals=function.__globals__,
                annotations=dict(function.__annotations__),
                defaults=function.__defaults__,
                keyword_defaults=function.__kwdefaults__,
                closure=closure,
                inputs=tuple(self._inputs.values()),
            ),
        )

    @classmethod
    def compile_class_function(
        cls,
        value: FunctionType,
        owner: p.AttributeProbe,
        attribute: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Prove one class emission without repeating authored construction.

        Only authenticated SDK compilers may receive closed source data and a
        fresh exact-type receiver. Authored class bodies, bases, metaclasses,
        decorators, constructors and default factories are never invoked.

        Returns:
            The source-derived code, metadata and every consulted physical input.

        Raises:
            ValueError: If the class has no native qualified source identity.

        """
        engine = cls(witness)
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        if type(qualified) is not str:
            msg = "generated class has no native qualified source identity"
            raise ValueError(msg)
        invocation = engine._tuple_invocation(owner, witness)
        declaration = engine._tuple_declaration(
            qualified, namespace, attribute, invocation
        )
        factory = (
            engine._dataclass_factory(declaration) if declaration is not None else None
        )
        if factory is not None and declaration is not None:
            return engine._compile_dataclass(
                value, owner, attribute, declaration, factory
            )
        return engine._compile_named_tuple(owner, attribute)

    def _compile_named_tuple(
        self,
        owner: p.AttributeProbe,
        attribute: str,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Compile the physical native tuple lambda from its declared field layout.

        Returns:
            Source-derived constructor code, metadata and authenticated inputs.

        Raises:
            TypeError: If a closed constructor operand has an unsupported native type.
            ValueError: If the declaration or native constructor witness differs.

        """
        if type(attribute) is not str:
            msg = "native tuple source proof supports only its generated constructor"
            raise TypeError(msg)
        if attribute != "__new__":
            msg = (
                "native tuple source proof supports only its generated constructor; "
                + self._tuple_constructor_diagnostic(owner, attribute, self._witness)
            )
            raise ValueError(msg)
        engine = self
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        if type(qualified) is not str:
            msg = "native tuple owner has no exact string qualified identity"
            raise ValueError(msg)
        invocation = engine._tuple_invocation(owner, self._witness)
        declaration = engine._tuple_declaration(
            qualified, namespace, attribute, invocation
        )
        operands = engine._tuple_inputs(declaration, namespace, invocation)
        compiler = engine._function(
            vars(engine._module("collections")).get("namedtuple")
        )
        engine._builtin("eval", compiler[2])
        emission = engine._tuple_emission(compiler[0], attribute)
        local = engine._tuple_normalization(
            compiler,
            operands,
            emission[0],
        )
        engine._tuple_field_layout(local[compiler[0].args.args[1].arg], namespace)
        engine._tuple_code_inputs(compiler, emission, local)
        code, globals_, annotations = engine._tuple_lambda(
            compiler, emission[1], local, namespace, declaration
        )
        engine._inputs_current("native tuple compiler source changed")
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=code,
                globals=globals_,
                annotations=annotations,
                defaults=local["defaults"],
                keyword_defaults=None,
                closure=(),
                inputs=tuple(engine._inputs.values()),
            ),
        )

    def _dataclass_factory(
        self,
        declaration: ast.ClassDef,
    ) -> t.Pair[FunctionType, t.DictKV[str, bool]] | None:
        """Elect the physical SDK decorator without invoking any decorator.

        Returns:
            The source-bound SDK factory and closed boolean options, if elected.

        Raises:
            ValueError: If the factory or its source options are ambiguous.

        """
        scope = next(
            (
                scope
                for scope in self._witness.scopes.values()
                if scope.get_kind() == "Class"
                and scope.get_start() == declaration.lineno
            ),
            None,
        )
        if scope is None or scope.parent is None:
            msg = "generated dataclass has no physical defining scope"
            raise ValueError(msg)
        namespace = vars(self._module(self._witness.module.get_name()))
        tree = self._trees[self._witness.source]
        elected: t.Pair[FunctionType, t.DictKV[str, bool]] | None = None
        for decorator in declaration.decorator_list:
            expression = (
                decorator.func if isinstance(decorator, ast.Call) else decorator
            )
            binding = u.Infra.resolve_symbol(scope.parent, expression)
            if binding is None:
                continue
            provider = binding.get_object().get_module()
            if provider is None or provider.get_name() != "dataclasses":
                continue
            factory = self._decorator_binding(expression, namespace, tree)
            compiler = self._module("dataclasses")
            if factory is not vars(compiler).get("dataclass"):
                continue
            if elected is not None:
                msg = "native dataclass decorator is repeated"
                raise ValueError(msg)
            options = self._dataclass_default_options(factory)
            if isinstance(decorator, ast.Call):
                self._dataclass_options(decorator, namespace, tree, options)
            elected = factory, options
        return elected

    def _dataclass_default_options(self, factory: FunctionType) -> t.DictKV[str, bool]:
        """Authenticate the SDK's declared boolean option defaults.

        Returns:
            Native boolean defaults derived from the physical function signature.

        Raises:
            TypeError: If an option default is not a native boolean.
            ValueError: If a compiler option has no physical default.

        """
        physical, tree, namespace = self._function(factory)
        options: t.DictKV[str, bool] = {}
        for parameter, default in zip(
            physical.args.kwonlyargs, physical.args.kw_defaults, strict=True
        ):
            if default is None:
                msg = "native dataclass compiler has an unbound option"
                raise ValueError(msg)
            value = self._default(default, namespace, tree)
            if type(value) is not bool:
                msg = "native dataclass compiler options are not native booleans"
                raise TypeError(msg)
            options[parameter.arg] = value
        return options

    def _decorator_binding(
        self,
        expression: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> FunctionType:
        match expression:
            case ast.Name(id=name):
                value = self._global(name, namespace, tree)
            case ast.Attribute(value=ast.Name(id=name), attr=attribute):
                provider = self._global(name, namespace, tree)
                if type(provider) is not ModuleType:
                    msg = "native compiler decorator has no exact module binding"
                    raise TypeError(msg)
                value = vars(provider).get(attribute)
            case _:
                msg = "native compiler decorator has no closed imported binding"
                raise ValueError(msg)
        if type(value) is not FunctionType:
            msg = "native compiler decorator is not a physical Python function"
            raise TypeError(msg)
        return value

    def _dataclass_options(
        self,
        decorator: ast.Call,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
        options: t.MutableMappingKV[str, bool],
    ) -> None:
        if decorator.args:
            msg = "native dataclass decorator has positional options"
            raise ValueError(msg)
        selected: set[str] = set()
        for keyword in decorator.keywords:
            if (
                keyword.arg is None
                or keyword.arg not in options
                or keyword.arg in selected
            ):
                msg = "native dataclass decorator options are not uniquely declared"
                raise ValueError(msg)
            value = self._source_scalar(keyword.value, namespace, tree)
            if type(value) is not bool:
                msg = "native dataclass decorator options are not native booleans"
                raise TypeError(msg)
            options[keyword.arg] = value
            selected.add(keyword.arg)

    def _source_scalar(
        self,
        expression: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        if isinstance(expression, ast.Name) and expression.id in namespace:
            declarations = [
                node.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == expression.id
            ]
            if len(declarations) != 1:
                msg = "native compiler argument has no unique physical literal binding"
                raise ValueError(msg)
            expected = self._default(declarations[0], namespace, tree)
            if not self._same_default(expected, namespace[expression.id]):
                msg = "native compiler argument differs from its physical literal"
                raise ValueError(msg)
            return expected
        return self._default(expression, namespace, tree)

    def _dataclass_annotation(
        self,
        field: ast.AnnAssign,
        namespace: t.MappingKV[str, p.AttributeProbe],
        fields: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe:
        """Read the annotation through its original native compilation semantics.

        Without postponed evaluation a declared field's annotation is the type
        object its executed SDK ``Field`` stores (read, never invoked); other
        annotations go through the closed interpreter.

        Returns:
            The exact compiled future string or a native annotation value.

        Raises:
            TypeError: If the compiler did not produce native annotation text.

        """
        tree = self._trees[self._witness.source]
        future = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ]
        if not any(
            alias.name == "annotations" for node in future for alias in node.names
        ):
            name = field.target.id if isinstance(field.target, ast.Name) else ""
            observed = fields.get(name)
            if type(observed) is vars(self._module("dataclasses")).get("Field"):
                return observed.type
            return self._expression(field.annotation, {}, namespace, tree)
        isolated = ast.Module(
            body=[
                *future,
                ast.copy_location(
                    ast.AnnAssign(
                        target=field.target,
                        annotation=field.annotation,
                        value=None,
                        simple=field.simple,
                    ),
                    field,
                ),
            ],
            type_ignores=[],
        )
        compiled = builtins.compile(
            ast.fix_missing_locations(isolated),
            str(self._witness.source),
            "exec",
            dont_inherit=True,
            optimize=sys.flags.optimize,
        )
        annotation = next(value for value in compiled.co_consts if type(value) is str)
        if type(annotation) is not str:
            msg = "native compiler did not emit an exact annotation string"
            raise TypeError(msg)
        return annotation

    def _dataclass_inputs(
        self,
        owner: p.AttributeProbe,
        declaration: ast.ClassDef,
    ) -> t.DictKV[str, p.AttributeProbe]:
        """Build only physical declaration data for an exact-type SDK receiver.

        Returns:
            Its native module/qualified names, annotations and literal defaults.

        Raises:
            ValueError: If source and the loaded class do not share their identity.

        """
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        module_name = self._witness.module.get_name()
        if not self._same_default(module_name, namespace.get("__module__")):
            msg = "native dataclass owner differs from its physical source module"
            raise ValueError(msg)
        source_globals = vars(self._module(module_name))
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        stored = namespace.get("__dataclass_fields__")
        observed_fields: t.MappingKV[str, p.AttributeProbe] = (
            stored if type(stored) is dict else {}
        )
        annotations: t.DictKV[str, p.AttributeProbe] = {}
        result: t.DictKV[str, p.AttributeProbe] = {
            "__module__": module_name,
            "__qualname__": qualified,
            "__annotations__": annotations,
        }
        for field in declaration.body:
            if not isinstance(field, ast.AnnAssign) or not isinstance(
                field.target, ast.Name
            ):
                continue
            annotations[field.target.id] = self._dataclass_annotation(
                field, source_globals, observed_fields
            )
            if isinstance(field.value, ast.Call) and self._sdk_field_call(
                field.value, source_globals
            ):
                result[field.target.id] = self._dataclass_field(
                    field.value, field.target.id, namespace, source_globals
                )
            elif isinstance(field.value, ast.Constant | ast.Tuple | ast.List | ast.Name):
                result[field.target.id] = self._source_scalar(
                    field.value, source_globals, self._trees[self._witness.source]
                )
            elif field.value is not None:
                # Any other physical expression (attribute, operator, a helper
                # returning a Field) was evaluated by the class body already:
                # rebuild the SDK field from its stored data.
                result[field.target.id] = self._rebuilt_field(
                    field.target.id, namespace
                )
        for ancestor in vars(type)["__mro__"].__get__(owner, type(owner)):
            body = vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            if "__post_init__" in body:
                # The SDK emits a call by name only; the hook is never invoked.
                result["__post_init__"] = body["__post_init__"]
                break
        return result

    def _dataclass_field(
        self,
        call: ast.Call,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        source_globals: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe:
        """Rebuild one physically declared SDK ``field(...)`` from its storage.

        The physical call must bind the SDK ``field`` factory; its executed
        ``Field`` supplies the data. Defaults and factories are never invoked.

        Returns:
            A fresh SDK field carrying the observed field data.

        Raises:
            ValueError: If the call or the executed field storage differs.

        """
        sdk = vars(self._module("dataclasses"))
        factory = sdk.get("field")
        if (
            self._decorator_binding(
                call.func, source_globals, self._trees[self._witness.source]
            )
            is not factory
            or type(factory) is not FunctionType
        ):
            msg = f"native dataclass default is not an SDK field call: {name}"
            raise ValueError(msg)
        self._physical_function(factory)
        return self._rebuilt_field(name, namespace)

    def _rebuilt_field(
        self, name: str, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> p.AttributeProbe:
        """Rebuild a fresh SDK field from one stored ``Field``'s data.

        Returns:
            A fresh SDK field; neither its default nor its factory is invoked.

        Raises:
            ValueError: If the SDK field factory is not an exact function.

        """
        factory = vars(self._module("dataclasses")).get("field")
        if type(factory) is not FunctionType:
            msg = "native dataclass field factory is not an exact Python function"
            raise ValueError(msg)
        self._physical_function(factory)
        observed = self._stored_field(name, namespace)
        return factory(
            default=observed.default,
            default_factory=observed.default_factory,
            init=observed.init,
            repr=observed.repr,
            hash=observed.hash,
            compare=observed.compare,
            kw_only=observed.kw_only,
        )

    def _sdk_field_call(
        self, call: ast.Call, source_globals: t.MappingKV[str, p.AttributeProbe]
    ) -> bool:
        """Recognize a physical call naming the SDK ``field`` factory.

        Returns:
            Whether the call target is bound to the SDK factory or its module.

        """
        sdk = self._module("dataclasses")
        match call.func:
            case ast.Name(id=name):
                return source_globals.get(name) is vars(sdk).get("field")
            case ast.Attribute(value=ast.Name(id=name), attr="field"):
                return source_globals.get(name) is sdk
            case _:
                return False

    def _stored_field(
        self, name: str, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> p.AttributeProbe:
        """Read one executed SDK ``Field`` whose default carries no authored hook.

        Returns:
            The exact stored SDK field.

        Raises:
            ValueError: If the storage is foreign or the default has a set-name hook.

        """
        sdk = vars(self._module("dataclasses"))
        fields = namespace.get("__dataclass_fields__")
        observed = fields.get(name) if type(fields) is dict else None
        if type(observed) is not sdk.get("Field"):
            msg = f"native dataclass field has no native storage: {name}"
            raise ValueError(msg)
        default = observed.default
        if default is not sdk.get("MISSING") and any(
            "__set_name__" in vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            for ancestor in vars(type)["__mro__"].__get__(
                type(default), type(type(default))
            )
        ):
            msg = f"native dataclass default carries an authored __set_name__: {name}"
            raise ValueError(msg)
        return observed

    def _compile_dataclass(
        self,
        value: FunctionType,
        owner: p.AttributeProbe,
        attribute: str,
        declaration: ast.ClassDef,
        factory: t.Pair[FunctionType, t.DictKV[str, bool]],
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Recompile the emission with the closed SDK on a fresh exact receiver.

        The SDK entry, its class processor and every helper it can reach are
        authenticated against their physical compilation first; the receiver
        carries only physical declaration data.

        Returns:
            The emitted function's proof at the observed slot position.

        Raises:
            TypeError: If an observed compiler callable has a foreign native type.

        """
        if type(value) is not FunctionType:
            msg = "native dataclass emission is not an exact Python function"
            raise TypeError(msg)
        self._dataclass_sdk(factory[0])
        receiver = self._dataclass_inputs(owner, declaration)
        fresh = type(
            vars(type)["__name__"].__get__(owner, type(owner)), (object,), receiver
        )
        emitted_owner = factory[0](fresh, **factory[1])
        return self._dataclass_emission(
            value, owner, attribute, (fresh, emitted_owner)
        )

    def _dataclass_sdk(self, factory: FunctionType) -> None:
        """Authenticate the selected SDK entry and its physical class processor.

        This proves these callable bindings without executing either one. The
        processor's consumed helpers and receiver inputs need their own proof
        before SDK emission is admitted.

        Raises:
            TypeError: If the processor binding is not an exact Python function.
            ValueError: If the selected entry or processor has a foreign namespace.

        """
        _declaration, _tree, namespace = self._function(factory)
        compiler = self._module("dataclasses")
        if namespace is not vars(compiler) or namespace.get("dataclass") is not factory:
            msg = "native dataclass SDK entry has a foreign execution namespace"
            raise ValueError(msg)
        processor = namespace.get("_process_class")
        if type(processor) is not FunctionType:
            msg = "native dataclass class processor is not a physical Python function"
            raise TypeError(msg)
        if processor.__globals__ is not namespace:
            msg = "native dataclass class processor has foreign globals"
            raise ValueError(msg)
        self._function(processor)
        self._dataclass_sdk_helpers(namespace)

    def _dataclass_sdk_helpers(
        self, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> None:
        """Authenticate every Python helper the SDK class processor can reach.

        Every function bound in the SDK namespace, and every function (raw
        wrapper chain included) declared in an SDK class body, must equal a
        code unit of its own module's physical compilation.

        Raises:
            ValueError: If a helper code unit differs from its physical compiler.

        """
        sdk = vars(self._module("dataclasses")).get("__name__")
        for member in namespace.values():
            if type(member) is FunctionType:
                functions = self.function_chain(member)
            elif type(member) is type:
                body = vars(type)["__dict__"].__get__(member, type)
                if body.get("__module__") != sdk:
                    continue
                functions = tuple(
                    function
                    for item in body.values()
                    for function in self.function_chain(item)
                )
            else:
                continue
            for function in functions:
                self._physical_function(function)

    def _physical_function(self, function: FunctionType) -> None:
        """Require one function's code to be a unit of its module's compilation.

        Raises:
            ValueError: If the globals are foreign or the code unit differs.

        """
        supplier = function.__globals__.get("__name__")
        if type(supplier) is not str or function.__globals__ is not vars(
            self._module(supplier)
        ):
            msg = "native SDK helper has foreign execution globals"
            raise ValueError(msg)
        path, _tree = self._source(self._module(supplier))
        code = function.__code__
        pending = [self._codes[path]]
        while pending:
            unit = pending.pop()
            if (
                unit == code
                and unit.co_filename == code.co_filename
                and unit.co_linetable == code.co_linetable
            ):
                return
            pending.extend(item for item in unit.co_consts if type(item) is CodeType)
        msg = (
            "native SDK helper differs from its physical compilation: "
            f"{supplier}::{code.co_qualname[:160]}"
        )
        raise ValueError(msg)

    @staticmethod
    def _tuple_constructor_diagnostic(
        owner: p.AttributeProbe,
        attribute: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> str:
        native = type(owner)
        qualified = vars(type)["__qualname__"].__get__(native, type(native))
        metadata = (
            f"attribute={attribute!r}; source={witness.source}; "
            "receiver_type="
            f"{qualified if type(qualified) is str else '<non-string>'}"
        )
        if not any(
            ancestor is type
            for ancestor in vars(type)["__mro__"].__get__(native, type(native))
        ):
            return metadata
        namespace = vars(type)["__dict__"].__get__(owner, native)
        supplier = namespace.get("__module__")
        qualified = vars(type)["__qualname__"].__get__(owner, native)
        metadata += (
            f"; supplier={supplier if type(supplier) is str else '<non-string>'}; "
            f"receiver={qualified if type(qualified) is str else '<non-string>'}"
        )
        selected = namespace.get(attribute)
        if type(selected) is classmethod or type(selected) is staticmethod:
            selected = selected.__func__
        if type(selected) is FunctionType:
            supplier = selected.__module__
            filename = selected.__code__.co_filename
            qualified = selected.__code__.co_qualname
            metadata += (
                f"; callable_supplier="
                f"{supplier if type(supplier) is str else '<non-string>'}; "
                "code_filename="
                f"{filename if type(filename) is str else '<non-string>'}; "
                "code_qualname="
                f"{qualified if type(qualified) is str else '<non-string>'}"
            )
        return metadata

    def _tuple_declaration(
        self,
        qualified: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        attribute: str,
        invocation: t.Triple[str, p.AttributeProbe, p.AttributeProbe | None] | None,
    ) -> ast.ClassDef | None:
        """Elect the physical class body when no literal constructor call owns it.

        Returns:
            The exact class declaration, or None for a proved factory invocation.

        Raises:
            ValueError: If the qualified declaration is missing or ambiguous.

        """
        first_line = namespace.get("__firstlineno__")
        location = str(first_line) if type(first_line) is int else "<unavailable>"
        nodes = self._trees[self._witness.source].body
        declaration = None
        for component in qualified.split(".") if invocation is None else ():
            candidates = [
                node
                for node in nodes
                if isinstance(node, ast.ClassDef) and node.name == component
            ]
            if len(candidates) != 1:
                msg = (
                    "native tuple has no unique physical class declaration: "
                    f"qualname={qualified[:160]!r}; attribute={attribute[:80]!r}; "
                    f"source={self._witness.source}; firstlineno={location}; "
                    f"component={component[:80]!r}; candidates={len(candidates)}"
                )
                raise ValueError(msg)
            declaration = candidates[0]
            nodes = declaration.body
        if declaration is None and invocation is None:
            msg = "native tuple has no physical declaration"
            raise ValueError(msg)
        return declaration

    def _tuple_inputs(
        self,
        declaration: ast.ClassDef | None,
        namespace: t.MappingKV[str, p.AttributeProbe],
        invocation: t.Triple[str, p.AttributeProbe, p.AttributeProbe | None] | None,
    ) -> t.Triple[str, p.AttributeProbe, p.AttributeProbe | None]:
        """Derive the same literal factory operands from a class or source call.

        Returns:
            The declared tuple name, field data and defaults.

        Raises:
            ValueError: If source ownership or ordered field defaults differ.

        """
        fields = (
            [
                (node.target.id, node)
                for node in declaration.body
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
            ]
            if declaration is not None
            else []
        )
        names = tuple(name for name, _field in fields)
        module_name = namespace.get("__module__")
        if type(module_name) is not str:
            msg = "native tuple declaration has no registered module"
            raise ValueError(msg)
        module = self._module(module_name)
        self._source(module)
        defaults = []
        for _name, field in fields:
            if field.value is None:
                if defaults:
                    msg = "native tuple required field follows a declared default"
                    raise ValueError(msg)
                continue
            defaults.append(
                self._expression(
                    field.value, {}, vars(module), self._trees[self._witness.source]
                )
            )
        if invocation is not None:
            return invocation
        if declaration is None:
            msg = "native tuple has no physical declaration"
            raise ValueError(msg)
        return declaration.name, list(names), tuple(defaults)

    @staticmethod
    def _tuple_emission(
        definition: ast.FunctionDef, attribute: str
    ) -> t.Pair[ast.Assign, t.Pair[ast.Name, ast.Name]]:
        """Locate the unique physical two-operand lambda emission.

        Returns:
            Its assignment and exact source operand names.

        Raises:
            ValueError: If compiler syntax or emission ownership is unsupported.

        """
        emissions: list[t.Pair[ast.Assign, t.Pair[ast.Name, ast.Name]]] = []
        for node in definition.body:
            match node:
                case ast.Assign(
                    targets=[ast.Name(id=name)],
                    value=ast.Call(
                        func=ast.Name(id="eval"),
                        args=[ast.Name() as first, ast.Name() as second],
                        keywords=[],
                    ),
                ) if name == attribute:
                    emissions.append((node, (first, second)))
        if len(emissions) != 1 or not definition.args.args[1:]:
            msg = "native tuple compiler has no unique physical lambda emission"
            raise ValueError(msg)
        return emissions[0]

    @staticmethod
    def _tuple_field_layout(
        names: p.AttributeProbe, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> None:
        """Require normalized fields to equal the native tuple's actual storage.

        Raises:
            TypeError: If fields do not have native tuple and string storage.
            ValueError: If field values, uniqueness or ordering differ.

        """
        observed_fields = namespace.get("_fields")
        if type(names) is not tuple or type(observed_fields) is not tuple:
            msg = "native tuple field layout differs from physical constructor data"
            raise TypeError(msg)
        if any(type(name) is not str for name in names) or any(
            type(name) is not str for name in observed_fields
        ):
            msg = "native tuple field layout differs from physical constructor data"
            raise TypeError(msg)
        if (
            observed_fields != names
            or len(set(names)) != len(names)
            or any(name.startswith("_") for name in names)
        ):
            module = namespace.get("__module__")
            msg = (
                "native tuple field layout differs from physical constructor data: "
                f"module={module if type(module) is str else '<non-string>'}; "
                f"declared={names[:16]!r}; observed={observed_fields[:16]!r}"
            )
            raise ValueError(msg)

    def _tuple_code_inputs(
        self,
        compiler: t.Triple[
            ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]
        ],
        emission: t.Pair[ast.Assign, t.Pair[ast.Name, ast.Name]],
        local: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        """Follow only source writes needed by the actual emission operands.

        Raises:
            ValueError: If selected inputs return before physical code emission.

        """
        definition, tree, globals_ = compiler
        assignment, arguments = emission
        needed = {argument.id for argument in arguments}
        before = definition.body[: definition.body.index(assignment)]
        selected = []
        changed = True
        while changed:
            changed = False
            for node in before:
                written = {
                    item.id
                    for item in ast.walk(node)
                    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
                }
                if written & needed and not written & set(local):
                    if not any(node is previous for previous in selected):
                        selected.append(node)
                        changed = True
                    needed.update(
                        item.id
                        for item in ast.walk(node)
                        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
                    )
        # The declaration's exact string fields already establish the native
        # constructor's normalization input; only code-bearing data flow runs.
        ordered = [node for node in before if any(node is item for item in selected)]
        returned = self._statements(ordered, local, globals_, tree)
        if returned is not None:
            msg = "native tuple code inputs return before their declared emission"
            raise ValueError(msg)

    def _tuple_lambda(
        self,
        compiler: t.Triple[
            ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]
        ],
        arguments: t.Pair[ast.Name, ast.Name],
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        declaration: ast.ClassDef | None,
    ) -> t.Triple[
        p.Infra.NativeCodeIdentity,
        t.MappingKV[str, p.AttributeProbe],
        t.MappingKV[str, p.AttributeProbe],
    ]:
        """Compile closed lambda text and authenticate its annotation attachment.

        Returns:
            The native code, globals and declared annotation storage.

        Raises:
            ValueError: If emitted source or construction inputs are unsupported.

        """
        tree = compiler[1]
        globals_ = compiler[2]
        text, generated_globals = (
            self._expression(argument, local, globals_, tree) for argument in arguments
        )
        if (
            type(text) is not str
            or type(generated_globals) is not dict
            or id(generated_globals) not in self._dictionaries
            or type(generated_globals.get("__builtins__")) is not dict
            or generated_globals["__builtins__"]
        ):
            msg = "native tuple emission lacks closed text and empty builtin storage"
            raise ValueError(msg)
        parsed = ast.parse(text, mode="eval")
        if (
            not isinstance(parsed.body, ast.Lambda)
            or parsed.body.args.defaults
            or parsed.body.args.kw_defaults
            or parsed.body.args.vararg is not None
            or parsed.body.args.kwarg is not None
        ):
            msg = "native tuple constructor is not a closed physical lambda"
            raise ValueError(msg)
        root = builtins.compile(
            text,
            "<string>",
            "eval",
            dont_inherit=True,
            optimize=sys.flags.optimize,
        )
        codes = tuple(item for item in root.co_consts if type(item) is CodeType)
        if len(codes) != 1 or codes[0].co_freevars or codes[0].co_cellvars:
            msg = "native tuple lambda has unsupported executable closure state"
            raise ValueError(msg)
        annotations: t.MappingKV[str, p.AttributeProbe] = (
            self._tuple_annotations(namespace, local[compiler[0].args.args[1].arg])
            if declaration is not None
            else {}
        )
        return codes[0], generated_globals, annotations

    def _tuple_annotations(
        self,
        namespace: t.MappingKV[str, p.AttributeProbe],
        names: p.AttributeProbe,
    ) -> t.MappingKV[str, p.AttributeProbe]:
        """Prove annotation metadata is attached by the physical typed-tuple factory.

        Returns:
            The native annotation storage in its declared field order.

        Raises:
            ValueError: If source attachment or observed annotation storage differs.

        """
        typing = self._module("typing")
        annotator, _typing_tree, _typing_globals = self._function(
            vars(typing).get("_make_nmtuple"),
        )
        assignments: list[ast.Assign] = []
        for node in annotator.body:
            match node:
                case ast.Assign(
                    targets=[
                        ast.Attribute(attr="__annotations__"),
                        ast.Attribute(
                            value=ast.Attribute(attr="__new__"),
                            attr="__annotations__",
                        ),
                    ]
                ):
                    assignments.append(node)
        annotations = namespace.get("__annotations__")
        if (
            len(assignments) != 1
            or type(annotations) is not dict
            or any(type(name) is not str for name in annotations)
            or tuple(annotations) != names
        ):
            msg = "native tuple annotation storage lacks its physical attachment"
            raise ValueError(msg)
        return annotations

    def _tuple_invocation(
        self,
        owner: p.AttributeProbe,
        witness: m.Infra.NativeSourceWitness,
    ) -> t.Triple[str, p.AttributeProbe, p.AttributeProbe | None] | None:
        """Elect a physical constructor assignment by its exact registered alias.

        Returns:
            The literal invocation data, or None for a class-body declaration.

        Raises:
            ValueError: If constructor identity or literal inputs are not proved.

        """
        supplier = vars(type)["__dict__"].__get__(owner, type(owner)).get("__module__")
        if type(supplier) is not str:
            msg = "native tuple constructor has no exact supplier name"
            raise ValueError(msg)
        namespace = vars(self._module(supplier))
        aliases = {
            name
            for name, value in namespace.items()
            if type(name) is str and value is owner
        }
        matches = self._physical_invocations(
            "${export} = ${invocation}",
            ("export", "invocation"),
            tuple(aliases),
        )
        tree = self._trees[witness.source]
        if len(matches) > 1:
            msg = "native tuple has competing physical constructor assignments"
            raise ValueError(msg)
        call = (
            ast.parse(matches[0]["invocation"], mode="eval").body
            if matches
            else self._tuple_base_call(owner, namespace, tree)
        )
        if call is None:
            return None
        match call:
            case ast.Call(args=[first, second]) if (
                not isinstance(first, ast.Starred)
                and not isinstance(second, ast.Starred)
                and len(call.keywords) <= 1
                and all(keyword.arg == "defaults" for keyword in call.keywords)
            ):
                pass
            case _:
                msg = "native tuple constructor has unsupported invocation inputs"
                raise ValueError(msg)
        collections = self._module("collections")
        if isinstance(call.func, ast.Name):
            factory = self._global(call.func.id, namespace, tree)
        elif (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.attr == "namedtuple"
            and self._global(call.func.value.id, namespace, tree) is collections
        ):
            factory = vars(collections).get(call.func.attr)
        else:
            msg = "native tuple constructor has no exact physical imported binding"
            raise ValueError(msg)
        if factory is not vars(self._module("collections")).get("namedtuple"):
            msg = "native tuple constructor differs from its physical imported owner"
            raise ValueError(msg)
        self._function(factory)
        typename, fields = (
            self._tuple_operand(argument, namespace) for argument in call.args
        )
        defaults = (
            self._tuple_operand(call.keywords[0].value, namespace)
            if call.keywords
            else None
        )
        if (
            type(typename) is not str
            or vars(type)["__name__"].__get__(owner, type(owner)) != typename
            or not (
                type(fields) is str
                or (
                    (type(fields) is list or type(fields) is tuple)
                    and all(type(field) is str for field in fields)
                )
            )
            or not (
                defaults is None or type(defaults) is list or type(defaults) is tuple
            )
        ):
            msg = "native tuple constructor arguments are not closed string data"
            raise ValueError(msg)
        return typename, fields, defaults

    @staticmethod
    def _tuple_base_call(
        owner: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> ast.expr | None:
        """Elect the module class whose physical base expression built the tuple.

        ``class TokenInfo(collections.namedtuple("TokenInfo", ...))`` binds no
        alias to the tuple itself: the registered subclass's native base at the
        same position as the physical base expression is the only owner proof.

        Returns:
            The unique physical base expression, or None when no class owns it.

        Raises:
            ValueError: If more than one module class declares the same base.

        """
        calls: list[ast.expr] = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            declared = namespace.get(node.name)
            if type(declared) is not type:
                continue
            bases = vars(type)["__bases__"].__get__(declared, type(declared))
            if len(bases) != len(node.bases):
                continue
            calls.extend(
                expression
                for base, expression in zip(bases, node.bases, strict=True)
                if base is owner
            )
        if len(calls) > 1:
            msg = "native tuple has competing physical base invocations"
            raise ValueError(msg)
        return calls[0] if calls else None

    def _tuple_operand(
        self,
        node: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe | None:
        """Read a constructor operand from literals and native tuple field storage.

        ``Name._fields`` reads the exact ``_fields`` storage of a module tuple
        class, and ``+`` joins two operands of the same sequence type; the
        normalized layout is still checked against the owner's own fields.

        Returns:
            The closed operand value.

        Raises:
            ValueError: If the operand is neither closed data nor tuple storage.

        """
        match node:
            case ast.BinOp(op=ast.Add(), left=left, right=right):
                first, second = (
                    self._tuple_operand(item, namespace) for item in (left, right)
                )
                if (type(first) is tuple or type(first) is list) and type(
                    first
                ) is type(second):
                    return first + second
            case ast.Attribute(value=ast.Name(id=name), attr="_fields"):
                owner = namespace.get(name)
                if type(owner) is type:
                    fields = next(
                        (
                            body["_fields"]
                            for ancestor in vars(type)["__mro__"].__get__(owner, type)
                            if "_fields"
                            in (body := vars(type)["__dict__"].__get__(ancestor, type))
                        ),
                        None,
                    )
                    if type(fields) is tuple and all(
                        type(item) is str for item in fields
                    ):
                        return fields
            case _:
                pass
        return self._tuple_literal(node)

    @staticmethod
    def _tuple_literal(node: ast.expr) -> p.AttributeProbe | None:
        """Read only exact scalar and fixed sequence literals from a constructor.

        Returns:
            The declared native scalar or fixed sequence.

        Raises:
            ValueError: If the constructor operand contains nonliteral data.

        """
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.List | ast.Tuple):
            items = [
                FlextInfraWorkspaceGeneratedFunction._tuple_literal(item)
                for item in node.elts
            ]
            return items if isinstance(node, ast.List) else tuple(items)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            # A literal sequence repeated by a literal count (``[None] * 4``)
            # is closed data; the count is bounded to native field arity.
            sequence, count = (
                FlextInfraWorkspaceGeneratedFunction._tuple_literal(operand)
                for operand in (node.left, node.right)
            )
            if (
                (type(sequence) is list or type(sequence) is tuple)
                and type(count) is int
                and 0 <= count <= c.Infra.NATIVE_TUPLE_REPEAT_LIMIT
            ):
                return sequence * count
        msg = (
            "native tuple constructor contains nonliteral data: "
            f"{ast.unparse(node)[:160]}"
        )
        raise ValueError(msg)

    def _tuple_normalization(
        self,
        compiler: t.Triple[
            ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]
        ],
        invocation: t.Triple[str, p.AttributeProbe, p.AttributeProbe | None],
        emission: ast.Assign,
    ) -> t.MutableMappingKV[str, p.AttributeProbe]:
        """Interpret the source's exact input writes before lambda construction.

        Returns:
            The normalized native inputs required by the physical emission.

        Raises:
            ValueError: If normalization or default attachment is not unique.

        """
        definition, tree, namespace = compiler
        typename, fields, defaults = invocation
        if len(emission.targets) != 1 or not isinstance(
            emission_target := emission.targets[0], ast.Name
        ):
            msg = "native tuple compiler has no unique physical lambda emission"
            raise ValueError(msg)
        first, second = (argument.arg for argument in definition.args.args[:2])
        local = {
            first: typename,
            second: fields,
            **{
                argument.arg: self._default(default, namespace, tree)
                for argument, default in zip(
                    definition.args.kwonlyargs,
                    definition.args.kw_defaults,
                    strict=True,
                )
                if default is not None
            },
        }
        if "defaults" not in local:
            msg = "native tuple compiler has no physical default input"
            raise ValueError(msg)
        local["defaults"] = defaults
        selected = []
        for statement in definition.body[: definition.body.index(emission)]:
            written = {
                node.id
                for node in ast.walk(statement)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            }
            written.update(
                node.value.id
                for node in ast.walk(statement)
                if isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Store)
                and isinstance(node.value, ast.Name)
            )
            if first in written or second in written:
                selected.append(statement)
        if self._statements(selected, local, namespace, tree) is not None:
            msg = "native tuple normalization returns before physical emission"
            raise ValueError(msg)
        conversion, attachment = self._tuple_default_bindings(
            definition, emission, emission_target.id
        )
        writes = [
            node
            for node in ast.walk(definition)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == "defaults"
        ]
        if len(writes) != 1 or writes[0] is not conversion.targets[0]:
            msg = "native tuple compiler has competing default metadata writes"
            raise ValueError(msg)
        if any(
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Store)
            and node.attr == "__defaults__"
            and node is not attachment.targets[0]
            for node in ast.walk(definition)
        ):
            msg = "native tuple compiler has competing default metadata writes"
            raise ValueError(msg)
        if defaults is not None:
            self._statements((conversion,), local, namespace, tree)
        if local["defaults"] is not None and type(local["defaults"]) is not tuple:
            msg = "native tuple defaults have unsupported normalized storage"
            raise ValueError(msg)
        return local

    @staticmethod
    def _tuple_default_bindings(
        definition: ast.FunctionDef, emission: ast.Assign, target_name: str
    ) -> t.Pair[ast.Assign, ast.Assign]:
        """Elect the actual default conversion and its later metadata attachment.

        Returns:
            The unique physical conversion and attachment assignments.

        Raises:
            ValueError: If either source operation is absent or ambiguous.

        """
        conversions: list[ast.Assign] = []
        attachments: list[ast.Assign] = []
        emission_index = definition.body.index(emission)
        for statement in definition.body:
            match statement:
                case ast.If(
                    test=ast.Compare(
                        left=ast.Name(id="defaults"),
                        ops=[ast.IsNot()],
                        comparators=[ast.Constant(value=None)],
                    ),
                    orelse=[],
                ):
                    pass
                case _:
                    continue
            for item in statement.body:
                match item:
                    case ast.Assign(
                        targets=[ast.Name(id="defaults")],
                        value=ast.Call(
                            func=ast.Name(id="tuple"),
                            args=[ast.Name(id="defaults")],
                            keywords=[],
                        ),
                    ) if definition.body.index(statement) < emission_index:
                        conversions.append(item)
                    case ast.Assign(
                        targets=[
                            ast.Attribute(value=ast.Name(id=name), attr="__defaults__")
                        ],
                        value=ast.Name(id="defaults"),
                    ) if name == target_name and (
                        definition.body.index(statement) > emission_index
                    ):
                        attachments.append(item)
        if len(conversions) != 1 or len(attachments) != 1:
            msg = (
                "native tuple defaults lack unique physical normalization "
                "and attachment"
            )
            raise ValueError(msg)
        return conversions[0], attachments[0]

    @staticmethod
    def _module(name: str) -> ModuleType:
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            msg = f"closed compiler supplier is not a native module: {name}"
            raise ValueError(msg)
        return module

    def _source(self, module: ModuleType) -> t.Pair[Path, ast.Module]:
        namespace = vars(module)
        name = namespace.get("__name__")
        if type(name) is not str or sys.modules.get(name) is not module:
            msg = "closed compiler module has no registered identity"
            raise ValueError(msg)
        path = FlextInfraWorkspaceEnvironmentProvenance.module_source(name).unwrap()
        if path.suffix != ".py":
            msg = f"closed compiler supplier has no physical Python source: {name}"
            raise ValueError(msg)
        if path not in self._inputs:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if state.content is None:
                msg = f"closed compiler source is absent: {path}"
                raise ValueError(msg)
            self._inputs[path] = state
            self._trees[path] = ast.parse(state.content, filename=str(path))
            self._codes[path] = builtins.compile(
                state.content,
                str(path),
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
        return path, self._trees[path]

    def _function(
        self,
        function: p.AttributeProbe | None,
    ) -> t.Triple[ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]]:
        if type(function) is not FunctionType:
            msg = "closed compiler callback is not an exact Python function"
            raise ValueError(msg)
        namespace = function.__globals__
        module_name = namespace.get("__name__")
        if type(module_name) is not str or namespace is not vars(
            self._module(module_name)
        ):
            msg = "closed compiler function has foreign globals"
            raise ValueError(msg)
        path, tree = self._source(self._module(module_name))
        if (
            function.__closure__ is not None
            or function.__builtins__ is not vars(builtins)
            or any(
                isinstance(item, ast.ImportFrom) and item.module == "__future__"
                for item in tree.body
            )
        ):
            msg = "closed compiler function has unsupported closure or future inputs"
            raise ValueError(msg)
        candidates = tuple(
            item
            for item in tree.body
            if isinstance(item, ast.FunctionDef)
            and item.name == function.__name__
            and item.lineno == function.__code__.co_firstlineno
            and not item.decorator_list
        )
        pending = [self._codes[path]]
        matched = False
        while pending:
            code = pending.pop()
            matched |= (
                code == function.__code__
                and code.co_filename == function.__code__.co_filename
                and code.co_linetable == function.__code__.co_linetable
                and code.co_exceptiontable == function.__code__.co_exceptiontable
            )
            pending.extend(item for item in code.co_consts if type(item) is CodeType)
        if len(candidates) != 1 or not matched:
            msg = "closed compiler function differs from its physical compilation"
            raise ValueError(msg)
        declaration = candidates[0]
        defaults = tuple(
            self._default(item, namespace, tree) for item in declaration.args.defaults
        )
        observed_defaults = function.__defaults__ or ()
        keyword_defaults = {
            argument.arg: self._default(default, namespace, tree)
            for argument, default in zip(
                declaration.args.kwonlyargs,
                declaration.args.kw_defaults,
                strict=True,
            )
            if default is not None
        }
        observed_keywords = function.__kwdefaults__ or {}
        if (
            len(defaults) != len(observed_defaults)
            or set(keyword_defaults) != set(observed_keywords)
            or any(
                not self._same_default(expected, observed)
                for expected, observed in zip(
                    defaults,
                    observed_defaults,
                    strict=True,
                )
            )
            or any(
                not self._same_default(expected, observed_keywords[name])
                for name, expected in keyword_defaults.items()
            )
        ):
            msg = "closed compiler defaults differ from physical source bindings"
            raise ValueError(msg)
        return declaration, tree, namespace

    @staticmethod
    def _same_default(
        expected: p.AttributeProbe | None,
        observed: p.AttributeProbe | None,
    ) -> bool:
        if (
            type(expected) is str
            or type(expected) is int
            or type(expected) is bool
            or expected is None
        ):
            return type(observed) is type(expected) and observed == expected
        return observed is expected

    def _default(
        self,
        node: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.Tuple):
            return tuple(self._default(item, namespace, tree) for item in node.elts)
        if isinstance(node, ast.Name) and node.id in namespace:
            assignments = [
                statement.value
                for statement in tree.body
                if isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == node.id
            ]
            match assignments:
                case [ast.Call(func=ast.Name(id="object"), args=[], keywords=[])] if (
                    namespace.get("object", vars(builtins).get("object")) is object
                    and type(namespace[node.id]) is object
                ):
                    return namespace[node.id]
                case [ast.Call(func=ast.Name(id=name), args=[], keywords=[])]:
                    owner = namespace.get(name)
                    definitions = [
                        item
                        for item in tree.body
                        if isinstance(item, ast.ClassDef) and item.name == name
                    ]
                    sentinel = namespace[node.id]
                    match definitions:
                        case [
                            ast.ClassDef(
                                decorator_list=[], bases=[], keywords=[], body=[ast.Pass()]
                            )
                        ]:
                            if (
                                type(owner) is type
                                and type(sentinel) is owner
                                and vars(type)["__bases__"].__get__(owner, type(owner))
                                == (object,)
                            ):
                                return sentinel
                        case [
                            ast.ClassDef(
                                decorator_list=[],
                                bases=[ast.Name(id="int")],
                                body=[ast.Pass()],
                            )
                        ]:
                            if (
                                type(owner) is type
                                and type(sentinel) is owner
                                and vars(type)["__bases__"].__get__(owner, type(owner))
                                == (int,)
                                and self._native_integer(sentinel)
                                and int.__index__(sentinel) == 0
                            ):
                                return sentinel
        msg = (
            "closed compiler default has no literal or native sentinel witness: "
            f"{ast.unparse(node)[:160]}; source={self._witness.source}"
        )
        raise ValueError(msg)

    @staticmethod
    def _builtin(
        name: str, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> p.AttributeProbe:
        value = namespace.get(name, vars(builtins).get(name))
        if name in {"enumerate", "zip", "map", "list", "tuple", "str"}:
            if type(value) is not type or vars(builtins).get(name) is not value:
                msg = f"closed compiler data type binding is not native: {name}"
                raise ValueError(msg)
            storage = vars(type)["__dict__"].__get__(value, type(value))
            constructor = storage.get("__new__")
            if (
                vars(type)["__name__"].__get__(value, type(value)) != name
                or vars(type)["__module__"].__get__(value, type(value)) != "builtins"
                or type(constructor) is not BuiltinFunctionType
                or constructor.__self__ is not value
                or constructor.__name__ != "__new__"
            ):
                msg = f"closed compiler data constructor is interposed: {name}"
                raise ValueError(msg)
            return value
        if (
            type(value) is not BuiltinFunctionType
            or vars(builtins).get(name) is not value
            or value.__self__ is not builtins
            or value.__module__ != "builtins"
            or value.__name__ != name
        ):
            msg = f"closed compiler builtin binding is not native: {name}"
            raise ValueError(msg)
        return value

    def _global(
        self,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if name not in namespace:
            if name in {
                "hasattr",
                "getattr",
                "exec",
                "isinstance",
                "str",
                "list",
                "tuple",
                "map",
            }:
                return self._builtin(name, namespace)
            if name == "bool" and vars(builtins).get(name) is bool:
                return bool
            msg = f"closed compiler global is not declared: {name}"
            raise ValueError(msg)
        value = namespace[name]
        bindings = [
            (statement, alias)
            for statement in tree.body
            if isinstance(statement, ast.Import | ast.ImportFrom)
            for alias in statement.names
            if (alias.asname or alias.name.split(".")[0]) == name
        ]
        if len(bindings) != 1:
            return self._constructed_global(name, value, namespace, tree)
        statement, alias = bindings[0]
        if isinstance(statement, ast.Import):
            expected = self._module(
                alias.name if alias.asname else alias.name.split(".")[0]
            )
        else:
            if statement.level or statement.module is None:
                msg = "closed compiler import requires an absolute physical supplier"
                raise ValueError(msg)
            provider = self._module(statement.module)
            self._source(provider)
            expected = vars(provider).get(alias.name)
        if value is not expected:
            msg = f"closed compiler import differs from its registered supplier: {name}"
            raise ValueError(msg)
        if type(value) is ModuleType:
            if value is sys:
                self._intern()
            else:
                self._source(value)
        return value

    def _constructed_global(
        self,
        name: str,
        value: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        """Authenticate a constructed global through its physical declaration.

        Returns:
            The native sentinel or regex value whose source construction is proved.

        Raises:
            ValueError: If no unique closed construction owns this binding.

        """
        assignments = [
            statement.value
            for statement in tree.body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
        ]
        if len(assignments) == 1 and isinstance(assignments[0], ast.Call):
            if type(value) is object:
                return self._default(ast.Name(id=name), namespace, tree)
            native = type(value)
            storage = vars(type)["__dict__"].__get__(native, type(native))
            operation = storage.get("findall")
            if (
                type(operation) is MethodDescriptorType
                and operation.__objclass__ is native
            ):
                self._regex(name, value, namespace, tree)
                return value
        msg = f"closed compiler global has no unique source import: {name}"
        raise ValueError(msg)

    def _intern(self) -> BuiltinFunctionType:
        """Authenticate the selected native string intrinsic and its interpreter.

        Returns:
            The registered native string intrinsic.

        Raises:
            ValueError: If its binding, supplier or physical interpreter differs.

        """
        path = FlextInfraWorkspaceEnvironmentProvenance.module_source("sys").unwrap()
        operation = vars(sys).get("intern")
        if self._module("sys") is not sys or path != Path(sys.executable).resolve():
            msg = "closed compiler string interning intrinsic is interposed"
            raise ValueError(msg)
        if (
            type(operation) is not BuiltinFunctionType
            or operation.__self__ is not sys
            or operation.__module__ != "sys"
            or operation.__name__ != "intern"
        ):
            msg = "closed compiler string interning intrinsic is interposed"
            raise ValueError(msg)
        if path not in self._inputs:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if state.content is None:
                msg = f"closed compiler interpreter is absent: {path}"
                raise ValueError(msg)
            self._inputs[path] = state
        return operation

    def _mapped_strings(
        self,
        node: ast.Call,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> t.VariadicTuple[str]:
        """Derive exact string map data without calling the selected callback.

        Returns:
            The exact string values consumed by the native map declaration.

        Raises:
            ValueError: If callback identity or input storage is unsupported.

        """
        match node:
            case ast.Call(
                func=ast.Name(id="map"),
                args=[operation_node, values_node],
                keywords=[],
            ) if "map" not in local:
                pass
            case _:
                msg = "closed compiler string map has unsupported construction"
                raise ValueError(msg)
        self._builtin("map", namespace)
        operation = self._expression(operation_node, local, namespace, tree)
        if (
            operation is not self._builtin("str", namespace)
            and operation is not self._intern()
        ):
            msg = "closed compiler map callback is outside native string data"
            raise ValueError(msg)
        values = self._expression(values_node, local, namespace, tree)
        if not (
            type(values) is str or type(values) is tuple or type(values) is list
        ) or any(type(value) is not str for value in values):
            msg = "closed compiler map contains authored conversion operands"
            raise ValueError(msg)
        return tuple(values)

    @staticmethod
    def _native_integer(value: p.AttributeProbe | None) -> TypeIs[int]:
        """Recognize actual integer ancestry without authored instance checks.

        Returns:
            Whether the native type's MRO contains the interpreter integer type.

        """
        return any(
            owner is int
            for owner in vars(type)["__mro__"].__get__(type(value), type(type(value)))
        )

    @staticmethod
    def _boolean(value: p.AttributeProbe) -> bool:
        if type(value) is bool:
            return value
        if value is None:
            return False
        if type(value) is int:
            return value != 0
        if (
            type(value) is str
            or type(value) is tuple
            or type(value) is list
            or type(value) is dict
        ):
            return len(value) != 0
        msg = "closed compiler condition has authored truth-value semantics"
        raise ValueError(msg)

    def _member(
        self,
        module: p.AttributeProbe,
        name: p.AttributeProbe,
    ) -> t.Pair[bool, p.AttributeProbe | None]:
        if type(module) is not ModuleType or type(name) is not str:
            msg = "closed compiler member lookup is not native module/string data"
            raise ValueError(msg)
        self._source(module)
        namespace = vars(module)
        if name in namespace:
            return True, namespace[name]
        if "__getattr__" in namespace:
            self._absent_member(module, name)
        return False, None

    def _absent_member(self, module: ModuleType, member: str) -> None:
        """Prove a literal hook ends at native AttributeError without running it.

        Raises:
            ValueError: If the selected hook path has unproved execution semantics.

        """
        function = vars(module)["__getattr__"]
        declaration, _tree, namespace = self._function(function)
        arguments = (*declaration.args.posonlyargs, *declaration.args.args)
        if (
            len(arguments) != 1
            or declaration.args.kwonlyargs
            or declaration.args.vararg is not None
            or declaration.args.kwarg is not None
            or declaration.args.defaults
        ):
            msg = "closed compiler module hook has unsupported argument storage"
            raise ValueError(msg)
        argument = arguments[0].arg
        statements = list(declaration.body)
        while statements:
            statement = statements.pop(0)
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and type(statement.value.value) is str
            ):
                continue
            if isinstance(statement, ast.If):
                condition = self._hook_condition(statement.test, argument, member)
                statements[:0] = statement.body if condition else statement.orelse
                continue
            if isinstance(statement, ast.Raise):
                self._hook_raise(statement, namespace, argument, member)
                return
            msg = (
                "closed compiler selected module-hook statement is unsupported: "
                f"{type(statement).__name__}"
            )
            raise ValueError(msg)
        msg = "closed compiler module hook has no proved missing-member outcome"
        raise ValueError(msg)

    @staticmethod
    def _hook_condition(test: ast.expr, argument: str, member: str) -> bool:
        """Read the selected literal member predicate without invoking the hook.

        Returns:
            Whether the physical literal predicate selects its body.

        Raises:
            ValueError: If the source predicate is outside the closed grammar.

        """
        match test:
            case ast.Compare(
                left=ast.Name(id=name), ops=[operation], comparators=[operand]
            ) if name == argument:
                pass
            case _:
                msg = "closed compiler hook condition is not a literal member test"
                raise ValueError(msg)
        if isinstance(operation, ast.In) and isinstance(operand, ast.Set):
            literals: list[str] = []
            for item in operand.elts:
                if not isinstance(item, ast.Constant) or type(item.value) is not str:
                    msg = "closed compiler hook membership has nonliteral operands"
                    raise ValueError(msg)
                literals.append(item.value)
            return member in literals
        if (
            isinstance(operation, ast.Eq)
            and isinstance(operand, ast.Constant)
            and type(operand.value) is str
        ):
            return member == operand.value
        msg = "closed compiler hook condition has unsupported semantics"
        raise ValueError(msg)

    def _hook_raise(
        self,
        statement: ast.Raise,
        namespace: t.MappingKV[str, p.AttributeProbe],
        argument: str,
        member: str,
    ) -> None:
        """Prove the selected raise uses the native exception and literal message.

        Raises:
            ValueError: If exception syntax, identity or constructor differs.

        """
        match statement:
            case ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="AttributeError"), args=[message], keywords=[]
                ),
                cause=None,
            ):
                pass
            case _:
                msg = "closed compiler hook does not raise native AttributeError"
                raise ValueError(msg)
        error = namespace.get("AttributeError", vars(builtins).get("AttributeError"))
        if type(error) is not type or error is not vars(builtins).get("AttributeError"):
            msg = "closed compiler hook exception binding is not native"
            raise ValueError(msg)
        storage = vars(type)["__dict__"].__get__(error, type(error))
        initializer = storage.get("__init__")
        if (
            (
                vars(type)["__name__"].__get__(error, type(error)),
                vars(type)["__module__"].__get__(error, type(error)),
            )
            != ("AttributeError", "builtins")
            or not (
                type(initializer) is WrapperDescriptorType
                or type(initializer) is MethodDescriptorType
            )
            or initializer.__objclass__ is not error
        ):
            msg = "closed compiler hook exception constructor is interposed"
            raise ValueError(msg)
        self._hook_message(message, namespace, argument, member)

    @staticmethod
    def _hook_message(
        message: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        argument: str,
        member: str,
    ) -> None:
        """Validate literal exception text and its exact string substitutions.

        Raises:
            TypeError: If a substitution has authored string semantics.
            ValueError: If message syntax or binding is outside the closed grammar.

        """
        match message:
            case ast.Constant(value=value) if type(value) is str:
                return
            case ast.JoinedStr(values=parts):
                pass
            case _:
                msg = "closed compiler hook exception message is not literal text"
                raise ValueError(msg)
        for part in parts:
            if isinstance(part, ast.Constant) and type(part.value) is str:
                continue
            if (
                not isinstance(part, ast.FormattedValue)
                or not isinstance(part.value, ast.Name)
                or part.format_spec is not None
                or part.conversion not in {-1, ord("r")}
            ):
                msg = "closed compiler hook exception message invokes formatting"
                raise ValueError(msg)
            name = part.value.id
            if name == argument:
                value = member
            elif name == "__name__":
                value = namespace.get(name)
            else:
                msg = "closed compiler hook exception message has an opaque binding"
                raise ValueError(msg)
            if type(value) is not str:
                msg = "closed compiler hook exception message has an authored operand"
                raise TypeError(msg)

    def _expression(
        self,
        node: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.Name):
            return (
                local[node.id]
                if node.id in local
                else self._global(node.id, namespace, tree)
            )
        if isinstance(node, ast.Attribute):
            return self._attribute_expression(node, local, namespace, tree)
        if isinstance(node, ast.Dict):
            return self._dictionary_expression(node, local, namespace, tree)
        if isinstance(node, ast.Tuple):
            return tuple(
                self._expression(item, local, namespace, tree) for item in node.elts
            )
        return self._computed_expression(node, local, namespace, tree)

    def _attribute_expression(
        self,
        node: ast.Attribute,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        """Resolve only the declared tuple constructor or native interning operation.

        Returns:
            The authenticated native operation.

        Raises:
            ValueError: If the attribute is outside the closed compiler grammar.

        """
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "tuple"
            and node.attr == "__new__"
            and self._global("tuple", namespace, tree) is tuple
        ):
            return vars(tuple)["__new__"]
        if node.attr == "intern":
            receiver = self._expression(node.value, local, namespace, tree)
            if receiver is sys:
                return self._intern()
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _dictionary_expression(
        self,
        node: ast.Dict,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> t.DictKV[str, p.AttributeProbe]:
        """Build admitted native dictionary storage from literal string keys.

        Returns:
            The fresh dictionary retained by this interpretation.

        Raises:
            ValueError: If unpacking or authored keys would execute.

        """
        result: t.DictKV[str, p.AttributeProbe] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                msg = "closed compiler dictionary unpacking is unsupported"
                raise ValueError(msg)
            scalar = self._expression(key, local, namespace, tree)
            if type(scalar) is not str:
                msg = "closed compiler dictionary keys must be exact strings"
                raise ValueError(msg)
            result[scalar] = self._expression(value, local, namespace, tree)
        self._dictionaries.add(id(result))
        return result

    def _computed_expression(
        self,
        node: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._boolean(
                self._expression(node.operand, local, namespace, tree)
            )
        if isinstance(node, ast.BoolOp):
            return self._boolean_expression(node, local, namespace, tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._addition_expression(node, local, namespace, tree)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            return self._comparison_expression(node, local, namespace, tree)
        return self._data_expression(node, local, namespace, tree)

    def _boolean_expression(
        self,
        node: ast.BoolOp,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        value = self._expression(node.values[0], local, namespace, tree)
        for item in node.values[1:]:
            if isinstance(node.op, ast.And) and not self._boolean(value):
                return value
            if isinstance(node.op, ast.Or) and self._boolean(value):
                return value
            value = self._expression(item, local, namespace, tree)
        return value

    def _addition_expression(
        self,
        node: ast.BinOp,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        left = self._expression(node.left, local, namespace, tree)
        right = self._expression(node.right, local, namespace, tree)
        if type(left) is str and type(right) is str:
            return left + right
        if type(left) is int and type(right) is int:
            return left + right
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _comparison_expression(
        self,
        node: ast.Compare,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        left = self._expression(node.left, local, namespace, tree)
        right = self._expression(node.comparators[0], local, namespace, tree)
        if isinstance(node.ops[0], ast.Is):
            return left is right
        if isinstance(node.ops[0], ast.IsNot):
            return left is not right
        if type(left) is type(right) and (
            type(left) is str or type(left) is int or type(left) is bool
        ):
            if isinstance(node.ops[0], ast.Eq):
                return left == right
            if isinstance(node.ops[0], ast.NotEq):
                return left != right
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _data_expression(
        self,
        node: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if isinstance(node, ast.JoinedStr):
            return self._interpolation(node, local, namespace, tree)
        if isinstance(node, ast.Subscript):
            return self._subscript(node, local, namespace, tree)
        return self._call_expression(node, local, namespace, tree)

    def _interpolation(
        self,
        node: ast.JoinedStr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> str:
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant) and type(part.value) is str:
                parts.append(part.value)
            elif (
                isinstance(part, ast.FormattedValue)
                and part.conversion == -1
                and part.format_spec is None
            ):
                value = self._expression(part.value, local, namespace, tree)
                if type(value) is not str:
                    msg = "closed compiler interpolation is not exact string data"
                    raise ValueError(msg)
                parts.append(value)
            else:
                msg = "closed compiler interpolation has executable formatting"
                raise ValueError(msg)
        return "".join(parts)

    def _subscript(
        self,
        node: ast.Subscript,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        mapping = self._expression(node.value, local, namespace, tree)
        if isinstance(node.slice, ast.Slice):
            raw_bounds = tuple(
                None if item is None else self._expression(item, local, namespace, tree)
                for item in (node.slice.lower, node.slice.upper, node.slice.step)
            )
            bounds: t.MutableSequenceOf[int | None] = []
            for bound in raw_bounds:
                if bound is not None and type(bound) is not int:
                    msg = "closed compiler slice has authored operands"
                    raise ValueError(msg)
                bounds.append(bound)
            if type(mapping) is str or type(mapping) is tuple or type(mapping) is list:
                return mapping[slice(*bounds)]
            msg = "closed compiler slice has authored operands"
            raise ValueError(msg)
        key = self._expression(node.slice, local, namespace, tree)
        if type(mapping) is dict and type(key) is str:
            return mapping[key]
        if type(key) is int and (
            type(mapping) is str or type(mapping) is tuple or type(mapping) is list
        ):
            return mapping[key]
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _call_expression(
        self,
        node: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if not isinstance(node, ast.Call) or node.keywords:
            msg = f"closed compiler expression is unsupported: {type(node).__name__}"
            raise ValueError(msg)
        match node.func, node.args:
            case ast.Name(id="isinstance"), [first, second] if (
                "isinstance" not in local
            ):
                return self._instance_call((first, second), local, namespace, tree)
            case ast.Name(id=operation), [argument] if (
                operation in {"str", "list", "tuple"} and operation not in local
            ):
                return self._conversion(operation, argument, local, namespace, tree)
            case ast.Name(id=operation), arguments if operation in {
                "hasattr",
                "getattr",
            }:
                return self._member_call(operation, arguments, local, namespace, tree)
            case ast.Name(id=operation), arguments if (
                operation in {"zip", "enumerate", "len"} and operation not in local
            ):
                return self._iteration_call(
                    operation, arguments, local, namespace, tree
                )
            case ast.Attribute() as function, arguments:
                return self._method_call(function, arguments, local, namespace, tree)
        function = self._expression(node.func, local, namespace, tree)
        if type(function) is FunctionType and len(node.args) == 1:
            text = self._expression(node.args[0], local, namespace, tree)
            if type(text) is str:
                return self._dedent(function, text)
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _instance_call(
        self,
        arguments: t.Pair[ast.expr, ast.expr],
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> bool:
        self._builtin("isinstance", namespace)
        value, expected = (
            self._expression(item, local, namespace, tree) for item in arguments
        )
        if expected is self._builtin("str", namespace) and (
            type(value) is str or type(value) is tuple or type(value) is list
        ):
            return type(value) is str
        msg = "closed compiler instance predicate has authored operands"
        raise ValueError(msg)

    def _conversion(
        self,
        operation: str,
        argument: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        self._builtin(operation, namespace)
        if (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Name)
            and argument.func.id == "map"
            and operation in {"list", "tuple"}
        ):
            values = self._mapped_strings(argument, local, namespace, tree)
            return list(values) if operation == "list" else values
        value = self._expression(argument, local, namespace, tree)
        if operation == "str" and type(value) is str:
            return value
        if type(value) is str or type(value) is tuple or type(value) is list:
            if operation == "list":
                return list(value)
            if operation == "tuple":
                return tuple(value)
        msg = "closed compiler construction has authored data operands"
        raise ValueError(msg)

    def _member_call(
        self,
        operation: str,
        arguments: t.SequenceOf[ast.expr],
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if operation in local:
            msg = "closed compiler shadows its native lookup"
            raise ValueError(msg)
        self._builtin(operation, namespace)
        match arguments:
            case [receiver, member]:
                present, value = self._member(
                    self._expression(receiver, local, namespace, tree),
                    self._expression(member, local, namespace, tree),
                )
            case _:
                msg = "closed compiler member lookup has unsupported arity"
                raise ValueError(msg)
        if operation == "hasattr":
            return present
        if present:
            return value
        msg = "closed compiler requires an absent module member"
        raise ValueError(msg)

    def _iteration_call(
        self,
        operation: str,
        arguments: t.SequenceOf[ast.expr],
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        self._builtin(operation, namespace)
        values = tuple(
            self._expression(item, local, namespace, tree) for item in arguments
        )
        sequences: t.MutableSequenceOf[t.SequenceOf[p.AttributeProbe]] = []
        for argument in values:
            if not (
                type(argument) is tuple
                or type(argument) is list
                or type(argument) is str
            ):
                msg = "closed compiler iteration has authored operands"
                raise ValueError(msg)
            sequences.append(argument)
        if operation == "zip":
            return tuple(zip(*sequences, strict=False))
        if len(sequences) != 1:
            msg = "closed compiler iteration has unsupported arity"
            raise ValueError(msg)
        if operation == "enumerate":
            return tuple(enumerate(sequences[0]))
        return len(sequences[0])

    def _method_call(
        self,
        function: ast.Attribute,
        arguments: t.SequenceOf[ast.expr],
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        receiver = self._expression(function.value, local, namespace, tree)
        values = tuple(
            self._expression(item, local, namespace, tree) for item in arguments
        )
        if type(receiver) is str:
            return self._string_method(function.attr, receiver, values)
        if id(receiver) in self._patterns:
            return self._pattern_method(
                function.attr, self._patterns[id(receiver)], values
            )
        if type(receiver) is ModuleType and function.attr == "sub":
            return self._prefix_sub(receiver, values)
        if receiver is sys and function.attr == "intern":
            self._intern()
            if len(values) == 1 and type(values[0]) is str:
                return values[0]
            msg = "closed compiler interning has authored data operands"
            raise ValueError(msg)
        msg = "closed compiler method is outside native string/regex data"
        raise ValueError(msg)

    @staticmethod
    def _string_method(
        operation: str,
        receiver: str,
        arguments: t.VariadicTuple[p.AttributeProbe],
    ) -> p.AttributeProbe:
        match operation, arguments:
            case "replace", (old, new) if type(old) is str and type(new) is str:
                return str.replace(receiver, old, new)
            case "split", ():
                return str.split(receiver)
            case "startswith", (prefix,) if type(prefix) is str:
                return str.startswith(receiver, prefix)
            case "join", (parts,) if (
                type(parts) is tuple or type(parts) is list
            ) and all(type(item) is str for item in parts):
                return str.join(receiver, parts)
        msg = "closed compiler method is outside native string/regex data"
        raise ValueError(msg)

    @staticmethod
    def _pattern_method(
        operation: str,
        pattern: str,
        arguments: t.VariadicTuple[p.AttributeProbe],
    ) -> p.AttributeProbe:
        match operation, arguments:
            case "sub", (replacement, text) if (
                type(replacement) is str
                and type(text) is str
                and pattern == "^[ \t]+$"
                and not replacement
            ):
                return "\n".join(
                    ""
                    if line and all(character in " \t" for character in line)
                    else line
                    for line in text.split("\n")
                )
            case "findall", (text,) if (
                type(text) is str and pattern == "(^[ \t]*)(?:[^ \t\n])"
            ):
                return [
                    line[: len(line) - len(line.lstrip(" \t"))]
                    for line in text.split("\n")
                    if line and any(character not in " \t" for character in line)
                ]
        msg = "closed compiler regex operation is outside its physical data grammar"
        raise ValueError(msg)

    def _statements(
        self,
        statements: t.SequenceOf[ast.stmt],
        local: t.MutableMappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        """Follow closed control flow and delegate only admitted local effects.

        Returns:
            The selected return or break value, or None on fallthrough.

        """
        for statement in statements:
            if isinstance(statement, ast.For) and not statement.orelse:
                returned = self._loop(statement, local, namespace, tree)
            elif isinstance(statement, ast.Break):
                return statement
            elif isinstance(statement, ast.If):
                condition = self._boolean(
                    self._expression(statement.test, local, namespace, tree)
                )
                returned = self._statements(
                    statement.body if condition else statement.orelse,
                    local,
                    namespace,
                    tree,
                )
            elif isinstance(statement, ast.Return) and statement.value is not None:
                return self._expression(statement.value, local, namespace, tree)
            else:
                self._statement_effect(statement, local, namespace, tree)
                continue
            if returned is not None:
                return returned
        return None

    def _statement_effect(
        self,
        statement: ast.stmt,
        local: t.MutableMappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        """Apply a local write, literal docstring or closed compilation.

        Raises:
            ValueError: If the effect or its operands are unsupported.

        """
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and type(statement.value.value) is str
        ):
            return
        if isinstance(statement, ast.Assign | ast.AnnAssign):
            self._assignment(statement, local, namespace, tree)
            return
        if (
            isinstance(statement, ast.AugAssign)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.op, ast.Add)
        ):
            current = local[statement.target.id]
            added = self._expression(statement.value, local, namespace, tree)
            if type(current) is not str or type(added) is not str:
                msg = "closed compiler augmentation has authored operands"
                raise ValueError(msg)
            local[statement.target.id] = current + added
            return
        if isinstance(statement, ast.Pass):
            return
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            self._compilation(statement.value, local, namespace, tree)
            return
        msg = f"closed compiler statement is unsupported: {type(statement).__name__}"
        raise ValueError(msg)

    def _assignment(
        self,
        statement: ast.Assign | ast.AnnAssign,
        local: t.MutableMappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        """Write a closed expression only to admitted local or dictionary storage.

        Raises:
            TypeError: If a dictionary target or key has an unsupported type.
            ValueError: If the target is not admitted local or dictionary storage.

        """
        if statement.value is None:
            msg = "closed compiler assignment has no value"
            raise ValueError(msg)
        value = self._expression(statement.value, local, namespace, tree)
        targets = (
            statement.targets
            if isinstance(statement, ast.Assign)
            else (statement.target,)
        )
        for target in targets:
            match target:
                case ast.Name(id=name):
                    local[name] = value
                case ast.Subscript(value=storage, slice=selector):
                    mapping = self._expression(storage, local, namespace, tree)
                    key = self._expression(selector, local, namespace, tree)
                    if type(mapping) is not dict or type(key) is not str:
                        msg = "closed compiler assignment has foreign native storage"
                        raise TypeError(msg)
                    if id(mapping) not in self._dictionaries:
                        msg = "closed compiler assignment has foreign native storage"
                        raise ValueError(msg)
                    mapping[key] = value
                case _:
                    msg = "closed compiler assignment target is unsupported"
                    raise ValueError(msg)

    def _loop(
        self,
        statement: ast.For,
        local: t.MutableMappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        """Evaluate one native data loop, consuming only its own break.

        Returns:
            The selected return value, or None when the loop finishes or breaks.

        Raises:
            ValueError: If the iterable has authored iteration semantics.

        """
        items = self._expression(statement.iter, local, namespace, tree)
        if (
            type(items) is not tuple
            and type(items) is not list
            and type(items) is not str
        ):
            msg = "closed compiler loop has an authored iterator"
            raise ValueError(msg)
        for item in items:
            self._assign(statement.target, item, local)
            returned = self._statements(statement.body, local, namespace, tree)
            if type(returned) is ast.Break:
                break
            if returned is not None:
                return returned
        return None

    def _compilation(
        self,
        call: ast.Call,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        """Compile admitted source without executing its emitted function.

        Raises:
            TypeError: If compilation operands have unsupported native types.
            ValueError: If source or storage is not an admitted native compilation.

        """
        match call:
            case ast.Call(
                func=ast.Name(id="exec"),
                args=[source, global_scope, local_scope],
                keywords=[],
            ):
                pass
            case _:
                msg = "closed compiler effect is not a native compilation"
                raise ValueError(msg)
        self._builtin("exec", namespace)
        text, globals_, locals_ = (
            self._expression(item, local, namespace, tree)
            for item in (source, global_scope, local_scope)
        )
        if (
            type(text) is not str
            or type(globals_) is not dict
            or type(locals_) is not dict
        ):
            msg = "closed compiler requires fresh exact native dictionaries"
            raise TypeError(msg)
        if (
            id(globals_) not in self._dictionaries
            or id(locals_) not in self._dictionaries
            or globals_ is locals_
        ):
            msg = "closed compiler requires fresh exact native dictionaries"
            raise ValueError(msg)
        proof = self._emission(text, globals_)
        self._emitted[id(proof.code)] = proof
        locals_[proof.code.co_qualname] = proof.code

    def _assign(
        self,
        target: ast.expr,
        value: p.AttributeProbe,
        local: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        if isinstance(target, ast.Name):
            local[target.id] = value
            return
        if (
            isinstance(target, ast.Tuple)
            and type(value) is tuple
            and len(target.elts) == len(value)
        ):
            for child, item in zip(target.elts, value, strict=True):
                self._assign(child, item, local)
            return
        msg = "closed compiler loop target is not native fixed tuple storage"
        raise ValueError(msg)

    @staticmethod
    def _emission(
        text: str,
        globals_: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> m.Infra.NativeGeneratedFunctionProof:
        parsed = ast.parse(text)
        if len(parsed.body) != 1 or not isinstance(parsed.body[0], ast.FunctionDef):
            msg = "closed compiler output is not one function declaration"
            raise ValueError(msg)
        function = parsed.body[0]
        arguments = (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
        if (
            function.decorator_list
            or function.type_params
            or function.args.defaults
            or function.args.kw_defaults
        ):
            msg = "closed compiler output has unsupported construction inputs"
            raise ValueError(msg)
        if (
            function.args.vararg is not None
            or function.args.kwarg is not None
            or "__builtins__" in globals_
        ):
            msg = "closed compiler output has unsupported construction inputs"
            raise ValueError(msg)
        globals_["__builtins__"] = vars(builtins)
        annotations = FlextInfraWorkspaceGeneratedFunction._emission_annotations(
            (
                *((argument.arg, argument.annotation) for argument in arguments),
                ("return", function.returns),
            ),
            globals_,
        )
        root = builtins.compile(
            text,
            "<string>",
            "exec",
            dont_inherit=True,
            optimize=sys.flags.optimize,
        )
        codes = tuple(item for item in root.co_consts if type(item) is CodeType)
        if len(codes) != 1 or codes[0].co_freevars or codes[0].co_cellvars:
            msg = "closed compiler output has executable nested construction"
            raise ValueError(msg)
        return m.Infra.NativeGeneratedFunctionProof(
            code=codes[0],
            globals=dict(globals_),
            annotations=annotations,
            defaults=None,
            keyword_defaults=None,
            closure=(),
            inputs=(),
        )

    @staticmethod
    def _emission_annotations(
        declarations: t.VariadicTuple[t.Pair[str, ast.expr | None]],
        globals_: t.MappingKV[str, p.AttributeProbe],
    ) -> t.DictKV[str, p.AttributeProbe]:
        annotations: t.DictKV[str, p.AttributeProbe] = {}
        for name, annotation in declarations:
            if annotation is None:
                continue
            if isinstance(annotation, ast.Constant) and type(annotation.value) is str:
                annotations[name] = annotation.value
            elif isinstance(annotation, ast.Name):
                if annotation.id in globals_:
                    annotations[name] = globals_[annotation.id]
                elif annotation.id == "bool" and vars(builtins).get("bool") is bool:
                    annotations[name] = bool
                else:
                    msg = "closed compiler annotation binding is not declared"
                    raise ValueError(msg)
            else:
                msg = "closed compiler annotation would execute an expression"
                raise ValueError(msg)
        return annotations

    def _dedent(self, function: FunctionType, text: str) -> str:
        """Interpret the physical transform body without invoking Python helpers.

        Returns:
            The exact string produced by the closed physical transform.

        Raises:
            ValueError: If the transform supplier, body or output is unsupported.

        """
        declaration, tree, namespace = self._function(function)
        module = self._module(function.__module__)
        if (
            function.__module__ not in sys.stdlib_module_names
            or function.__name__ != "dedent"
            or vars(module).get("dedent") is not function
        ):
            msg = "closed compiler string transform is not the physical stdlib dedent"
            raise ValueError(msg)
        if (
            len(declaration.args.args) != 1
            or declaration.args.posonlyargs
            or declaration.args.kwonlyargs
            or declaration.args.vararg is not None
            or declaration.args.kwarg is not None
        ):
            msg = "closed compiler string transform is not the physical stdlib dedent"
            raise ValueError(msg)
        self._dedent_callbacks(declaration, namespace, tree)
        returned = self._statements(
            declaration.body,
            {declaration.args.args[0].arg: text},
            namespace,
            tree,
        )
        if type(returned) is not str:
            msg = "closed compiler string transform did not return exact text"
            raise ValueError(msg)
        return returned

    def _dedent_callbacks(
        self,
        declaration: ast.FunctionDef,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        for call in (
            node for node in ast.walk(declaration) if isinstance(node, ast.Call)
        ):
            if isinstance(call.func, ast.Name) and call.func.id in {"zip", "enumerate"}:
                self._builtin(call.func.id, namespace)
            if not isinstance(call.func, ast.Attribute) or not isinstance(
                call.func.value, ast.Name
            ):
                continue
            name = call.func.value.id
            if name not in namespace:
                continue
            target = namespace[name]
            if type(target) is ModuleType:
                self._global(name, namespace, tree)
                operation = vars(target).get(call.func.attr)
                if type(operation) is not FunctionType:
                    msg = "dedent module callback is not a physical function"
                    raise ValueError(msg)
                self._function(operation)
            elif call.func.attr in {"sub", "findall"}:
                self._regex(name, target, namespace, tree)

    def _prefix_sub(
        self,
        module: ModuleType,
        arguments: tuple[p.AttributeProbe, ...],
    ) -> str:
        """Admit only the native regex operation's literal multiline prefix form.

        Returns:
            The text after removing the declared multiline prefix.

        Raises:
            ValueError: If native delegation or literal operands are unsupported.

        """
        match arguments:
            case (pattern, replacement, text):
                pass
            case _:
                msg = "closed compiler regex substitution requires exact string data"
                raise ValueError(msg)
        if (
            type(pattern) is not str
            or type(replacement) is not str
            or type(text) is not str
        ):
            msg = "closed compiler regex substitution requires exact string data"
            raise ValueError(msg)
        declaration, _tree, namespace = self._function(vars(module).get("sub"))
        self._function(namespace.get(self._regex_delegation(declaration)))
        if (
            replacement
            or not pattern.startswith("(?m)^")
            or any(character not in " \t" for character in pattern[5:])
        ):
            msg = "closed compiler regex pattern is outside literal prefix grammar"
            raise ValueError(msg)
        prefix = pattern[5:]
        return "\n".join(line.removeprefix(prefix) for line in text.split("\n"))

    @staticmethod
    def _regex_delegation(declaration: ast.FunctionDef) -> str:
        body = [
            statement
            for statement in declaration.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and type(statement.value.value) is str
            )
        ]
        # The wrapper's only preceding branch handles positional extras, which
        # this exact three-argument call does not supply.
        match body:
            case [
                ast.If(test=ast.Name(id=extra), orelse=[]),
                ast.Return(value=ast.Call(keywords=[]) as result),
            ] if (
                declaration.args.vararg is not None
                and extra == declaration.args.vararg.arg
            ):
                pass
            case _:
                msg = "closed compiler regex wrapper has unsupported source semantics"
                raise ValueError(msg)
        match (
            result.func,
            result.args,
            declaration.args.args,
            declaration.args.kwonlyargs,
        ):
            case (
                ast.Attribute(
                    attr="sub",
                    value=ast.Call(
                        func=ast.Name(id=compiler_name),
                        args=[_, _] as compiler_inputs,
                        keywords=[],
                    ),
                ),
                [_, _, _] as operation_inputs,
                [_, _, _] as positional,
                [_, _] as keywords,
            ):
                pass
            case _:
                msg = "closed compiler regex wrapper is not its native delegation"
                raise ValueError(msg)
        expected = (
            positional[0].arg,
            keywords[1].arg,
            positional[1].arg,
            positional[2].arg,
            keywords[0].arg,
        )
        if any(
            not isinstance(node, ast.Name) or node.id != name
            for node, name in zip(
                (*compiler_inputs, *operation_inputs), expected, strict=True
            )
        ):
            msg = "closed compiler regex delegation operands differ from source"
            raise ValueError(msg)
        return compiler_name

    def _regex(
        self,
        name: str,
        pattern: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        """Authenticate regex identity and literal state without running its factory.

        Raises:
            TypeError: If observed regex data or flags have unsupported native types.
            ValueError: If its source, descriptors or state do not match.

        """
        assignments = [
            statement.value
            for statement in tree.body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
        ]
        match assignments:
            case [
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id=module_name), attr="compile"),
                    args=[
                        ast.Constant(value=literal),
                        ast.Attribute(value=ast.Name(id=flag_module), attr=flag_name),
                    ],
                    keywords=[],
                )
            ] if type(literal) is str and flag_module == module_name:
                pass
            case _:
                msg = "dedent regex has no closed physical constructor"
                raise ValueError(msg)
        supplier = self._global(module_name, namespace, tree)
        if type(supplier) is not ModuleType or vars(supplier).get(
            "Pattern"
        ) is not type(pattern):
            msg = "dedent regex is not its registered native pattern type"
            raise ValueError(msg)
        self._function(vars(supplier)["compile"])
        native = type(pattern)
        storage = vars(type)["__dict__"].__get__(native, type(native))
        for operation in ("sub", "findall"):
            descriptor = storage.get(operation)
            if (
                type(descriptor) is not MethodDescriptorType
                or descriptor.__objclass__ is not native
            ):
                msg = "dedent pattern has no interpreter-owned regex operations"
                raise ValueError(msg)
        observed = {}
        for attribute in ("pattern", "flags"):
            descriptor = storage.get(attribute)
            if not (
                type(descriptor) is MemberDescriptorType
                or type(descriptor) is GetSetDescriptorType
            ) or descriptor.__objclass__ is not type(pattern):
                msg = "dedent regex has no native read-only state"
                raise ValueError(msg)
            observed[attribute] = descriptor.__get__(pattern, type(pattern))
        flag = vars(supplier).get(flag_name)
        unicode = vars(supplier).get("UNICODE")
        if not self._native_integer(flag) or not self._native_integer(unicode):
            msg = "dedent regex flags are not native integers"
            raise TypeError(msg)
        if type(observed["pattern"]) is not str or type(observed["flags"]) is not int:
            msg = "dedent regex state differs from its physical constructor"
            raise TypeError(msg)
        if observed["pattern"] != literal or observed["flags"] != (
            int.__index__(flag) | int.__index__(unicode)
        ):
            msg = "dedent regex state differs from its physical constructor"
            raise ValueError(msg)
        self._patterns[id(pattern)] = literal


__all__: t.VariadicTuple[str] = ("FlextInfraWorkspaceGeneratedFunction",)
