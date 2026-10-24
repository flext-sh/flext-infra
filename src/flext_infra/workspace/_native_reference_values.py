"""Native value serialization and module binding inventories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections import deque
from functools import partial
from json import dumps
from pathlib import Path
from types import (
    CodeType,
    FunctionType,
    GenericAlias,
    GetSetDescriptorType,
    MappingProxyType,
    MemberDescriptorType,
    MethodType,
    ModuleType,
    UnionType,
)
from typing import Literal

from flext_infra import m, p, r, t
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace._native_reference_symbols import (
    FlextInfraWorkspaceNativeReferenceSymbolsMixin,
)


class FlextInfraWorkspaceNativeReferenceValuesMixin(
    FlextInfraWorkspaceNativeReferenceSymbolsMixin
):
    @classmethod
    def _native_container_operands(
        cls,
        name: str,
        item: p.AttributeProbe,
    ) -> t.SequenceOf[t.Pair[str, p.AttributeProbe | None]] | None:
        """Read ordered native container edges before executable classification.

        Returns:
            The exact container edges, or no matching native container.

        """
        children: list[t.Infra.NativeOperand] | None = None
        native = type(item)
        if cls._is_operand_sequence(item) and native is not deque:
            children = list(item)
            if native is frozenset or native is set:
                children.sort(key=lambda child: cls._value(child, construction=True))
        if children is not None:
            return tuple(
                (f"{name}.{index}", child) for index, child in enumerate(children)
            )
        if cls._is_operand_mapping(item):
            entries: t.SequenceOf[t.Pair[p.AttributeProbe, p.AttributeProbe]] = tuple(
                item.items()
            )
            return tuple(
                (f"{name}.{index}.{part}", child)
                for index, pair in enumerate(entries)
                for part, child in enumerate(pair)
            )
        if native is MappingProxyType:
            return ((f"{name}.mapping", cls._native_mapping_proxy_backing(item)),)
        if (slice_state := cls._slice_state(item)) is not None:
            return tuple(
                (f"{name}.{attribute}", stored)
                for attribute, stored in zip(
                    ("start", "stop", "step"), slice_state, strict=True
                )
            )
        if (alias_state := cls._generic_alias_state(item)) is not None:
            operands = [
                (f"{name}.{attribute}", stored) for attribute, stored in alias_state
            ]
            if type(item) is not GenericAlias:
                operands.append((f"{name}.type", type(item)))
            return tuple(operands)
        return None

    @classmethod
    def _executable_operands(
        cls,
        binding: str,
        value: p.AttributeProbe | None,
        *,
        role: Literal["execution", "storage_type"] = "execution",
    ) -> t.SequenceOf[
        t.Triple[str, p.AttributeProbe, Literal["execution", "storage_type"]]
    ]:
        """Retain nested executable operands through exact native containers.

        Returns:
            Ordered executable references reached through admitted native storage.

        """
        # The 21fcf255 walker links reduced arguments to the existing code proof.
        pending: list[t.Pair[str, p.AttributeProbe | None]] = [(binding, value)]
        seen: set[int] = set()
        result: list[
            t.Triple[str, p.AttributeProbe, Literal["execution", "storage_type"]]
        ] = []
        while pending:
            name, item = pending.pop()
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            children = cls._native_container_operands(name, item)
            if children is not None:
                pending.extend(children)
            elif cls._is_class(item):
                result.append((name, item, role))
            elif cls._callable_storage(item):
                result.append((name, item, "execution"))
            elif cls._python_storage_class(type(item)):
                storage = cls._instance_storage(item)
                # Empty Python slots still retain a physical receiver type.
                result.append((f"{name}.receiver_type", type(item), "execution"))
                pending.extend(
                    (f"{name}.{attribute}", stored)
                    for attribute, present, stored in storage
                    if present
                )
        return tuple(result)

    @classmethod
    def _value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int] = frozenset(),
        *,
        construction: bool = False,
        context: m.Infra.NativeObservationContext | None = None,
        binding: str = "",
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
                context=context,
                binding=binding,
            )
        )

    @classmethod
    def _value_data(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        *,
        construction: bool,
        context: m.Infra.NativeObservationContext | None = None,
        binding: str = "",
    ) -> t.JsonValue:
        """Observe native slots as JSON data without authored accessors.

        Returns:
            Structural values read through admitted native storage.

        Raises:
            TypeError: A native descriptor differs from its registered owner.

        """
        scalar = cls._scalar_value(value)
        if scalar is not None:
            return scalar
        if cls._is_descriptor(value):
            owner = value.__objclass__
            if cls._class_namespace(owner).get(value.__name__) is not value:
                msg = "native descriptor differs from its registered owner"
                raise TypeError(msg)
            return ["native-descriptor", cls._symbol(owner), value.__name__]
        if id(value) in seen:
            return ["cycle", cls._symbol(value)]
        seen |= {id(value)}
        return cls._retained_value(
            value, seen, context, binding, construction=construction
        )

    @classmethod
    def _sequence_value(
        cls,
        value: t.IterableOf[t.Infra.NativeOperand],
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
        *,
        construction: bool,
    ) -> t.JsonValue:
        """Observe exact native sequence elements and retained deque capacity.

        Returns:
            The original ordered or canonically sorted native sequence payload.

        Raises:
            TypeError: The deque's native capacity descriptor is not authenticated.

        """
        native = type(value)
        observe = partial(
            cls._value_data,
            seen=seen,
            construction=construction,
            context=context,
            binding=binding,
        )
        items = list(map(observe, value))
        if native is deque:
            descriptor = cls._native_metadata_slot(
                cls._class_namespace(deque), "maxlen"
            )
            if (
                not cls._is_native(descriptor, GetSetDescriptorType)
                or descriptor.__objclass__ is not deque
            ):
                message = "native deque lacks its interpreter-owned maxlen slot"
                raise TypeError(message)
            if context is not None:
                context.references.append((f"{binding}.sequence_type", deque))
            return [
                "deque",
                observe(descriptor.__get__(value, deque)),
                items,
            ]
        return [
            native.__name__,
            sorted(items, key=dumps) if native is set or native is frozenset else items,
        ]

    @classmethod
    def _mapping_proxy_value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
        *,
        construction: bool,
    ) -> t.JsonValue:
        """Observe the actual native proxy backing under construction policy.

        Returns:
            Mutable identity or its fully observed native dictionary backing.

        Raises:
            TypeError: The proxy does not retain one exact native dictionary.

        """
        if not construction:
            return ["mutable", "mappingproxy"]
        backing = cls._native_instance_referents(value)
        if len(backing) != 1 or type(backing[0]) is not dict:
            msg = "native mappingproxy does not contain an exact interpreter dict"
            raise TypeError(msg)
        return [
            "mappingproxy",
            cls._value_data(
                backing[0],
                seen,
                construction=construction,
                context=context,
                binding=binding,
            ),
        ]

    @classmethod
    def _code_value(
        cls,
        value: t.Infra.NativeCode,
        context: m.Infra.NativeObservationContext | None,
    ) -> t.JsonValue:
        """Observe code through the same complete native compiler witness.

        Returns:
            Validated structured compiler evidence without a second slot catalog.

        """
        if context is not None and context.paths:
            value = cls._relocate_code(value, context.paths)
        return ["code", cls._code_evidence(value).model_dump(mode="json")]

    @classmethod
    def _container_value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
        *,
        construction: bool,
    ) -> t.JsonValue | None:
        """Observe an admitted native container without changing construction policy.

        Returns:
            Its structural payload, or no matching native container.

        """
        native = type(value)
        if (
            any(native is kind for kind in (list, set, dict, deque))
            and not construction
        ):
            return ["mutable", native.__name__]
        if cls._is_operand_sequence(value):
            return cls._sequence_value(
                value, seen, context, binding, construction=construction
            )
        if cls._is_operand_mapping(value):
            observe = partial(
                cls._value_data,
                seen=seen,
                construction=construction,
                context=context,
                binding=binding,
            )
            return [
                "dict",
                sorted([list(map(observe, pair)) for pair in value.items()], key=dumps),
            ]
        if native is MappingProxyType:
            return cls._mapping_proxy_value(
                value, seen, context, binding, construction=construction
            )
        if cls._is_native(value, CodeType):
            return cls._code_value(value, context)
        return None

    @classmethod
    def _executable_value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
        *,
        construction: bool,
    ) -> t.JsonValue | None:
        """Observe native executable references after the container categories.

        Returns:
            The executable payload, or no matching native executable.

        """
        native = type(value)
        observe = partial(
            cls._value_data,
            seen=seen,
            construction=construction,
            context=context,
            binding=binding,
        )
        if cls._is_native(value, FunctionType):
            return [
                "function",
                cls._symbol(value),
                cls._code_value(value.__code__, context),
                observe(value.__defaults__),
                observe(value.__kwdefaults__),
                observe(
                    tuple(cell.cell_contents for cell in value.__closure__ or ()),
                ),
            ]
        if native is UnionType:
            arguments = vars(UnionType)["__args__"].__get__(value, UnionType)
            return ["union", observe(arguments, construction=False)]
        if any(owner is GenericAlias for owner in cls._native_mro(native)):
            storage = vars(GenericAlias)
            return [
                "generic_alias",
                cls._symbol(native),
                *(
                    observe(storage[name].__get__(value, native), construction=False)
                    for name in ("__origin__", "__args__")
                ),
            ]
        if (
            cls._native_builtin(value)
            and value.__self__ is not None
            and not cls._is_class(value.__self__)
            and type(value.__self__) is not ModuleType
        ):
            return [
                "native_method",
                cls._symbol(value),
                observe(
                    value.__self__,
                    binding=f"{binding}; receiver_of={cls._symbol(value)}",
                ),
            ]
        if cls._is_class(value) or cls._native_builtin(value) or native is ModuleType:
            return ["symbol", cls._symbol(value)]
        return None

    @classmethod
    def _retained_value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
        *,
        construction: bool,
    ) -> t.JsonValue:
        """Observe a cycle-guarded value through its original storage categories.

        Returns:
            The first matching native representation in its original category order.

        """
        container = cls._container_value(
            value, seen, context, binding, construction=construction
        )
        if container is not None:
            return container
        executable = cls._executable_value(
            value, seen, context, binding, construction=construction
        )
        if executable is not None:
            return executable
        if not construction:
            return ["instance", cls._symbol(type(value))]
        return cls._instance_value(value, seen, context, binding)

    @classmethod
    def _storage_values(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
    ) -> list[t.JsonValue]:
        """Observe interpreter-owned dictionaries and slots in native MRO order.

        Returns:
            The original ordered slot identities and structural payloads.

        """
        ancestry = cls._native_mro(type(value))
        elected = {
            name: descriptor
            for owner in reversed(ancestry)
            for name, descriptor in cls._class_namespace(owner).items()
        }
        native_lookup = (
            elected["__getattribute__"] is vars(object)["__getattribute__"]
            and "__getattr__" not in elected
        )
        observe = partial(
            cls._value_data,
            seen=seen,
            construction=True,
            context=context,
            binding=binding,
        )
        observed: list[t.JsonValue] = []
        for owner in ancestry:
            for name, descriptor in sorted(cls._class_namespace(owner).items()):
                if (
                    cls._is_native(descriptor, MemberDescriptorType)
                    or (
                        name == "__dict__"
                        and cls._is_native(descriptor, GetSetDescriptorType)
                    )
                ) and descriptor.__objclass__ is owner:
                    kind, stored = cls._slot_storage(
                        value, name, descriptor, elected, native_lookup=native_lookup
                    )
                    observed.append([
                        f"{cls._symbol(owner)}::{name}",
                        ["shadowed", cls._symbol(stored)]
                        if kind == "shadowed"
                        else ["uninitialized"]
                        if kind == "uninitialized"
                        else observe(stored),
                    ])
        return observed

    @classmethod
    def _instance_value(
        cls,
        value: t.Infra.NativeOperand,
        seen: frozenset[int],
        context: m.Infra.NativeObservationContext | None,
        binding: str,
    ) -> t.JsonValue:
        """Authenticate full instance storage or its registered native singleton.

        Returns:
            The original structural instance observation.

        Raises:
            ValueError: No callback-free storage or registered binding exists.

        """
        native = type(value)
        observed = cls._storage_values(value, seen, context, binding)
        observe = partial(
            cls._value_data,
            seen=seen,
            construction=True,
            context=context,
            binding=binding,
        )
        if cls._native_callable_instance(value):
            return [
                "native_callable_storage",
                cls._symbol(native),
                observed,
                [
                    observe(item, construction=True)
                    for item in cls._native_instance_referents(value)
                ],
            ]
        if observed:
            return ["storage", cls._symbol(native), observed]
        supplier = cls._native_type_supplier(native)
        if supplier is not None:
            supplier_name, module = supplier
            namespace = cls._module_namespace(module)
            bindings = tuple(
                name
                for name, registered in sorted(namespace.items())
                if registered is value
            )
            if bindings:
                FlextInfraWorkspaceEnvironmentProvenance.module_source(
                    supplier_name
                ).unwrap()
                if context is not None:
                    context.references.append((
                        f"{supplier_name}::{bindings[0]}",
                        native,
                    ))
                return ["registered_instance", cls._symbol(native), list(bindings)]
        raise ValueError(
            "native import operand has no callback-free storage or registered binding: "
            + cls._symbol(native)
            + (f"; binding={binding}" if binding else ""),
        )

    @classmethod
    def _module_generated_owners(
        cls,
        context: m.Infra.NativeObservationContext,
        name: str,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> None:
        """Retain actual generated function receivers from an elected namespace."""
        for attribute, member in namespace.items():
            if (
                cls._is_native(member, FunctionType)
                and member.__code__.co_filename.startswith("<")
                and not member.__code__.co_filename.startswith("<frozen ")
                and (
                    id(member) not in context.generated_owners
                    or context.generated_owners[id(member)][2] is None
                )
            ):
                context.generated_owners[id(member)] = (name, attribute, None)
            elif cls._is_class(member):
                supplier = cls._type_attr("__module__", member, type(member))
                if type(supplier) is str:
                    cls._remember_generated_descriptors(
                        member, supplier, context.generated_owners
                    )

    @classmethod
    def _namespace_functions(
        cls,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> t.SequenceOf[t.Infra.NativeOperand]:
        """Collect functions from the elected module and its raw class namespaces.

        Returns:
            Functions and native function wrappers in their original inventory order.

        """
        functions: list[t.Infra.NativeOperand] = [
            value for value in namespace.values() if type(value) is FunctionType
        ]
        functions.extend(
            member.__func__ if cls._is_function_binding(member) else member
            for value in namespace.values()
            if cls._is_class(value)
            for member in cls._class_namespace(value).values()
            if type(member) is FunctionType or cls._is_function_binding(member)
        )
        return functions

    @classmethod
    def _mutable_module_globals(
        cls,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        instructions: t.Infra.NativeInstructionFacts,
    ) -> set[str]:
        """Elect globals written by the namespace's actual native functions.

        Returns:
            Global names assigned by the original ordered function inventory.

        """
        mutable: set[str] = set()
        for function in cls._namespace_functions(namespace):
            if not (
                cls._is_native(function, FunctionType)
                or cls._is_native(function, MethodType)
            ):
                continue
            mutable.update(
                instruction.argval
                for instruction in cls._instructions(function.__code__, instructions)
                if instruction.opname == "STORE_GLOBAL"
            )
        return mutable

    @classmethod
    def _module_inventory(
        cls,
        context: m.Infra.NativeObservationContext,
        name: str,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        instructions: t.Infra.NativeInstructionFacts,
    ) -> None:
        """Observe complete-module booleans and enqueue its executable bindings."""
        mutable = cls._mutable_module_globals(namespace, instructions)
        context.evidence.extend(
            m.Infra.NativeBindingEvidence(
                binding=f"{name}::{key}",
                kind="boolean",
                supplier=name,
                name=key,
                qualname=key,
                operands=(
                    (
                        "value",
                        cls._value(value, context=context),
                    ),
                ),
            )
            for key, value in sorted(namespace.items())
            if type(value) is bool and key not in mutable
        )
        context.pending.extend(cls._module_bindings(name, namespace))

    @classmethod
    def _module_bindings(
        cls,
        name: str,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> t.SequenceOf[
        t.Quint[
            str, t.Infra.NativeOperand, str, str, Literal["execution", "storage_type"]
        ]
    ]:
        """Elect a complete module's executable bindings in stable name order.

        Returns:
            Native graph work for every admitted executable binding.

        """
        return tuple(
            (f"{name}::{key}", value, name, "", "execution")
            for key, value in sorted(namespace.items())
            if cls._is_class(value)
            or type(value) is FunctionType
            or type(value) is MethodType
            or cls._native_builtin(value)
            or type(value) is property
            or cls._is_function_binding(value)
            or cls._callable_storage(value)
        )

    @classmethod
    def _nominate_lexical_binding(
        cls,
        context: m.Infra.NativeObservationContext,
        nomination: m.Infra.SourceClassReference,
        module: t.Infra.NativeOperand,
        source: Path,
    ) -> p.Result[bool]:
        """Enqueue the exact declared lexical binding in its elected module.

        Returns:
            Success after the original lexical path has been fully resolved.

        """
        value = module
        qualified = ".".join(nomination.attributes)
        for component in nomination.attributes:
            namespace: t.MappingKV[str, t.Infra.NativeOperand] = (
                cls._class_namespace(value)
                if cls._is_class(value)
                else cls._module_namespace(value)
                if isinstance(value, ModuleType)
                else {}
            )
            if component not in namespace:
                return r[bool].fail(
                    "selected producer binding is absent: "
                    f"{nomination.target}::{qualified}",
                )
            value = namespace[component]
        context.pending.append((
            f"{nomination.target}::{qualified}",
            value,
            nomination.target,
            str(source),
            "execution",
        ))
        return r[bool].ok(value=True)

    @classmethod
    def _nominate_module(
        cls,
        context: m.Infra.NativeObservationContext,
        nomination: m.Infra.SourceClassReference,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Elect one physical module anchor before observing its selected bindings.

        Returns:
            The first election failure or a fully enqueued native nomination.

        """
        name = nomination.target
        module = sys.modules.get(name)
        origin = FlextInfraWorkspaceEnvironmentProvenance.module_source(name)
        if origin.failure:
            return r[bool].from_failure(origin)
        if sys.modules.get(name) is not module:
            return r[bool].fail(
                f"native reference module election changed: {name}",
            )
        anchored = name in context.module_anchors
        selected_origin = cls._source_path(origin.value, context.paths)
        if anchored:
            if (
                context.module_anchors[name] is not module
                or cls._source_path(context.origins[name], context.paths)
                != selected_origin
            ):
                return r[bool].fail(
                    f"native reference module anchor changed: {name}",
                )
            if not nomination.attributes:
                return r[bool].ok(value=True)
        namespace = cls._module_namespace(module)
        cls._module_generated_owners(context, name, namespace)
        context.origins[name] = origin.value
        context.sources.add((name, str(selected_origin), ""))
        if not anchored:
            context.module_anchors[name] = module
            context.evidence.append(
                m.Infra.NativeBindingEvidence.model_validate({
                    "binding": name,
                    "kind": "module",
                    "supplier": name,
                    "name": namespace["__name__"],
                    "qualname": "",
                    "operands": (("module_type", cls._symbol(type(module))),),
                })
            )
        if type(module) is not ModuleType:
            context.pending.append((
                f"{name}.module_type",
                type(module),
                name,
                str(selected_origin),
                "storage_type",
            ))
        if nomination.attributes:
            return cls._nominate_lexical_binding(
                context, nomination, module, selected_origin
            )
        cls._module_inventory(context, name, namespace, instructions)
        return r[bool].ok(value=True)

    @classmethod
    def _executable_binding(cls, value: t.Infra.NativeOperand) -> bool:
        """Classify executable graph members through native storage alone.

        Returns:
            Whether the original native inventory admits the member for traversal.

        """
        return (
            cls._is_class(value)
            or any(
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
            or cls._callable_storage(value)
        )

    @classmethod
    def _class_declaration(
        cls,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        declared: t.VariadicTuple[frozenset[str]],
    ) -> t.DictKV[str, t.Infra.NativeOperand]:
        """Elect source-declared class data without traversing executable members.

        Returns:
            Ordered native declaration values belonging to the source class body.

        """
        return {
            name: item
            for name, item in sorted(namespace.items())
            if name != "__annotations__"
            and (not declared or name in declared[0])
            and not cls._is_class(item)
            and not cls._callable_storage(item)
            and not (cls._is_native(item, property) or cls._is_function_binding(item))
        }

    @classmethod
    def _enqueue_class_members(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeType,
        binding: str,
        identity: t.Quad[str, str, str, t.MappingKV[str, t.Infra.NativeOperand]],
    ) -> None:
        """Queue executed constructors or retain an existing type's native ancestry."""
        supplier, source, _qualname, namespace = identity
        role = context.role if context.lexical else "execution"
        if role == "execution" and id(value) not in context.expanded_classes:
            context.expanded_classes.add(id(value))
            context.pending.extend(
                (f"{binding}.{key}", item, supplier, source, "execution")
                for key, item in sorted(namespace.items())
                if (not context.lexical or key in {"__new__", "__init__", "__call__"})
                and cls._executable_binding(item)
            )
        context.pending.append((
            f"{binding}.metaclass",
            type(value),
            supplier,
            source,
            role,
        ))
        context.pending.extend(
            (f"{binding}.base.{index}", base, supplier, source, role)
            for index, base in enumerate(
                cls._type_attr("__bases__", value, type(value))
            )
        )


__all__: list[str] = ["FlextInfraWorkspaceNativeReferenceValuesMixin"]
