"""Exact interpreter type, namespace and storage probes for native references.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import itertools
import sys
from base64 import b64encode
from collections import deque
from dis import Instruction, get_instructions
from gc import get_referents
from pathlib import Path
from types import (
    BuiltinFunctionType,
    CellType,
    ClassMethodDescriptorType,
    CodeType,
    FunctionType,
    GetSetDescriptorType,
    MappingProxyType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodWrapperType,
    ModuleType,
    WrapperDescriptorType,
)
from typing import Literal, TypeGuard, overload

from flext_infra import m, p, r, t
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance


class FlextInfraWorkspaceNativeReferencePrimitivesMixin:
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
                for value in FlextInfraWorkspaceNativeReferencePrimitivesMixin._native_code_constants(
                    current
                )
                if FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_native(
                    value, CodeType
                )
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
            # A plain method writes class state only through the global class
            # name; a class or static method may also write through ``cls``.
            if FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_function_binding(
                member
            ):
                function = member.__func__
            elif FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_native(
                member, FunctionType
            ):
                function = member
            else:
                continue
            if not FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_native(
                function, FunctionType
            ):
                continue
            if not declarations.intersection(function.__code__.co_names):
                continue
            if (
                FlextInfraWorkspaceNativeReferencePrimitivesMixin._native_type(
                    member, classmethod
                )
                and not function.__code__.co_argcount
            ):
                continue
            receiver = (
                function.__code__.co_varnames[0]
                if FlextInfraWorkspaceNativeReferencePrimitivesMixin._native_type(
                    member, classmethod
                )
                else None
            )
            instructions = (
                FlextInfraWorkspaceNativeReferencePrimitivesMixin._instructions(
                    function.__code__, instruction_cache
                )
            )
            if receiver is not None and any(
                (
                    instruction.opname.startswith("STORE_FAST")
                    or instruction.opname == "DELETE_FAST"
                )
                and (
                    instruction.argval == receiver
                    or (
                        FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_operand_tuple(
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
                        and FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_operand_tuple(
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
            # ``Owner.field += value`` loads the global receiver, copies it to
            # read the field, and swaps it back under the result before storing.
            augmented = frozenset(
                instruction.argval
                for index, instruction in enumerate(instructions)
                if instruction.opname == "STORE_ATTR"
                and isinstance(instruction.argval, str)
                and instruction.argval in declarations
                and index > 0
                and instructions[index - 1].opname == "SWAP"
                and any(
                    load.opname == "LOAD_GLOBAL"
                    and load.argval in global_receivers - rebound_globals
                    and copy.opname == "COPY"
                    and read.opname == "LOAD_ATTR"
                    and read.argval == instruction.argval
                    for load, copy, read in zip(
                        instructions[:index],
                        instructions[1:index],
                        instructions[2:index],
                        strict=False,
                    )
                )
            )
            if fields | augmented:
                writers.append((name, member, fields | augmented))
        return tuple(writers)

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
        supplier = cls._native_type_supplier(native)
        return supplier is not None and any(
            registered is native for registered in vars(supplier[1]).values()
        )

    @classmethod
    def _native_type_supplier(
        cls, native: t.Infra.NativeType
    ) -> t.Pair[str, ModuleType] | None:
        """Resolve native type metadata through the actual module registry.

        Returns:
            Its exact string/module registration or no native registration.

        """
        name = cls._type_attr("__module__", native, type(native))
        if cls._is_native(name, str):
            module = sys.modules.get(name)
            if type(module) is ModuleType:
                return name, module
        return None

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

    @classmethod
    def _function_chain(
        cls,
        value: t.Infra.NativeOperand | None,
    ) -> t.VariadicTuple[FunctionType]:
        """Read a slot function and its raw wrapped functions without hooks.

        Returns:
            The slot function followed by every raw ``__wrapped__`` function.

        Raises:
            TypeError: A wrapper has foreign callable or dictionary storage.
            ValueError: The raw wrapper chain is cyclic or retains another inner.

        """
        if cls._is_function_binding(value):
            value = value.__func__
        functions: list[FunctionType] = []
        seen: set[int] = set()
        while cls._is_native(value, FunctionType):
            if id(value) in seen:
                msg = "generated receiver function wrapper chain is cyclic"
                raise ValueError(msg)
            seen.add(id(value))
            functions.append(value)
            attributes = vars(value)
            if not cls._is_operand_mapping(attributes) or any(
                type(key) is not str for key in attributes
            ):
                msg = (
                    "native function metadata requires an exact string-keyed dictionary"
                )
                raise TypeError(msg)
            inner = attributes.get("__wrapped__")
            if inner is None:
                break
            if not cls._is_native(inner, FunctionType):
                msg = "generated receiver wrapper has foreign callable storage"
                raise TypeError(msg)
            cells = cls._function_cells(value)
            if (
                "user_function" in cells
                and cells["user_function"].cell_contents is not inner
            ):
                msg = "generated receiver wrapper does not retain its raw inner"
                raise ValueError(msg)
            value = inner
        return tuple(functions)

    @staticmethod
    def _function_cells(
        value: FunctionType,
    ) -> t.DictKV[str, CellType]:
        """Read exact interpreter closure cells without accessing their payloads.

        Returns:
            The original native cell for every declared free variable.

        Raises:
            TypeError: Closure storage or a cell has a foreign native type.

        """
        closure = value.__closure__
        if closure is None:
            closure = ()
        elif type(closure) is not tuple:
            msg = "native function has foreign closure storage"
            raise TypeError(msg)
        if any(type(cell) is not CellType for cell in closure):
            msg = "native function has a foreign closure cell"
            raise TypeError(msg)
        return dict(zip(value.__code__.co_freevars, closure, strict=True))

    @classmethod
    def _remember_generated_descriptors(
        cls,
        owner: p.AttributeProbe,
        supplier: str,
        owners: t.MutableMappingKV[int, t.Triple[str, str, p.AttributeProbe | None]],
    ) -> None:
        """Keep the actual class receiver while traversing native wrappers."""
        for attribute, descriptor in cls._class_namespace(owner).items():
            for function in cls._function_chain(descriptor):
                if function.__code__.co_filename.startswith(
                    "<"
                ) and not function.__code__.co_filename.startswith("<frozen "):
                    owners[id(function)] = (supplier, attribute, owner)

    @classmethod
    def _python_storage_class(cls, native: t.Infra.NativeType) -> bool:
        """Require Python storage to cover every non-object ancestry payload.

        Returns:
            Whether every ancestor exposes only admitted Python instance storage.

        """
        return cls._python_storage_owners(
            vars(type)["__mro__"].__get__(native, type(native))
        )

    @classmethod
    def _python_storage_owners(cls, owners: t.SequenceOf[t.Infra.NativeType]) -> bool:
        """Reject native payloads within the selected raw ancestry owners.

        Returns:
            Whether the selected owners contain no unproved native payload.

        """
        for ancestor in owners:
            if ancestor is object:
                continue
            for name, descriptor in cls._class_namespace(ancestor).items():
                if cls._native_payload_descriptor(ancestor, name, descriptor):
                    return False
        return True

    @classmethod
    def _native_payload_descriptor(
        cls,
        ancestor: t.Infra.NativeType,
        name: str,
        descriptor: t.Infra.NativeOperand,
    ) -> bool:
        """Elect a native owner slot that implies non-Python instance payload.

        Returns:
            Whether the original ancestry check rejects this exact native slot.

        """
        if cls._is_descriptor(descriptor):
            if cls._is_native(descriptor, MemberDescriptorType):
                return False
            return descriptor.__objclass__ is ancestor and not (
                cls._is_native(descriptor, GetSetDescriptorType)
                and name in {"__dict__", "__weakref__"}
            )
        return (
            cls._is_native(descriptor, BuiltinFunctionType)
            and descriptor.__self__ is ancestor
        )

    @classmethod
    def _native_mapping_proxy_backing(cls, value: p.AttributeProbe) -> p.AttributeProbe:
        """Read the sole exact-dict backing of the CPython mapping proxy.

        Returns:
            The single interpreter-owned dictionary backing the proxy.

        Raises:
            ValueError: The proxy or interpreter traversal lacks its native proof.

        """
        if type(value) is not MappingProxyType or MappingProxyType is not type(
            vars(type)
        ):
            msg = "mapping proxy has no admitted interpreter type"
            raise ValueError(msg)
        elected = FlextInfraWorkspaceEnvironmentProvenance.module_source("gc").unwrap()
        supplier = sys.modules.get("gc")
        if (
            elected != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
            or type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
        ):
            msg = "mapping proxy storage has no admitted interpreter traversal"
            raise ValueError(msg)
        if (
            not cls._native_text(get_referents.__module__, "gc")
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
    def _inherited_member_state(
        cls,
        value: p.AttributeProbe,
        owner: t.Infra.NativeType,
        name: str,
        descriptor: p.AttributeProbe,
        predecessor: t.Infra.NativeType,
    ) -> t.Pair[bool, p.AttributeProbe | None]:
        """Use native super lookup to retain inherited-slot presence as data.

        Returns:
            The inherited slot's native presence and retained value.

        Raises:
            ValueError: The inherited descriptor or lookup context is not proved.

        """
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        index = next(
            position for position, ancestor in enumerate(ancestry) if ancestor is owner
        )
        if (
            not index
            or ancestry[index - 1] is not predecessor
            or name == "__class__"
            or not cls._is_native(descriptor, MemberDescriptorType)
        ):
            msg = "native optional slot has no exact inherited descriptor"
            raise ValueError(msg)
        if (
            descriptor.__objclass__ is not owner
            or cls._class_namespace(owner).get(name) is not descriptor
        ):
            msg = "native optional slot has no exact inherited descriptor"
            raise ValueError(msg)
        builtins = sys.modules.get("builtins")
        elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
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
        ):
            msg = "native optional slot lookup bindings differ"
            raise ValueError(msg)
        if type(super_type) is not type:
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
            or not cls._is_native(constructor, BuiltinFunctionType)
            or constructor.__self__ is not super_type
        ):
            msg = "native optional slot lacks the interpreter super implementation"
            raise ValueError(msg)
        if (
            not cls._is_native(accessor, WrapperDescriptorType)
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

    @staticmethod
    def _native_type(
        value: p.AttributeProbe | None, *expected: t.Infra.NativeType
    ) -> bool:
        """Compare type identity without invoking an authored metaclass hash.

        Returns:
            Whether the exact native type matches one of the supplied identities.

        """
        native = type(value)
        return any(native is candidate for candidate in expected)

    @staticmethod
    def _native_text(value: p.AttributeProbe | None, expected: str) -> bool:
        """Reject authored equality before comparing native metadata text.

        Returns:
            Whether the value is exact native text equal to the expected text.

        """
        return type(value) is str and value == expected

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
    ) -> TypeGuard[p.Infra.FunctionDescriptor]:
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
        if FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_descriptor(slot) and (
            FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_native(
                slot, GetSetDescriptorType
            )
            or FlextInfraWorkspaceNativeReferencePrimitivesMixin._is_native(
                slot, MemberDescriptorType
            )
        ):
            return slot
        return None

    @classmethod
    def _native_wrapper_kind(cls, value: p.AttributeProbe) -> str | None:
        """Identify exact interpreter wrapper types through their registered exports.

        Returns:
            The registered native wrapper kind, or no matching wrapper.

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
            sys.modules.get(supplier_name)
            if cls._is_native(supplier_name, str)
            else None
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
    def _scalar_value(
        cls,
        value: t.Infra.NativeOperand,
    ) -> t.JsonValue | None:
        """Observe exact native scalar values before inspecting any descriptors.

        Returns:
            The structural scalar value, or no matching native scalar.

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
        return None

    @classmethod
    def _slot_storage(
        cls,
        value: t.Infra.NativeOperand,
        name: str,
        descriptor: t.Infra.NativeDescriptor,
        elected: t.MappingKV[str, t.Infra.NativeOperand],
        *,
        native_lookup: bool,
    ) -> t.Pair[Literal["shadowed", "uninitialized", "value"], t.Infra.NativeOperand]:
        """Read one native slot while retaining shadowing and absence distinctly.

        Returns:
            The original native slot category and its retained value or type.

        """
        member = type(descriptor) is MemberDescriptorType
        if member and elected[name] is not descriptor:
            return "shadowed", type(elected[name])
        absent = object()
        stored = (
            getattr(value, name, absent)
            if member and native_lookup
            else descriptor.__get__(value, descriptor.__objclass__)
        )
        return ("uninitialized", None) if stored is absent else ("value", stored)

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

    @classmethod
    def _absent_edge(
        cls,
        context: m.Infra.NativeObservationContext,
        facts: m.Infra.NativeFunctionObservationContext,
        edge: str,
        name: str,
    ) -> p.Result[bool]:
        """Record one absent native attribute edge once, or contradict a known edge.

        Returns:
            Success after recording, or the contradiction of a now-absent edge.

        """
        missing = f"{edge}.{name}"
        if missing in context.edges:
            return r[bool].fail(
                f"native edge became absent: {missing}; "
                f"supplier={facts.supplier}; "
                f"qualname={facts.value[0].__qualname__}",
            )
        if missing not in context.absent_edges:
            context.absent_edges.add(missing)
            context.evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=missing,
                    kind="absent",
                    supplier=facts.supplier,
                    name=name,
                    qualname=edge,
                )
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceNativeReferencePrimitivesMixin"]
