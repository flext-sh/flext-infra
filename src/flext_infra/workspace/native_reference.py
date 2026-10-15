"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import itertools
import marshal
import sys
from base64 import b64encode
from collections import deque
from collections.abc import Callable, Generator
from contextlib import contextmanager
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
from typing import ClassVar, Literal, TypeGuard, overload

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournalRelocation,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    _compilation_facts: ClassVar[ContextVar[t.Infra.NativeInvocationFacts | None]] = (
        ContextVar("native_compilation_facts", default=None)
    )

    @classmethod
    @contextmanager
    def compilation_scope(cls) -> Generator[None]:
        """Share immutable compilation facts for one enclosing invocation.

        Nested consumers reuse class facts and instructions for exact, strongly
        retained code identities. No namespace, receipt or authority verdict is
        retained. Physical source reads and runtime observations stay uncached;
        standalone captures keep their own instruction cache.

        Yields:
            Control with invocation-local compiler facts available.

        """
        if (
            ContextVar[t.Infra.NativeInvocationFacts | None].get(cls._compilation_facts)
            is not None
        ):
            yield
            return
        token = ContextVar[t.Infra.NativeInvocationFacts | None].set(
            cls._compilation_facts, ({}, {})
        )
        try:
            yield
        finally:
            ContextVar[t.Infra.NativeInvocationFacts | None].reset(
                cls._compilation_facts, token
            )

    @staticmethod
    def _is_native[NativeT](
        value: t.Infra.NativeOperand,
        native: type[NativeT],
    ) -> TypeGuard[NativeT]:
        """Retain an exact native identity without reading authored attributes.

        Returns:
            Whether the value has exactly the supplied interpreter type.

        """
        return type(value) is native

    @staticmethod
    def _is_function_binding(
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[p.Infra.NativeFunctionBinding]:
        """Admit the two interpreter-owned function wrapper slots.

        Returns:
            Whether the value stores a classmethod or staticmethod function.

        """
        return type(value) is classmethod or type(value) is staticmethod

    @staticmethod
    def _is_descriptor(
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[t.Infra.NativeDescriptor]:
        """Admit exact native descriptor storage without executing a hook.

        Returns:
            Whether the value is an interpreter descriptor with native metadata.

        """
        native = type(value)
        return (
            native is GetSetDescriptorType
            or native is MemberDescriptorType
            or native is ClassMethodDescriptorType
            or native is MethodDescriptorType
            or native is WrapperDescriptorType
        )

    @staticmethod
    def _is_operand_sequence(
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[t.IterableOf[t.Infra.NativeOperand]]:
        """Admit exact native operand sequences before iterating their values.

        Returns:
            Whether the value has callback-free native sequence storage.

        """
        native = type(value)
        return any(
            native is expected for expected in (tuple, list, set, frozenset, deque)
        )

    @staticmethod
    def _is_operand_mapping(
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[t.DictKV[t.Infra.NativeOperand, t.Infra.NativeOperand]]:
        """Admit exact native dictionary storage before reading its entries.

        Returns:
            Whether the value has exactly the interpreter dictionary type.

        """
        return type(value) is dict

    @staticmethod
    def _is_operand_tuple(
        value: t.Infra.NativeOperand,
    ) -> TypeGuard[t.VariadicTuple[t.Infra.NativeOperand]]:
        """Retain exact native tuple contents without untyped element inference.

        Returns:
            Whether the value is exactly an interpreter tuple.

        """
        return type(value) is tuple

    @staticmethod
    @overload
    def _type_attr(
        member: Literal["__name__", "__qualname__"],
        obj: t.Infra.NativeType,
        owner: t.Infra.NativeType,
    ) -> str: ...

    @staticmethod
    @overload
    def _type_attr(
        member: Literal["__bases__"],
        obj: t.Infra.NativeType,
        owner: t.Infra.NativeType,
    ) -> t.VariadicTuple[t.Infra.NativeType]: ...

    @staticmethod
    @overload
    def _type_attr(
        member: str,
        obj: t.Infra.NativeType,
        owner: t.Infra.NativeType,
    ) -> p.AttributeProbe | None: ...

    @staticmethod
    def _type_attr(
        member: str,
        obj: t.Infra.NativeType,
        owner: t.Infra.NativeType,
    ) -> p.AttributeProbe | None:
        """Read a native type member through its defining descriptor.

        Returns:
            The exact stored native member value.

        """
        descriptor: p.Infra.NativeStorageSlot[p.AttributeProbe | None] = vars(type)[
            member
        ]
        return descriptor.__get__(obj, owner)

    @staticmethod
    def _native_mro(
        owner: t.Infra.NativeType,
    ) -> t.SequenceOf[t.Infra.NativeType]:
        """Read native method resolution order without metaclass hooks.

        Returns:
            The interpreter-owned method resolution order.

        """
        descriptor: p.Infra.NativeStorageSlot[t.SequenceOf[t.Infra.NativeType]] = vars(
            type
        )["__mro__"]
        return descriptor.__get__(owner, type(owner))

    @staticmethod
    def _module_namespace(
        value: t.Infra.NativeOperand,
    ) -> t.DictKV[str, t.Infra.NativeOperand]:
        """Read native module storage without authored attribute lookup.

        Returns:
            The interpreter-owned module dictionary.

        """
        descriptor: p.Infra.NativeStorageSlot[t.DictKV[str, t.Infra.NativeOperand]] = (
            vars(ModuleType)["__dict__"]
        )
        return descriptor.__get__(value, type(value))

    @classmethod
    def producer_selection(
        cls,
        entrypoint: t.Infra.NativeOperand,
    ) -> p.Result[m.Infra.SourceClassReference]:
        """Elect a source-owned callable or receiver through static lexical storage.

        Returns:
            The lexical source reference or its admission failure.

        """
        value = (
            entrypoint.__func__
            if cls._is_native(entrypoint, MethodType)
            else entrypoint
        )
        if cls._is_class(value):
            module = cls._class_namespace(value).get("__module__")
            qualified = cls._type_attr("__qualname__", value, type(value))
        elif cls._is_native(value, FunctionType):
            module = value.__globals__.get("__name__")
            qualified = value.__code__.co_qualname
        else:
            return r[m.Infra.SourceClassReference].fail(
                "producer selection is not a native function or source class"
            )
        if type(module) is not str:
            return r[m.Infra.SourceClassReference].fail(
                "producer entrypoint has no source module"
            )
        source = FlextInfraWorkspaceEnvironmentProvenance.module_source(module)
        if source.failure:
            return r[m.Infra.SourceClassReference].from_failure(source)
        state = u.Cli.atomic_read_binary_file_state(source.value, required=True)
        if state.failure:
            return r[m.Infra.SourceClassReference].from_failure(state)
        if state.value.content is None:
            return r[m.Infra.SourceClassReference].fail(
                "producer declaration source is absent",
            )
        return cls._producer_lexical_reference(module, qualified, value)

    @classmethod
    def _producer_lexical_reference(
        cls,
        module: str,
        qualified: str,
        value: t.Infra.NativeOperand,
    ) -> p.Result[m.Infra.SourceClassReference]:
        """Resolve a physically admitted producer through native lexical storage.

        Returns:
            The exact lexical reference or its binding admission failure.

        """
        attributes = tuple(qualified.split("."))
        if any(not component.isidentifier() for component in attributes):
            return r[m.Infra.SourceClassReference].fail(
                "producer selection has no portable source declaration"
            )
        current: t.Infra.NativeOperand = sys.modules[module]
        for component in attributes:
            namespace: t.MappingKV[str, t.Infra.NativeOperand] = (
                cls._class_namespace(current)
                if cls._is_class(current)
                else cls._module_namespace(current)
                if type(current) is ModuleType
                else {}
            )
            if component not in namespace:
                return r[m.Infra.SourceClassReference].fail(
                    "producer selection has no source-owned lexical binding: "
                    f"{qualified}",
                )
            current = namespace[component]
        if cls._is_function_binding(current):
            current = current.__func__
        if current is not value:
            return r[m.Infra.SourceClassReference].fail(
                f"producer callable differs from its source binding: {qualified}",
            )
        return r[m.Infra.SourceClassReference].ok(
            m.Infra.SourceClassReference(target=module, attributes=attributes),
        )

    @classmethod
    def producer_selections(
        cls,
        entrypoint: t.Infra.NativeOperand,
        collaborators: t.SequenceOf[t.Infra.NativeOperand],
    ) -> p.Result[t.VariadicTuple[m.Infra.SourceClassReference]]:
        """Retain actual entrypoints, receiver types and explicitly wired ports.

        Returns:
            Unique lexical source references or the first admission failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.SourceClassReference]]
        selected: t.DictKV[t.Pair[str, t.StrTuple], m.Infra.SourceClassReference] = {}
        for callable_root in (entrypoint, *collaborators):
            roots = [callable_root]
            if cls._is_native(callable_root, MethodType):
                receiver = callable_root.__self__
                roots.append(receiver if cls._is_class(receiver) else type(receiver))
            for root in roots:
                nominated = cls.producer_selection(root)
                if nominated.failure:
                    return result_type.from_failure(nominated)
                identity = (nominated.value.target, nominated.value.attributes)
                selected[identity] = nominated.value
        return result_type.ok(tuple(selected.values()))

    @staticmethod
    def _class_namespace(
        value: t.Infra.NativeOperand,
    ) -> t.MappingKV[str, t.Infra.NativeOperand]:
        """Read exact class storage through the interpreter type descriptor.

        Returns:
            The native class namespace, without authored metaclass lookup.

        """
        descriptor: p.Infra.NativeStorageSlot[
            t.MappingKV[str, t.Infra.NativeOperand]
        ] = vars(type)["__dict__"]
        return descriptor.__get__(value, type(value))

    @classmethod
    def _executable_operands(
        cls,
        binding: str,
        value: t.Infra.NativeOperand,
    ) -> t.SequenceOf[t.Pair[str, t.Infra.NativeOperand]]:
        """Walk native operand containers once, excluding data and cyclic aliases.

        Returns:
            Executable operands with their structural binding paths.

        """
        pending: list[t.Pair[str, t.Infra.NativeOperand]] = [(binding, value)]
        seen: set[int] = set()
        result: list[t.Pair[str, t.Infra.NativeOperand]] = []
        while pending:
            name, item = pending.pop()
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            native = type(item)
            if cls._is_operand_sequence(item):
                children: list[t.Infra.NativeOperand] = list(item)
                if native is frozenset or native is set:
                    children.sort(key=partial(cls._value, construction=True))
                pending.extend(
                    (f"{name}.{index}", child) for index, child in enumerate(children)
                )
            elif cls._is_operand_mapping(item):
                entries = tuple(item.items())
                pending.extend(
                    (f"{name}.{index}.{part}", child)
                    for index, pair in enumerate(entries)
                    for part, child in enumerate(pair)
                )
            elif any(owner is GenericAlias for owner in cls._native_mro(type(item))):
                storage = vars(GenericAlias)
                pending.extend(
                    (
                        f"{name}.{attribute}",
                        storage[attribute].__get__(item, type(item)),
                    )
                    for attribute in ("__origin__", "__args__")
                )
                if type(item) is not GenericAlias:
                    pending.append((f"{name}.type", type(item)))
            elif cls._is_class(item) or cls._callable_storage(item):
                result.append((name, item))
        return tuple(result)

    @staticmethod
    def _native_metadata_slot(
        slots: t.MappingKV[str, t.Infra.NativeOperand],
        attribute: str,
    ) -> t.Infra.NativeDescriptor | None:
        """Read one exact native metadata descriptor from a class namespace.

        Returns:
            The native metadata slot, or None when the slot is not admitted.

        """
        slot = slots.get(attribute)
        if FlextInfraWorkspaceNativeReference._is_descriptor(slot) and (
            FlextInfraWorkspaceNativeReference._is_native(slot, GetSetDescriptorType)
            or FlextInfraWorkspaceNativeReference._is_native(slot, MemberDescriptorType)
        ):
            return slot
        return None

    @classmethod
    def _extension_callback(
        cls,
        value: t.Infra.NativeOperand,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Read registered native extension slots without authored accessors.

        Returns:
            Supplier, name and qualified name, or the first admission failure.

        """
        native = type(value)
        slots = cls._class_namespace(native)
        metadata: t.DictKV[str, str] = {}
        for attribute in ("__module__", "__name__", "__qualname__"):
            descriptor = cls._native_metadata_slot(slots, attribute)
            if descriptor is None:
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback lacks a native metadata slot: {attribute} "
                    f"type={native.__module__}.{native.__qualname__}",
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
                "extension callback supplier is not a native extension: "
                f"{metadata['__module__']}.{metadata['__qualname__']} "
                f"type={native.__module__}.{native.__qualname__} "
                f"loader={type(supplier.__spec__.loader).__qualname__}",
            )
        if slots.get("__globals__") is not None:
            globals_slot = cls._native_metadata_slot(slots, "__globals__")
            if globals_slot is None or globals_slot.__objclass__ is not native:
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals are not native storage",
                )
            if globals_slot.__get__(value, globals_slot.__objclass__) is not vars(
                supplier
            ):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals differ from its native supplier: "
                    f"{metadata['__module__']}.{metadata['__qualname__']}",
                )
            return r[t.Triple[str, str, str]].ok((
                metadata["__module__"],
                metadata["__name__"],
                metadata["__qualname__"],
            ))
        return cls._extension_lexical_reference(
            value,
            native,
            cls._module_namespace(supplier),
            metadata,
        )

    @classmethod
    def _extension_lexical_reference(
        cls,
        value: t.Infra.NativeOperand,
        native: t.Infra.NativeType,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        metadata: t.StrMapping,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Authenticate an extension callback in its elected native namespace.

        Returns:
            The registered callback identity or its lexical admission failure.

        """
        components = metadata["__qualname__"].split(".")
        lexical_owner = None
        for component in components[:-1]:
            owner = namespace.get(component)
            if not cls._is_class(owner):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback has no registered lexical owner",
                )
            lexical_owner = owner
            namespace = cls._class_namespace(owner)
        registered = namespace.get(components[-1])
        descriptor_owner: type | None = None
        if registered is not value and cls._is_descriptor(registered):
            descriptor_owner = registered.__objclass__
        registered_functions = (
            registered.__func__ if cls._is_function_binding(registered) else registered
            for registered in namespace.values()
        )
        if not any(registered is value for registered in registered_functions):
            return r[t.Triple[str, str, str]].fail(
                "extension callback differs from its registered descriptor: "
                f"{metadata['__module__']}.{metadata['__qualname__']}",
                error_data={
                    "supplier": metadata["__module__"],
                    "name": metadata["__name__"],
                    "qualname": metadata["__qualname__"],
                    "native_type": cls._symbol(native),
                    "registered_descriptor_present": components[-1] in namespace,
                    "registered_descriptor_kind": (
                        cls._symbol(type(registered))
                        if components[-1] in namespace
                        else None
                    ),
                    "registered_lexical_owner": (
                        cls._symbol(lexical_owner)
                        if lexical_owner is not None
                        else None
                    ),
                    "registered_descriptor_owner": (
                        cls._symbol(descriptor_owner)
                        if descriptor_owner is not None
                        and cls._is_class(descriptor_owner)
                        else None
                    ),
                },
            )
        return r[t.Triple[str, str, str]].ok((
            metadata["__module__"],
            metadata["__name__"],
            metadata["__qualname__"],
        ))

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
            or get_referents.__module__ != "gc"
            or get_referents.__name__ != "get_referents"
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
        caches = [
            index
            for index, item in enumerate(references)
            if type(item) is dict and item is not attributes
        ]
        if not caches:
            return result_type.fail(
                "native cache wrapper has no unique interpreter-owned cache storage",
            )
        cache_index = caches[-1]
        if cache_index + 1 >= len(references):
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

    @classmethod
    def _symbol_metadata(
        cls,
        value: t.Infra.NativeOperand,
    ) -> t.Pair[t.Infra.NativeOperand, str]:
        """Read native symbolic metadata with its original kind precedence.

        Returns:
            The stored module and qualified name without registration election.

        """
        if cls._is_class(value):
            module = cls._type_attr("__module__", value, type(value))
            name = cls._type_attr("__qualname__", value, type(value))
        elif cls._is_native(value, MethodWrapperType):
            module = None
            name = value.__qualname__
        elif cls._is_native(value, FunctionType):
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
            module = cls._type_attr("__module__", type(value), type(type(value)))
            name = cls._type_attr("__qualname__", type(value), type(type(value)))
        return module, name

    @classmethod
    def _symbol(cls, value: t.Infra.NativeOperand) -> str:
        if (
            cls._native_builtin(value)
            and value.__self__ is not None
            and type(value.__self__) is not ModuleType
        ):
            return cls._bound_native_symbol(value)
        module, name = cls._symbol_metadata(value)
        if type(module) is str:
            return f"{module}::{name}"
        if module is None and cls._native_builtin(value) and type(name) is str:
            registered: t.Infra.NativeOperand = sys.modules.get("builtins")
            for component in name.split("."):
                namespace: t.MappingKV[str, t.Infra.NativeOperand] = (
                    cls._class_namespace(registered)
                    if cls._is_class(registered)
                    else cls._module_namespace(registered)
                    if type(registered) is ModuleType
                    else {}
                )
                registered = namespace.get(component)
            if type(registered) is staticmethod:
                registered = registered.__func__
            if registered is value:
                return f"builtins::{name}"
        if type(module) is GetSetDescriptorType or type(module) is MemberDescriptorType:
            owner = value if cls._is_class(value) else type(value)
            builtin_module = sys.modules.get("builtins")
            owner_name = cls._type_attr("__name__", owner, type(owner))
            if (
                type(builtin_module) is ModuleType
                and vars(builtin_module).get(owner_name) is owner
            ):
                origin = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                    "builtins",
                )
                if origin.failure:
                    raise TypeError(origin.error)
                return f"builtins::{name}"
            msg = (
                "native module descriptor has no registered interpreter owner: "
                f"qualified={name}; "
                f"module_type={
                    vars(type)['__qualname__'].__get__(type(module), type(type(module)))
                }"
            )
            raise TypeError(
                msg,
            )
        msg = (
            "native symbolic metadata has no text or descriptor module: "
            f"qualified={name}; "
            f"module_type={
                cls._type_attr('__name__', type(module), type(type(module)))
            }; "
            f"value_type={cls._type_attr('__name__', type(value), type(type(value)))}"
        )
        raise TypeError(
            msg,
        )

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
        if value is None:
            return ["NoneType", None]
        if (native is str or native is int or native is bool) and isinstance(
            value, str | int | bool
        ):
            return [native.__name__, value]
        if native is float and isinstance(value, float):
            return ["float", float.hex(value)]
        if native is bytes and isinstance(value, bytes):
            return ["bytes", b64encode(value).decode("ascii")]
        if value is Ellipsis:
            return ["ellipsis"]
        if cls._is_descriptor(value):
            owner = value.__objclass__
            if cls._class_namespace(owner).get(value.__name__) is not value:
                msg = "native descriptor differs from its registered owner"
                raise TypeError(msg)
            return ["native-descriptor", cls._symbol(owner), value.__name__]
        if id(value) in seen:
            return ["cycle", cls._symbol(value)]
        seen |= {id(value)}
        observe = partial(
            cls._value_data,
            seen=seen,
            construction=construction,
            references=references,
            binding=binding,
            paths=paths,
        )
        if any(native is kind for kind in (list, set, dict)) and not construction:
            return ["mutable", native.__name__]
        if cls._is_operand_sequence(value):
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
                if references is not None:
                    references.append((f"{binding}.sequence_type", deque))
                return [
                    "deque",
                    observe(descriptor.__get__(value, deque)),
                    items,
                ]
            return [
                native.__name__,
                sorted(items, key=dumps)
                if native is set or native is frozenset
                else items,
            ]
        if cls._is_operand_mapping(value):
            return [
                "dict",
                sorted(
                    [list(map(observe, pair)) for pair in value.items()],
                    key=dumps,
                ),
            ]
        if native is MappingProxyType:
            if not construction:
                return ["mutable", "mappingproxy"]
            backing = cls._native_instance_referents(value)
            if len(backing) != 1 or type(backing[0]) is not dict:
                msg = "native mappingproxy does not contain an exact interpreter dict"
                raise TypeError(
                    msg,
                )
            return ["mappingproxy", observe(backing[0])]
        if cls._is_native(value, CodeType):
            if paths:
                value = cls._relocate_code(value, paths)
            return [
                "code",
                [
                    [
                        name,
                        observe(
                            descriptor.__get__(value, CodeType), construction=False
                        ),
                    ]
                    for name, descriptor in sorted(vars(CodeType).items())
                    if (
                        type(descriptor) is MemberDescriptorType
                        or (
                            type(descriptor) is GetSetDescriptorType
                            and type(vars(p.Infra.NativeCodeIdentity).get(name))
                            is property
                        )
                    )
                    and descriptor.__objclass__ is CodeType
                ],
            ]
        if cls._is_native(value, FunctionType):
            return [
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
            ]
        if type(value) is UnionType:
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
        if not construction:
            return ["instance", cls._symbol(native)]
        observed: list[t.JsonValue] = []
        ancestry = cls._native_mro(native)
        elected = {
            name: descriptor
            for owner in reversed(ancestry)
            for name, descriptor in cls._class_namespace(owner).items()
        }
        native_lookup = (
            elected["__getattribute__"] is vars(object)["__getattribute__"]
            and "__getattr__" not in elected
        )
        absent = object()
        for owner in ancestry:
            namespace = cls._class_namespace(owner)
            for name, descriptor in sorted(namespace.items()):
                if (
                    type(descriptor) is MemberDescriptorType
                    or (name == "__dict__" and type(descriptor) is GetSetDescriptorType)
                ) and descriptor.__objclass__ is owner:
                    member = type(descriptor) is MemberDescriptorType
                    if member and elected[name] is not descriptor:
                        payload: t.JsonValue = [
                            "shadowed",
                            cls._symbol(type(elected[name])),
                        ]
                    else:
                        stored = (
                            getattr(value, name, absent)
                            if member and native_lookup
                            else descriptor.__get__(value, native)
                        )
                        payload = (
                            ["uninitialized"] if stored is absent else observe(stored)
                        )
                    observed.append([
                        f"{cls._symbol(owner)}::{name}",
                        payload,
                    ])
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
        supplier_name = cls._type_attr("__module__", native, type(native))
        supplier = (
            sys.modules.get(supplier_name) if type(supplier_name) is str else None
        )
        if type(supplier_name) is str and type(supplier) is ModuleType:
            namespace = cls._module_namespace(supplier)
            bindings = tuple(
                name
                for name, registered in sorted(namespace.items())
                if registered is value
            )
            if bindings:
                FlextInfraWorkspaceEnvironmentProvenance.module_source(
                    supplier_name
                ).unwrap()
                if references is not None:
                    references.append((f"{supplier_name}::{bindings[0]}", native))
                return ["registered_instance", cls._symbol(native), list(bindings)]
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
    def capture(
        cls,
        names: t.SequenceOf[str | m.Infra.SourceClassReference],
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe nominated modules or lexical entrypoints without running factories.

        Plain module names request complete inventories through the existing
        public API. Typed lexical paths select an invocation's executable graph.

        Returns:
            Native binding evidence and sources, or the first admission failure.

        """
        origins: t.DictKV[str, Path] = {}
        module_anchors: t.DictKV[str, t.Infra.NativeOperand] = {}
        sources: set[t.Triple[str, str, str]] = set()
        evidence: list[m.Infra.NativeBindingEvidence] = []
        compiled: t.DictKV[Path, t.Infra.NativeClassDeclarations] = {}
        scope = ContextVar[t.Infra.NativeInvocationFacts | None].get(
            cls._compilation_facts
        )
        instructions: t.Infra.NativeInstructionFacts = (
            scope[1] if scope is not None else {}
        )
        references: list[t.Pair[str, t.Infra.NativeOperand]] = []
        observe_value = partial(cls._value, references=references, paths=paths)
        pending: list[t.Quad[str, t.Infra.NativeOperand, str, str]] = []
        nominations = tuple(
            m.Infra.SourceClassReference(target=item)
            if cls._is_native(item, str)
            else m.Infra.SourceClassReference.model_validate(item)
            for item in names
        )
        if not nominations or any(
            not item.target
            or not all(part.isidentifier() for part in item.target.split("."))
            or any(not part.isidentifier() for part in item.attributes)
            or item.qualified_base
            for item in nominations
        ):
            return r[m.Infra.NativeImportObservation].fail(
                "invalid native source selection"
            )
        selected = all(item.attributes for item in nominations)
        if any(item.attributes for item in nominations) and not selected:
            return r[m.Infra.NativeImportObservation].fail(
                "mixed native selection contracts"
            )
        for nomination in nominations:
            name = nomination.target
            qualified = ".".join(nomination.attributes)
            module = sys.modules.get(name)
            origin = FlextInfraWorkspaceEnvironmentProvenance.module_source(name)
            if origin.failure:
                return r[m.Infra.NativeImportObservation].from_failure(origin)
            if sys.modules.get(name) is not module:
                return r[m.Infra.NativeImportObservation].fail(
                    f"native reference module election changed: {name}",
                )
            anchored = name in module_anchors
            selected_origin = cls._source_path(origin.value, paths)
            if anchored and (
                module_anchors[name] is not module
                or cls._source_path(origins[name], paths) != selected_origin
            ):
                return r[m.Infra.NativeImportObservation].fail(
                    f"native reference module anchor changed: {name}",
                )
            if anchored and not nomination.attributes:
                continue
            namespace: t.MappingKV[str, t.Infra.NativeOperand] = cls._module_namespace(
                module
            )
            origins[name] = origin.value
            sources.add((name, str(selected_origin), ""))
            if not anchored:
                module_anchors[name] = module
                evidence.append(
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
                pending.append((
                    f"{name}.module_type",
                    type(module),
                    name,
                    str(selected_origin),
                ))
            if nomination.attributes:
                value = module
                for component in nomination.attributes:
                    namespace = (
                        cls._class_namespace(value)
                        if cls._is_class(value)
                        else cls._module_namespace(value)
                        if isinstance(value, ModuleType)
                        else {}
                    )
                    if component not in namespace:
                        return r[m.Infra.NativeImportObservation].fail(
                            f"selected producer binding is absent: {name}::{qualified}",
                        )
                    value = namespace[component]
                pending.append((
                    f"{name}::{qualified}",
                    value,
                    name,
                    str(selected_origin),
                ))
                continue
            mutable_globals: set[str] = set()
            functions: list[t.Infra.NativeOperand] = [
                value for value in namespace.values() if type(value) is FunctionType
            ]
            functions.extend(
                member.__func__ if cls._is_function_binding(member) else member
                for value in namespace.values()
                if cls._is_class(value)
                for member in cls._class_namespace(value).values()
                if any(
                    type(member) is kind
                    for kind in (FunctionType, classmethod, staticmethod)
                )
            )
            for function in functions:
                if not (
                    cls._is_native(function, FunctionType)
                    or cls._is_native(function, MethodType)
                ):
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
                or type(value) is FunctionType
                or type(value) is MethodType
                or cls._native_builtin(value)
                or any(
                    type(value) is kind
                    for kind in (property, classmethod, staticmethod)
                )
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
            if cls._is_class(value):
                namespace = cls._class_namespace(value)
                actual_supplier = cls._type_attr("__module__", value, type(value))
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native source supplier: {binding}",
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
                    if (not selected or key in {"__new__", "__init__", "__call__"})
                    and (
                        cls._is_class(item)
                        or type(item) is FunctionType
                        or type(item) is MethodType
                        or cls._native_builtin(item)
                        or any(
                            type(item) is kind
                            for kind in (property, classmethod, staticmethod)
                        )
                        or cls._callable_storage(item)
                    )
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
            if cls._is_descriptor(value) and any(
                cls._is_native(value, kind)
                for kind in (
                    ClassMethodDescriptorType,
                    MethodDescriptorType,
                    WrapperDescriptorType,
                )
            ):
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
            kind = cls._type_attr("__name__", type(value), type(type(value)))
            if any(owner is GenericAlias for owner in cls._native_mro(type(value))):
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="generic_alias",
                        supplier="types",
                        name="",
                        qualname="",
                        operands=(
                            (
                                "alias",
                                observe_value(value, construction=True),
                            ),
                        ),
                    ),
                )
                pending.extend(
                    (edge, item, supplier, owner_source)
                    for edge, item in cls._executable_operands(binding, value)
                )
                continue
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
                        operands.append((
                            attribute,
                            observe_value(
                                slot.__get__(value, slot.__objclass__),
                                construction=True,
                                binding=(
                                    f"{incoming}.{attribute}; body={binding}; "
                                    f"supplier={supplier}; "
                                    f"callable={cls._symbol(function.value)}"
                                ),
                            ),
                        ))
                        stored = slot.__get__(value, slot.__objclass__)
                        pending.extend(
                            (operand_binding, item, supplier, owner_source)
                            for operand_binding, item in cls._executable_operands(
                                f"{binding}.{attribute}",
                                stored,
                            )
                        )
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
                    or type(item) is FunctionType
                    or cls._native_builtin(item)
                    or cls._native_wrapper_kind(item) is not None
                    if not selected or key == "__wrapped__"
                )
                continue
            if not cls._is_native(value, FunctionType):
                native_builtin = value if cls._native_builtin(value) else None
                if cls._native_callable_instance(
                    value
                ) or cls._python_callable_instance(value):
                    native = type(value)
                    evidence.append(
                        m.Infra.NativeBindingEvidence(
                            binding=binding,
                            kind="callable_instance",
                            supplier=vars(type)["__module__"].__get__(
                                native, type(native)
                            ),
                            name=vars(type)["__name__"].__get__(native, type(native)),
                            qualname=vars(type)["__qualname__"].__get__(
                                native, type(native)
                            ),
                            operands=(
                                (
                                    "storage",
                                    observe_value(value, construction=True),
                                ),
                            ),
                        ),
                    )
                    pending.append((
                        f"{binding}.native_class",
                        native,
                        supplier,
                        owner_source,
                    ))
                    continue
                if native_builtin is None:
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
                    origin = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                        actual_supplier,
                    )
                    if origin.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(origin)
                    sources.add((
                        f"{actual_supplier}::{qualified}",
                        str(cls._source_path(origin.value, paths)),
                        "",
                    ))
                else:
                    actual_supplier, _, qualified = cls._symbol(
                        native_builtin
                    ).partition("::")
                    native_name = native_builtin.__name__
                    elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                        actual_supplier,
                    )
                    if elected.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(elected)
                    sources.add((
                        f"{actual_supplier}::{qualified}",
                        str(cls._source_path(elected.value, paths)),
                        "",
                    ))
                receiver_operands: t.VariadicTuple[t.Pair[str, str]] = ()
                receiver_operational: t.VariadicTuple[t.Pair[str, str]] = ()
                if native_builtin is not None:
                    receiver = native_builtin.__self__
                    if cls._native_iterator_receiver(native_builtin):
                        receiver_inputs = cls._native_instance_referents(receiver)
                        receiver_operands = (
                            ("receiver_type", cls._symbol(type(receiver))),
                            (
                                "receiver_inputs",
                                observe_value(receiver_inputs, construction=True),
                            ),
                        )
                        receiver_operational = (
                            (
                                "receiver",
                                dumps((cls._symbol(type(receiver)), id(receiver))),
                            ),
                        )
                        pending.append((
                            f"{binding}.receiver_type",
                            type(receiver),
                            actual_supplier,
                            owner_source,
                        ))
                        pending.extend(
                            (edge, item, actual_supplier, owner_source)
                            for edge, item in cls._executable_operands(
                                f"{binding}.receiver_inputs", receiver_inputs
                            )
                        )
                    else:
                        receiver_operands = (
                            (
                                "receiver",
                                observe_value(
                                    receiver,
                                    construction=True,
                                    binding=(
                                        f"{binding}; supplier={actual_supplier}; "
                                        f"method={native_name}"
                                    ),
                                ),
                            ),
                        )
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=kind,
                        supplier=actual_supplier,
                        name=native_name,
                        qualname=qualified,
                        operands=receiver_operands,
                        operational=receiver_operational,
                    ),
                )
                continue
            raw_code = value.__code__
            code = cls._relocate_code(raw_code, paths)
            generated = code.co_filename.startswith(
                "<"
            ) and not code.co_filename.startswith("<frozen ")
            if generated:
                if (
                    not owner_source
                    or type(sys.modules.get(supplier)) is not ModuleType
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        "generated executable has no elected declaration owner: "
                        f"{binding}",
                    )
                actual_supplier = supplier
            else:
                actual_supplier = value.__globals__.get("__name__")
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer globals have no supplier identity: {binding}",
                    )
                module = sys.modules.get(actual_supplier)
                if module is None or (
                    not generated
                    and value.__globals__ is not cls._module_namespace(module)
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
            global_namespace = value.__globals__
            # This read-only native slot is the function's actual builtins
            # namespace, even if its module later rebinds "__builtins__".
            builtin_slot: p.Infra.NativeStorageSlot[
                t.DictKV[str, t.Infra.NativeOperand]
            ] = vars(FunctionType)["__builtins__"]
            builtin_namespace = builtin_slot.__get__(value, FunctionType)
            for namespace_name, namespace in (
                ("globals", global_namespace),
                ("builtins", builtin_namespace),
            ):
                if type(namespace) is not dict:
                    pending.append((
                        f"{binding}.{namespace_name}.type",
                        type(namespace),
                        actual_supplier,
                        owner_source,
                    ))
            global_names = {
                instruction.argval
                for instruction in cls._instructions(code, instructions)
                if instruction.opname == "LOAD_GLOBAL"
                and isinstance(instruction.argval, str)
            }
            # Read dictionary storage directly, never subclass lookup overrides.
            native_getitem: Callable[
                [t.DictKV[str, t.Infra.NativeOperand], str], t.Infra.NativeOperand
            ] = vars(dict)["__getitem__"]
            native_contains: Callable[
                [t.DictKV[str, t.Infra.NativeOperand], str], bool
            ] = vars(dict)["__contains__"]
            global_bindings: t.DictKV[str, t.Infra.NativeOperand] = {
                name: (
                    native_getitem(global_namespace, name)
                    if native_contains(global_namespace, name)
                    else native_getitem(builtin_namespace, name)
                )
                for name in sorted(global_names)
                if native_contains(global_namespace, name)
                or native_contains(builtin_namespace, name)
            }
            operational_globals = frozenset(
                instruction.argval
                for unit in cls._code_units(code)
                if not global_bindings.keys().isdisjoint(unit.co_names)
                for instruction in cls._instructions(unit, instructions)
                if instruction.opname in {"STORE_GLOBAL", "DELETE_GLOBAL"}
                and isinstance(instruction.argval, str)
            )
            globals_used = tuple(global_bindings.values())
            if selected:
                # Query actual native global/attribute edges, not every name in
                # an ambient module's dictionary. No descriptor is executed.
                receiver = None
                edge = binding
                for instruction in cls._instructions(code, instructions):
                    if instruction.opname == "LOAD_GLOBAL":
                        receiver = global_bindings.get(instruction.argval)
                        edge = f"{binding}.global.{instruction.argval}"
                    elif instruction.opname == "LOAD_ATTR" and receiver is not None:
                        namespaces = (
                            tuple(
                                cls._class_namespace(owner)
                                for owner in cls._native_mro(receiver)
                            )
                            if cls._is_class(receiver)
                            else (cls._module_namespace(receiver),)
                            if isinstance(receiver, ModuleType)
                            else ()
                        )
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
                            missing = f"{edge}.{instruction.argval}"
                            if missing in edges:
                                return r[m.Infra.NativeImportObservation].fail(
                                    f"native edge became absent: {missing}; "
                                    f"supplier={actual_supplier}; "
                                    f"qualname={value.__qualname__}",
                                )
                            if missing not in absent_edges:
                                absent_edges.add(missing)
                                evidence.append(
                                    m.Infra.NativeBindingEvidence(
                                        binding=missing,
                                        kind="absent",
                                        supplier=actual_supplier,
                                        name=instruction.argval,
                                        qualname=edge,
                                    )
                                )
                            receiver = None
                            continue
                        receiver = found[instruction.argval]
                        edge += f".{instruction.argval}"
                        if (
                            cls._is_class(receiver)
                            or any(
                                type(receiver) is kind
                                for kind in (
                                    FunctionType,
                                    MethodType,
                                    property,
                                    classmethod,
                                    staticmethod,
                                )
                            )
                            or cls._native_builtin(receiver)
                            or cls._native_wrapper_kind(receiver) is not None
                            or cls._callable_storage(receiver)
                        ):
                            pending.append((
                                edge,
                                receiver,
                                actual_supplier,
                                str(cls._source_path(origin, paths)),
                            ))
                    else:
                        receiver = None
                # Native code names select static descriptor slots. Namespace
                # storage authenticates the edge; unrelated members stay dormant.
                class_roots = [item for item in globals_used if cls._is_class(item)]
                lexical = sys.modules.get(actual_supplier)
                for component in code.co_qualname.split(".")[:-1]:
                    namespace = (
                        cls._class_namespace(lexical)
                        if cls._is_class(lexical)
                        else vars(lexical)
                        if type(lexical) is ModuleType
                        else {}
                    )
                    lexical = namespace.get(component)
                    if cls._is_class(lexical):
                        class_roots.append(lexical)
                inspected: set[int] = set()
                while class_roots:
                    owner = class_roots.pop()
                    if id(owner) in inspected:
                        continue
                    inspected.add(id(owner))
                    resolved_names: set[str] = set()
                    for ancestor in cls._native_mro(owner):
                        namespace = cls._class_namespace(ancestor)
                        for name in code.co_names:
                            if name in resolved_names or name not in namespace:
                                continue
                            resolved_names.add(name)
                            item = namespace.get(name)
                            if cls._is_class(item):
                                class_roots.append(item)
                            elif (
                                any(
                                    type(item) is kind
                                    for kind in (
                                        FunctionType,
                                        MethodType,
                                        property,
                                        classmethod,
                                        staticmethod,
                                    )
                                )
                                or cls._native_builtin(item)
                                or cls._native_wrapper_kind(item) is not None
                                or cls._callable_storage(item)
                            ):
                                pending.append((
                                    f"{binding}.descriptor.{cls._symbol(ancestor)}.{name}",
                                    item,
                                    actual_supplier,
                                    str(cls._source_path(origin, paths)),
                                ))
            pending.extend(
                (f"{binding}.global.{name}", item, actual_supplier, owner_source)
                for name, item in global_bindings.items()
                if item is not None
                and (
                    cls._is_class(item)
                    or type(item) is FunctionType
                    or type(item) is MethodType
                    or cls._native_builtin(item)
                    or cls._callable_storage(item)
                )
            )
            pending.extend(
                (operand_binding, item, actual_supplier, owner_source)
                for label, stored in (
                    ("defaults", value.__defaults__),
                    ("keyword_defaults", value.__kwdefaults__),
                    ("closure", nonlocals),
                )
                for operand_binding, item in cls._executable_operands(
                    f"{binding}.{label}",
                    stored,
                )
            )
            wrapped = vars(value).get("__wrapped__")
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
                        ("wrapped", observe_value(wrapped)),
                    ),
                    operational=tuple(
                        (
                            f"global.{name}",
                            observe_value(item, construction=generated),
                        )
                        for name, item in global_bindings.items()
                        if name in operational_globals
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
            current = u.Cli.atomic_read_binary_file_receipt(
                receipt.path, required=receipt.device is not None
            )
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != receipt:
                return r[bool].fail(f"native source authority changed: {receipt.path}")

        return FlextInfraCodegenPreconditions.source_trees_current(
            authority.generator_trees,
            tuple(outputs),
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

        Returns:
            Successful source authentication or the first provenance failure.

        """
        states = {item.path: item for item in inputs}
        compiled: t.DictKV[str, t.VariadicTuple[t.Infra.NativeCode]] = {}
        admitted = 0
        for binding in observed.bindings:
            if binding.code is None:
                continue
            executed = m.Infra.NativeCodeEvidence.model_validate_json(binding.code)
            module = sys.modules[binding.supplier]
            module_spec = FlextInfraWorkspaceNativeReference._module_namespace(module)[
                "__spec__"
            ]
            if not FlextInfraWorkspaceNativeReference._is_native(
                module_spec, ModuleSpec
            ):
                return r[bool].fail(
                    f"authored native supplier has no module spec: {binding.supplier}"
                )
            frozen = module_spec.origin == "frozen"
            if executed.filename.startswith("<") and not frozen:
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
