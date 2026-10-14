"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import marshal
import sys
from base64 import b64decode, b64encode
from dis import get_instructions
from functools import partial
from gc import get_referents
from importlib.machinery import ExtensionFileLoader, FrozenImporter
from inspect import CO_NEWLOCALS, CO_OPTIMIZED, getclosurevars
from json import dumps
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

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournalRelocation,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)


def _type_attr(member: str, obj: p.AttributeProbe, owner: type) -> p.AttributeProbe:
    """Read one exact native type-object member through its defining descriptor."""
    return vars(type)[member].__get__(obj, owner)


def _native_mro(owner: type) -> t.SequenceOf[type]:
    """Read the exact native method resolution order of one type owner."""
    return vars(type)["__mro__"].__get__(owner, type(owner))


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @classmethod
    def producer_selection(
        cls,
        entrypoint: p.AttributeProbe,
    ) -> p.Result[m.Infra.SourceClassReference]:
        """Elect a source-owned callable or receiver through static lexical storage."""
        value = entrypoint.__func__ if type(entrypoint) is MethodType else entrypoint
        if cls._is_class(value):
            module = cls._class_namespace(value).get("__module__")
            qualified = vars(type)["__qualname__"].__get__(value, type(value))
        elif type(value) is FunctionType:
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
        attributes = tuple(qualified.split("."))
        if any(not component.isidentifier() for component in attributes):
            return r[m.Infra.SourceClassReference].fail(
                "producer selection has no portable source declaration"
            )
        current = sys.modules[module]
        for component in attributes:
            namespace = (
                cls._class_namespace(current)
                if cls._is_class(current)
                else vars(ModuleType)["__dict__"].__get__(current, type(current))
                if type(current) is ModuleType
                else {}
            )
            if component not in namespace:
                return r[m.Infra.SourceClassReference].fail(
                    f"producer selection has no source-owned lexical binding: {qualified}",
                )
            current = namespace[component]
        if type(current) in {classmethod, staticmethod}:
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
        entrypoint: p.AttributeProbe,
        collaborators: t.SequenceOf[p.AttributeProbe],
    ) -> p.Result[t.VariadicTuple[m.Infra.SourceClassReference]]:
        """Retain actual entrypoints, bound receiver types and explicitly wired ports."""
        result_type = r[t.VariadicTuple[m.Infra.SourceClassReference]]
        selected: dict[t.Pair[str, t.StrTuple], m.Infra.SourceClassReference] = {}
        for callable_root in (entrypoint, *collaborators):
            roots = [callable_root]
            if type(callable_root) is MethodType:
                receiver = callable_root.__self__
                roots.append(receiver if cls._is_class(receiver) else type(receiver))
            for root in roots:
                nominated = cls.producer_selection(root)
                if nominated.failure:
                    return result_type.from_failure(nominated)
                identity = (nominated.value.target, nominated.value.attributes)
                selected[identity] = nominated.value
        return result_type.ok(tuple(selected.values()))

    @classmethod
    def authenticate(
        cls,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Authenticate consumed sources through an isolated native loader/compiler.

        This read-only operation owns no publication transaction. The isolated
        loader proves bindings, and its executed code is checked against the
        pinned source bytes before the reference is accepted.
        """
        result = r[m.Infra.NativeImportReference]
        authority = request.source_authority
        current = FlextInfraCodegenPreconditions.source_authority_current(authority)
        if current.failure:
            return result.from_failure(current)
        inputs = FlextInfraMiseArtifactsVerification.states_current(request.inputs)
        if inputs.failure:
            return result.from_failure(inputs)
        environment = u.Infra.runtime_environment_dir(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        runtime = u.Infra.runtime_python(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        if (
            environment.is_symlink()
            or environment.absolute() != Path(sys.prefix).absolute()
            or not runtime.is_file()
            or runtime.resolve() != authority.runtime
            or sys.flags.optimize != authority.optimize
        ):
            return result.fail("native reference runtime authority differs")
        observed = cls.capture(request.modules)
        if observed.failure:
            return result.from_failure(observed)
        authored = cls.authored_sources_current(observed.value, authority.inputs)
        if authored.failure:
            return result.from_failure(authored)
        from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport

        consumer = FlextInfraValidateFreshImport(
            repository_root=request.repository_root,
            runtime_root=request.runtime_root,
        )

        roots = tuple(dict.fromkeys(request.import_roots))
        selections = tuple(item.model_dump_json() for item in request.modules)
        code = (
            consumer.PRELUDE
            + f"sys.path[:0] = tuple(root for root in {tuple(str(root) for root in roots)!r} if root not in sys.path)\n"
            + "from flext_infra import m\n"
            + "from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference as native\n"
            + f"selections = tuple(m.Infra.SourceClassReference.model_validate_json(item) for item in {selections!r})\n"
            + "for item in selections: importlib.import_module(item.target)\n"
            + consumer.ORIGIN_CODE.replace(
                consumer.ORIGINS_PLACEHOLDER,
                repr(
                    tuple(
                        (namespace, str(source))
                        for namespace, source in authority.generator_modules
                        if source.is_dir()
                    )
                ),
            )
            + "reference = native.capture(selections).unwrap()\n"
            + "sys.stdout.write(reference.model_dump_json())\n"
        )
        output = consumer.execute_probe(
            m.Infra.FreshImportProbe(subject="native reference", code=code),
            cwd=request.repository_root,
            source_roots=roots,
            isolated=True,
        )
        if output.failure:
            return result.from_failure(output)
        if not u.Cli.process_succeeded(output.value.outcome) or output.value.stderr:
            return result.fail(
                f"cold native source import failed: {output.value.outcome}\n"
                f"stdout:\n{output.value.stdout}\nstderr:\n{output.value.stderr}",
            )
        reference = m.Infra.NativeImportObservation.model_validate_json(
            output.value.stdout
        )
        compared = cls.compare(observed.value, reference)
        if compared.failure:
            return result.from_failure(compared)
        authored = cls.authored_sources_current(reference, authority.inputs)
        if authored.failure:
            return result.from_failure(authored)
        current = FlextInfraCodegenPreconditions.source_authority_current(authority)
        if current.failure:
            return result.from_failure(current)
        inputs = FlextInfraMiseArtifactsVerification.states_current(request.inputs)
        if inputs.failure:
            return result.from_failure(inputs)
        return result.ok(
            m.Infra.NativeImportReference(
                **reference.model_dump(),
                source_authority=authority,
            )
        )

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

    @classmethod
    def _executable_operands(
        cls,
        binding: str,
        value: p.AttributeProbe | None,
    ) -> t.SequenceOf[t.Pair[str, p.AttributeProbe]]:
        """Walk native operand containers once, excluding data and cyclic aliases."""
        pending: list[t.Pair[str, p.AttributeProbe | None]] = [(binding, value)]
        seen: set[int] = set()
        result: list[t.Pair[str, p.AttributeProbe]] = []
        while pending:
            name, item = pending.pop()
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            if type(item) is frozenset or type(item) is set:
                children = sorted(
                    item,
                    key=lambda child: cls._value(child, construction=True),
                )
            elif type(item) is tuple or type(item) is list:
                children = list(item)
            else:
                children = None
            if children is not None:
                pending.extend(
                    (f"{name}.{index}", child) for index, child in enumerate(children)
                )
            elif type(item) is dict:
                entries: t.SequenceOf[t.Pair[p.AttributeProbe, p.AttributeProbe]] = (
                    tuple(item.items())
                )
                pending.extend(
                    (f"{name}.{index}.{part}", child)
                    for index, pair in enumerate(entries)
                    for part, child in enumerate(pair)
                )
            elif any(owner is GenericAlias for owner in _native_mro(type(item))):
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
        slots: t.MappingKV[str, p.AttributeProbe],
        attribute: str,
    ) -> GetSetDescriptorType | MemberDescriptorType | None:
        """Read one exact native metadata descriptor from a class namespace."""
        slot = slots.get(attribute)
        if type(slot) is GetSetDescriptorType or type(slot) is MemberDescriptorType:
            return slot
        return None

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
                "extension callback supplier is not a native extension: "
                f"{metadata['__module__']}.{metadata['__qualname__']} "
                f"type={native.__module__}.{native.__qualname__} "
                f"loader={type(supplier.__spec__.loader).__qualname__}",
            )
        globals_slot = slots.get("__globals__")
        if globals_slot is not None:
            if (
                type(globals_slot) not in {GetSetDescriptorType, MemberDescriptorType}
                or globals_slot.__objclass__ is not native
            ):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals are not native storage",
                )
            if globals_slot.__get__(value, native) is not vars(supplier):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals differ from its native supplier: "
                    f"{metadata['__module__']}.{metadata['__qualname__']}",
                )
            return r[t.Triple[str, str, str]].ok((
                metadata["__module__"],
                metadata["__name__"],
                metadata["__qualname__"],
            ))
        namespace = vars(supplier)
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
        if registered is not value:
            descriptor_owner: p.AttributeProbe | None = None
            if (
                type(registered) is GetSetDescriptorType
                or type(registered) is MemberDescriptorType
                or type(registered) is ClassMethodDescriptorType
                or type(registered) is MethodDescriptorType
                or type(registered) is WrapperDescriptorType
            ):
                descriptor_owner = registered.__objclass__
        registered_functions = (
            registered.__func__
            if type(registered) in {classmethod, staticmethod}
            else registered
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
    def _native_callable_instance(cls, value: p.AttributeProbe) -> bool:
        """Recognize a registered native callable object through its call slot."""
        native = type(value)
        namespace = cls._class_namespace(native)
        descriptor = namespace.get("__call__")
        if (
            type(descriptor) not in {MethodDescriptorType, WrapperDescriptorType}
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
    def _python_callable_instance(cls, value: p.AttributeProbe) -> bool:
        """Recognize authored call behavior separately from function metadata."""
        return any(
            type(cls._class_namespace(owner).get("__call__")) is FunctionType
            for owner in vars(type)["__mro__"].__get__(
                type(value), type(type(value))
            )
        )

    @staticmethod
    def _native_instance_referents(
        value: p.AttributeProbe,
    ) -> t.VariadicTuple[p.AttributeProbe]:
        """Read opaque native argument storage through authenticated CPython traversal."""
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
    def _native_cache_state(cls, value: p.AttributeProbe) -> p.Result[str]:
        """Retain operational reference identities through authenticated native GC."""
        return r[str].ok(
            dumps(
                tuple(
                    (cls._symbol(type(item)), id(item))
                    for item in cls._native_instance_referents(value)
                )
            )
        )

    @classmethod
    def _native_iterator_receiver(cls, value: p.AttributeProbe) -> bool:
        """Prove a bound next slot on an explicitly registered native iterator type."""
        if not cls._native_builtin(value) or value.__name__ != "__next__":
            return False
        native = type(value.__self__)
        namespace = cls._class_namespace(native)
        for name in ("__iter__", "__next__"):
            slot = namespace.get(name)
            if (
                type(slot) not in {MethodDescriptorType, WrapperDescriptorType}
                or slot.__objclass__ is not native
            ):
                return False
        supplier_name = _type_attr("__module__", native, type(native))
        supplier = (
            sys.modules.get(supplier_name) if type(supplier_name) is str else None
        )
        return type(supplier) is ModuleType and any(
            registered is native for registered in vars(supplier).values()
        )

    @staticmethod
    def _is_class(value: p.AttributeProbe) -> bool:
        """Recognize a class through native metaclass storage, never __class__."""
        return any(base is type for base in _native_mro(type(value)))

    @staticmethod
    def _native_builtin(value: p.AttributeProbe) -> bool:
        """Recognize interpreter callable ancestry, including native subtypes."""
        return any(
            owner is BuiltinFunctionType or owner is MethodWrapperType
            for owner in _native_mro(type(value))
        )

    @classmethod
    def _symbol(cls, value: p.AttributeProbe) -> str:
        if (
            cls._native_builtin(value)
            and value.__self__ is not None
            and type(value.__self__) is not ModuleType
        ):
            receiver = value.__self__
            class_receiver = cls._is_class(receiver)
            receiver_owner = receiver if class_receiver else type(receiver)
            for owner in _native_mro(receiver_owner):
                descriptor = cls._class_namespace(owner).get(value.__name__)
                if type(descriptor) in {classmethod, staticmethod}:
                    descriptor = descriptor.__func__
                if descriptor is value:
                    return f"{cls._symbol(owner)}.{value.__name__}"
                if (
                    type(descriptor)
                    in {
                        ClassMethodDescriptorType,
                        MethodDescriptorType,
                        WrapperDescriptorType,
                    }
                    and descriptor.__objclass__ is owner
                ):
                    bound = descriptor.__get__(
                        None if class_receiver else receiver,
                        receiver if class_receiver else type(receiver),
                    )
                    if type(bound) is type(value) and bound == value:
                        return f"{cls._symbol(owner)}.{value.__name__}"
            msg = (
                "native callable has no defining descriptor for its receiver: "
                f"{cls._symbol(receiver_owner)}.{value.__name__}"
            )
            raise TypeError(msg)
        if cls._is_class(value):
            module = _type_attr("__module__", value, type(value))
            name = _type_attr("__qualname__", value, type(value))
        elif type(value) is FunctionType or cls._native_builtin(value):
            module = None if type(value) is MethodWrapperType else value.__module__
            name = value.__qualname__
        elif type(value) is ModuleType:
            module, name = value.__name__, ""
        else:
            module = _type_attr("__module__", type(value), type(type(value)))
            name = _type_attr("__qualname__", type(value), type(type(value)))
        if type(module) is str:
            return f"{module}::{name}"
        if module is None and cls._native_builtin(value) and type(name) is str:
            registered: p.AttributeProbe | None = sys.modules.get("builtins")
            for component in name.split("."):
                namespace = (
                    cls._class_namespace(registered)
                    if cls._is_class(registered)
                    else vars(registered)
                    if type(registered) is ModuleType
                    else {}
                )
                registered = namespace.get(component)
            if type(registered) is staticmethod:
                registered = registered.__func__
            if registered is value:
                return f"builtins::{name}"
        if type(module) in {GetSetDescriptorType, MemberDescriptorType}:
            owner = value if cls._is_class(value) else type(value)
            builtin_module = sys.modules.get("builtins")
            owner_name = _type_attr("__name__", owner, type(owner))
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
                f"module_type={vars(type)['__qualname__'].__get__(type(module), type(type(module)))}"
            )
            raise TypeError(
                msg,
            )
        msg = (
            "native symbolic metadata has no text or descriptor module: "
            f"qualified={name}; module_type={type(module).__name__}; "
            f"value_type={type(value).__name__}"
        )
        raise TypeError(
            msg,
        )

    @classmethod
    def _value(
        cls,
        value: p.AttributeProbe | None,
        seen: frozenset[int] = frozenset(),
        *,
        construction: bool = False,
        references: list[t.Pair[str, p.AttributeProbe]] | None = None,
        binding: str = "",
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> str:
        """Serialize one structural observation without recursively escaping JSON."""
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
        value: p.AttributeProbe | None,
        seen: frozenset[int],
        *,
        construction: bool,
        references: list[t.Pair[str, p.AttributeProbe]] | None = None,
        binding: str = "",
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> t.JsonValue:
        """Observe native slots as JSON data without authored accessors."""
        native = type(value)
        if native in {
            GetSetDescriptorType,
            MemberDescriptorType,
            ClassMethodDescriptorType,
            MethodDescriptorType,
            WrapperDescriptorType,
        }:
            owner = value.__objclass__
            if cls._class_namespace(owner).get(value.__name__) is not value:
                msg = "native descriptor differs from its registered owner"
                raise TypeError(msg)
            return ["native-descriptor", cls._symbol(owner), value.__name__]
        if value is None:
            return ["NoneType", None]
        if native in {str, int, bool} and isinstance(value, str | int | bool):
            return [native.__name__, value]
        if native is float and isinstance(value, float):
            return ["float", float.hex(value)]
        if native is bytes and isinstance(value, bytes):
            return ["bytes", b64encode(value).decode("ascii")]
        if value is Ellipsis:
            return ["ellipsis"]
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
        if any(native is kind for kind in (tuple, list, set, frozenset)):
            items = list(map(observe, value))
            return [
                native.__name__,
                sorted(items, key=dumps) if native in {set, frozenset} else items,
            ]
        if native is dict:
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
        if native is CodeType:
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
        if native is FunctionType:
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
        if native is UnionType:
            arguments = vars(UnionType)["__args__"].__get__(value, UnionType)
            return ["union", observe(arguments, construction=False)]
        if any(owner is GenericAlias for owner in _native_mro(native)):
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
                observe(value.__self__),
            ]
        if cls._is_class(value) or cls._native_builtin(value) or native is ModuleType:
            return ["symbol", cls._symbol(value)]
        if not construction:
            return ["instance", cls._symbol(native)]
        observed: list[t.JsonValue] = []
        ancestry = _native_mro(native)
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
        if observed:
            return ["storage", cls._symbol(native), observed]
        if cls._native_callable_instance(value):
            return [
                "native_callable_storage",
                cls._symbol(native),
                [
                    observe(item, construction=True)
                    for item in cls._native_instance_referents(value)
                ],
            ]
        supplier_name = _type_attr("__module__", native, type(native))
        supplier = (
            sys.modules.get(supplier_name) if type(supplier_name) is str else None
        )
        if type(supplier) is ModuleType:
            namespace = vars(ModuleType)["__dict__"].__get__(supplier, type(supplier))
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
    def _code_locations(code: p.Infra.NativeCodeIdentity) -> t.JsonValue:
        """Retain physical locations for every nested native compiler code unit."""
        pending: list[t.Pair[p.Infra.NativeCodeIdentity, t.VariadicTuple[int]]] = [
            (code, ())
        ]
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
                for index, value in enumerate(current.co_consts)
                if type(value) is CodeType
            )
        return locations

    @staticmethod
    def _code_units(
        root: p.Infra.NativeCodeIdentity,
    ) -> t.VariadicTuple[p.Infra.NativeCodeIdentity]:
        """Collect the native compiler's nested code units without executing them."""
        pending = [root]
        units: list[p.Infra.NativeCodeIdentity] = []
        while pending:
            current = pending.pop()
            units.append(current)
            pending.extend(
                value for value in current.co_consts if isinstance(value, CodeType)
            )
        return tuple(units)

    @classmethod
    def _declared_class_names(
        cls,
        supplier: str,
        qualname: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        compiled: dict[Path, t.VariadicTuple[p.Infra.NativeCodeIdentity]],
    ) -> p.Result[t.VariadicTuple[frozenset[str]]]:
        """Separate authored class bindings from a metaclass's operational outputs."""
        result = r[t.VariadicTuple[frozenset[str]]]
        source = FlextInfraWorkspaceEnvironmentProvenance.module_source(supplier)
        if source.failure:
            return result.from_failure(source)
        path = source.value
        if path.suffix != c.Infra.EXT_PYTHON:
            return result.ok(())
        if path not in compiled:
            before = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if before.content is None:
                return result.fail(f"native class declaration source is absent: {path}")
            root = compile(
                before.content,
                str(path),
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
            after = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if before != after:
                return result.fail(f"native class declaration source changed: {path}")
            compiled[path] = cls._code_units(root)
        candidates = [
            unit
            for unit in compiled[path]
            if unit.co_qualname == qualname
            and not unit.co_flags & (CO_NEWLOCALS | CO_OPTIMIZED)
            and isinstance(unit, CodeType)
        ]
        if len(candidates) > 1:
            candidates = [
                unit
                for unit in candidates
                if unit.co_firstlineno == namespace.get("__firstlineno__")
            ]
            if len(candidates) != 1:
                return result.fail(
                    f"native class declaration is ambiguous: {supplier}::{qualname}"
                )
        if not candidates:
            # Factory-created classes retain their existing complete native
            # payload and generated-code/declaration provenance.
            return result.ok(())
        return result.ok(
            (
                frozenset(
                    instruction.argval
                    for instruction in get_instructions(candidates[0])
                    if instruction.opname == "STORE_NAME"
                    and isinstance(instruction.argval, str)
                ),
            )
        )

    @staticmethod
    def _class_state_writers(
        owner: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        declarations: frozenset[str],
    ) -> t.VariadicTuple[t.Triple[str, p.AttributeProbe, frozenset[str]]]:
        """Prove state writes through the exact native class or global receiver."""
        writers: list[t.Triple[str, p.AttributeProbe, frozenset[str]]] = []
        for name, member in sorted(namespace.items()):
            if type(member) not in {classmethod, staticmethod}:
                continue
            function = member.__func__
            if type(function) is not FunctionType:
                continue
            if type(member) is classmethod and not function.__code__.co_argcount:
                continue
            receiver = (
                function.__code__.co_varnames[0]
                if type(member) is classmethod
                else None
            )
            instructions = tuple(get_instructions(function.__code__))
            if receiver is not None and any(
                (
                    instruction.opname.startswith("STORE_FAST")
                    or instruction.opname == "DELETE_FAST"
                )
                and (
                    instruction.argval == receiver
                    or (
                        type(instruction.argval) is tuple
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
                for previous, instruction in zip(
                    instructions, instructions[1:], strict=False
                )
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
                        and
                        previous.opname == "LOAD_FAST_LOAD_FAST"
                        and type(previous.argval) is tuple
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
        """
        origins: dict[str, Path] = {}
        sources: set[t.Triple[str, str, str]] = set()
        evidence: list[m.Infra.NativeBindingEvidence] = []
        compiled: dict[Path, t.VariadicTuple[p.Infra.NativeCodeIdentity]] = {}
        references: list[t.Pair[str, p.AttributeProbe]] = []
        observe_value = partial(cls._value, references=references, paths=paths)
        pending = []
        nominations = tuple(
            m.Infra.SourceClassReference(target=item) if type(item) is str else item
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
            namespace = vars(ModuleType)["__dict__"].__get__(module, type(module))
            origins[name] = cls._source_path(origin.value, paths)
            sources.add((name, str(origins[name]), ""))
            evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=name,
                    kind="module",
                    supplier=name,
                    name=namespace["__name__"],
                    qualname="",
                    operands=(("module_type", cls._symbol(type(module))),),
                )
            )
            if type(module) is not ModuleType:
                pending.append((
                    f"{name}.module_type",
                    type(module),
                    name,
                    str(origins[name]),
                ))
            if nomination.attributes:
                value = module
                for component in nomination.attributes:
                    namespace = (
                        cls._class_namespace(value)
                        if cls._is_class(value)
                        else vars(ModuleType)["__dict__"].__get__(value, type(value))
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
                    str(origins[name]),
                ))
                continue
            mutable_globals = set()
            functions = [
                value for value in namespace.values() if type(value) is FunctionType
            ]
            functions.extend(
                member.__func__
                if type(member) in {classmethod, staticmethod}
                else member
                for value in namespace.values()
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
                    operands=(("value", observe_value(value)),),
                )
                for key, value in sorted(namespace.items())
                if type(value) is bool and key not in mutable_globals
            )
            pending.extend(
                (f"{name}::{key}", value, name, "")
                for key, value in sorted(namespace.items())
                if cls._is_class(value)
                or type(value) in {FunctionType, MethodType}
                or cls._native_builtin(value)
                or type(value) in {property, classmethod, staticmethod}
                or cls._callable_storage(value)
            )
        visited: dict[int, tuple[p.AttributeProbe, str]] = {}
        while pending or references:
            for registered, owner in references:
                supplier, _, _qualified = cls._symbol(owner).partition("::")
                pending.append((f"{registered}.native_type", owner, supplier, ""))
            references.clear()
            binding, value, supplier, owner_source = pending.pop()
            if id(value) in visited:
                if binding == visited[id(value)][1]:
                    continue
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="alias",
                        supplier=supplier,
                        name="",
                        qualname="",
                        operands=(("target", visited[id(value)][1]),),
                    ),
                )
                continue
            visited[id(value)] = (value, binding)
            if type(value) in {classmethod, staticmethod}:
                function = value.__func__
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind=type(value).__name__,
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
                actual_supplier = _type_attr("__module__", value, type(value))
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
                    origin = origins[actual_supplier] = cls._source_path(
                        observed.value,
                        paths,
                    )
                source = str(origin)
                qualname = _type_attr("__qualname__", value, type(value))
                if type(qualname) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native qualified name: {binding}",
                    )
                sources.add((f"{actual_supplier}::{qualname}", source, ""))
                declarations = cls._declared_class_names(
                    actual_supplier, qualname, namespace, compiled
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
                    and type(item) not in {property, classmethod, staticmethod}
                }
                writers = cls._class_state_writers(
                    value, namespace, frozenset(declaration)
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
                        name=_type_attr("__name__", value, type(value)),
                        qualname=qualname,
                        operands=(
                            ("metaclass", cls._symbol(type(value))),
                            (
                                "bases",
                                dumps(
                                    tuple(
                                        cls._symbol(base)
                                        for base in _type_attr(
                                            "__bases__", value, type(value)
                                        )
                                    )
                                ),
                            ),
                            (
                                "annotations",
                                observe_value(
                                    namespace.get(
                                        "__annotations__", dict[str, p.AttributeProbe]()
                                    ),
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
                        or type(item) in {FunctionType, MethodType}
                        or cls._native_builtin(item)
                        or type(item) in {property, classmethod, staticmethod}
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
                        _type_attr("__bases__", value, type(value))
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
                actual_supplier = _type_attr("__module__", owner, type(owner))
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
            if any(owner is GenericAlias for owner in _native_mro(type(value))):
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="generic_alias",
                        supplier="types",
                        name="",
                        qualname="",
                        operands=((
                            "alias",
                            observe_value(value, construction=True),
                        ),),
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
                    ("function", observe_value(function.value, construction=True)),
                    ("attributes", observe_value(attributes, construction=True)),
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
                            observe_value(
                                slot.__get__(value, type(value)),
                                construction=True,
                            ),
                        ))
                        stored = slot.__get__(value, type(value))
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
                    or type(item) is FunctionType
                    or cls._native_builtin(item)
                    or cls._native_wrapper_kind(item) is not None
                    if not selected or key == "__wrapped__"
                )
                continue
            if type(value) is not FunctionType:
                native_builtin = cls._native_builtin(value)
                if cls._native_callable_instance(value) or cls._python_callable_instance(
                    value
                ):
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
                            operands=((
                                "storage",
                                observe_value(value, construction=True),
                            ),),
                        ),
                    )
                    pending.append((
                        f"{binding}.native_class",
                        native,
                        supplier,
                        owner_source,
                    ))
                    continue
                if not native_builtin:
                    extension = cls._extension_callback(value)
                    if extension.failure:
                        return r[m.Infra.NativeImportObservation].fail(
                            f"{extension.error}; binding={binding}; "
                            f"binding_supplier={supplier}; "
                            f"native_type={cls._symbol(type(value))}; "
                            f"native_ancestry={tuple(cls._symbol(owner) for owner in _native_mro(type(value)))}"
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
                    actual_supplier, _, qualified = cls._symbol(value).partition("::")
                    native_name = value.__name__
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
                if native_builtin:
                    receiver = value.__self__
                    if cls._native_iterator_receiver(value):
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
                        f"generated executable has no elected declaration owner: {binding}",
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
                    and value.__globals__
                    is not vars(ModuleType)["__dict__"].__get__(module, type(module))
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
                origin = origins[actual_supplier] = cls._source_path(
                    observed.value,
                    paths,
                )
            supplier_module = sys.modules[actual_supplier]
            supplier_namespace = vars(ModuleType)["__dict__"].__get__(
                supplier_module, type(supplier_module)
            )
            frozen_source = supplier_namespace["__spec__"].origin == "frozen"
            sources.add((
                f"{actual_supplier}::{value.__qualname__}",
                str(origin) if generated or frozen_source else code.co_filename,
                owner_source if generated else "",
            ))
            closure = getclosurevars(value)
            nonlocals = closure.nonlocals
            global_bindings = dict(sorted((closure.builtins | closure.globals).items()))
            operational_globals = frozenset(
                instruction.argval
                for unit in cls._code_units(code)
                if isinstance(unit, CodeType)
                for instruction in get_instructions(unit)
                if instruction.opname in {"STORE_GLOBAL", "DELETE_GLOBAL"}
                and isinstance(instruction.argval, str)
            )
            globals_used = tuple(global_bindings.values())
            if selected:
                # Query actual native global/attribute edges, not every name in
                # an ambient module's dictionary. No descriptor is executed.
                receiver = None
                edge = binding
                for instruction in get_instructions(code):
                    if instruction.opname == "LOAD_GLOBAL":
                        receiver = global_bindings.get(instruction.argval)
                        edge = f"{binding}.global.{instruction.argval}"
                    elif instruction.opname == "LOAD_ATTR" and receiver is not None:
                        namespaces = (
                            tuple(
                                cls._class_namespace(owner)
                                for owner in _native_mro(receiver)
                            )
                            if cls._is_class(receiver)
                            else (
                                vars(ModuleType)["__dict__"].__get__(
                                    receiver, type(receiver)
                                ),
                            )
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
                            evidence.append(
                                m.Infra.NativeBindingEvidence(
                                    binding=f"{edge}.{instruction.argval}",
                                    kind="absent",
                                    supplier=actual_supplier,
                                    name=instruction.argval,
                                    qualname=edge,
                                ),
                            )
                            receiver = None
                            continue
                        receiver = found[instruction.argval]
                        edge += f".{instruction.argval}"
                        if (
                            cls._is_class(receiver)
                            or type(receiver)
                            in {
                                FunctionType,
                                MethodType,
                                property,
                                classmethod,
                                staticmethod,
                            }
                            or cls._native_builtin(receiver)
                            or cls._native_wrapper_kind(receiver) is not None
                            or cls._callable_storage(receiver)
                        ):
                            pending.append((
                                edge,
                                receiver,
                                actual_supplier,
                                str(origin),
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
                inspected = set()
                while class_roots:
                    owner = class_roots.pop()
                    if id(owner) in inspected:
                        continue
                    inspected.add(id(owner))
                    resolved_names = set()
                    for ancestor in _native_mro(owner):
                        namespace = cls._class_namespace(ancestor)
                        for name in code.co_names:
                            if name in resolved_names or name not in namespace:
                                continue
                            resolved_names.add(name)
                            item = namespace.get(name)
                            if cls._is_class(item):
                                class_roots.append(item)
                            elif (
                                type(item)
                                in {
                                    FunctionType,
                                    MethodType,
                                    property,
                                    classmethod,
                                    staticmethod,
                                }
                                or cls._native_builtin(item)
                                or cls._native_wrapper_kind(item) is not None
                                or cls._callable_storage(item)
                            ):
                                pending.append((
                                    f"{binding}.descriptor.{cls._symbol(ancestor)}.{name}",
                                    item,
                                    actual_supplier,
                                    str(origin),
                                ))
            pending.extend(
                (f"{binding}.global.{name}", item, actual_supplier, owner_source)
                for name, item in global_bindings.items()
                if item is not None
                and (
                    cls._is_class(item)
                    or type(item) in {FunctionType, MethodType}
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
                    code=b64encode(marshal.dumps(code)).decode("ascii"),
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
        actual = {item.binding for item in observed.bindings}
        if set(expected) != actual:
            only_native = actual - expected.keys()
            only_imported = expected.keys() - actual
            return r[bool].fail(
                "producer executable binding inventory differs: "
                f"only_native_count={len(only_native)} "
                f"first={sorted(only_native, key=len)[:3]}; "
                f"only_imported_count={len(only_imported)} "
                f"first={sorted(only_imported, key=len)[:3]}"
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
                    f"fields={tuple(key for key in live if key != 'operands' and live[key] != cold[key])}; "
                    f"operands={tuple(sorted(key for key in operands.keys() | imported.keys() if operands.get(key) != imported.get(key)))}; "
                    f"observed_kind={item.kind}; reference_kind={native.kind}; "
                    f"observed_target={operands.get('target')}; "
                    f"reference_target={imported.get('target')}"
                )
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
        """
        states = {item.path: item for item in inputs}
        compiled: dict[str, t.VariadicTuple[p.Infra.NativeCodeIdentity]] = {}
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
                compiled[key] = FlextInfraWorkspaceNativeReference._code_units(root)
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
