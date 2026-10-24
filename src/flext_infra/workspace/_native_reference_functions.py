"""Capture of authored function sources, namespaces and attribute edges.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import partial
from importlib.machinery import ModuleSpec
from json import dumps
from types import FunctionType, MethodType, ModuleType

from flext_infra import m, p, r, t
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace._native_reference_values import (
    FlextInfraWorkspaceNativeReferenceValuesMixin,
)


class FlextInfraWorkspaceNativeReferenceFunctionsMixin(
    FlextInfraWorkspaceNativeReferenceValuesMixin
):
    @classmethod
    def _receiver_path(
        cls, supplier: str, receiver: t.Infra.NativeType
    ) -> p.Result[str]:
        """Name a generated receiver by the lexical path that resolves to it.

        The qualified name is the path when it resolves to this exact class;
        a tuple built as ``Alias = namedtuple("Name", ...)`` resolves only
        through its unique module alias.

        Returns:
            The module-relative path the receipt re-resolves to this receiver.

        """
        module = sys.modules.get(supplier)
        if type(module) is not ModuleType:
            return r[str].fail(f"generated receiver supplier is not loaded: {supplier}")
        if not cls._is_class(receiver):
            return r[str].fail(f"generated receiver is not a native class: {supplier}")
        namespace = cls._module_namespace(module)
        qualified = cls._type_attr("__qualname__", receiver, type(receiver))
        resolved: p.AttributeProbe | None = module
        for component in qualified.split("."):
            scope = (
                cls._module_namespace(resolved)
                if type(resolved) is ModuleType
                else cls._class_namespace(resolved)
                if cls._is_class(resolved)
                else {}
            )
            resolved = scope.get(component)
        if resolved is receiver:
            return r[str].ok(qualified)
        aliases = sorted(
            name for name, value in namespace.items() if value is receiver
        ) or sorted(
            f"{name}.<base:{index}>"
            for name, value in namespace.items()
            if type(value) is type
            for index, base in enumerate(vars(type)["__bases__"].__get__(value, type))
            if base is receiver
        )
        if len(aliases) != 1:
            return r[str].fail(
                f"generated receiver has no unique lexical path: {supplier}::"
                f"{qualified}; aliases={aliases[:8]}"
            )
        return r[str].ok(aliases[0])

    @classmethod
    def _generated_function_source(
        cls,
        context: m.Infra.NativeObservationContext,
        value: FunctionType,
    ) -> p.Result[t.Pair[str, t.VariadicTuple[t.Pair[str, str]]]]:
        """Observe the registered supplier and receiver without replaying a compiler.

        Returns:
            The actual binding identities, pending independent cold authentication.

        """
        result_type = r[t.Pair[str, t.VariadicTuple[t.Pair[str, str]]]]
        owner = context.generated_owners.get(id(value))
        if owner is None:
            return result_type.fail(
                "generated function has no physical source owner: "
                f"{context.binding_context}"
            )
        supplier, attribute, receiver = owner
        if receiver is not None and not cls._is_class(receiver):
            return result_type.fail(
                f"generated receiver is not a native class: {context.binding}"
            )
        receiver_path = (
            r[str].ok("")
            if receiver is None
            else cls._receiver_path(supplier, receiver)
        )
        if receiver_path.failure:
            return result_type.from_failure(receiver_path)
        return result_type.ok((
            supplier,
            (
                ("generated_attribute", attribute),
                ("generated_receiver", receiver_path.value),
            ),
        ))

    @classmethod
    def _capture_function_source(
        cls,
        context: m.Infra.NativeObservationContext,
        value: FunctionType,
    ) -> p.Result[m.Infra.NativeFunctionObservationContext]:
        """Elect the actual function source before inspecting executable operands.

        Returns:
            Complete native function/source facts, or the first source refusal.

        """
        code = cls._relocate_code(value.__code__, context.paths)
        generated = code.co_filename.startswith(
            "<"
        ) and not code.co_filename.startswith("<frozen ")
        generated_operands: t.VariadicTuple[t.Pair[str, str]] = ()
        if generated:
            compiled = cls._generated_function_source(context, value)
            if compiled.failure:
                return r[m.Infra.NativeFunctionObservationContext].from_failure(
                    compiled
                )
            actual_supplier, generated_operands = compiled.value
        else:
            actual_supplier = value.__globals__.get("__name__")
            if type(actual_supplier) is not str:
                return r[m.Infra.NativeFunctionObservationContext].fail(
                    f"producer globals have no supplier identity: {context.binding}",
                )
            module = sys.modules.get(actual_supplier)
            if module is None or (
                not generated and value.__globals__ is not cls._module_namespace(module)
            ):
                return r[m.Infra.NativeFunctionObservationContext].fail(
                    f"producer globals have no native supplier: {context.binding}",
                )
        origin = context.origins.get(actual_supplier)
        if origin is None:
            observed = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                actual_supplier,
            )
            if observed.failure:
                return r[m.Infra.NativeFunctionObservationContext].from_failure(
                    observed
                )
            origin = context.origins[actual_supplier] = observed.value
        supplier_namespace = cls._module_namespace(sys.modules[actual_supplier])
        supplier_spec = supplier_namespace["__spec__"]
        if not cls._is_native(supplier_spec, ModuleSpec):
            return r[m.Infra.NativeFunctionObservationContext].fail(
                f"producer native supplier has no module spec: {actual_supplier}"
            )
        # A physical function is named by its compiled qualified name: library
        # code may rewrite ``__qualname__`` (attrs re-labels ``evolve`` for each
        # class it serves), which would make the source epoch process-local.
        context.sources.add((
            (
                f"{actual_supplier}::"
                f"{value.__qualname__ if generated else code.co_qualname}"
            ),
            str(cls._source_path(origin, context.paths))
            if generated or supplier_spec.origin == "frozen"
            else code.co_filename,
            context.owner_source if generated else "",
        ))
        return r[m.Infra.NativeFunctionObservationContext].ok(
            m.Infra.NativeFunctionObservationContext(
                value=(value,),
                code=code,
                supplier=actual_supplier,
                origin=origin,
                generated=generated,
                generated_operands=generated_operands,
            )
        )

    @classmethod
    def _function_namespaces(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> None:
        """Observe actual closure, globals and builtins before lexical expansion."""
        facts.nonlocals.update(
            (name, cell.cell_contents)
            for name, cell in cls._function_cells(facts.value[0]).items()
        )
        global_namespace = facts.value[0].__globals__
        # The native function slot retains its actual builtins dictionary.
        builtin_slot: p.Infra.NativeStorageSlot[
            t.DictKV[str, t.Infra.NativeOperand]
        ] = vars(FunctionType)["__builtins__"]
        builtin_namespace = builtin_slot.__get__(facts.value[0], FunctionType)
        for namespace_name, namespace in (
            ("globals", global_namespace),
            ("builtins", builtin_namespace),
        ):
            if type(namespace) is not dict:
                context.pending.append((
                    f"{context.binding}.{namespace_name}.type",
                    type(namespace),
                    facts.supplier,
                    context.owner_source,
                    "storage_type",
                ))
        global_names = {
            instruction.argval
            for instruction in cls._instructions(facts.code, instructions)
            if instruction.opname == "LOAD_GLOBAL"
            and isinstance(instruction.argval, str)
        }
        native_getitem: Callable[
            [t.DictKV[str, t.Infra.NativeOperand], str], t.Infra.NativeOperand
        ] = vars(dict)["__getitem__"]
        native_contains: Callable[[t.DictKV[str, t.Infra.NativeOperand], str], bool] = (
            vars(dict)["__contains__"]
        )
        facts.global_bindings.update({
            name: (
                native_getitem(global_namespace, name)
                if native_contains(global_namespace, name)
                else native_getitem(builtin_namespace, name)
            )
            for name in sorted(global_names)
            if native_contains(global_namespace, name)
            or native_contains(builtin_namespace, name)
        })
        facts.operational_globals = frozenset(
            instruction.argval
            for unit in cls._code_units(facts.code)
            if not facts.global_bindings.keys().isdisjoint(unit.co_names)
            for instruction in cls._instructions(unit, instructions)
            if instruction.opname in {"STORE_GLOBAL", "DELETE_GLOBAL"}
            and isinstance(instruction.argval, str)
        )

    @classmethod
    def _function_class_roots(
        cls,
        facts: m.Infra.NativeFunctionObservationContext,
    ) -> list[t.Infra.NativeType]:
        """Elect lexical and globally retained classes in the original native order.

        Returns:
            The original ordered class roots for native descriptor traversal.

        """
        class_roots = [
            item
            for item in tuple(facts.global_bindings.values())
            if cls._is_class(item)
        ]
        lexical = sys.modules.get(facts.supplier)
        for component in facts.code.co_qualname.split(".")[:-1]:
            namespace: t.MappingKV[str, t.Infra.NativeOperand] = (
                cls._class_namespace(lexical)
                if cls._is_class(lexical)
                else vars(lexical)
                if type(lexical) is ModuleType
                else {}
            )
            lexical = namespace.get(component)
            if cls._is_class(lexical):
                class_roots.append(lexical)
        return class_roots

    @classmethod
    def _function_descriptor_edges(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
    ) -> None:
        """Queue native descriptor identities through actual lexical class ancestry."""
        class_roots = cls._function_class_roots(facts)
        inspected: set[int] = set()
        while class_roots:
            owner = class_roots.pop()
            if id(owner) in inspected:
                continue
            inspected.add(id(owner))
            resolved_names: set[str] = set()
            for ancestor in cls._native_mro(owner):
                namespace = cls._class_namespace(ancestor)
                for name in facts.code.co_names:
                    if name in resolved_names or name not in namespace:
                        continue
                    resolved_names.add(name)
                    item = namespace.get(name)
                    if cls._is_class(item):
                        class_roots.append(item)
                    elif cls._callable_operand(item):
                        context.pending.append((
                            f"{context.binding}.descriptor.{cls._symbol(ancestor)}.{name}",
                            item,
                            facts.supplier,
                            str(cls._source_path(facts.origin, context.paths)),
                            "execution",
                        ))

    @classmethod
    def _enqueue_function_operands(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
    ) -> None:
        """Queue actual globals, defaults and closure operands in original order."""
        context.pending.extend(
            (
                f"{context.binding}.global.{name}",
                item,
                facts.supplier,
                context.owner_source,
                "execution",
            )
            for name, item in facts.global_bindings.items()
            if item is not None
            and (
                cls._is_class(item)
                or type(item) is FunctionType
                or type(item) is MethodType
                or cls._native_builtin(item)
                or cls._callable_storage(item)
            )
        )
        context.pending.extend(
            (operand_binding, item, facts.supplier, context.owner_source, role)
            for label, stored in (
                ("defaults", facts.value[0].__defaults__),
                ("keyword_defaults", facts.value[0].__kwdefaults__),
                ("closure", facts.nonlocals),
            )
            for operand_binding, item, role in cls._executable_operands(
                f"{context.binding}.{label}",
                stored,
            )
        )

    @classmethod
    def _capture_function_evidence(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
        kind: str,
    ) -> None:
        """Record complete function evidence after expanding its native graph.

        Raises:
            TypeError: Generated globals have foreign storage or non-string keys.

        """
        observe_value = partial(
            cls._value, context=context, binding=context.binding_context
        )
        function = facts.value[0]
        wrapped = vars(function).get("__wrapped__")
        globals_owner = cls._module_namespace(sys.modules[facts.supplier])
        builtin_slot: p.Infra.NativeStorageSlot[
            t.DictKV[str, t.Infra.NativeOperand]
        ] = vars(FunctionType)["__builtins__"]
        builtins = builtin_slot.__get__(function, FunctionType)
        native_builtins = cls._module_namespace(sys.modules["builtins"])
        if facts.generated and (
            type(function.__globals__) is not dict
            or any(type(name) is not str for name in function.__globals__)
        ):
            msg = "generated globals require native string-keyed storage"
            raise TypeError(msg)
        generated_storage = (
            (
                (
                    "generated_globals",
                    dumps(("module", facts.supplier))
                    if function.__globals__ is globals_owner
                    else dumps(
                        tuple(
                            (
                                name,
                                observe_value(
                                    item,
                                    construction=name != "__builtins__",
                                ),
                            )
                            for name, item in sorted(function.__globals__.items())
                        )
                    ),
                ),
                (
                    "generated_builtins",
                    dumps(("module", "builtins"))
                    if builtins is native_builtins
                    else observe_value(builtins),
                ),
            )
            if facts.generated
            else ()
        )
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind=kind,
                supplier=facts.supplier,
                name=facts.value[0].__name__,
                qualname=function.__qualname__,
                code=cls._code_evidence(facts.code).model_dump_json(),
                operands=(
                    *facts.generated_operands,
                    *generated_storage,
                    ("module", observe_value(facts.value[0].__module__)),
                    (
                        "annotations",
                        observe_value(function.__annotations__, construction=True),
                    ),
                    (
                        "globals",
                        dumps(
                            tuple(
                                (
                                    name,
                                    observe_value(
                                        item,
                                        construction=facts.generated,
                                    ),
                                )
                                for name, item in sorted(facts.global_bindings.items())
                                if name not in facts.operational_globals
                            )
                        ),
                    ),
                    ("defaults", observe_value(facts.value[0].__defaults__)),
                    (
                        "keyword_defaults",
                        dumps(
                            tuple(
                                (name, observe_value(item))
                                for name, item in sorted(
                                    (facts.value[0].__kwdefaults__ or {}).items()
                                )
                            )
                        ),
                    ),
                    (
                        "closure",
                        dumps(
                            tuple(
                                (name, observe_value(item))
                                for name, item in sorted(facts.nonlocals.items())
                            )
                        ),
                    ),
                    ("wrapped", observe_value(wrapped)),
                ),
                operational=tuple(
                    (
                        f"global.{name}",
                        observe_value(item, construction=facts.generated),
                    )
                    for name, item in facts.global_bindings.items()
                    if name in facts.operational_globals
                ),
            ),
        )

    @classmethod
    def _receiver_namespaces(
        cls,
        receiver: t.Infra.NativeOperand,
    ) -> t.VariadicTuple[t.MappingKV[str, t.Infra.NativeOperand]]:
        """Read a LOAD_ATTR receiver's raw storage in native lookup order.

        Returns:
            Class storage along the native MRO, the module storage, or none.

        """
        if cls._is_class(receiver):
            return tuple(
                cls._class_namespace(owner) for owner in cls._native_mro(receiver)
            )
        if isinstance(receiver, ModuleType):
            return (cls._module_namespace(receiver),)
        return ()

    @classmethod
    def _callable_operand(cls, value: t.Infra.NativeOperand) -> bool:
        """Elect a non-class edge target that the observation must follow.

        Returns:
            Whether the target is a function, native descriptor or callable storage.

        """
        return (
            any(
                type(value) is kind
                for kind in (
                    FunctionType,
                    MethodType,
                    property,
                    classmethod,
                    staticmethod,
                )
            )
            or cls._native_builtin(value)
            or cls._native_wrapper_kind(value) is not None
            or cls._callable_storage(value)
        )

    @classmethod
    def _function_attribute_edges(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Follow actual native LOAD_GLOBAL and LOAD_ATTR edges without descriptors.

        Returns:
            The original lexical attribute graph or its first absent-edge contradiction.

        """
        # Query actual native global/attribute edges, not every name in
        # an ambient module's dictionary. No descriptor is executed.
        receiver = None
        edge = context.binding
        for instruction in cls._instructions(facts.code, instructions):
            if instruction.opname == "LOAD_GLOBAL":
                receiver = facts.global_bindings.get(instruction.argval)
                edge = f"{context.binding}.global.{instruction.argval}"
            elif instruction.opname == "LOAD_ATTR" and receiver is not None:
                namespaces = cls._receiver_namespaces(receiver)
                if not namespaces:
                    receiver = None
                    continue
                found = next(
                    (
                        namespace
                        for namespace in namespaces
                        if instruction.argval in namespace
                    ),
                    None,
                )
                if found is None:
                    absent = cls._absent_edge(context, facts, edge, instruction.argval)
                    if absent.failure:
                        return absent
                    receiver = None
                    continue
                if isinstance(receiver, ModuleType):
                    supplier = found.get("__name__")
                    if cls._is_native(supplier, str):
                        cls._module_generated_owners(context, supplier, found)
                receiver = found[instruction.argval]
                edge += f".{instruction.argval}"
                if cls._is_class(receiver) or cls._callable_operand(receiver):
                    context.pending.append((
                        edge,
                        receiver,
                        facts.supplier,
                        str(cls._source_path(facts.origin, context.paths)),
                        "execution",
                    ))
            else:
                receiver = None
        return r[bool].ok(value=True)

    @classmethod
    def _capture_function(
        cls,
        context: m.Infra.NativeObservationContext,
        value: FunctionType,
        kind: str,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Observe one actual function in original source, graph and evidence order.

        Returns:
            Complete native function evidence or its first authentication failure.

        """
        captured = cls._capture_function_source(context, value)
        if captured.failure:
            return r[bool].from_failure(captured)
        facts = captured.value
        cls._function_namespaces(context, facts, instructions)
        if context.lexical:
            attributes = cls._function_attribute_edges(context, facts, instructions)
            if attributes.failure:
                return attributes
            cls._function_descriptor_edges(context, facts)
        cls._enqueue_function_operands(context, facts)
        cls._capture_function_evidence(context, facts, kind)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceNativeReferenceFunctionsMixin"]
