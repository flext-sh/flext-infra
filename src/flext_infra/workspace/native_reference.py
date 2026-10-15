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
    MappingProxyType,
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
            finder=u.Infra.semantic_finder(native),
        )
        witnesses[name] = witness
        return r[m.Infra.NativeSourceWitness].ok(witness)

    @staticmethod
    def _witnesses_current(
        witnesses: t.MappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[bool]:
        """Revalidate the invocation-local source cache before returning proof."""
        for witness in witnesses.values():
            current = u.Cli.atomic_read_binary_file_state(witness.source, required=True)
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != witness.state:
                return r[bool].fail(
                    f"generated compiler source changed: {witness.source}"
                )
        return r[bool].ok(value=True)

    @classmethod
    def _generated_proof(
        cls,
        value: FunctionType,
        supplier: str,
        attribute: str,
        receiver: p.AttributeProbe | None,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[t.Triple[str, str, m.Infra.NativeGeneratedFunctionProof]]:
        """Use one closed source compiler for observation and effective admission."""
        from flext_infra.workspace.generated_function import (
            FlextInfraWorkspaceGeneratedFunction,
        )

        result_type = r[t.Triple[str, str, m.Infra.NativeGeneratedFunctionProof]]
        seen: set[t.Pair[str, str]] = set()
        while True:
            identity = (supplier, attribute)
            if identity in seen:
                return result_type.fail("generated source import binding is cyclic")
            seen.add(identity)
            captured = cls._source_witness(supplier, project, witnesses)
            if captured.failure:
                return result_type.from_failure(captured)
            witness = captured.value
            if receiver is not None:
                proof = FlextInfraWorkspaceGeneratedFunction.compile_named_tuple(
                    receiver, attribute, witness
                )
                break
            module = sys.modules[supplier]
            if vars(module).get(attribute) is not value:
                return result_type.fail(
                    f"generated export differs from its source binding: "
                    f"{supplier}::{attribute}"
                )
            declared = witness.module.get_scope().get_names().get(attribute)
            if isinstance(declared, p.Infra.RopeImportedName):
                provider, _line = declared.get_definition_location()
                if provider is None:
                    return result_type.fail(
                        "generated import lacks its physical source supplier"
                    )
                supplier, attribute = provider.get_name(), declared.imported_name
                continue
            proof = FlextInfraWorkspaceGeneratedFunction.compile(
                value, supplier, attribute, witness
            )
            break
        if proof.failure:
            return result_type.from_failure(proof)
        expected = proof.value
        if (
            type(expected.code) is not CodeType
            or type(expected.globals) is not dict
            or type(expected.annotations) is not dict
            or not cls._native_type(expected.defaults, tuple, type(None))
            or not cls._native_type(expected.keyword_defaults, dict, type(None))
            or type(expected.closure) is not tuple
        ):
            return result_type.fail("generated compiler returned non-native storage")
        if (
            value.__code__ != expected.code
            or cls._code_locations(value.__code__)
            != cls._code_locations(expected.code)
            or cls._value(value.__defaults__, construction=True)
            != cls._value(expected.defaults, construction=True)
            or cls._value(value.__kwdefaults__, construction=True)
            != cls._value(expected.keyword_defaults, construction=True)
            or cls._value(
                tuple(cell.cell_contents for cell in value.__closure__ or ()),
                construction=True,
            )
            != cls._value(expected.closure, construction=True)
            or cls._value(value.__globals__, construction=True)
            != cls._value(expected.globals, construction=True)
            or cls._value(value.__builtins__, construction=True)
            != cls._value(expected.globals.get("__builtins__"), construction=True)
            or cls._value(value.__annotations__, construction=True)
            != cls._value(expected.annotations, construction=True)
        ):
            return result_type.fail(
                f"generated executable differs from its physical compiler: "
                f"{supplier}::{attribute}"
            )
        for state in expected.inputs:
            current = u.Cli.atomic_read_binary_file_state(state.path, required=True)
            if current.failure:
                return result_type.from_failure(current)
            if current.value != state:
                return result_type.fail(
                    f"generated compiler source changed: {state.path}"
                )
        return result_type.ok((supplier, attribute, expected))

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

    @classmethod
    def _executable_operands(
        cls,
        binding: str,
        value: p.AttributeProbe | None,
    ) -> t.SequenceOf[t.Pair[str, p.AttributeProbe]]:
        """Retain nested executable operands through exact native containers."""
        # The 21fcf255 walker links reduced arguments to the existing code proof.
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
            elif type(item) is MappingProxyType:
                pending.append((
                    f"{name}.mapping",
                    cls._native_mapping_proxy_backing(item),
                ))
            elif (slice_state := cls._slice_state(item)) is not None:
                pending.extend(
                    (f"{name}.{attribute}", stored)
                    for attribute, stored in zip(
                        ("start", "stop", "step"), slice_state, strict=True
                    )
                )
            elif (alias_state := cls._generic_alias_state(item)) is not None:
                pending.extend(
                    (f"{name}.{attribute}", stored)
                    for attribute, stored in alias_state
                )
                if type(item) is not GenericAlias:
                    pending.append((f"{name}.type", type(item)))
            elif cls._is_class(item) or cls._callable_storage(item):
                result.append((name, item))
            elif cls._python_storage_class(type(item)):
                storage = cls._instance_storage(item)
                # Empty Python slots still retain a physical receiver type.
                result.append((f"{name}.receiver_type", type(item)))
                pending.extend(
                    (f"{name}.{attribute}", stored)
                    for attribute, present, stored in storage
                    if present
                )
        return tuple(result)

    @classmethod
    def _extension_callback(
        cls,
        value: p.AttributeProbe,
        binding: str,
    ) -> p.Result[t.Triple[str, str, str]]:
        """Read registered native extension slots without authored accessors."""
        native = type(value)
        slots = cls._class_namespace(native)
        metadata: dict[str, str] = {}
        for attribute in ("__module__", "__name__", "__qualname__"):
            descriptor = slots.get(attribute)
            if not cls._native_type(
                descriptor, GetSetDescriptorType, MemberDescriptorType
            ):
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback lacks a native metadata slot: {attribute} "
                    f"native_type={cls._symbol(native)[:160]}; "
                    f"binding={binding[:320]!r}",
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
                f"module={metadata['__module__'][:160]!r}; "
                f"qualname={metadata['__qualname__'][:160]!r}; "
                f"native_type={cls._symbol(native)[:160]!r}",
            )
        # Cython retains compiled callbacks in native read-only globals storage.
        # Authenticate its exact descriptor and registered extension namespace.
        globals_slot = slots.get("__globals__")
        if globals_slot is not None:
            if (
                not cls._native_type(
                    globals_slot, GetSetDescriptorType, MemberDescriptorType
                )
                or globals_slot.__objclass__ is not native
            ):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals are not native storage",
                )
            if globals_slot.__get__(value, native) is not vars(supplier):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback globals differ from its native supplier: "
                    f"{metadata['__module__']}::{metadata['__qualname__']}",
                )
            return r[t.Triple[str, str, str]].ok((
                metadata["__module__"],
                metadata["__name__"],
                metadata["__qualname__"],
            ))
        namespace = vars(supplier)
        components = metadata["__qualname__"].split(".")
        for component in components[:-1]:
            owner = namespace.get(component)
            if not cls._is_class(owner):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback has no registered lexical owner",
                )
            namespace = cls._class_namespace(owner)
        # Native aliases retain compiled names; authenticate the same lexical owner.
        # Adopt the bounded owner correction from 8ab3eff without supplier exclusions.
        registered_functions = (
            descriptor.__func__
            if cls._native_type(descriptor, classmethod, staticmethod)
            else descriptor
            for descriptor in namespace.values()
        )
        if not any(registered is value for registered in registered_functions):
            return r[t.Triple[str, str, str]].fail(
                "extension callback differs from its registered descriptor: "
                f"{metadata['__module__']}::{metadata['__qualname__']} "
                f"native_type={cls._symbol(native)[:160]}",
            )
        return r[t.Triple[str, str, str]].ok((
            metadata["__module__"],
            metadata["__name__"],
            metadata["__qualname__"],
        ))

    @classmethod
    def _extension_state(
        cls,
        value: p.AttributeProbe,
        supplier_name: str,
        qualified: str,
        binding: str,
    ) -> p.Result[t.MappingKV[str, p.AttributeProbe]]:
        """Bind native code and raw exports without invoking opaque getters."""
        result_type = r[t.MappingKV[str, p.AttributeProbe]]
        supplier = sys.modules[supplier_name]
        native = type(value)
        aliases: list[str] = []
        lexical_owners: list[p.AttributeProbe] = []
        pending = [("", vars(supplier), None)]
        visited: set[int] = set()
        while pending:
            prefix, namespace, owner = pending.pop()
            if any(type(name) is not str for name in namespace):
                return result_type.fail("native export namespace has non-text keys")
            for name, descriptor in sorted(namespace.items()):
                registered = (
                    descriptor.__func__
                    if cls._native_type(descriptor, classmethod, staticmethod)
                    else descriptor
                )
                path = f"{prefix}.{name}" if prefix else name
                if registered is value:
                    aliases.append(path)
                    if owner is not None:
                        lexical_owners.append(owner)
                if (
                    cls._is_class(descriptor)
                    and id(descriptor) not in visited
                    and supplier_name
                    in cls._class_identity(descriptor, supplier_name, binding)[1]
                ):
                    visited.add(id(descriptor))
                    pending.append((path, cls._class_namespace(descriptor), descriptor))
        if not aliases:
            native_name = vars(type)["__qualname__"].__get__(native, type(native))
            module_metadata = vars(type)["__module__"].__get__(native, type(native))
            metadata_kind = vars(type)["__qualname__"].__get__(
                type(module_metadata), type(type(module_metadata))
            )
            if type(native_name) is not str or type(metadata_kind) is not str:
                msg = "native diagnostic type identity is not text"
                raise ValueError(msg)
            return result_type.fail(
                "native callback has no registered raw export: "
                f"binding={binding[:320]!r}; supplier={supplier_name[:160]!r}; "
                f"qualname={qualified[:160]!r}; "
                f"native_type={native_name[:160]!r}; "
                f"module_metadata_kind={metadata_kind[:160]!r}"
            )
        storage: dict[str, p.AttributeProbe] = {"aliases": tuple(sorted(aliases))}
        slots = cls._class_namespace(native)
        if "__globals__" not in slots:
            return result_type.ok(storage)
        code_slot = slots.get("__code__")
        if (
            type(code_slot) is not GetSetDescriptorType
            or code_slot.__objclass__ is not native
        ):
            return result_type.fail("native callback has no readonly code witness")
        code = code_slot.__get__(value, native)
        if (
            type(code) is not CodeType
            or code.co_freevars
            or "<locals>" in code.co_qualname
        ):
            return result_type.fail("native callback closure has no complete witness")
        known = [native, vars(supplier), code, *lexical_owners]
        storage["code"] = code
        # Defaults may invoke a lazy helper; the closure getter may report None
        # despite retained native state. Neither getter is an admission witness.
        for attribute in (
            "__module__", "__name__", "__qualname__",
            "__dict__", "__annotations__", "__doc__",
        ):
            descriptor = slots.get(attribute)
            if (
                not cls._native_type(
                    descriptor, GetSetDescriptorType, MemberDescriptorType
                )
                or descriptor.__objclass__ is not native
            ):
                return result_type.fail(
                    f"native callback lacks retained storage: {attribute}"
                )
            observed = descriptor.__get__(value, native)
            if (
                attribute in {"__dict__", "__annotations__"}
                and type(observed) is not dict
            ) or (
                attribute not in {"__dict__", "__annotations__"}
                and not cls._native_type(observed, str, type(None))
            ):
                return result_type.fail("native callback storage is not native data")
            known.append(observed)
            storage[attribute] = observed
        referents = cls._native_referents(value)
        if referents.failure:
            return result_type.from_failure(referents)
        if any(
            not any(reference is admitted for admitted in known)
            for reference in referents.value
        ):
            return result_type.fail(
                "native callback closure/default state has no complete witness"
            )
        return result_type.ok(storage)

    @classmethod
    def _native_referents(
        cls, value: p.AttributeProbe
    ) -> p.Result[t.VariadicTuple[p.AttributeProbe]]:
        """Authenticate the interpreter before copying native GC references."""
        result_type = r[t.VariadicTuple[p.AttributeProbe]]
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source("gc")
        if elected.failure:
            return result_type.from_failure(elected)
        supplier = sys.modules.get("gc")
        if (
            elected.value != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
            or type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or get_referents.__self__ is not supplier
            or not cls._native_text(get_referents.__module__, "gc")
            or not cls._native_text(get_referents.__name__, "get_referents")
        ):
            return result_type.fail("native traversal has no elected interpreter owner")
        return result_type.ok(tuple(get_referents(value)))

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
            or not cls._native_text(get_referents.__module__, "gc")
            or not cls._native_text(get_referents.__name__, "get_referents")
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
            if cls._native_type(item, FunctionType, BuiltinFunctionType)
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
    def _python_callable_implementation(
        cls,
        value: p.AttributeProbe,
    ) -> p.AttributeProbe | None:
        """Elect the effective authored call function without invoking accessors."""
        ancestry = vars(type)["__mro__"].__get__(type(value), type(type(value)))
        for owner in ancestry:
            namespace = cls._class_namespace(owner)
            if "__call__" not in namespace:
                continue
            implementation = namespace["__call__"]
            if cls._native_type(implementation, classmethod, staticmethod):
                implementation = implementation.__func__
            if type(implementation) is not FunctionType:
                return None
            return implementation if cls._python_storage_class(type(value)) else None
        return None

    @classmethod
    def _python_storage_class(cls, native: type) -> bool:
        """Require Python storage to cover every non-object ancestry payload."""
        return cls._python_storage_owners(
            vars(type)["__mro__"].__get__(native, type(native))
        )

    @classmethod
    def _python_storage_owners(cls, owners: t.SequenceOf[p.AttributeProbe]) -> bool:
        """Reject native payloads within the selected raw ancestry owners."""
        for ancestor in owners:
            if ancestor is object:
                continue
            for name, descriptor in cls._class_namespace(ancestor).items():
                if (
                    (
                        cls._native_type(
                            descriptor,
                            MethodDescriptorType,
                            ClassMethodDescriptorType,
                            WrapperDescriptorType,
                        )
                        or (
                            type(descriptor) is GetSetDescriptorType
                            and name not in {"__dict__", "__weakref__"}
                        )
                    )
                    and descriptor.__objclass__ is ancestor
                ) or (
                    type(descriptor) is BuiltinFunctionType
                    and descriptor.__self__ is ancestor
                ):
                    return False
        return True

    @classmethod
    def _native_mapping_proxy_backing(cls, value: p.AttributeProbe) -> p.AttributeProbe:
        """Read the sole exact-dict backing of the CPython mapping proxy."""
        if (
            type(value) is not MappingProxyType
            or MappingProxyType is not type(vars(type))
        ):
            msg = "mapping proxy has no admitted interpreter type"
            raise ValueError(msg)
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source("gc").unwrap()
        supplier = sys.modules.get("gc")
        if (
            elected != Path(sys.executable).resolve()
            or sys.implementation.name != "cpython"
            or type(supplier) is not ModuleType
            or vars(supplier).get("get_referents") is not get_referents
            or type(get_referents) is not BuiltinFunctionType
            or not cls._native_text(get_referents.__module__, "gc")
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
    def _instance_storage(
        cls,
        value: p.AttributeProbe,
    ) -> t.SequenceOf[t.Triple[str, bool, p.AttributeProbe | None]]:
        """Read interpreter-owned instance dictionaries and declared member slots."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        result = []
        for index, owner in enumerate(ancestry):
            for name, descriptor in sorted(cls._class_namespace(owner).items()):
                if not (
                    type(descriptor) is MemberDescriptorType
                    or (name == "__dict__" and type(descriptor) is GetSetDescriptorType)
                ) or descriptor.__objclass__ is not owner:
                    continue
                if index and type(descriptor) is MemberDescriptorType:
                    present, stored = cls._inherited_member_state(
                        value, owner, name, descriptor, ancestry[index - 1]
                    )
                else:
                    # A first-MRO unset slot retains its original native failure.
                    present, stored = True, descriptor.__get__(value, native)
                result.append((f"{cls._symbol(owner)}::{name}", present, stored))
        return tuple(result)

    @classmethod
    def _inherited_member_state(
        cls,
        value: p.AttributeProbe,
        owner: p.AttributeProbe,
        name: str,
        descriptor: p.AttributeProbe,
        predecessor: p.AttributeProbe,
    ) -> t.Pair[bool, p.AttributeProbe | None]:
        """Use native super lookup to retain inherited-slot presence as data."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        index = next(
            position for position, ancestor in enumerate(ancestry) if ancestor is owner
        )
        if (
            not index
            or ancestry[index - 1] is not predecessor
            or name == "__class__"
            or type(descriptor) is not MemberDescriptorType
            or descriptor.__objclass__ is not owner
            or cls._class_namespace(owner).get(name) is not descriptor
        ):
            msg = "native optional slot has no exact inherited descriptor"
            raise ValueError(msg)
        builtins = sys.modules.get("builtins")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
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
            or type(super_type) is not type
        ):
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
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not super_type
            or type(accessor) is not WrapperDescriptorType
            or accessor.__objclass__ is not super_type
        ):
            msg = "native optional slot lacks the interpreter super implementation"
            raise ValueError(msg)
        root = vars(type)["__base__"].__get__(type(0), type(type(0)))
        if ancestry[-1] is not root:
            msg = "native optional slot lacks the interpreter object root"
            raise ValueError(msg)
        absent = root()
        stored = getter(super_type(predecessor, value), name, absent)
        current = vars(type)["__mro__"].__get__(type(value), type(type(value)))
        if (
            type(value) is not native
            or len(current) != len(ancestry)
            or any(left is not right for left, right in zip(current, ancestry, strict=True))
            or cls._class_namespace(owner).get(name) is not descriptor
        ):
            msg = "native optional slot context changed during observation"
            raise ValueError(msg)
        return (False, None) if stored is absent else (True, stored)

    @classmethod
    def _native_callable_instance(cls, value: p.AttributeProbe) -> bool:
        """Recognize only the declared CPython operator state intrinsics."""
        native = type(value)
        namespace = cls._class_namespace(native)
        descriptor = namespace.get("__call__")
        if (
            not (
                type(descriptor) is MethodDescriptorType
                or type(descriptor) is WrapperDescriptorType
            )
            or descriptor.__objclass__ is not native
            or "__name__" in namespace
        ):
            return False
        module_name = namespace.get("__module__")
        if type(module_name) is not str:
            return False
        supplier = sys.modules.get("_operator")
        return type(supplier) is ModuleType and any(
            vars(supplier).get(name) is native
            and vars(type)["__name__"].__get__(native, type(native)) == name
            and module_name == "operator"
            for name in ("itemgetter", "attrgetter", "methodcaller")
        )

    @classmethod
    def _native_operator_authority(cls) -> p.Result[bool]:
        """Admit the native reducer's complete import and constructor boundary."""
        result_type = r[bool]
        builtins = sys.modules.get("builtins")
        operator = sys.modules.get("operator")
        native_operator = sys.modules.get("_operator")
        functools = sys.modules.get("functools")
        native_functools = sys.modules.get("_functools")
        if sys.implementation.name != "cpython" or not all(
            type(module) is ModuleType
            for module in (
                builtins, operator, native_operator, functools, native_functools
            )
        ):
            return result_type.fail(
                "native operator state requires its loaded CPython suppliers",
            )
        importer = vars(builtins).get("__import__")
        observer = cls._class_namespace(cls)["_native_operator_state"].__func__
        if (
            type(importer) is not BuiltinFunctionType
            or importer.__self__ is not builtins
            or not cls._native_text(importer.__module__, "builtins")
            or not cls._native_text(importer.__name__, "__import__")
            or observer.__builtins__ is not vars(builtins)
        ):
            return result_type.fail(
                "native operator reduction has no admitted interpreter importer",
            )
        if (
            cls._language_singleton(vars(builtins).get("NotImplemented"))
            != "NotImplemented"
            or cls._language_singleton(vars(builtins).get("Ellipsis")) != "Ellipsis"
        ):
            return result_type.fail("language singleton builtin binding differs")
        partial = vars(native_functools).get("partial")
        if not cls._is_class(partial) or type(partial) is not type:
            return result_type.fail("native partial constructor is not registered")
        partial_namespace = cls._class_namespace(partial)
        constructor = partial_namespace.get("__new__")
        if (
            vars(functools).get("partial") is not partial
            or not cls._native_text(partial_namespace.get("__module__"), "functools")
            or vars(type)["__name__"].__get__(partial, type(partial)) != "partial"
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not partial
            or constructor.__name__ != "__new__"
        ):
            return result_type.fail(
                "native operator reduction has no admitted partial constructor",
            )
        for name in ("itemgetter", "attrgetter", "methodcaller"):
            native = vars(native_operator).get(name)
            if not cls._is_class(native) or type(native) is not type:
                return result_type.fail(f"native operator type is not registered: {name}")
            namespace = cls._class_namespace(native)
            reduction = namespace.get("__reduce__")
            if (
                vars(operator).get(name) is not native
                or not cls._native_text(namespace.get("__module__"), "operator")
                or vars(type)["__name__"].__get__(native, type(native)) != name
                or type(reduction) is not MethodDescriptorType
                or reduction.__objclass__ is not native
            ):
                return result_type.fail(
                    f"native operator reduction differs from its registered owner: {name}",
                )
        for name in ("builtins", "_operator", "_functools", "operator", "functools"):
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
            if elected.failure:
                return result_type.from_failure(elected)
            if name.startswith("_") or name == "builtins":
                if elected.value != Path(sys.executable).resolve():
                    return result_type.fail(
                        "native operator supplier is not the elected interpreter: "
                        f"{name}={elected.value}",
                    )
        return result_type.ok(value=True)

    @classmethod
    def _native_operator_state(cls, value: p.AttributeProbe) -> p.Result[p.AttributeProbe]:
        """Copy complete constructor state through authenticated native reducers."""
        authority = cls._native_operator_authority()
        if authority.failure:
            return r[p.AttributeProbe].from_failure(authority)
        if not cls._native_callable_instance(value):
            return r[p.AttributeProbe].fail(
                "native callable has no complete admitted constructor state",
            )
        native = type(value)
        descriptor = cls._class_namespace(native)["__reduce__"]
        # Native operator reducers retain C scalar distinctions that GC omits.
        # Their only dynamic constructor is the preflighted native partial.
        return r[p.AttributeProbe].ok(descriptor.__get__(value, native)())

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

    @staticmethod
    def _native_type(value: p.AttributeProbe | None, *expected: type) -> bool:
        """Compare type identity without invoking an authored metaclass hash."""
        native = type(value)
        return any(native is candidate for candidate in expected)

    @staticmethod
    def _native_text(value: p.AttributeProbe | None, expected: str) -> bool:
        """Reject authored equality before comparing native metadata text."""
        return type(value) is str and value == expected

    @classmethod
    def _class_identity(
        cls,
        value: p.AttributeProbe,
        supplier: str,
        binding: str,
    ) -> t.Pair[str, t.StrSequence]:
        """Keep class metadata distinct from its native instance descriptors."""
        module = vars(type)["__module__"].__get__(value, type(value))
        name = vars(type)["__qualname__"].__get__(value, type(value))
        if type(name) is not str:
            msg = "native lexical identity has non-text metadata"
            raise ValueError(msg)
        if type(module) is str:
            return f"{module}::{name}", (module,)
        native_descriptor = cls._native_type(
            module, GetSetDescriptorType, MemberDescriptorType
        )
        owner_in_mro = native_descriptor and any(
            ancestor is module.__objclass__
            for ancestor in vars(type)["__mro__"].__get__(value, type(value))
        )
        if owner_in_mro:
            registrations = tuple(
                sorted(
                    (supplier, attribute)
                    for supplier, exported in tuple(sys.modules.items())
                    if type(supplier) is str and type(exported) is ModuleType
                    for attribute, registered in vars(exported).items()
                    if type(attribute) is str and registered is value
                )
            )
            if not registrations:
                msg = "native class has no identity-matched module registration"
                raise ValueError(msg)
            return (
                dumps(("native_class", registrations, name)),
                tuple(dict.fromkeys(supplier for supplier, _name in registrations)),
            )
        metadata_kind = vars(type)["__qualname__"].__get__(
            type(module), type(type(module))
        )
        descriptor_owner = (
            vars(type)["__qualname__"].__get__(
                module.__objclass__, type(module.__objclass__)
            )
            if native_descriptor
            else ""
        )
        if type(metadata_kind) is not str or type(descriptor_owner) is not str:
            msg = "native diagnostic type identity is not text"
            raise ValueError(msg)
        msg = (
            "native lexical identity has non-text metadata: "
            f"qualname={name[:160]!r}; module_metadata_kind={metadata_kind[:160]!r}; "
            f"descriptor_owner={descriptor_owner[:160]!r}; owner_in_mro={owner_in_mro}; "
            f"binding={binding[:320]!r}; supplier={supplier[:160]!r}"
        )
        raise ValueError(msg)

    @classmethod
    def _symbol(cls, value: p.AttributeProbe) -> str:
        if cls._is_class(value):
            return cls._class_identity(value, "", "")[0]
        elif cls._native_type(value, FunctionType, BuiltinFunctionType):
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
        if module is None:
            module = "None"
        if type(module) is not str or type(name) is not str:
            msg = "native lexical identity has non-text metadata"
            raise ValueError(msg)
        return f"{module}::{name}"

    @classmethod
    def _language_singleton(cls, value: p.AttributeProbe | None) -> str | None:
        """Recognize language singletons independently of mutable builtin aliases."""
        if value is ...:
            export, identity = "Ellipsis", ...
        else:
            integer = type(0)
            comparison = cls._class_namespace(integer)["__eq__"]
            if (
                type(comparison) is not WrapperDescriptorType
                or comparison.__objclass__ is not integer
            ):
                msg = "language comparison has no native integer owner"
                raise ValueError(msg)
            identity = comparison.__get__(0, integer)("")
            if value is not identity:
                return None
            export = "NotImplemented"
        builtins = sys.modules.get("builtins")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(builtins) is not ModuleType
            or vars(builtins).get(export) is not identity
        ):
            msg = "language singleton differs from its elected builtin export"
            raise ValueError(msg)
        return export

    @classmethod
    def _typing_singleton(cls, value: p.AttributeProbe) -> str | None:
        """Prove CPython's object-header-only NoDefault intrinsic without calls."""
        owner = sys.modules.get("_typing")
        public = sys.modules.get("typing")
        if type(owner) is not ModuleType or vars(owner).get("NoDefault") is not value:
            return None
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "_typing"
        ).unwrap()
        native = type(value)
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(public) is not ModuleType
            or vars(public).get("NoDefault") is not value
            or type(native) is not type
        ):
            msg = "typing singleton lacks its elected interpreter exports"
            raise ValueError(msg)
        namespace = cls._class_namespace(native)
        constructor = namespace.get("__new__")
        reduction = namespace.get("__reduce__")
        if (
            not cls._native_text(
                vars(type)["__name__"].__get__(native, type(native)), "NoDefaultType"
            )
            or not cls._native_text(
                vars(type)["__module__"].__get__(native, type(native)), "builtins"
            )
            or vars(type)["__base__"].__get__(native, type(native)) is not object
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not native
            or not cls._native_text(constructor.__name__, "__new__")
            or type(reduction) is not MethodDescriptorType
            or reduction.__objclass__ is not native
            or not cls._native_text(reduction.__name__, "__reduce__")
        ):
            msg = "typing singleton differs from its static native type contract"
            raise ValueError(msg)
        for attribute in (
            "__basicsize__", "__itemsize__", "__dictoffset__", "__weakrefoffset__"
        ):
            descriptor = vars(type)[attribute]
            if descriptor.__get__(native, type(native)) != descriptor.__get__(
                object, type
            ):
                msg = "typing singleton has an unproved native payload"
                raise ValueError(msg)
        if any(
            cls._native_type(descriptor, MemberDescriptorType, GetSetDescriptorType)
            for descriptor in namespace.values()
        ):
            msg = "typing singleton has unproved native instance slots"
            raise ValueError(msg)
        return "_typing.NoDefault"

    @classmethod
    def _slice_state(
        cls, value: p.AttributeProbe | None
    ) -> (
        t.Triple[p.AttributeProbe | None, p.AttributeProbe | None, p.AttributeProbe | None]
        | None
    ):
        """Read the three retained references of the exact CPython slice type."""
        builtins = sys.modules.get("builtins")
        if type(builtins) is not ModuleType:
            msg = "native slice has no registered builtin supplier"
            raise ValueError(msg)
        native = vars(builtins).get("slice")
        if type(value) is not native:
            return None
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
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
            or type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not native
            or not cls._native_text(constructor.__name__, "__new__")
            or tuple(
                sorted(
                    name for name, descriptor in namespace.items()
                    if cls._native_type(
                        descriptor, MemberDescriptorType, GetSetDescriptorType
                    )
                )
            )
            != ("start", "step", "stop")
        ):
            msg = "native slice has unproved construction or storage"
            raise ValueError(msg)
        result = []
        for name in ("start", "stop", "step"):
            descriptor = namespace[name]
            if (
                type(descriptor) is not MemberDescriptorType
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
        """Read retained alias operands without populating its lazy parameters."""
        native = type(value)
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        if not any(owner is GenericAlias for owner in ancestry):
            return None
        supplier = sys.modules.get("types")
        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(
            "builtins"
        ).unwrap()
        if (
            sys.implementation.name != "cpython"
            or elected != Path(sys.executable).resolve()
            or type(supplier) is not ModuleType
            or vars(supplier).get("GenericAlias") is not GenericAlias
            or type(GenericAlias) is not type
            or not cls._native_text(
                vars(type)["__name__"].__get__(GenericAlias, type), "GenericAlias"
            )
            or not cls._native_text(
                vars(type)["__module__"].__get__(GenericAlias, type), "types"
            )
        ):
            msg = "generic alias lacks its elected interpreter type"
            raise ValueError(msg)
        namespace = cls._class_namespace(GenericAlias)
        constructor = namespace.get("__new__")
        if (
            type(constructor) is not BuiltinFunctionType
            or constructor.__self__ is not GenericAlias
            or not cls._native_text(constructor.__name__, "__new__")
        ):
            msg = "generic alias has no native constructor owner"
            raise ValueError(msg)
        result = []
        for name in ("__origin__", "__args__", "__unpacked__"):
            descriptor = namespace.get(name)
            if (
                type(descriptor) is not MemberDescriptorType
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
            owners = tuple(
                owner for owner in ancestry if owner is not GenericAlias
            )
            if not cls._python_storage_owners(owners):
                msg = "generic alias subclass has an unproved native payload"
                raise ValueError(msg)
            # Native operand slots and the subclass's Python storage both matter.
            result.append(("storage", cls._instance_storage(value)))
        return tuple(result)

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
        if (
            native is BuiltinFunctionType
            and value.__self__ is not None
            and type(value.__self__) is not ModuleType
            and not cls._is_class(value.__self__)
        ):
            msg = "native bound callable has no admitted receiver state"
            raise ValueError(msg)
        if cls._native_type(value, str, int, bool, type(None)):
            return dumps((native.__name__, value), ensure_ascii=True)
        if native is float:
            return dumps(("float", float.hex(value)))
        if native is bytes:
            return dumps(("bytes", b64encode(value).decode("ascii")))
        singleton = cls._language_singleton(value)
        if singleton is not None:
            return dumps(("language_singleton", singleton))
        typing_singleton = cls._typing_singleton(value)
        if typing_singleton is not None:
            return dumps((
                "native_typing_singleton",
                typing_singleton,
                ("_typing.NoDefault", "typing.NoDefault"),
            ))
        if id(value) in seen:
            return dumps(("cycle", cls._symbol(value)))
        seen |= {id(value)}
        slice_state = cls._slice_state(value)
        if slice_state is not None:
            return dumps((
                "slice",
                tuple(
                    cls._value(item, seen, construction=construction)
                    for item in slice_state
                ),
            ))
        if cls._native_type(value, list, set, dict) and not construction:
            return dumps(("mutable", native.__name__))
        if cls._native_type(value, tuple, list, set, frozenset):
            items = tuple(
                cls._value(item, seen, construction=construction) for item in value
            )
            return dumps((
                native.__name__,
                sorted(items) if cls._native_type(value, set, frozenset) else items,
            ))
        if native is MappingProxyType:
            return dumps((
                "mapping_proxy",
                cls._value(
                    cls._native_mapping_proxy_backing(value),
                    seen,
                    construction=construction,
                ),
            ))
        if native is dict:
            # Construction order is observable through native keyword arguments.
            return dumps((
                "dict",
                tuple(
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
                    if cls._native_type(
                        descriptor, MemberDescriptorType, GetSetDescriptorType
                    )
                    and descriptor.__objclass__ is CodeType
                ),
            ))
        if cls._native_type(
            value,
            MemberDescriptorType,
            GetSetDescriptorType,
            ClassMethodDescriptorType,
            MethodDescriptorType,
            WrapperDescriptorType,
        ):
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
        alias_state = cls._generic_alias_state(value)
        if alias_state is not None:
            return dumps((
                "generic_alias",
                cls._symbol(native),
                tuple(
                    (name, cls._value(stored, seen, construction=construction))
                    for name, stored in alias_state
                ),
            ))
        if cls._is_class(value) or cls._native_type(
            value, BuiltinFunctionType, ModuleType
        ):
            return dumps(("symbol", cls._symbol(value)))
        if not construction:
            return dumps(("instance", cls._symbol(native)))
        native_callable = cls._native_callable_instance(value)
        python_callable = cls._python_callable_implementation(value)
        if not native_callable and not cls._python_storage_class(native):
            raise ValueError(
                "native import operand has no complete storage witness: "
                + cls._symbol(native),
            )
        observed = tuple(
            (
                name,
                present,
                cls._value(stored, seen, construction=True) if present else None,
            )
            for name, present, stored in cls._instance_storage(value)
        )
        module_name = cls._class_namespace(native).get("__module__")
        module = sys.modules.get(module_name) if type(module_name) is str else None
        declared = (
            tuple(
                sorted(
                    name
                    for name, candidate in vars(module).items()
                    if type(name) is str and candidate is value
                )
            )
            if type(module) is ModuleType
            else ()
        )
        if native_callable:
            # Member slots supplement the complete constructor-state witness.
            return dumps((
                "native_callable_storage",
                cls._symbol(native),
                observed,
                cls._value(
                    cls._native_operator_state(value).unwrap(),
                    seen,
                    construction=True,
                ),
            ))
        if python_callable is not None:
            # Registered callable singletons retain their receiver state too.
            return dumps((
                "python_callable_storage", cls._symbol(native), observed, declared
            ))
        if native is not object or declared:
            return dumps(("storage", cls._symbol(native), observed, declared))
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
    def _remember_generated_descriptors(
        cls,
        owner: p.AttributeProbe,
        supplier: str,
        owners: t.MutableMappingKV[
            int, t.Triple[str, str, p.AttributeProbe | None]
        ],
    ) -> None:
        """Keep the actual class receiver while traversing native wrappers."""
        for attribute, descriptor in cls._class_namespace(owner).items():
            value = (
                descriptor.__func__
                if cls._native_type(descriptor, classmethod, staticmethod)
                else descriptor
            )
            if (
                type(value) is FunctionType
                and value.__code__.co_filename.startswith("<")
                and not value.__code__.co_filename.startswith("<frozen ")
            ):
                owners[id(value)] = (supplier, attribute, owner)

    @classmethod
    def capture(
        cls,
        names: t.StrSequence,
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe the complete native epoch without reconstructing class factories."""
        # Reject substituted importers or constructors before any source traversal.
        authority = cls._native_operator_authority()
        if authority.failure:
            return r[m.Infra.NativeImportObservation].from_failure(authority)
        with u.Infra.open_import_project(Path.cwd()) as project:
            return cls._capture(names, paths, project, {})

    @classmethod
    def _capture(
        cls,
        names: t.StrSequence,
        paths: t.SequenceOf[t.Pair[Path, Path]],
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe one epoch with one source graph and no cross-invocation cache."""
        origins: dict[str, Path] = {}
        sources: set[t.Triple[str, str, str]] = set()
        for supplier in (
            "builtins", "_operator", "_functools", "_typing",
            "operator", "functools", "typing", "types", "gc"
        ):
            elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(supplier)
            if elected.failure:
                return r[m.Infra.NativeImportObservation].from_failure(elected)
            sources.add((supplier, str(cls._source_path(elected.value, paths)), ""))
        evidence: list[m.Infra.NativeBindingEvidence] = []
        generated_owners: dict[
            int, t.Triple[str, str, p.AttributeProbe | None]
        ] = {}
        compiler_inputs: dict[Path, m.Cli.AtomicFileState] = {}
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
            for attribute, value in vars(module).items():
                if (
                    type(value) is FunctionType
                    and value.__code__.co_filename.startswith("<")
                    and not value.__code__.co_filename.startswith("<frozen ")
                    and (
                        id(value) not in generated_owners
                        or generated_owners[id(value)][2] is None
                    )
                ):
                    generated_owners[id(value)] = (name, attribute, None)
                elif cls._is_class(value):
                    class_supplier = vars(type)["__module__"].__get__(
                        value, type(value)
                    )
                    if type(class_supplier) is str:
                        cls._remember_generated_descriptors(
                            value, class_supplier, generated_owners
                        )
            mutable_globals = set()
            functions = [
                value for value in vars(module).values() if type(value) is FunctionType
            ]
            functions.extend(
                member.__func__
                if cls._native_type(member, classmethod, staticmethod)
                else member
                for value in vars(module).values()
                if cls._is_class(value)
                for member in cls._class_namespace(value).values()
                if cls._native_type(member, FunctionType, classmethod, staticmethod)
            )
            for function in functions:
                if type(function) is not FunctionType:
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
                or cls._native_type(value, FunctionType, BuiltinFunctionType, MethodType)
                or cls._native_type(value, property, classmethod, staticmethod)
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
            if cls._generic_alias_state(value) is not None:
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="generic_alias",
                        supplier="types",
                        name="GenericAlias",
                        qualname="GenericAlias",
                        operands=(("state", cls._value(value, construction=True)),),
                    )
                )
                pending.extend(
                    (edge, item, supplier, owner_source)
                    for edge, item in cls._executable_operands(binding, value)
                )
                continue
            if cls._native_type(value, classmethod, staticmethod):
                function = value.__func__
                # A native class target must re-enter the existing class proof.
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
                actual_supplier = vars(type)["__module__"].__get__(
                    value,
                    type(value),
                )
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer class has no native source supplier: {binding}",
                    )
                cls._remember_generated_descriptors(
                    value, actual_supplier, generated_owners
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
                    or cls._native_type(item, FunctionType, BuiltinFunctionType, MethodType)
                    or cls._native_type(item, property, classmethod, staticmethod)
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
            if cls._native_type(
                value,
                ClassMethodDescriptorType,
                MethodDescriptorType,
                WrapperDescriptorType,
            ):
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
            kind = vars(type)["__name__"].__get__(type(value), type(type(value)))
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
                        stored = slot.__get__(value, type(value))
                        operands.append((
                            attribute,
                            cls._value(
                                stored,
                                construction=True,
                            ),
                        ))
                        pending.extend(
                            (edge, item, supplier, owner_source)
                            for edge, item in cls._executable_operands(
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
                    or cls._native_type(item, FunctionType, BuiltinFunctionType)
                    or cls._native_wrapper_kind(item) is not None
                )
                continue
            if type(value) is not FunctionType:
                if cls._native_callable_instance(value):
                    # Native instances retain constructor state and nested code.
                    reduction = cls._native_operator_state(value)
                    if reduction.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(reduction)
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
                                cls._value(value, construction=True),
                            ),),
                        ),
                    )
                    pending.append((
                        f"{binding}.native_class",
                        native,
                        supplier,
                        owner_source,
                    ))
                    pending.extend(
                        (edge, item, supplier, owner_source)
                        for edge, item in cls._executable_operands(
                            f"{binding}.constructor",
                            reduction.value,
                        )
                    )
                    continue
                implementation = cls._python_callable_implementation(value)
                if implementation is not None:
                    native = type(value)
                    actual_supplier = vars(type)["__module__"].__get__(
                        native, type(native)
                    )
                    if type(actual_supplier) is not str:
                        return r[m.Infra.NativeImportObservation].fail(
                            f"Python callable receiver has no source supplier: {binding}",
                        )
                    origin = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                        actual_supplier,
                    )
                    if origin.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(origin)
                    source = str(cls._source_path(origin.value, paths))
                    evidence.append(
                        m.Infra.NativeBindingEvidence(
                            binding=binding,
                            kind="callable_instance",
                            supplier=actual_supplier,
                            name=vars(type)["__name__"].__get__(native, type(native)),
                            qualname=vars(type)["__qualname__"].__get__(
                                native, type(native)
                            ),
                            operands=(("storage", cls._value(value, construction=True)),),
                        ),
                    )
                    pending.extend((
                        (
                            f"{binding}.implementation",
                            implementation,
                            actual_supplier,
                            source,
                        ),
                        (f"{binding}.receiver_type", native, actual_supplier, source),
                    ))
                    pending.extend(
                        (edge, item, actual_supplier, source)
                        for field, present, stored in cls._instance_storage(value)
                        if present
                        for edge, item in cls._executable_operands(
                            f"{binding}.receiver.{field}", stored
                        )
                    )
                    continue
                if type(value) is not BuiltinFunctionType:
                    extension = cls._extension_callback(value, binding)
                    if extension.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(
                            extension
                        )
                    actual_supplier, native_name, qualified = extension.value
                    retained = cls._extension_state(
                        value, actual_supplier, qualified, binding
                    )
                    if retained.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(retained)
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
                            operands=(
                                (
                                    "native_type",
                                    cls._class_identity(
                                        type(value), actual_supplier, binding
                                    )[0],
                                ),
                                (
                                    "native_storage",
                                    cls._value(retained.value, construction=True),
                                ),
                            ),
                        ),
                    )
                    pending.extend(
                        (edge, item, actual_supplier, owner_source)
                        for edge, item in cls._executable_operands(
                            f"{binding}.native_storage", retained.value
                        )
                    )
                    continue
                if (
                    value.__self__ is not None
                    and type(value.__self__) is not ModuleType
                    and not cls._is_class(value.__self__)
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"native bound callable has no admitted receiver state: {binding}",
                    )
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
            compiler_generated = generated and not code.co_filename.startswith(
                "<frozen "
            )
            generated_operands: t.VariadicTuple[t.Pair[str, str]] = ()
            if compiler_generated:
                generated_owner = generated_owners.get(id(value))
                if generated_owner is None:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"generated function has no physical source owner: {binding}",
                    )
                source_supplier, source_attribute, receiver = generated_owner
                generated_proof = cls._generated_proof(
                    value,
                    source_supplier,
                    source_attribute,
                    receiver,
                    project,
                    witnesses,
                )
                if generated_proof.failure:
                    return r[m.Infra.NativeImportObservation].from_failure(
                        generated_proof
                    )
                actual_supplier, source_attribute, expected = generated_proof.value
                for state in expected.inputs:
                    previous = compiler_inputs.get(state.path)
                    if previous is not None and previous != state:
                        return r[m.Infra.NativeImportObservation].fail(
                            f"generated compiler input changed within observation: {state.path}"
                        )
                    compiler_inputs[state.path] = state
                    sources.add((
                        f"native_compiler::{state.path}",
                        str(cls._source_path(state.path, paths)),
                        "",
                    ))
                generated_operands = (
                    ("generated_attribute", source_attribute),
                    (
                        "generated_receiver",
                        ""
                        if receiver is None
                        else vars(type)["__qualname__"].__get__(
                            receiver, type(receiver)
                        ),
                    ),
                    (
                        "generated_inputs",
                        dumps(tuple(str(state.path) for state in expected.inputs)),
                    ),
                )
            else:
                actual_supplier = value.__globals__.get("__name__")
                if type(actual_supplier) is not str:
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer globals have no native supplier: {binding}",
                    )
                module = sys.modules.get(actual_supplier)
                if type(module) is not ModuleType or value.__globals__ is not vars(
                    module
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer globals have no native supplier: {binding}",
                    )
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
                    or cls._native_type(item, FunctionType, BuiltinFunctionType, MethodType)
                )
            )
            if compiler_generated:
                pending.extend(
                    (edge, item, actual_supplier, owner_source)
                    for name in code.co_names
                    if name in value.__globals__
                    for edge, item in cls._executable_operands(
                        f"{binding}.construction_global.{name}",
                        value.__globals__[name],
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
                    )
                    + generated_operands
                    + (
                        (
                            (
                                "anonymous_globals",
                                cls._value(value.__globals__, construction=True),
                            ),
                            (
                                "anonymous_builtins",
                                cls._value(value.__builtins__, construction=True),
                            ),
                        )
                        if compiler_generated
                        and value.__globals__ is not vars(sys.modules[actual_supplier])
                        else ()
                    ),
                ),
            )
        for witness in witnesses.values():
            previous = compiler_inputs.get(witness.source)
            if previous is not None and previous != witness.state:
                return r[m.Infra.NativeImportObservation].fail(
                    f"generated compiler witness changed: {witness.source}"
                )
            compiler_inputs[witness.source] = witness.state
            sources.add((
                f"native_compiler::{witness.source}",
                str(cls._source_path(witness.source, paths)),
                "",
            ))
        for state in compiler_inputs.values():
            current = u.Cli.atomic_read_binary_file_state(state.path, required=True)
            if current.failure:
                return r[m.Infra.NativeImportObservation].from_failure(current)
            if current.value != state:
                return r[m.Infra.NativeImportObservation].fail(
                    f"generated compiler source changed during observation: {state.path}"
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

    @classmethod
    def _generated_binding_current(
        cls,
        binding: m.Infra.NativeBindingEvidence,
        executed: CodeType,
        states: t.MappingKV[Path, m.Cli.AtomicFileReceipt],
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[bool]:
        """Re-derive a generated witness against its pinned physical receipts."""
        result_type = r[bool]
        metadata = dict(binding.operands)
        attribute = metadata.get("generated_attribute")
        receiver_name = metadata.get("generated_receiver")
        if type(attribute) is not str or type(receiver_name) is not str:
            return result_type.fail(
                f"generated binding lacks its physical compiler receipt: {binding.binding}"
            )
        module = sys.modules.get(binding.supplier)
        if type(module) is not ModuleType:
            return result_type.fail("generated compiler supplier is not loaded")
        receiver = None
        if receiver_name:
            receiver = module
            for component in receiver_name.split("."):
                namespace = (
                    vars(receiver)
                    if type(receiver) is ModuleType
                    else cls._class_namespace(receiver)
                    if cls._is_class(receiver)
                    else None
                )
                if namespace is None or component not in namespace:
                    return result_type.fail(
                        "generated class has no registered physical receiver"
                    )
                receiver = namespace[component]
            if not cls._is_class(receiver):
                return result_type.fail("generated receiver is not a native class")
        namespace = vars(module) if receiver is None else cls._class_namespace(receiver)
        value = namespace.get(attribute)
        if cls._native_type(value, classmethod, staticmethod):
            value = value.__func__
        if type(value) is not FunctionType:
            return result_type.fail("generated receipt has no native function")
        proved = cls._generated_proof(
            value, binding.supplier, attribute, receiver, project, witnesses
        )
        if proved.failure:
            return result_type.from_failure(proved)
        _supplier, _attribute, expected = proved.value
        if (
            executed != expected.code
            or cls._code_locations(executed) != cls._code_locations(expected.code)
            or metadata.get("generated_inputs")
            != dumps(tuple(str(state.path) for state in expected.inputs))
        ):
            return result_type.fail(
                f"generated receipt differs from its physical compiler: {binding.binding}"
            )
        for state in expected.inputs:
            receipt = states.get(state.path)
            if receipt is None:
                return result_type.fail(
                    f"generated compiler input is not pinned: {state.path}"
                )
            measured = u.Cli.atomic_read_binary_file_receipt(state.path, required=True)
            if measured.failure:
                return result_type.from_failure(measured)
            if measured.value != receipt:
                return result_type.fail(
                    f"generated compiler receipt changed: {state.path}"
                )
            with u.Cli.atomic_binary_file_reader(receipt) as reader:
                if reader.read_range(0, receipt.size) != state.content:
                    return result_type.fail(
                        f"generated compiler source differs from its receipt: {state.path}"
                    )
        return result_type.ok(value=True)

    @classmethod
    def authored_sources_current(
        cls,
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
    ) -> p.Result[bool]:
        """Authenticate physical and generated driver code before any effects."""
        authority = cls._native_operator_authority()
        if authority.failure:
            return authority
        with u.Infra.open_import_project(Path.cwd()) as project:
            witnesses: dict[str, m.Infra.NativeSourceWitness] = {}
            proved = cls._authored_sources_current(
                observed, inputs, project, witnesses
            )
            if proved.failure:
                return proved
            current = cls._witnesses_current(witnesses)
            return current if current.failure else proved

    @classmethod
    def _authored_sources_current(
        cls,
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[bool]:
        """Authenticate one call using its own closed graph and source witnesses."""
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
                generated = cls._generated_binding_current(
                    binding, executed, states, project, witnesses
                )
                if generated.failure:
                    return generated
                admitted += 1
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
