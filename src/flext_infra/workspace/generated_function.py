"""Closed source-template witnesses for module-level generated functions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import sys
from dis import get_instructions
from importlib.machinery import FrozenImporter
from inspect import CO_VARARGS, CO_VARKEYWORDS
from pathlib import Path
from types import (
    BuiltinFunctionType,
    CodeType,
    FunctionType,
    GetSetDescriptorType,
    MemberDescriptorType,
    MethodDescriptorType,
    ModuleType,
    NoneType,
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
        self._inputs: t.DictKV[Path, m.Cli.AtomicFileState] = {
            witness.source: witness.state,
        }
        self._trees: t.DictKV[Path, ast.Module] = {
            witness.source: ast.parse(
                witness.module.source_code,
                filename=str(witness.source),
            ),
        }
        self._codes: t.DictKV[Path, p.Infra.NativeCodeIdentity] = {
            witness.source: witness.code,
        }
        self._emitted: t.DictKV[int, m.Infra.NativeGeneratedFunctionProof] = {}
        self._dictionaries: set[int] = set()
        self._patterns: t.DictKV[int, str] = {}

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
            ValueError: If a source binding or closed compiler grammar is unproved.

        """
        engine = cls(witness)
        namespace = engine._module(supplier)
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
        current: p.AttributeProbe | None = value
        holder = type(current)
        if holder is classmethod or holder is staticmethod:
            # The builtin descriptor's own C member, never an authored hook.
            current = vars(holder)["__func__"].__get__(current, holder)
        functions: list[FunctionType] = []
        seen: set[int] = set()
        while type(current) is FunctionType:
            if id(current) in seen:
                msg = "generated receiver function wrapper chain is cyclic"
                raise ValueError(msg)
            seen.add(id(current))
            functions.append(current)
            current = vars(current).get("__wrapped__")
        return tuple(functions)

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
        if "__attrs_attrs__" in namespace and "__attrs_props__" in namespace:
            return engine._compile_attrs(value, owner, attribute, namespace, qualified)
        helper = engine._attrs_helper(owner, attribute, namespace)
        if helper is not None:
            return engine._compile_attrs_helper(
                (value, owner), attribute, namespace, qualified, helper
            )
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

    def _compile_attrs(
        self,
        value: FunctionType,
        owner: p.AttributeProbe,
        attribute: str,
        storage: t.MappingKV[str, p.AttributeProbe],
        qualified: str,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Re-run the authenticated attrs script builders on stored class state.

        attrs keeps its final construction inputs on the class: the
        ``__attrs_attrs__`` records (after any field transformer) and the
        ``__attrs_props__`` options. The physical builders receive only that
        native data and fresh plain receivers carrying the class identity; no
        authored decorator, metaclass, factory, validator, converter or
        transformer runs.

        Returns:
            The independent emission of the observed generated method, or the
            first stored class state that differs from what attrs writes.

        Raises:
            ValueError: If the builders did not emit the class slot.

        """
        result_type = r[m.Infra.NativeGeneratedFunctionProof]
        namespace = vars(self._module("attr._make"))
        self._attrs_sdk(namespace)
        module = self._witness.module.get_name()
        if storage.get(attribute) is not value or not self._same_default(
            (module, f"{qualified}.{attribute}", attribute),
            (value.__module__, value.__qualname__, value.__name__),
        ):
            return result_type.fail(
                f"native attrs generated method is not its class slot: {attribute}"
            )
        stored = self._attrs_records(storage, namespace, qualified)
        if stored.failure:
            return result_type.from_failure(stored)
        options = self._attrs_props(storage, namespace)
        if options.failure:
            return result_type.from_failure(options)
        records, props = stored.value, options.value
        layout = self._attrs_layout(owner, storage, records, props, namespace)
        if layout.failure:
            return result_type.from_failure(layout)
        identity = type(
            qualified.rsplit(".", 1)[-1],
            (object,),
            {"__module__": module, "__qualname__": qualified},
        )
        script, globs, init_name, annotations = self._attrs_script(
            (identity, owner), records, props, namespace, qualified
        )
        local: t.DictKV[str, p.AttributeProbe] = {}
        self._attrs_builder(namespace, "_compile_and_eval")(
            script, globs, local, self._attrs_filename(value, identity, namespace)
        )
        expected = local.get(attribute)
        if type(expected) is not FunctionType:
            msg = f"native attrs builders did not emit the class slot: {attribute}"
            raise ValueError(msg)
        if attribute == init_name:
            expected.__annotations__ = dict(annotations)
        self._inputs_current("native attrs compiler input changed")
        return result_type.ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=expected.__code__,
                globals=expected.__globals__,
                annotations=expected.__annotations__,
                defaults=expected.__defaults__,
                keyword_defaults=expected.__kwdefaults__,
                closure=(),
                inputs=tuple(self._inputs.values()),
                hashed=self._attrs_hashed(identity, namespace),
            )
        )

    def _attrs_hashed(
        self, receiver: type, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> t.VariadicTuple[str]:
        """Derive the strings whose hash the attrs hash builder embeds.

        The builder hashes the unique file name it derives for the receiver;
        string hashing is randomized per process, so evidence names the string.

        Returns:
            Each file name the physical hash builder passes to ``hash``.

        Raises:
            TypeError: If the file name builder returns foreign storage.
            ValueError: If the builder derives no file name from a literal label.

        """
        declaration, _tree, _namespace = self._function(
            namespace.get("_make_hash_script"),
            source_name="_make_hash_script",
            source_namespace=namespace,
        )
        labels = [
            label
            for node in ast.walk(declaration)
            for label in (
                (node.args[1].value,)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_generate_unique_filename"
                and len(node.args) == len(("cls", "func_name"))
                and isinstance(node.args[1], ast.Constant)
                and type(node.args[1].value) is str
                else ()
            )
        ]
        if not labels:
            msg = "native attrs hash builder derives no literal file name"
            raise ValueError(msg)
        builder = self._attrs_builder(namespace, "_generate_unique_filename")
        names = tuple(builder(receiver, label) for label in labels)
        if any(type(name) is not str for name in names):
            msg = "native attrs file name builder returned foreign storage"
            raise TypeError(msg)
        return tuple(str(name) for name in names)

    def _attrs_helper(
        self,
        owner: p.AttributeProbe,
        attribute: str,
        storage: t.MappingKV[str, p.AttributeProbe],
    ) -> t.Pair[FunctionType, ast.Call] | None:
        """Elect the attrs class helper whose physical application wrote a slot.

        attrs completes its own record classes with module statements such as
        ``Factory = _add_hash(_add_eq(_add_repr(Factory, attrs=_f), ...))``.

        Returns:
            The helper and its physical call, or None outside that statement form.

        """
        sdk = sys.modules.get("attr._make")
        supplier = storage.get("__module__")
        if (
            type(sdk) is not ModuleType
            or type(supplier) is not str
            or supplier != self._witness.module.get_name()
        ):
            return None
        namespace = vars(self._module(supplier))
        aliases = {
            name for name, item in namespace.items() if type(name) is str and item is owner
        }
        statements = [
            node.value
            for node in self._trees[self._witness.source].body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in aliases
            and isinstance(node.value, ast.Call)
        ]
        if len(statements) != 1:
            return None
        call: ast.expr = statements[0]
        while isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
            helper = namespace.get(call.func.id)
            if helper is not vars(sdk).get(call.func.id) or type(helper) is not FunctionType:
                return None
            if attribute in self._attrs_helper_slots(helper, call.func.id, vars(sdk)):
                return helper, call
            match call.args:
                case [inner]:
                    call = inner
                case _:
                    return None
        return None

    def _attrs_helper_slots(
        self,
        helper: FunctionType,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> frozenset[str]:
        """Derive the class slots a helper fills from its compiled globals.

        Returns:
            Every ``cls.<slot> = globs["<slot>"]`` target of the physical helper.

        """
        declaration, _tree, _namespace = self._function(
            helper, source_name=name, source_namespace=namespace
        )
        slots: set[str] = set()
        for node in ast.walk(declaration):
            match node:
                case ast.Assign(
                    targets=[ast.Attribute(value=ast.Name(id="cls"), attr=slot)],
                    value=ast.Subscript(slice=ast.Constant(value=key)),
                ) if key == slot:
                    slots.add(slot)
                case _:
                    pass
        return frozenset(slots)

    def _compile_attrs_helper(
        self,
        observed: t.Pair[FunctionType, p.AttributeProbe],
        attribute: str,
        storage: t.MappingKV[str, p.AttributeProbe],
        qualified: str,
        helper: t.Pair[FunctionType, ast.Call],
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Re-run an authenticated attrs class helper on a fresh plain receiver.

        Returns:
            The independent emission of the observed helper-written method.

        Raises:
            TypeError: If a helper operand has foreign storage.
            ValueError: If the call form, slot or emitted method differs.

        """
        value, _owner = observed
        function, call = helper
        sdk = vars(self._module("attr._make"))
        self._attrs_sdk(sdk)
        module = self._witness.module.get_name()
        supplier = vars(self._module(module))
        arguments: t.DictKV[str, p.AttributeProbe] = {}
        for keyword in call.keywords:
            match keyword:
                case ast.keyword(arg="attrs", value=expression):
                    arguments["attrs"] = self._attrs_helper_records(
                        expression, supplier, sdk, call.lineno
                    )
                case ast.keyword(arg="ns", value=ast.Constant(value=None)):
                    arguments["ns"] = None
                case _:
                    msg = f"native attrs helper call has unproved operands: {module}"
                    raise ValueError(msg)
        records = arguments.get("attrs", storage.get("__attrs_attrs__"))
        if type(records) is not list and type(records) is not tuple:
            msg = "native attrs helper records have foreign storage"
            raise TypeError(msg)
        for record in records:
            self._attrs_record(record, sdk["Attribute"], sdk)
        body: t.DictKV[str, p.AttributeProbe] = {
            "__module__": module,
            "__qualname__": qualified,
        }
        if "attrs" not in arguments:
            body["__attrs_attrs__"] = records
        receiver = type(qualified.rsplit(".", 1)[-1], (object,), body)
        function(receiver, **arguments)
        expected = vars(type)["__dict__"].__get__(receiver, type).get(attribute)
        if (
            type(expected) is not FunctionType
            or storage.get(attribute) is not value
            or not self._same_default(
                (expected.__module__, expected.__qualname__, expected.__name__),
                (value.__module__, value.__qualname__, value.__name__),
            )
        ):
            msg = f"native attrs helper did not emit the class slot: {attribute}"
            raise ValueError(msg)
        self._inputs_current("native attrs helper input changed")
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=expected.__code__,
                # The helper evaluates the method into its own globals; that
                # self-binding is the observed slot, as a closure cell of a
                # recreated class is its observed owner.
                globals={
                    key: value if item is expected else item
                    for key, item in expected.__globals__.items()
                },
                annotations=expected.__annotations__,
                defaults=expected.__defaults__,
                keyword_defaults=expected.__kwdefaults__,
                closure=(),
                inputs=tuple(self._inputs.values()),
                hashed=self._attrs_hashed(receiver, sdk),
            )
        )

    def _attrs_helper_records(
        self,
        expression: ast.expr,
        supplier: t.MappingKV[str, p.AttributeProbe],
        sdk: t.MappingKV[str, p.AttributeProbe],
        position: int,
    ) -> p.AttributeProbe:
        """Evaluate a helper's ``attrs`` operand over native record slots.

        The operand is a module record list, or one comprehension filtering it
        by comparisons of record slots with literals.

        Returns:
            The record sequence the physical statement passed to the helper.

        Raises:
            ValueError: If the operand is outside that closed form.

        """
        match expression:
            case ast.Name(id=name):
                return self._attrs_bound_records(name, supplier, sdk, position)
            case ast.ListComp(
                elt=ast.Name(id=element),
                generators=[
                    ast.comprehension(
                        target=ast.Name(id=target),
                        iter=ast.Name(id=source),
                        ifs=conditions,
                        is_async=0,
                    )
                ],
            ) if element == target:
                records = self._attrs_bound_records(source, supplier, sdk, position)
                if type(records) is not list:
                    msg = "native attrs helper record source is not a list"
                    raise ValueError(msg)
                return [
                    record
                    for record in records
                    if all(
                        self._attrs_condition(condition, target, record, sdk["Attribute"])
                        for condition in conditions
                    )
                ]
            case _:
                msg = "native attrs helper records are outside the closed form"
                raise ValueError(msg)

    def _attrs_bound_records(
        self,
        name: str,
        supplier: t.MappingKV[str, p.AttributeProbe],
        sdk: t.MappingKV[str, p.AttributeProbe],
        position: int,
    ) -> p.AttributeProbe:
        """Resolve a module record list as it was bound at a physical line.

        A name rebound by a later top-level assignment no longer holds the list
        the earlier statement consumed; that list is rebuilt from its physical
        comprehension instead.

        Returns:
            The record list bound to ``name`` before ``position``.

        Raises:
            ValueError: If no physical binding precedes the consuming line.

        """
        bindings = [
            node
            for node in self._trees[self._witness.source].body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ]
        preceding = [node for node in bindings if node.lineno < position]
        if not preceding or name not in supplier:
            msg = f"native attrs helper records have no physical binding: {name}"
            raise ValueError(msg)
        if all(node.lineno < position for node in bindings):
            return supplier[name]
        return self._attrs_record_list(preceding[-1].value, supplier, sdk)

    def _attrs_record_list(
        self,
        expression: ast.expr,
        supplier: t.MappingKV[str, p.AttributeProbe],
        sdk: t.MappingKV[str, p.AttributeProbe],
    ) -> list[p.AttributeProbe]:
        """Rebuild a shadowed record list from its closed physical comprehension.

        Returns:
            Fresh records built by the authenticated ``Attribute`` initializer.

        Raises:
            TypeError: If the record constructor is not the attrs class.
            ValueError: If the comprehension is outside the closed form.

        """
        match expression:
            case ast.ListComp(
                elt=ast.Call(func=ast.Name(id=constructor), args=[], keywords=keywords),
                generators=[
                    ast.comprehension(
                        target=ast.Name(id=variable), iter=iterable, ifs=[], is_async=0
                    )
                ],
            ) if all(keyword.arg is not None for keyword in keywords):
                pass
            case _:
                msg = "native attrs record list is outside the closed comprehension"
                raise ValueError(msg)
        kind = supplier.get(constructor)
        if type(kind) is not type or kind is not sdk.get("Attribute"):
            msg = "native attrs record list constructor is not the attrs record"
            raise TypeError(msg)
        self._function(
            vars(type)["__dict__"].__get__(kind, type).get("__init__"),
            source_name="Attribute.__init__",
            source_namespace=sdk,
        )
        return [
            kind(**{
                str(keyword.arg): self._attrs_record_operand(
                    keyword.value, (variable, item), supplier, sdk
                )
                for keyword in keywords
            })
            for item in self._attrs_slot_names(iterable, supplier)
        ]

    def _attrs_slot_names(
        self, iterable: ast.expr, supplier: t.MappingKV[str, p.AttributeProbe]
    ) -> t.VariadicTuple[str]:
        """Read the closed names a record comprehension iterates.

        Returns:
            A class's raw ``__slots__`` strings or a literal string tuple.

        Raises:
            ValueError: If the iterable is not native string storage.

        """
        match iterable:
            case ast.Attribute(value=ast.Name(id=owner), attr="__slots__") if (
                type(supplier.get(owner)) is type
            ):
                slots = vars(type)["__dict__"].__get__(supplier[owner], type).get(
                    "__slots__"
                )
            case ast.Tuple(elts=elements):
                slots = tuple(
                    element.value
                    for element in elements
                    if isinstance(element, ast.Constant)
                )
                if len(slots) != len(elements):
                    slots = None
            case _:
                slots = None
        if type(slots) is not tuple or any(type(name) is not str for name in slots):
            msg = "native attrs record comprehension iterates foreign names"
            raise ValueError(msg)
        return tuple(str(name) for name in slots)

    def _attrs_record_operand(
        self,
        node: ast.expr,
        binding: t.Pair[str, str],
        supplier: t.MappingKV[str, p.AttributeProbe],
        sdk: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe:
        """Evaluate one record keyword of a closed comprehension.

        Returns:
            A literal, the loop name, an SDK marker, a literal comparison of the
            loop name, or an authenticated SDK function of the loop name.

        Raises:
            ValueError: If the operand is outside that closed form.

        """
        variable, item = binding
        match node:
            case ast.Constant(value=literal) if type(literal) in {bool, NoneType, str}:
                return literal
            case ast.Name(id=name) if name == variable:
                return item
            case ast.Name(id=name) if (
                name in supplier and supplier[name] is sdk.get("NOTHING")
            ):
                return supplier[name]
            case ast.Compare(
                left=ast.Name(id=name),
                ops=[ast.Eq() | ast.NotEq() as operator],
                comparators=[ast.Constant(value=str() as literal)],
            ) if name == variable:
                return (item == literal) is isinstance(operator, ast.Eq)
            case ast.Call(
                func=ast.Name(id=function), args=[ast.Name(id=name)], keywords=[]
            ) if name == variable:
                self._function(
                    supplier.get(function), source_name=function, source_namespace=sdk
                )
                return self._attrs_builder(sdk, function)(item)
            case _:
                msg = "native attrs record operand is outside the closed form"
                raise ValueError(msg)

    def _attrs_condition(
        self,
        condition: ast.expr,
        target: str,
        record: p.AttributeProbe,
        kind: p.AttributeProbe,
    ) -> bool:
        """Evaluate one closed record filter over native slot values.

        Returns:
            Whether the record satisfies the physical filter.

        Raises:
            ValueError: If the filter is outside slot truth and literal equality.

        """
        match condition:
            case ast.BoolOp(op=ast.And(), values=operands):
                return all(
                    self._attrs_condition(operand, target, record, kind)
                    for operand in operands
                )
            case ast.Attribute(value=ast.Name(id=name), attr=slot) if name == target:
                truth = self._attrs_slot(record, kind, slot)
                if type(truth) not in {bool, NoneType, str}:
                    msg = f"native attrs filter slot is not a native scalar: {slot}"
                    raise ValueError(msg)
                return bool(truth)
            case ast.Compare(
                left=ast.Attribute(value=ast.Name(id=name), attr=slot),
                ops=[ast.Eq() | ast.NotEq() as operator],
                comparators=[ast.Constant(value=literal)],
            ) if name == target and type(literal) in {bool, NoneType, str}:
                equal = self._same_default(literal, self._attrs_slot(record, kind, slot))
                return equal if isinstance(operator, ast.Eq) else not equal
            case _:
                msg = "native attrs helper filter is outside the closed form"
                raise ValueError(msg)

    def _attrs_sdk(self, namespace: t.MappingKV[str, p.AttributeProbe]) -> None:
        """Authenticate the attrs builders and record classes before any call.

        Raises:
            TypeError: If a record class has a foreign metaclass or lookup hook.

        """
        for name in (
            "_compile_and_eval",
            "_make_attr_tuple_class",
            "_generate_unique_filename",
            "_make_repr_script",
            "_make_eq_script",
            "_make_hash_script",
            "_make_init_script",
            "_attrs_to_init_script",
            "_determine_setters",
            "_setattr",
            "_setattr_with_converter",
            "_assign",
            "_assign_with_converter",
            "_is_slot_attr",
            "_determine_attrib_eq_order",
        ):
            self._function(
                namespace.get(name), source_name=name, source_namespace=namespace
            )
        for name in ("Attribute", "ClassProps", "Factory", "Converter"):
            kind = namespace.get(name)
            if type(kind) is not type or not self._attrs_plain(
                kind, frozenset({"__getattribute__", "__getattr__"})
            ):
                msg = f"native attrs record class has a lookup hook: {name}"
                raise TypeError(msg)
        converter = vars(type)["__dict__"].__get__(namespace["Converter"], type)
        for name in ("__init__", "_fmt_converter_call"):
            self._function(
                converter.get(name),
                source_name=f"Converter.{name}",
                source_namespace=namespace,
            )
        self._physical_function(
            vars(staticmethod)["__func__"].__get__(
                converter.get("_get_global_name"), staticmethod
            ),
            decorator="staticmethod",
        )

    @staticmethod
    def _attrs_slot(
        record: p.AttributeProbe, kind: p.AttributeProbe, name: str
    ) -> p.AttributeProbe:
        """Read one attrs record slot through its native member descriptor.

        Returns:
            The exact slot value; no property or lookup hook executes.

        Raises:
            TypeError: If the record or the slot is not native attrs storage.

        """
        if type(kind) is not type or type(record) is not kind:
            msg = f"native attrs record has a foreign native type: {name}"
            raise TypeError(msg)
        descriptor = vars(type)["__dict__"].__get__(kind, type).get(name)
        if type(descriptor) is not MemberDescriptorType:
            msg = f"native attrs record slot is not native storage: {name}"
            raise TypeError(msg)
        slot: p.AttributeProbe = descriptor.__get__(record, kind)
        return slot

    @staticmethod
    def _attrs_names(
        records: p.AttributeProbe, kind: p.AttributeProbe
    ) -> t.VariadicTuple[str]:
        """Read the field names of the stored records in their stored order.

        Returns:
            Each record's native ``name`` slot.

        Raises:
            TypeError: If the records are no tuple or a name is not a string.

        """
        if not isinstance(records, tuple):
            msg = "native attrs records are not tuple storage"
            raise TypeError(msg)
        names: list[str] = []
        for item in vars(tuple)["__getitem__"](records, slice(None)):
            name = FlextInfraWorkspaceGeneratedFunction._attrs_slot(item, kind, "name")
            if type(name) is not str:
                msg = "native attrs record name is not a string"
                raise TypeError(msg)
            names.append(name)
        return tuple(names)

    @staticmethod
    def _attrs_plain(value: p.AttributeProbe, hooks: frozenset[str]) -> bool:
        """Prove that native type checks of a value run no authored hook.

        Returns:
            Whether no heap ancestor of the value's type defines one of ``hooks``.

        """
        kind = value if type(value) is type else type(value)
        for ancestor in vars(type)["__mro__"].__get__(kind, type(kind)):
            flags = vars(type)["__flags__"].__get__(ancestor, type(ancestor))
            if flags & c.Infra.CPYTHON_IMMUTABLE_TYPE_FLAG:
                continue
            if not hooks.isdisjoint(
                vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            ):
                return False
        return True

    def _attrs_records(
        self,
        storage: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        qualified: str,
    ) -> p.Result[p.AttributeProbe]:
        """Authenticate the stored attrs field tuple and every record operand.

        A stored tuple that is not the attrs accessor class is changed class
        state and fails the proof; an operand the builders cannot read without
        an authored hook is unsupported and raises.

        Returns:
            The exact stored record tuple, or the first stored-state difference.

        Raises:
            TypeError: If a record alias the initializer spells is not a string.

        """
        result_type = r[p.AttributeProbe]
        records = storage.get("__attrs_attrs__")
        holder = type(records)
        if type(holder) is not type or vars(type)["__bases__"].__get__(
            holder, type
        ) != (tuple,):
            return result_type.fail("native attrs records have foreign tuple storage")
        maker = self._attrs_builder(namespace, "_make_attr_tuple_class")
        getter = next(
            (
                item
                for item in maker.__code__.co_consts
                if type(item) is CodeType and item.co_name == "getter"
            ),
            None,
        )
        body = vars(type)["__dict__"].__get__(holder, type)
        kind = namespace["Attribute"]
        names = self._attrs_names(records, kind)
        name = vars(type)["__name__"].__get__(holder, type)
        if getter is None or name != f"{qualified.rsplit('.', 1)[-1]}Attributes":
            return result_type.fail(
                "native attrs record tuple is not the attrs accessor class"
            )
        for key, accessor in body.items():
            if key not in names:
                if type(accessor) is GetSetDescriptorType or key in {
                    "__module__",
                    "__doc__",
                }:
                    continue
                return result_type.fail(
                    f"native attrs record tuple has authored storage: {key}"
                )
            getter_function = accessor.fget if type(accessor) is property else None
            if (
                type(getter_function) is not FunctionType
                or getter_function.__code__ is not getter
                or getter_function.__defaults__ != (names.index(key),)
                or (accessor.fset, accessor.fdel) != (None, None)
            ):
                return result_type.fail(
                    f"native attrs record accessor differs from attrs: {key}"
                )
        for item in vars(tuple)["__getitem__"](records, slice(None)):
            self._attrs_record(item, kind, namespace)
            # The class initializer spells each parameter by its alias.
            if type(self._attrs_slot(item, kind, "alias")) is not str:
                msg = "native attrs record alias is not a string"
                raise TypeError(msg)
        return result_type.ok(records)

    def _attrs_record(
        self,
        record: p.AttributeProbe,
        kind: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> None:
        """Admit only record operands whose builder checks run no authored hook.

        Raises:
            TypeError: If an operand can run an authored hook in the builders.
            ValueError: If the record is inherited, which needs ancestor proof.

        """
        lookup = frozenset({"__class__", "__getattribute__", "__getattr__"})
        truth = frozenset({"__bool__", "__len__"})
        flags = ("eq", "order", "hash", "init", "kw_only", "inherited")
        if any(
            type(self._attrs_slot(record, kind, name)) not in {bool, NoneType}
            for name in flags
        ):
            msg = "native attrs record has foreign flag storage"
            raise TypeError(msg)
        if self._attrs_slot(record, kind, "inherited") is not False:
            msg = "native attrs inherited fields need their ancestor proof"
            raise ValueError(msg)
        converter = self._attrs_slot(record, kind, "converter")
        operands = (
            (self._attrs_slot(record, kind, "default"), lookup),
            (self._attrs_slot(record, kind, "validator"), truth),
            (self._attrs_slot(record, kind, "eq_key"), truth),
            (converter, lookup),
        )
        if not all(self._attrs_plain(item, hooks) for item, hooks in operands) or (
            not self._attrs_callable(self._attrs_slot(record, kind, "repr"))
        ):
            msg = "native attrs record operand can run an authored hook"
            raise TypeError(msg)
        if converter is not None and type(converter) is not namespace["Converter"]:
            self._attrs_callable(converter, required=True)

    def _attrs_callable(
        self, value: p.AttributeProbe, *, required: bool = False
    ) -> bool:
        """Admit a builder-inspected callable whose signature is its own code.

        Returns:
            Whether the value is a native flag or an unwrapped Python function.

        Raises:
            TypeError: If a required callable carries signature overrides.

        """
        if type(value) is bool and not required:
            return True
        attributes = (
            self._function_attributes(value) if type(value) is FunctionType else None
        )
        admitted = attributes is not None and not {
            "__signature__",
            "__wrapped__",
        }.intersection(attributes)
        if required and not admitted:
            msg = "native attrs converter signature is not its physical code"
            raise TypeError(msg)
        return admitted

    def _attrs_props(
        self,
        storage: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.Result[t.MappingKV[str, p.AttributeProbe]]:
        """Read the stored attrs class options through their native slots.

        Returns:
            Every declared option slot by name, or the first foreign option.

        Raises:
            TypeError: If the attrs options class declares no slots.

        """
        result_type = r[t.MappingKV[str, p.AttributeProbe]]
        kind = namespace["ClassProps"]
        slots = vars(type)["__dict__"].__get__(kind, type).get("__slots__")
        props = storage.get("__attrs_props__")
        if type(slots) is not tuple or type(kind) is not type:
            msg = "native attrs class options have no declared slots"
            raise TypeError(msg)
        if type(props) is not kind:
            return result_type.fail("native attrs class options have a foreign type")
        values = {
            name: self._attrs_slot(props, kind, name)
            for name in slots
            if type(name) is str
        }
        hashability = vars(type)["__dict__"].__get__(kind, type).get("Hashability")
        members = vars(type)["__dict__"].__get__(
            hashability, type(hashability)
        ).get("_member_map_")
        hook = values.get("on_setattr_hook")
        if (
            any(
                type(values.get(name)) is not bool
                for name in (
                    "is_exception",
                    "is_slotted",
                    "has_weakref_slot",
                    "is_frozen",
                    "added_init",
                    "added_repr",
                    "added_eq",
                )
            )
            or type(members) is not dict
            or not any(item is values.get("hashability") for item in members.values())
            or not (
                hook is None
                or hook is vars(self._module("attr.setters")).get("NO_OP")
                or type(hook) is FunctionType
            )
        ):
            return result_type.fail("native attrs class options have foreign storage")
        return result_type.ok({**values, "hashability_members": members})

    def _attrs_layout(
        self,
        owner: p.AttributeProbe,
        storage: t.MappingKV[str, p.AttributeProbe],
        records: p.AttributeProbe,
        props: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.Result[bool]:
        """Prove the class slot layout is the one attrs derives from its records.

        Returns:
            Success, or the first declared slot or descriptor that differs.

        """
        result_type = r[bool]
        slots = storage.get("__slots__")
        if props["is_slotted"] is not True:
            if "__slots__" in storage:
                return result_type.fail(
                    "native attrs class declares slots its options do not"
                )
            return result_type.ok(value=True)
        names = list(self._attrs_names(records, namespace["Attribute"]))
        ancestry = vars(type)["__mro__"].__get__(owner, type(owner))[1:-1]
        inherited = any(
            vars(type)["__dict__"].__get__(base, type(base)).get("__weakref__")
            is not None
            for base in ancestry
        )
        if (
            props["has_weakref_slot"] is True
            and "__weakref__" not in names
            and not inherited
        ):
            names.append("__weakref__")
        cache_field = namespace.get("_HASH_CACHE_FIELD")
        if self._attrs_hashability(props)[1] and type(cache_field) is str:
            names.append(cache_field)
        if type(slots) is not tuple or slots != tuple(names):
            return result_type.fail("native attrs slot layout differs from its records")
        for name in names:
            expected = (
                GetSetDescriptorType if name == "__weakref__" else MemberDescriptorType
            )
            if type(storage.get(name)) is not expected:
                return result_type.fail(
                    f"native attrs slot has no native descriptor: {name}"
                )
        return result_type.ok(value=True)

    @staticmethod
    def _attrs_hashability(
        props: t.MappingKV[str, p.AttributeProbe],
    ) -> t.Pair[bool, bool]:
        """Mirror ``ClassProps.is_hashable`` over the stored enum members.

        Returns:
            Whether attrs writes a ``__hash__`` and whether it caches the hash.

        Raises:
            TypeError: If the hashability members have foreign storage.

        """
        members = props["hashability_members"]
        if type(members) is not dict:
            msg = "native attrs hashability members have foreign storage"
            raise TypeError(msg)
        selected = props["hashability"]
        cached = members.get("HASHABLE_CACHED") is selected
        return cached or members.get("HASHABLE") is selected, cached

    @staticmethod
    def _attrs_builder(
        namespace: t.MappingKV[str, p.AttributeProbe], name: str
    ) -> FunctionType:
        """Return one already authenticated attrs builder by its module binding.

        Returns:
            The exact Python function bound in the attrs SDK namespace.

        Raises:
            TypeError: If the binding is not an exact Python function.

        """
        builder = namespace.get(name)
        if type(builder) is not FunctionType:
            msg = f"native attrs builder is not a Python function: {name}"
            raise TypeError(msg)
        return builder

    def _attrs_script(
        self,
        receivers: t.Pair[type, p.AttributeProbe],
        records: p.AttributeProbe,
        props: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        qualified: str,
    ) -> t.Quad[
        str,
        t.DictKV[str, p.AttributeProbe],
        str,
        t.MappingKV[str, p.AttributeProbe],
    ]:
        """Assemble the snippets in the order the attrs class decorator adds them.

        Returns:
            Joined script, merged globals, initializer name and its annotations.

        Raises:
            TypeError: If a builder returns foreign script or globals storage.

        """
        identity, owner = receivers
        hashable, cached = self._attrs_hashability(props)
        snippets: list[p.AttributeProbe] = []
        if props["added_repr"] is True:
            builder = self._attrs_builder(namespace, "_make_repr_script")
            snippets.append(builder(records, None))
        if props["added_eq"] is True:
            snippets.append(self._attrs_builder(namespace, "_make_eq_script")(records))
        if hashable:
            builder = self._attrs_builder(namespace, "_make_hash_script")
            snippets.append(
                builder(identity, records, frozen=props["is_frozen"], cache_hash=cached)
            )
        init_name, init_script, annotations = self._attrs_init(
            owner, records, props, namespace, qualified
        )
        snippets.append(init_script)
        texts: list[str] = []
        globs: t.DictKV[str, p.AttributeProbe] = {}
        for snippet in snippets:
            if (
                type(snippet) is not tuple
                or type(snippet[0]) is not str
                or type(snippet[1]) is not dict
            ):
                msg = "native attrs builder returned foreign script storage"
                raise TypeError(msg)
            texts.append(snippet[0])
            globs.update(snippet[1])
        return "\n".join(texts), globs, init_name, annotations

    def _attrs_init(
        self,
        owner: p.AttributeProbe,
        records: p.AttributeProbe,
        props: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        qualified: str,
    ) -> t.Triple[str, p.AttributeProbe, t.MappingKV[str, p.AttributeProbe]]:
        """Build the initializer snippet with the module globals of its emission.

        The builder merges the live module namespace between its own globals
        and its trailing keys; a detached receiver keeps it from reading the
        module, and the namespace as it stood at the class statement is merged
        at that same position.

        Returns:
            The initializer name, its ``(script, globals)`` snippet and annotations.

        Raises:
            TypeError: If the builder output has foreign storage.
            ValueError: If no detached module name is free.

        """
        pre_init, pre_init_has_args = self._attrs_hook(owner, "__attrs_pre_init__")
        post_init, _post_args = self._attrs_hook(owner, "__attrs_post_init__")
        detached_module = f"{self._witness.module.get_name()}.<attrs-detached>"
        if detached_module in sys.modules:
            msg = "native attrs detached receiver module is registered"
            raise ValueError(msg)
        detached = type("Detached", (object,), {"__module__": detached_module})
        init_name = "__init__" if props["added_init"] is True else "__attrs_init__"
        built = self._attrs_builder(namespace, "_make_init_script")(
            detached,
            records,
            pre_init,
            pre_init_has_args,
            post_init,
            props["is_frozen"],
            props["is_slotted"],
            self._attrs_hashability(props)[1],
            {},
            props["is_exception"],
            self._attrs_on_setattr(records, props, namespace),
            attrs_init=props["added_init"] is not True,
        )
        if (
            type(built) is not tuple
            or len(built) != len(("script", "globals", "annotations"))
            or type(built[1]) is not dict
            or type(built[2]) is not dict
        ):
            msg = "native attrs initializer builder returned foreign storage"
            raise TypeError(msg)
        script, generated, annotations = built
        tail = self._attrs_init_tail(namespace)
        merged: t.DictKV[str, p.AttributeProbe] = {
            key: item for key, item in generated.items() if key not in tail
        }
        merged.update(self._attrs_module_snapshot(qualified))
        merged.update({key: generated[key] for key in tail if key in generated})
        return init_name, (script, merged), annotations

    def _attrs_init_tail(
        self, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> frozenset[str]:
        """Derive the globals the initializer builder writes after the module merge.

        Returns:
            Keys the physical builder assigns after reading ``sys.modules``.

        Raises:
            ValueError: If the builder has no physical module merge.

        """
        declaration, _tree, _namespace = self._function(
            namespace["_make_init_script"],
            source_name="_make_init_script",
            source_namespace=namespace,
        )
        merge = next(
            (
                index
                for index, node in enumerate(declaration.body)
                if any(
                    isinstance(item, ast.Attribute)
                    and item.attr == "modules"
                    and isinstance(item.value, ast.Name)
                    and item.value.id == "sys"
                    for item in ast.walk(node)
                )
            ),
            None,
        )
        if merge is None:
            msg = "native attrs initializer builder has no physical module merge"
            raise ValueError(msg)
        keys: set[str] = set()
        for node in declaration.body[merge + 1 :]:
            for item in ast.walk(node):
                match item:
                    case ast.Call(
                        func=ast.Attribute(attr="update"), args=[ast.Dict(keys=entries)]
                    ):
                        keys.update(
                            entry.value
                            for entry in entries
                            if isinstance(entry, ast.Constant)
                            and type(entry.value) is str
                        )
                    case ast.Subscript(
                        slice=ast.Constant(value=str() as key), ctx=ast.Store()
                    ):
                        keys.add(key)
                    case _:
                        pass
        return frozenset(keys)

    def _attrs_module_snapshot(
        self, qualified: str
    ) -> t.DictKV[str, p.AttributeProbe]:
        """Read the defining module namespace as it stood at the class statement.

        Names first bound by the class statement or a later top-level statement
        did not exist when the decorator ran and are left out.

        Returns:
            The live module bindings that precede the class statement.

        Raises:
            ValueError: If the class has no unique top-level declaration.

        """
        tree = self._trees[self._witness.source]
        top = qualified.split(".", 1)[0]
        positions = [
            index
            for index, node in enumerate(tree.body)
            if isinstance(node, ast.ClassDef) and node.name == top
        ]
        if len(positions) != 1 or "<locals>" in qualified:
            msg = f"native attrs class has no unique top-level statement: {qualified}"
            raise ValueError(msg)
        early = self._module_bindings(tree.body[: positions[0]])
        late = self._module_bindings(tree.body[positions[0] :]).difference(early)
        live = vars(self._module(self._witness.module.get_name()))
        return {name: item for name, item in live.items() if name not in late}

    @staticmethod
    def _module_bindings(statements: t.SequenceOf[ast.stmt]) -> frozenset[str]:
        """Collect the module-scope names bound by top-level statements.

        Returns:
            Every name a statement binds in module scope.

        Raises:
            ValueError: If a star import binds names the source does not spell.

        """
        names: set[str] = set()
        pending: list[ast.AST] = list(statements)
        while pending:
            node = pending.pop()
            match node:
                case (
                    ast.FunctionDef(name=name)
                    | ast.AsyncFunctionDef(name=name)
                    | ast.ClassDef(name=name)
                ):
                    names.add(name)
                case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                    for alias in aliases:
                        if alias.name == "*":
                            msg = "native attrs module binds names by star import"
                            raise ValueError(msg)
                        names.add(alias.asname or alias.name.split(".", 1)[0])
                case ast.Name(id=name, ctx=ast.Store()):
                    names.add(name)
                case ast.MatchAs(name=str() as captured):
                    names.add(captured)
                    pending.extend(ast.iter_child_nodes(node))
                case (
                    ast.Lambda()
                    | ast.ListComp()
                    | ast.SetComp()
                    | ast.DictComp()
                    | ast.GeneratorExp()
                ):
                    continue
                case _:
                    pending.extend(ast.iter_child_nodes(node))
        return frozenset(names)

    def _attrs_hook(self, owner: p.AttributeProbe, name: str) -> t.Pair[bool, bool]:
        """Resolve an attrs initializer hook through raw class storage.

        Returns:
            Whether the hook exists and whether it takes more than ``self``.

        Raises:
            TypeError: If the hook is not an unwrapped Python function.

        """
        for ancestor in vars(type)["__mro__"].__get__(owner, type(owner)):
            body = vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            if name not in body:
                continue
            hook = body[name]
            if type(hook) is not FunctionType or not self._attrs_callable(hook):
                msg = f"native attrs hook is not an unwrapped Python function: {name}"
                raise TypeError(msg)
            code = hook.__code__
            count = (
                code.co_argcount
                + code.co_kwonlyargcount
                + bool(code.co_flags & CO_VARARGS)
                + bool(code.co_flags & CO_VARKEYWORDS)
            )
            return True, count > 1
        return False, False

    def _attrs_on_setattr(
        self,
        records: p.AttributeProbe,
        props: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe:
        """Mirror the class builder's reduction of the default setattr hook.

        A non-frozen class whose hook only validates or converts drops it when
        no field has a validator or converter to run.

        Returns:
            The setattr hook the initializer builder receives.

        """
        hook = props["on_setattr_hook"]
        setters = vars(self._module("attr.setters"))
        defaults = (
            namespace.get("_DEFAULT_ON_SETATTR"),
            setters.get("validate"),
            setters.get("convert"),
        )
        if props["is_frozen"] is True or not any(hook is item for item in defaults):
            return hook
        kind = namespace["Attribute"]
        items = vars(tuple)["__getitem__"](records, slice(None))
        validated = any(
            self._attrs_slot(item, kind, "validator") is not None for item in items
        )
        converted = any(
            self._attrs_slot(item, kind, "converter") is not None for item in items
        )
        unused = (
            (hook is defaults[0] and not (validated or converted))
            or (hook is defaults[1] and not validated)
            or (hook is defaults[2] and not converted)
        )
        return None if unused else hook

    def _attrs_filename(
        self,
        value: FunctionType,
        identity: type,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> str:
        """Prove the observed code file is the attrs methods file of this class.

        Returns:
            The observed file name, possibly carrying its linecache suffix.

        Raises:
            ValueError: If the observed file name is not the attrs methods file.

        """
        base = self._attrs_builder(namespace, "_generate_unique_filename")(
            identity, "methods"
        )
        observed = value.__code__.co_filename
        stem = base[:-1] if type(base) is str else ""
        suffix = observed[len(stem) + 1 : -1]
        if not stem or not (
            observed == base
            or (
                observed.startswith(f"{stem}-")
                and observed.endswith(">")
                and suffix.isdigit()
            )
        ):
            msg = f"native attrs generated code has a foreign file: {observed[:160]}"
            raise ValueError(msg)
        return observed

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
                hashed=(),
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
        physical, tree, namespace = self._function(
            factory,
            source_name="dataclass",
            source_namespace=vars(self._module("dataclasses")),
        )
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
                return self._field_slot(observed, "type")
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
            TypeError: If the receiver has no native SDK field storage.
            ValueError: If source and the loaded class do not share their identity.

        """
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        module_name = self._witness.module.get_name()
        if not self._same_default(module_name, namespace.get("__module__")):
            msg = "native dataclass owner differs from its physical source module"
            raise ValueError(msg)
        source_globals = vars(self._module(module_name))
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        observed_fields: t.MappingKV[str, p.AttributeProbe] = namespace.get(
            "__dataclass_fields__"
        )
        if type(observed_fields) is not dict:
            msg = "native dataclass receiver has no native field storage"
            raise TypeError(msg)
        annotations: t.DictKV[str, p.AttributeProbe] = {}
        result: t.DictKV[str, p.AttributeProbe] = {
            "__module__": module_name,
            "__qualname__": qualified,
            "__annotations__": annotations,
        }
        documentation = namespace.get("__doc__")
        if type(documentation) is not str or not documentation:
            msg = "native dataclass receiver has no callback-free documentation"
            raise ValueError(msg)
        result["__doc__"] = documentation
        self._dataclass_members(owner, declaration, namespace, result)
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
            elif isinstance(
                field.value, ast.Constant | ast.Tuple | ast.List | ast.Name
            ):
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
        self._dataclass_inherited_fields(
            namespace, observed_fields, annotations, result
        )
        return result

    def _dataclass_inherited_fields(
        self,
        namespace: t.MappingKV[str, p.AttributeProbe],
        observed_fields: t.MappingKV[str, p.AttributeProbe],
        annotations: t.DictKV[str, p.AttributeProbe],
        result: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        """Lay out inherited fields in the SDK's own stored order.

        The stored ``__dataclass_fields__`` already holds the final order (base
        fields first, redefinitions in place). Declared fields keep their
        physical data; inherited ones are rebuilt from their stored SDK
        ``Field``, never invoked.

        Raises:
            ValueError: If an own annotation is not a stored field beside inherited
                fields, so the stored order cannot place it.

        """
        if all(name in annotations for name in observed_fields):
            return
        unstored = [name for name in annotations if name not in observed_fields]
        if unstored:
            msg = (
                "native dataclass annotation has no stored field beside inherited "
                f"fields: {unstored[:8]}"
            )
            raise ValueError(msg)
        sdk = vars(self._module("dataclasses"))
        ordered: t.DictKV[str, p.AttributeProbe] = {}
        for name in observed_fields:
            if name in annotations:
                ordered[name] = annotations[name]
                continue
            stored = self._stored_field(name, namespace)
            ordered[name] = self._field_slot(stored, "type")
            if self._field_slot(stored, "_field_type") is not sdk.get("_FIELD"):
                # ClassVar/InitVar pseudo-fields are plain class values to the SDK.
                default = self._field_slot(stored, "default")
                if default is not sdk.get("MISSING"):
                    result[name] = default
                continue
            result[name] = self._rebuilt_field(name, namespace)
        annotations.clear()
        annotations.update(ordered)

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
        empty = vars(self._module("dataclasses")).get("_EMPTY_METADATA")
        metadata = self._field_slot(observed, "metadata")
        rebuilt: p.AttributeProbe = factory(
            default=self._field_slot(observed, "default"),
            default_factory=self._field_slot(observed, "default_factory"),
            init=self._field_slot(observed, "init"),
            repr=self._field_slot(observed, "repr"),
            hash=self._field_slot(observed, "hash"),
            compare=self._field_slot(observed, "compare"),
            metadata=None if metadata is empty else metadata,
            kw_only=self._field_slot(observed, "kw_only"),
        )
        return rebuilt

    def _field_slot(self, observed: p.AttributeProbe, name: str) -> p.AttributeProbe:
        """Read one stored SDK ``Field`` slot through its authenticated C member.

        Returns:
            The exact slot value; no Python descriptor or hook executes.

        Raises:
            TypeError: If the record or its slot is not native ``Field`` storage.

        """
        owner = vars(self._module("dataclasses")).get("Field")
        if type(owner) is not type or type(observed) is not owner:
            msg = f"native dataclass field record is not SDK storage: {name}"
            raise TypeError(msg)
        descriptor = vars(type)["__dict__"].__get__(owner, type).get(name)
        if type(descriptor) is not MemberDescriptorType:
            msg = f"native dataclass field slot is not a native member: {name}"
            raise TypeError(msg)
        value: p.AttributeProbe = descriptor.__get__(observed, owner)
        return value

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
        default = self._field_slot(observed, "default")
        if default is not sdk.get("MISSING") and any(
            "__set_name__" in vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            for ancestor in vars(type)["__mro__"].__get__(
                type(default), type(type(default))
            )
        ):
            msg = f"native dataclass default carries an authored __set_name__: {name}"
            raise ValueError(msg)
        return observed

    def _dataclass_members(
        self,
        owner: p.AttributeProbe,
        declaration: ast.ClassDef,
        namespace: t.MappingKV[str, p.AttributeProbe],
        result: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        """Retain source-defined methods without invoking their descriptors or bodies.

        Raises:
            TypeError: If abstract state has foreign storage.

        """
        # ABCMeta derives ``__abstractmethods__`` from the authored markers; the
        # SDK never reads it from the plain ``type`` receiver, so it is only
        # checked for native storage and never copied into the receiver.
        abstract = namespace.get("__abstractmethods__", frozenset())
        if type(abstract) is not frozenset or any(
            type(name) is not str for name in abstract
        ):
            msg = (
                "native dataclass abstract state has foreign storage: "
                f"{declaration.name}; source={self._witness.source}"
            )
            raise TypeError(msg)
        for ancestor in vars(type)["__mro__"].__get__(owner, type(owner))[1:]:
            inherited = vars(type)["__dict__"].__get__(ancestor, type(ancestor))
            # ``_dataclass_inherited_fields`` lays inherited fields out on the
            # receiver, which carries no authored ancestor, so an inherited hook
            # the SDK looks up by name is proved and copied here.
            if "__post_init__" in inherited and "__post_init__" not in result:
                self._dataclass_method(inherited["__post_init__"])
                result["__post_init__"] = inherited["__post_init__"]
        for node in declaration.body:
            if isinstance(node, ast.FunctionDef):
                method = namespace.get(node.name)
                self._dataclass_method(method)
                result[node.name] = method
            elif isinstance(node, ast.Assign):
                self._dataclass_class_values(node, result)

    def _dataclass_method(self, value: p.AttributeProbe | None) -> None:
        """Prove method code and raw wrapper storage without calling the method.

        Raises:
            TypeError: If method storage can invoke an authored accessor.

        """
        # A native method descriptor names its own source decorator; the
        # declaration carries exactly that decorator and nothing else.
        decorator: str | None = None
        if type(value) is property:
            getter = value.fget
            if type(getter) is not FunctionType:
                msg = "native dataclass property has no exact Python getter"
                raise TypeError(msg)
            name = getter.__name__
            for accessor, expected in (
                (getter, "property"),
                (value.fset, f"{name}.setter"),
                (value.fdel, f"{name}.deleter"),
            ):
                if accessor is not None:
                    self._dataclass_accessor(accessor, expected)
            return
        if type(value) is classmethod or type(value) is staticmethod:
            decorator = vars(type)["__name__"].__get__(type(value), type)
            value = value.__func__
        if type(value) is not FunctionType:
            msg = (
                "native dataclass method is not an exact Python function: "
                f"{type(value).__module__}.{type(value).__qualname__}"
            )
            raise TypeError(msg)
        # ``abc.abstractmethod`` returns the same function after storing an
        # exact ``True`` marker; the declaration must carry that decorator.
        marker = self._function_attributes(value).get("__isabstractmethod__")
        if marker is True and decorator is None:
            decorator = "abstractmethod"
        elif marker is not None:
            msg = (
                "native dataclass method has a foreign abstract marker: "
                f"{value.__qualname__}"
            )
            raise TypeError(msg)
        self._dataclass_accessor(value, decorator)

    def _dataclass_accessor(
        self,
        value: p.AttributeProbe | None,
        decorator: str | None,
    ) -> None:
        """Prove one method body and its raw ``__wrapped__`` chain.

        Raises:
            TypeError: If storage can invoke an authored accessor.
            ValueError: If the raw wrapper chain is cyclic or lacks physical code.

        """
        if type(value) is not FunctionType:
            msg = "native dataclass accessor is not an exact Python function"
            raise TypeError(msg)
        if decorator is None and vars(value).get("__isabstractmethod__") is True:
            # ``abc.abstractmethod`` marks the function in place and returns it.
            decorator = "abstractmethod"
        seen: set[int] = set()
        wrapper: FunctionType | None = None
        while type(value) is FunctionType:
            if id(value) in seen:
                msg = "native dataclass method has a cyclic raw wrapper"
                raise ValueError(msg)
            seen.add(id(value))
            self._physical_function(value, decorator=decorator, wrapper=wrapper)
            decorator = None
            wrapper = value
            value = self._function_attributes(value).get("__wrapped__")
        if value is not None:
            msg = "native dataclass method has callback-bearing descriptor storage"
            raise TypeError(msg)

    def _dataclass_class_values(
        self,
        assignment: ast.Assign,
        result: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        """Retain physical class constants that control native SDK emission.

        Raises:
            ValueError: If source assigns class state through non-name targets.

        """
        namespace = vars(self._module(self._witness.module.get_name()))
        for target in assignment.targets:
            match target:
                case ast.Name(id=name):
                    member = self._native_type_member(assignment.value, namespace)
                    result[name] = (
                        member
                        if member is not None
                        else self._source_scalar(
                            assignment.value,
                            namespace,
                            self._trees[self._witness.source],
                        )
                    )
                case _:
                    msg = "native dataclass class value has no closed source name"
                    raise ValueError(msg)

    def _native_type_member(
        self,
        expression: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> p.AttributeProbe | None:
        """Bind ``<builtin type>.<slot>`` to the native slot it physically names.

        pydantic's ``PydanticRecursiveRef`` declares ``__hash__ = object.__hash__``
        to keep identity hashing under ``eq=True``; the SDK hash action reads
        that class value, so it must be the native slot descriptor itself.

        Returns:
            The native slot descriptor, or ``None`` for any other expression.

        Raises:
            TypeError: If the named member is not a native slot descriptor.

        """
        match expression:
            case ast.Attribute(value=ast.Name(id=owner_name), attr=member) if (
                owner_name not in namespace
            ):
                owner = self._builtin(owner_name, namespace)
                if type(owner) is not type:
                    msg = "native dataclass class value owner is not a builtin type"
                    raise TypeError(msg)
                value = vars(type)["__dict__"].__get__(owner, type(owner)).get(member)
                if (
                    type(value) is not WrapperDescriptorType
                    and type(value) is not MethodDescriptorType
                ):
                    msg = (
                        "native dataclass class value is not a native slot: "
                        f"{owner_name}.{member}"
                    )
                    raise TypeError(msg)
                return value
            case _:
                return None

    def _compile_dataclass(
        self,
        value: FunctionType,
        owner: p.AttributeProbe,
        attribute: str,
        declaration: ast.ClassDef,
        factory: t.Pair[FunctionType, t.DictKV[str, bool]],
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Invoke the authenticated SDK on closed data and an exact-type receiver.

        Returns:
            Independent native emission and the physical inputs that admitted it,
            or a class value that names a builtin type its module rebinds.

        Raises:
            TypeError: If the SDK returns a receiver of a foreign native type.

        """
        module = vars(self._module(self._witness.module.get_name()))
        shadowed = sorted(
            f"{node.value.id}.{node.attr}"
            for statement in declaration.body
            if isinstance(statement, ast.Assign)
            for node in (statement.value,)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in module
            and node.value.id in vars(builtins)
        )
        if shadowed:
            # ``__hash__ = object.__hash__`` names a native slot only while the
            # module leaves the builtin type unbound.
            return r[m.Infra.NativeGeneratedFunctionProof].fail(
                f"native dataclass class value names a rebound builtin: {shadowed}"
            )
        self._dataclass_sdk(factory[0])
        namespace = self._dataclass_inputs(owner, declaration)
        self._dataclass_hash_action(factory[1], namespace)
        self._dataclass_sdk_state()
        self._inputs_current("native dataclass compiler input changed")
        receiver = type(declaration.name, (object,), namespace)
        emitted = factory[0](receiver, **factory[1])
        if type(emitted) is not type:
            msg = "native dataclass SDK returned a foreign receiver"
            raise TypeError(msg)
        self._dataclass_records(owner, emitted)
        expected = self._dataclass_emission(value, owner, emitted, attribute)
        closure = tuple(
            owner
            if cell.cell_contents is receiver or cell.cell_contents is emitted
            else cell.cell_contents
            for cell in expected.__closure__ or ()
        )
        self._inputs_current("native dataclass compiler source changed")
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=expected.__code__,
                globals=expected.__globals__,
                annotations=expected.__annotations__,
                defaults=expected.__defaults__,
                keyword_defaults=expected.__kwdefaults__,
                closure=closure,
                inputs=tuple(self._inputs.values()),
                hashed=(),
            )
        )

    def _dataclass_hash_action(
        self,
        options: t.MappingKV[str, bool],
        receiver: t.MappingKV[str, p.AttributeProbe],
    ) -> None:
        """Prove only the hash action elected by physical options and methods.

        Raises:
            TypeError: If the SDK hash table or its keys have foreign storage.
            ValueError: If its selected action differs from the physical literal.

        """
        compiler = self._module("dataclasses")
        namespace = vars(compiler)
        _path, tree = self._source(compiler)
        table = namespace.get("_hash_action")
        if type(table) is not dict:
            msg = "native dataclass hash action table is not a native dictionary"
            raise TypeError(msg)
        for key in table:
            if type(key) is not tuple or any(type(flag) is not bool for flag in key):
                msg = "native dataclass hash action key has foreign operands"
                raise TypeError(msg)
        selected = (
            options["unsafe_hash"],
            options["eq"],
            options["frozen"],
            "__hash__" in receiver
            and not (receiver["__hash__"] is None and "__eq__" in receiver),
        )
        literals = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_hash_action"
            and isinstance(node.value, ast.Dict)
        ]
        if len(literals) != 1:
            msg = "native dataclass hash action table has no physical literal"
            raise ValueError(msg)
        values = [
            value
            for key, value in zip(literals[0].keys, literals[0].values, strict=True)
            if key is not None and self._default(key, namespace, tree) == selected
        ]
        if len(values) != 1:
            msg = "native dataclass hash action has no unique physical key"
            raise ValueError(msg)
        self._dataclass_hash_binding(table[selected], values[0], namespace)

    def _dataclass_hash_binding(
        self,
        action: p.AttributeProbe | None,
        expression: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> None:
        """Bind the selected native action to its sole physical table entry.

        Raises:
            ValueError: If a hash action is replaced or not a physical function.

        """
        match expression:
            case ast.Constant(value=None) if action is None:
                return
            case ast.Name(id=name) if namespace.get(name) is action:
                # The action reaches its collaborators (``_tuple_str``,
                # ``_FuncBuilder``) through globals already proved by the SDK
                # check; the 3.13 compiler has no separate hash builder.
                self._function(action, source_name=name, source_namespace=namespace)
            case _:
                msg = "native dataclass selected hash action is interposed"
                raise ValueError(msg)

    def _dataclass_sdk_state(self) -> None:
        """Check native marker identities and execution namespaces before SDK calls.

        Raises:
            TypeError: If module storage or a source marker has a foreign type.
            ValueError: If a marker is not its physical constructor instance.

        """
        compiler = self._module("dataclasses")
        namespace = vars(compiler)
        _path, tree = self._source(compiler)
        if type(sys.modules) is not dict:
            msg = "native dataclass SDK module registry has foreign storage"
            raise TypeError(msg)
        for name in (
            "MISSING",
            "_HAS_DEFAULT_FACTORY",
            "KW_ONLY",
            "_FIELD",
            "_FIELD_CLASSVAR",
            "_FIELD_INITVAR",
        ):
            constructors = [
                node.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name
            ]
            match constructors:
                case [ast.Call(func=ast.Name(id=class_name), keywords=[])]:
                    owner = namespace.get(class_name)
                    self._sdk_class(owner, namespace, tree)
                    if type(namespace.get(name)) is not owner:
                        msg = f"native dataclass marker has foreign identity: {name}"
                        raise ValueError(msg)
                case _:
                    msg = (
                        "native dataclass marker lacks its physical constructor: "
                        f"{name}"
                    )
                    raise ValueError(msg)

    def _dataclass_records(self, owner: p.AttributeProbe, emitted: type) -> None:
        """Compare SDK output records through exact native slots, never properties.

        Raises:
            TypeError: If parameter or field records have foreign native storage.
            ValueError: If an original compiler record differs from the emission.

        """
        compiler = self._module("dataclasses")
        namespace = vars(compiler)
        _path, tree = self._source(compiler)
        actual = vars(type)["__dict__"].__get__(owner, type(owner))
        expected = vars(type)["__dict__"].__get__(emitted, type)
        self._dataclass_record(
            actual.get("__dataclass_params__"),
            expected.get("__dataclass_params__"),
            namespace,
            tree,
        )
        fields = actual.get("__dataclass_fields__")
        expected_fields = expected.get("__dataclass_fields__")
        if type(fields) is not dict or type(expected_fields) is not dict:
            msg = "native dataclass fields have foreign dictionary storage"
            raise TypeError(msg)
        if any(type(name) is not str for name in fields) or tuple(fields) != tuple(
            expected_fields
        ):
            msg = "native dataclass field order differs from its physical declaration"
            raise ValueError(msg)
        for name, field in expected_fields.items():
            self._dataclass_record(fields[name], field, namespace, tree)

    def _dataclass_record(
        self,
        actual: p.AttributeProbe | None,
        expected: p.AttributeProbe | None,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        """Read output record cells only through their authenticated C descriptors.

        Raises:
            TypeError: If an original record has a different native owner.
            ValueError: If any record cell differs from the independent emission.

        """
        owner = type(expected)
        storage = self._sdk_class(owner, namespace, tree)
        if type(actual) is not owner:
            msg = "native dataclass output record has a foreign native type"
            raise TypeError(msg)
        for name, descriptor in storage.items():
            if type(descriptor) is not MemberDescriptorType:
                continue
            if not self._same_default(
                descriptor.__get__(expected, owner),
                descriptor.__get__(actual, owner),
            ):
                msg = f"native dataclass output record differs from source: {name}"
                raise ValueError(msg)

    def _dataclass_emission(
        self,
        value: FunctionType,
        owner: p.AttributeProbe,
        emitted: type,
        attribute: str,
    ) -> FunctionType:
        """Select the identical raw wrapper depth and physical owner metadata.

        Returns:
            The independent function corresponding to the observed exact slot.

        Raises:
            ValueError: If wrapper ownership or emitted function metadata differ.

        """
        actual = self._dataclass_function_chain(
            vars(type)["__dict__"].__get__(owner, type(owner)).get(attribute)
        )
        expected = self._dataclass_function_chain(
            vars(type)["__dict__"].__get__(emitted, type).get(attribute)
        )
        if len(actual) != len(expected):
            msg = "native dataclass generated wrapper chain differs from source"
            raise ValueError(msg)
        for observed, generated in zip(actual, expected, strict=True):
            if observed is value:
                if (
                    not self._same_default(generated.__module__, observed.__module__)
                    or not self._same_default(generated.__name__, observed.__name__)
                    or not self._same_default(
                        generated.__qualname__, observed.__qualname__
                    )
                ):
                    msg = "native dataclass generated function has a foreign owner"
                    raise ValueError(msg)
                return generated
        msg = "native dataclass generated function is not its registered class slot"
        raise ValueError(msg)

    @staticmethod
    def _dataclass_function_chain(
        value: p.AttributeProbe | None,
    ) -> t.VariadicTuple[FunctionType]:
        """Read native wrappers and their inner callable cell without callbacks.

        Returns:
            The exact, acyclic wrapper chain including its terminal function.

        Raises:
            TypeError: If the SDK emission has foreign wrapper storage.
            ValueError: If a wrapper cell and its raw inner binding disagree.

        """
        result: list[FunctionType] = []
        while type(value) is FunctionType:
            if any(item is value for item in result):
                msg = "native dataclass generated wrapper has a cycle"
                raise ValueError(msg)
            result.append(value)
            inner = FlextInfraWorkspaceGeneratedFunction._function_attributes(
                value
            ).get("__wrapped__")
            if inner is None:
                return tuple(result)
            cells = dict(
                zip(value.__code__.co_freevars, value.__closure__ or (), strict=True)
            )
            if (
                "user_function" in cells
                and cells["user_function"].cell_contents is not inner
            ):
                msg = "native dataclass wrapper does not retain its registered inner"
                raise ValueError(msg)
            value = inner
        msg = "native dataclass emission is not an exact Python function"
        raise TypeError(msg)

    def _dataclass_sdk(self, factory: FunctionType) -> None:
        """Authenticate the selected SDK entry and its physical class processor.

        This proves these callable bindings without executing either one. The
        processor's consumed helpers and receiver inputs need their own proof
        before SDK emission is admitted.

        Raises:
            TypeError: If the processor binding is not an exact Python function.
            ValueError: If the selected entry or processor has a foreign namespace.

        """
        _declaration, _tree, namespace = self._function(
            factory,
            source_name="dataclass",
            source_namespace=vars(self._module("dataclasses")),
        )
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
        self._function(
            processor, source_name="_process_class", source_namespace=namespace
        )
        _source, tree = self._source(compiler)
        for name in ("Field", "_DataclassParams", "_FuncBuilder"):
            self._sdk_class(namespace.get(name), namespace, tree)
        for name in (
            "field",
            "fields",
            "_fields_in_init_order",
            "_get_field",
            "_is_classvar",
            "_is_initvar",
            "_is_kw_only",
            "_is_type",
            "_init_fn",
            "_init_param",
            "_field_init",
            "_field_assign",
            "_set_new_attribute",
            "_tuple_str",
            "_frozen_set_del_attr",
            "_add_slots",
            "_get_slots",
            "_update_func_cell_for__class__",
            "_replace",
            "_dataclass_getstate",
            "_dataclass_setstate",
        ):
            self._function(
                namespace.get(name), source_name=name, source_namespace=namespace
            )
        for name in ("_FIELDS", "_PARAMS", "_POST_INIT_NAME"):
            self._source_scalar(ast.Name(id=name, ctx=ast.Load()), namespace, tree)
        pattern = namespace.get("_MODULE_IDENTIFIER_RE")
        if pattern is None:
            msg = "native dataclass annotation matcher has no physical binding"
            raise ValueError(msg)
        self._regex("_MODULE_IDENTIFIER_RE", pattern, namespace, tree)
        for module_name, operation in (
            ("inspect", "get_annotations"),
            ("inspect", "unwrap"),
            ("abc", "update_abstractmethods"),
        ):
            module = self._global(module_name, namespace, tree)
            if type(module) is not ModuleType:
                msg = "native dataclass collaborator is not its physical module"
                raise TypeError(msg)
            self._function(
                vars(module).get(operation),
                source_name=operation,
                source_namespace=vars(module),
            )
        self._function(
            self._global("recursive_repr", namespace, tree),
            source_name="recursive_repr",
            source_namespace=vars(self._module("reprlib")),
        )

    def _sdk_class(
        self,
        owner: p.AttributeProbe | None,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> t.MappingKV[str, p.AttributeProbe]:
        """Prove SDK class storage and methods before any instance is constructed.

        Returns:
            The raw namespace whose native type, bases and source are authenticated.

        Raises:
            TypeError: If the compiler owner does not have the exact native metaclass.
            ValueError: If storage, slots or methods differ from the physical class.

        """
        if type(owner) is not type:
            msg = "native compiler class has a foreign metaclass"
            raise TypeError(msg)
        storage: t.MappingKV[str, p.AttributeProbe] = vars(type)["__dict__"].__get__(
            owner, type
        )
        name = vars(type)["__name__"].__get__(owner, type)
        if namespace.get(name) is not owner or vars(type)["__bases__"].__get__(
            owner, type
        ) != (object,):
            msg = "native compiler class has foreign identity or bases"
            raise ValueError(msg)
        declarations = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == name
        ]
        if len(declarations) != 1:
            msg = "native compiler class has no unique physical declaration"
            raise ValueError(msg)
        declaration = declarations[0]
        module_name = namespace.get("__name__")
        if type(module_name) is not str:
            msg = "native compiler class has no physical supplier"
            raise TypeError(msg)
        source, _tree = self._source(self._module(module_name))
        bodies = [
            code
            for code in self._codes[source].co_consts
            if type(code) is CodeType
            and code.co_name == name
            and code.co_firstlineno == declaration.lineno
        ]
        slots: t.VariadicTuple[str] = ()
        for member in declaration.body:
            if isinstance(member, ast.FunctionDef) and not member.decorator_list:
                self._function(
                    storage.get(member.name),
                    source_name=f"{declaration.name}.{member.name}",
                    source_namespace=namespace,
                )
            elif (
                isinstance(member, ast.Assign)
                and len(member.targets) == 1
                and isinstance(member.targets[0], ast.Name)
                and member.targets[0].id == "__slots__"
            ):
                slots = self._sdk_slots(owner, storage, member.value, namespace, tree)
        if len(bodies) != 1 or (
            set(storage)
            - set(bodies[0].co_names)
            - set(slots)
            - {"__dict__", "__weakref__", "__doc__"}
        ):
            msg = "native compiler class has undeclared runtime storage or hooks"
            raise ValueError(msg)
        if not self._same_default(
            ast.get_docstring(declaration), storage.get("__doc__")
        ):
            msg = "native compiler class documentation differs from its declaration"
            raise ValueError(msg)
        return storage

    def _sdk_slots(
        self,
        owner: type,
        storage: t.MappingKV[str, p.AttributeProbe],
        expression: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> t.VariadicTuple[str]:
        """Check each source-declared slot through its native owning descriptor.

        Returns:
            Slot names whose native descriptors have their exact physical owner.

        Raises:
            TypeError: If the physical slot declaration is not a tuple of names.
            ValueError: If a slot descriptor is replaced or belongs to another class.

        """
        slots = self._default(expression, namespace, tree)
        if type(slots) is not tuple:
            msg = "native compiler slots are not a physical tuple"
            raise TypeError(msg)
        names: list[str] = []
        for name in slots:
            if type(name) is not str:
                msg = "native compiler slot name is not a physical string"
                raise TypeError(msg)
            descriptor = storage.get(name)
            if (
                type(descriptor) is not MemberDescriptorType
                or descriptor.__objclass__ is not owner
                or descriptor.__name__ != name
            ):
                msg = "native compiler slot descriptor differs from its declaration"
                raise ValueError(msg)
            names.append(name)
        return tuple(names)

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
        fields: list[t.Pair[str, ast.AnnAssign]] = (
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
        defaults: list[p.AttributeProbe] = []
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
        selected: list[ast.stmt] = []
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
        CodeType,
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

        Any other operand is read by ``_tuple_literal``.

        Returns:
            The closed operand value.

        """
        match node:
            case ast.BinOp(op=ast.Add(), left=left, right=right):
                first, second = (
                    self._tuple_operand(item, namespace) for item in (left, right)
                )
                if type(first) is tuple and type(second) is tuple:
                    return first + second
                if type(first) is list and type(second) is list:
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
        selected: list[ast.stmt] = []
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
        specification = namespace["__spec__"]
        frozen = specification.origin == "frozen"
        if frozen:
            if path not in self._inputs:
                self._inputs[path] = u.Cli.atomic_read_binary_file_state(
                    path, required=True
                ).unwrap()
            path = Path(specification.loader_state.filename).absolute()
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
            compiled = (
                FrozenImporter.get_code(specification.name)
                if frozen
                else builtins.compile(
                    state.content,
                    str(path),
                    "exec",
                    dont_inherit=True,
                    optimize=sys.flags.optimize,
                )
            )
            if type(compiled) is not CodeType:
                msg = "closed compiler supplier has no native compiled code"
                raise TypeError(msg)
            self._codes[path] = compiled
        return path, self._trees[path]

    def _physical_function(
        self,
        function: p.AttributeProbe | None,
        *,
        decorator: str | None = None,
        wrapper: FunctionType | None = None,
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
        # _decorator_spellings is the single owner that authenticates the
        # expected decorator (native descriptor type or abc.abstractmethod).
        candidates = self._function_declarations(
            function,
            tree,
            spellings=self._decorator_spellings(decorator, namespace),
            wrapper=wrapper,
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
            msg = (
                "closed compiler function differs from its physical compilation: "
                f"{module_name}.{function.__code__.co_qualname} "
                f"declarations={len(candidates)} compiled_match={matched}"
            )
            raise ValueError(msg)
        return candidates[0], tree, namespace

    def _function(
        self,
        function: p.AttributeProbe | None,
        *,
        source_name: str | None = None,
        source_namespace: t.MappingKV[str, p.AttributeProbe] | None = None,
    ) -> t.Triple[ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]]:
        declaration, tree, namespace = self._physical_function(function)
        if type(function) is not FunctionType:
            msg = "closed compiler callback is not an exact Python function"
            raise TypeError(msg)
        if source_name is not None:
            if source_namespace is None:
                msg = "closed compiler SDK binding has no elected namespace"
                raise ValueError(msg)
            self._function_binding(function, source_name, source_namespace)
        if (
            function.__closure__ is not None
            or vars(FunctionType)["__builtins__"].__get__(function, FunctionType)
            is not vars(builtins)
            # Postponed annotations only defer annotation evaluation; the
            # physical compilation honours them, so code identity still holds.
            or any(
                isinstance(item, ast.ImportFrom)
                and item.module == "__future__"
                and any(alias.name != "annotations" for alias in item.names)
                for item in tree.body
            )
        ):
            msg = "closed compiler function has unsupported closure or future inputs"
            raise ValueError(msg)
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
        self._native_globals(function)
        return declaration, tree, namespace

    @staticmethod
    def _function_attributes(
        function: FunctionType,
    ) -> t.MappingKV[str, p.AttributeProbe]:
        """Read exact function metadata storage before any named key lookup.

        Returns:
            The native string-keyed function dictionary.

        Raises:
            TypeError: If function metadata can invoke a mapping callback.

        """
        attributes = vars(function)
        if type(attributes) is not dict or any(
            type(name) is not str for name in attributes
        ):
            msg = "closed compiler function metadata has foreign dictionary storage"
            raise TypeError(msg)
        return attributes

    def _function_binding(
        self,
        function: FunctionType,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> None:
        """Bind a consumed SDK name to its exact physical function declaration.

        Raises:
            ValueError: If a helper is rebound or gains an unproved raw wrapper.

        """
        expected = (name, name, name.rsplit(".", 1)[-1], namespace["__name__"])
        observed = (
            function.__code__.co_qualname,
            function.__qualname__,
            function.__name__,
            function.__module__,
        )
        if (
            function.__globals__ is not namespace
            or not self._same_default(expected, observed)
            or "__wrapped__" in self._function_attributes(function)
        ):
            msg = f"closed compiler SDK binding differs from its physical name: {name}"
            raise ValueError(msg)

    def _native_globals(self, function: FunctionType) -> None:
        """Prove native builtin lookups without invoking any selected operation.

        A module's own identity attributes (``__name__``, ``__spec__``, ...) are
        also attributes of the ``builtins`` module, but a global lookup of one
        resolves to the supplier module's metadata, never to a builtin: the
        stdlib ``dataclasses._process_class`` reads ``sys.modules[__name__]``.
        Those names are derived from a fresh module's namespace and proved as
        the supplier's identity instead of as builtins.

        Raises:
            ValueError: If a builtin lookup is interposed in the SDK namespace, or a
                module identity lookup does not name the function's own module.

        """
        names: set[str] = set()
        pending = [function.__code__]
        while pending:
            code = pending.pop()
            names.update(
                instruction.argval
                for instruction in get_instructions(code)
                if instruction.opname == "LOAD_GLOBAL"
                and type(instruction.argval) is str
            )
            pending.extend(item for item in code.co_consts if type(item) is CodeType)
        identity = vars(ModuleType(function.__module__)).keys()
        if (
            "__name__" in names
            and function.__globals__.get("__name__") != function.__module__
        ):
            msg = "closed compiler module identity is interposed: __name__"
            raise ValueError(msg)
        for name in names.intersection(vars(builtins)).difference(identity):
            if (
                name in function.__globals__
                and function.__globals__[name] is not vars(builtins)[name]
            ):
                msg = f"closed compiler builtin lookup is interposed: {name}"
                raise ValueError(msg)
            self._builtin(name, function.__globals__)

    def _decorator_spellings(
        self,
        decorator: str | None,
        namespace: t.MappingKV[str, p.AttributeProbe],
    ) -> frozenset[str] | None:
        """Return the source spellings that bind the expected sole decorator.

        A native descriptor type (``classmethod``, ``staticmethod``,
        ``property``) must be the builtin itself; a property's own
        ``<name>.setter``/``.deleter`` is spelled as such; ``abstractmethod``
        is every module binding of ``abc.abstractmethod`` or of ``abc``.

        Returns:
            The accepted decorator spellings, or ``None`` for an undecorated body.

        Raises:
            TypeError: If ``abc.abstractmethod`` is not its physical function.

        """
        if decorator is None:
            return None
        if decorator == "abstractmethod":
            abc = self._module("abc")
            marker = vars(abc).get("abstractmethod")
            if type(marker) is not FunctionType:
                msg = "native abstract method marker is not a Python function"
                raise TypeError(msg)
            self._function(marker)
            return frozenset(
                name if value is marker else f"{name}.abstractmethod"
                for name, value in namespace.items()
                if value is marker or value is abc
            )
        if "." not in decorator:
            self._builtin(decorator, namespace)
        return frozenset((decorator,))

    @staticmethod
    def _function_declarations(
        function: FunctionType,
        tree: ast.Module,
        *,
        spellings: frozenset[str] | None = None,
        wrapper: FunctionType | None = None,
    ) -> t.VariadicTuple[ast.FunctionDef]:
        """Locate the physical module or class method without running its body.

        ``spellings`` names the sole decorator the declaration may carry; the
        code's first line is then the decorator line, as CPython records it.
        ``wrapper`` is the outer function of a raw ``__wrapped__`` chain: the
        innermost decorator may then be the factory whose own code nests the
        wrapper's code object.

        Returns:
            Declarations matching the native qualified code identity and carrying
            exactly an accepted decorator, or none.

        """
        components = function.__code__.co_qualname.split(".")
        nodes = FlextInfraWorkspaceGeneratedFunction._qualified_scope(components, tree)
        return tuple(
            node
            for node in nodes
            if isinstance(node, ast.FunctionDef)
            and node.name == components[-1]
            and (node.decorator_list[0] if node.decorator_list else node).lineno
            == function.__code__.co_firstlineno
            and FlextInfraWorkspaceGeneratedFunction._declared_decorator(
                node.decorator_list, function, spellings, wrapper
            )
        )

    @staticmethod
    def _qualified_scope(
        components: t.SequenceOf[str], tree: ast.Module
    ) -> t.SequenceOf[ast.stmt]:
        """Walk the physical class and ``<locals>`` scopes of a qualified name.

        A function parent owns the next scope only through ``<locals>``.

        Returns:
            The body holding the final component, or none when not unique.

        """
        nodes: t.SequenceOf[ast.stmt] = tree.body
        for index, component in enumerate(components[:-1]):
            if component == "<locals>":
                continue
            kind = (
                ast.FunctionDef if components[index + 1] == "<locals>" else ast.ClassDef
            )
            parents = [
                node
                for node in nodes
                if isinstance(node, ast.FunctionDef | ast.ClassDef)
                and type(node) is kind
                and node.name == component
            ]
            if len(parents) != 1:
                return ()
            nodes = parents[0].body
        return nodes

    @staticmethod
    def _declared_decorator(
        decorators: t.SequenceOf[ast.expr],
        function: FunctionType,
        spellings: frozenset[str] | None,
        wrapper: FunctionType | None,
    ) -> bool:
        """Accept exactly the expected decorator after native wrapper records.

        Returns:
            Whether the remaining decorator list is the accepted spelling.

        """
        if (
            wrapper is not None
            and decorators
            and FlextInfraWorkspaceGeneratedFunction._factory_marker(
                decorators[-1], function, wrapper
            )
        ):
            decorators = decorators[:-1]
        if (
            "__wrapped__" in vars(function)
            and decorators
            and FlextInfraWorkspaceGeneratedFunction._wraps_marker(
                decorators[-1], function
            )
        ):
            decorators = decorators[:-1]
        match decorators:
            case []:
                return spellings is None
            case [ast.Name(id=name)]:
                return spellings is not None and name in spellings
            case [ast.Attribute(value=ast.Name(id=owner), attr=member)]:
                return spellings is not None and f"{owner}.{member}" in spellings
            case _:
                return False

    @staticmethod
    def _wraps_marker(expression: ast.expr, function: FunctionType) -> bool:
        """Recognize ``functools.wraps(...)`` bound in the function's own globals.

        ``functools.wraps`` returns the same function after recording the native
        ``__wrapped__``; only that binding may sit innermost.

        Returns:
            Whether the expression calls the loaded ``functools.wraps``.

        """
        module = sys.modules.get("functools")
        wraps = vars(module).get("wraps") if module is not None else None
        if wraps is None:
            return False
        match expression:
            case ast.Call(func=ast.Name(id=name)):
                return function.__globals__.get(name) is wraps
            case ast.Call(func=ast.Attribute(value=ast.Name(id=owner), attr="wraps")):
                return function.__globals__.get(owner) is module
            case _:
                return False

    @staticmethod
    def _factory_marker(
        expression: ast.expr, function: FunctionType, wrapper: FunctionType
    ) -> bool:
        """Recognize the wrapper factory whose own code nests the wrapper code.

        Returns:
            Whether the decorator binds a Python function compiling the wrapper.

        """
        match expression:
            case ast.Name(id=name):
                factory = function.__globals__.get(name)
            case ast.Attribute(value=ast.Name(id=owner), attr=member):
                module = function.__globals__.get(owner)
                factory = (
                    vars(module).get(member) if type(module) is ModuleType else None
                )
            case _:
                return False
        if type(factory) is not FunctionType:
            return False
        pending: list[CodeType] = [factory.__code__]
        while pending:
            code = pending.pop()
            if code is wrapper.__code__:
                return True
            pending.extend(item for item in code.co_consts if type(item) is CodeType)
        return False

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
        if type(expected) is tuple:
            return (
                type(observed) is tuple
                and len(expected) == len(observed)
                and all(
                    map(
                        FlextInfraWorkspaceGeneratedFunction._same_default,
                        expected,
                        observed,
                    )
                )
            )
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
                case [ast.Call(func=ast.Name(id=name), args=[], keywords=[])] if (
                    self._class_sentinel(name, namespace[node.id], namespace, tree)
                ):
                    return namespace[node.id]
        msg = (
            "closed compiler default has no literal or native sentinel witness: "
            f"{ast.unparse(node)[:160]}; source={self._witness.source}"
        )
        raise ValueError(msg)

    def _class_sentinel(
        self,
        name: str,
        sentinel: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> bool:
        """Prove a module sentinel built by calling one empty physical class.

        An ``object`` subclass is authenticated as SDK class storage; an ``int``
        subclass must be the native zero integer.

        Returns:
            Whether the sentinel is the exact instance of that unique class.

        """
        owner = namespace.get(name)
        if type(owner) is not type or type(sentinel) is not owner:
            return False
        bases = vars(type)["__bases__"].__get__(owner, type)
        definitions = [
            item
            for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == name
        ]
        match definitions:
            case [
                ast.ClassDef(
                    decorator_list=[], bases=[], keywords=[], body=[ast.Pass()]
                )
            ] if bases == (object,):
                self._sdk_class(owner, namespace, tree)
                return True
            case [
                ast.ClassDef(
                    decorator_list=[], bases=[ast.Name(id="int")], body=[ast.Pass()]
                )
            ] if bases == (int,):
                return self._native_integer(sentinel) and int.__index__(sentinel) == 0
            case _:
                return False

    @staticmethod
    def _builtin(
        name: str, namespace: t.MappingKV[str, p.AttributeProbe]
    ) -> p.AttributeProbe:
        value = namespace.get(name, vars(builtins).get(name))
        if type(value) is type:
            if vars(builtins).get(name) is not value:
                msg = f"closed compiler data type binding is not native: {name}"
                raise ValueError(msg)
            if (
                vars(type)["__name__"].__get__(value, type(value)) != name
                or vars(type)["__module__"].__get__(value, type(value)) != "builtins"
                or not (
                    vars(type)["__flags__"].__get__(value, type(value))
                    & c.Infra.CPYTHON_IMMUTABLE_TYPE_FLAG
                )
            ):
                msg = f"closed compiler data constructor is interposed: {name}"
                raise ValueError(msg)
            return value
        native: BuiltinFunctionType | None = (
            value if type(value) is BuiltinFunctionType else None
        )
        if (
            native is None
            or native.__self__ is not builtins
            or native.__module__ != "builtins"
            or native.__name__ != name
            or vars(builtins).get(name) is not native
        ):
            msg = f"closed compiler builtin binding is not native: {name}"
            raise ValueError(msg)
        return native

    def _global(
        self,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if name not in namespace:
            if name in vars(builtins):
                return self._builtin(name, namespace)
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
            constructor: p.AttributeProbe = vars(tuple)["__new__"]
            return constructor
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
            item: p.AttributeProbe = mapping[key]
            return item
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
            hashed=(),
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
        module_name, literal, flag_name = self._regex_constructor(assignments)
        supplier = self._global(module_name, namespace, tree)
        if type(supplier) is not ModuleType or vars(supplier).get(
            "Pattern"
        ) is not type(pattern):
            msg = "dedent regex is not its registered native pattern type"
            raise ValueError(msg)
        self._function(vars(supplier)["compile"])
        native = type(pattern)
        storage = vars(type)["__dict__"].__get__(native, type(native))
        for operation in ("sub", "findall", "match"):
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
        flag = vars(supplier).get(flag_name) if flag_name is not None else 0
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

    @staticmethod
    def _regex_constructor(
        assignments: t.SequenceOf[ast.expr],
    ) -> t.Triple[str, str, str | None]:
        """Read either native regex constructor's literal pattern and flag binding.

        Returns:
            The imported module name, literal pattern and optional flag attribute.

        Raises:
            ValueError: If no unique physical regex constructor owns the binding.

        """
        match assignments:
            case [
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id=module_name), attr="compile"),
                    args=[ast.Constant(value=literal)],
                    keywords=[],
                )
            ] if type(literal) is str:
                return module_name, literal, None
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
                return module_name, literal, flag_name
            case _:
                msg = "dedent regex has no closed physical constructor"
                raise ValueError(msg)


__all__: t.VariadicTuple[str] = ("FlextInfraWorkspaceGeneratedFunction",)
