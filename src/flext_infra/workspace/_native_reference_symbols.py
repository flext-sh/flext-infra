"""Native symbol identities, extension callbacks and code evidence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import marshal
import sys
from base64 import b64encode
from contextvars import ContextVar
from dis import get_instructions
from importlib.machinery import ExtensionFileLoader
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
    MethodWrapperType,
    ModuleType,
    WrapperDescriptorType,
)
from typing import ClassVar

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace._native_reference_primitives import (
    FlextInfraWorkspaceNativeReferencePrimitivesMixin,
)


class FlextInfraWorkspaceNativeReferenceSymbolsMixin(
    FlextInfraWorkspaceNativeReferencePrimitivesMixin
):
    _compilation_facts: ClassVar[ContextVar[t.Infra.NativeInvocationFacts | None]] = (
        ContextVar("native_compilation_facts", default=None)
    )

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
        compiled: t.MutableMappingKV[Path, t.Infra.NativeClassDeclarations],
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

    @classmethod
    def _instance_storage(
        cls,
        value: p.AttributeProbe,
    ) -> t.SequenceOf[t.Triple[str, bool, p.AttributeProbe | None]]:
        """Read interpreter-owned instance dictionaries and declared member slots.

        Returns:
            Ordered native storage identities, presence and retained values.

        """
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        result: list[t.Triple[str, bool, p.AttributeProbe | None]] = []
        for index, owner in enumerate(ancestry):
            for name, descriptor in sorted(cls._class_namespace(owner).items()):
                if (
                    not (
                        cls._is_native(descriptor, MemberDescriptorType)
                        or (
                            name == "__dict__"
                            and cls._is_native(descriptor, GetSetDescriptorType)
                        )
                    )
                    or descriptor.__objclass__ is not owner
                ):
                    continue
                if index and cls._is_native(descriptor, MemberDescriptorType):
                    present, stored = cls._inherited_member_state(
                        value, owner, name, descriptor, ancestry[index - 1]
                    )
                else:
                    # A first-MRO unset slot retains its original native failure.
                    present, stored = True, descriptor.__get__(value, native)
                result.append((f"{cls._symbol(owner)}::{name}", present, stored))
        return tuple(result)

    @classmethod
    def _extension_metadata(
        cls,
        value: t.Infra.NativeOperand,
        slots: t.MappingKV[str, t.Infra.NativeOperand],
    ) -> p.Result[t.StrMapping]:
        """Read exact native extension metadata slots without authored accessors.

        Returns:
            The native supplier, name and qualified name, or its first failure.

        """
        native = type(value)
        metadata: t.DictKV[str, str] = {}
        for attribute in ("__module__", "__name__", "__qualname__"):
            descriptor = cls._native_metadata_slot(slots, attribute)
            if descriptor is None:
                return r[t.StrMapping].fail(
                    f"extension callback lacks a native metadata slot: {attribute} "
                    f"type={native.__module__}.{native.__qualname__}",
                )
            if descriptor.__objclass__ is not native:
                return r[t.StrMapping].fail(
                    "extension callback metadata belongs to another native type",
                )
            observed = descriptor.__get__(value, descriptor.__objclass__)
            if type(observed) is not str:
                return r[t.StrMapping].fail(
                    f"extension callback metadata is not text: {attribute}",
                )
            metadata[attribute] = observed
        return r[t.StrMapping].ok(metadata)

    @classmethod
    def _extension_callback(
        cls,
        value: t.Infra.NativeOperand,
        binding: str,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Read registered native extension slots without authored accessors.

        Returns:
            Supplier, name and qualified name, or the first admission failure.

        """
        native = type(value)
        slots = cls._class_namespace(native)
        captured = cls._extension_metadata(value, slots)
        if captured.failure:
            return r[t.Triple[str, str, str]].from_failure(captured)
        metadata = captured.value
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
            return cls._extension_globals_reference(value, metadata, slots, supplier)
        return cls._extension_lexical_reference(
            value,
            native,
            cls._module_namespace(supplier),
            metadata,
            binding,
        )

    @classmethod
    def _extension_globals_reference(
        cls,
        value: t.Infra.NativeOperand,
        metadata: t.StrMapping,
        slots: t.MappingKV[str, t.Infra.NativeOperand],
        supplier: ModuleType,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Authenticate an extension's native globals against its actual supplier.

        Returns:
            The registered callback identity or its native globals failure.

        """
        globals_slot = cls._native_metadata_slot(slots, "__globals__")
        if globals_slot is None or globals_slot.__objclass__ is not type(value):
            return r[t.Triple[str, str, str]].fail(
                "extension callback globals are not native storage",
            )
        if globals_slot.__get__(value, globals_slot.__objclass__) is not vars(supplier):
            return r[t.Triple[str, str, str]].fail(
                "extension callback globals differ from its native supplier: "
                f"{metadata['__module__']}.{metadata['__qualname__']}",
            )
        return r[t.Triple[str, str, str]].ok((
            metadata["__module__"],
            metadata["__name__"],
            metadata["__qualname__"],
        ))

    @classmethod
    def _extension_lexical_reference(
        cls,
        value: t.Infra.NativeOperand,
        native: t.Infra.NativeType,
        namespace: t.MappingKV[str, t.Infra.NativeOperand],
        metadata: t.StrMapping,
        binding: str,
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
                    "binding": binding,
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
            if cls._is_native(registered, staticmethod):
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
    def _slice_state(
        cls, value: p.AttributeProbe | None
    ) -> (
        t.Triple[
            p.AttributeProbe | None, p.AttributeProbe | None, p.AttributeProbe | None
        ]
        | None
    ):
        """Read the three retained references of the exact CPython slice type.

        Returns:
            The native start, stop and step references, or no matching slice.

        Raises:
            ValueError: The slice's native supplier, construction or storage differs.

        """
        builtins = sys.modules.get("builtins")
        if type(builtins) is not ModuleType:
            msg = "native slice has no registered builtin supplier"
            raise ValueError(msg)
        native = vars(builtins).get("slice")
        if type(value) is not native:
            return None
        elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
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
            or not cls._is_native(constructor, BuiltinFunctionType)
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
        result: list[p.AttributeProbe | None] = []
        for name in ("start", "stop", "step"):
            descriptor = namespace[name]
            if (
                not cls._is_native(descriptor, MemberDescriptorType)
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
        """Read retained alias operands without populating its lazy parameters.

        Returns:
            The authenticated retained operands, or no matching generic alias.

        Raises:
            ValueError: The alias's native owner, construction or storage differs.

        """
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        if not any(owner is GenericAlias for owner in ancestry):
            return None
        supplier = sys.modules.get("types")
        elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(supplier) is not ModuleType
            or vars(supplier).get("GenericAlias") is not GenericAlias
            or type(GenericAlias) is not type
        ):
            msg = "generic alias lacks its elected interpreter type"
            raise ValueError(msg)
        if not cls._native_text(
            vars(type)["__name__"].__get__(GenericAlias, type), "GenericAlias"
        ) or not cls._native_text(
            vars(type)["__module__"].__get__(GenericAlias, type), "types"
        ):
            msg = "generic alias lacks its elected interpreter type"
            raise ValueError(msg)
        namespace = cls._class_namespace(GenericAlias)
        constructor = namespace.get("__new__")
        if (
            not cls._is_native(constructor, BuiltinFunctionType)
            or constructor.__self__ is not GenericAlias
            or not cls._native_text(constructor.__name__, "__new__")
        ):
            msg = "generic alias has no native constructor owner"
            raise ValueError(msg)
        result: list[t.Pair[str, p.AttributeProbe | None]] = []
        for name in ("__origin__", "__args__", "__unpacked__"):
            descriptor = namespace.get(name)
            if (
                not cls._is_native(descriptor, MemberDescriptorType)
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
    def _code_nonportable_constants(
        cls, code: t.Infra.NativeCode
    ) -> t.VariadicTuple[t.Pair[t.VariadicTuple[int], str]]:
        """Elect native constants before any relocation or binary encoding.

        Returns:
            Structural paths and native types whose equality is not portable.

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
        """Capture complete compiler bytes without changing code or source positions.

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
            locations=None if nonportable else cls._code_locations(code),
            nonportable_constants=nonportable,
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
        FlextInfraWorkspaceNativeReferenceSymbolsMixin._code_nonportable_constants(code)
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
            FlextInfraWorkspaceNativeReferenceSymbolsMixin._relocate_code(value, paths)
            if FlextInfraWorkspaceNativeReferenceSymbolsMixin._is_native(
                value, CodeType
            )
            else value
            for value in FlextInfraWorkspaceNativeReferenceSymbolsMixin._native_code_constants(
                code
            )
        )
        return code.replace(co_filename=filename, co_consts=constants)

    @classmethod
    def _code_locations(cls, code: t.Infra.NativeCode) -> t.VariadicTuple[t.JsonValue]:
        """Retain flat locations for every exact native code unit in co_consts.

        Returns:
            Structural constant paths and complete original native positions.

        """
        pending: list[t.Pair[t.VariadicTuple[int], t.Infra.NativeCode]] = [((), code)]
        locations: list[t.JsonValue] = []
        while pending:
            position, unit = pending.pop()
            locations.append([
                list(position),
                unit.co_qualname,
                unit.co_filename,
                unit.co_firstlineno,
                b64encode(unit.co_linetable).decode("ascii"),
                b64encode(unit.co_exceptiontable).decode("ascii"),
            ])
            pending.extend(
                ((*position, index), child)
                for index, child in enumerate(cls._native_code_constants(unit))
                if cls._is_native(child, CodeType)
            )
        return tuple(locations)


__all__: list[str] = ["FlextInfraWorkspaceNativeReferenceSymbolsMixin"]
