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


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

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
            descriptor = slots.get(attribute)
            if type(descriptor) not in {GetSetDescriptorType, MemberDescriptorType}:
                return r[t.Triple[str, str, str]].fail(
                    f"extension callback lacks a native metadata slot: {attribute}",
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
                "extension callback supplier is not a native extension",
            )
        namespace = vars(supplier)
        components = metadata["__qualname__"].split(".")
        for component in components[:-1]:
            owner = namespace.get(component)
            if not cls._is_class(owner):
                return r[t.Triple[str, str, str]].fail(
                    "extension callback has no registered lexical owner",
                )
            namespace = cls._class_namespace(owner)
        registered = tuple(
            name
            for name, candidate in namespace.items()
            if (
                candidate.__func__
                if type(candidate) in {classmethod, staticmethod}
                else candidate
            )
            is value
        )
        if not registered:
            return r[t.Triple[str, str, str]].fail(
                "extension callback differs from its registered descriptor: "
                f"supplier={metadata['__module__']}; "
                f"qualified={metadata['__qualname__']}; "
                f"actual_type={cls._symbol(native)}; "
                f"owner={'.'.join(components[:-1]) or metadata['__module__']}; "
                f"registered_type={cls._symbol(type(namespace.get(components[-1])))}",
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
            if type(item) in {FunctionType, BuiltinFunctionType}
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

    @classmethod
    def _symbol(cls, value: p.AttributeProbe) -> str:
        if cls._is_class(value):
            module = vars(type)["__module__"].__get__(value, type(value))
            name = vars(type)["__qualname__"].__get__(value, type(value))
        elif type(value) in {FunctionType, BuiltinFunctionType}:
            module = value.__module__
            name = value.__qualname__
            if (
                module is None
                and type(value) is BuiltinFunctionType
                and cls._is_class(value.__self__)
            ):
                module = vars(type)["__module__"].__get__(
                    value.__self__,
                    type(value.__self__),
                )
        elif type(value) is ModuleType:
            module, name = value.__name__, ""
        else:
            module = vars(type)["__module__"].__get__(
                type(value),
                type(type(value)),
            )
            name = vars(type)["__qualname__"].__get__(type(value), type(type(value)))
        if type(module) is str:
            return f"{module}::{name}"
        if type(module) in {GetSetDescriptorType, MemberDescriptorType}:
            owner = value if cls._is_class(value) else type(value)
            if module.__objclass__ is not owner:
                msg = "native module slot belongs to another symbolic type"
                raise TypeError(msg)
            return f"native-type::{name};module-slot={module.__name__}"
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
    ) -> str:
        """Encode native value slots without authored repr/hash/equality callbacks."""
        native = type(value)
        if any(native is kind for kind in (str, int, bool, type(None))):
            return dumps((native.__name__, value), ensure_ascii=True)
        if native is float:
            return dumps(("float", float.hex(value)))
        if native is bytes:
            return dumps(("bytes", b64encode(value).decode("ascii")))
        if value is Ellipsis:
            return dumps(("ellipsis",))
        if id(value) in seen:
            return dumps(("cycle", cls._symbol(value)))
        seen |= {id(value)}
        if any(native is kind for kind in (list, set, dict)) and not construction:
            return dumps(("mutable", native.__name__))
        if any(native is kind for kind in (tuple, list, set, frozenset)):
            items = tuple(
                cls._value(item, seen, construction=construction) for item in value
            )
            return dumps((
                native.__name__,
                sorted(items) if native is set or native is frozenset else items,
            ))
        if native is dict:
            return dumps((
                "dict",
                sorted(
                    (
                        cls._value(key, seen, construction=construction),
                        cls._value(item, seen, construction=construction),
                    )
                    for key, item in value.items()
                ),
            ))
        if native is MappingProxyType:
            if not construction:
                return dumps(("mutable", "mappingproxy"))
            supplier = sys.modules.get("gc")
            if (
                type(supplier) is not ModuleType
                or vars(supplier).get("get_referents") is not get_referents
                or type(get_referents) is not BuiltinFunctionType
                or get_referents.__module__ != "gc"
                or get_referents.__name__ != "get_referents"
            ):
                msg = "Native mappingproxy traversal has no interpreter owner"
                raise TypeError(msg)
            backing = get_referents(value)
            if len(backing) != 1 or type(backing[0]) is not dict:
                msg = "native mappingproxy does not contain an exact interpreter dict"
                raise TypeError(
                    msg,
                )
            return dumps((
                "mappingproxy",
                cls._value(backing[0], seen, construction=True),
            ))
        if native is CodeType:
            return dumps((
                "code",
                tuple(
                    (name, cls._value(descriptor.__get__(value, CodeType), seen))
                    for name, descriptor in sorted(vars(CodeType).items())
                    if type(descriptor) in {MemberDescriptorType, GetSetDescriptorType}
                    and descriptor.__objclass__ is CodeType
                ),
            ))
        if any(
            native is kind
            for kind in (
                MemberDescriptorType,
                GetSetDescriptorType,
                ClassMethodDescriptorType,
                MethodDescriptorType,
                WrapperDescriptorType,
            )
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
        if any(
            owner is GenericAlias
            for owner in vars(type)["__mro__"].__get__(native, type(native))
        ):
            storage = vars(GenericAlias)
            return dumps((
                "generic_alias",
                cls._symbol(native),
                cls._value(storage["__origin__"].__get__(value, native), seen),
                cls._value(storage["__args__"].__get__(value, native), seen),
            ))
        if (
            cls._is_class(value)
            or native is BuiltinFunctionType
            or native is ModuleType
        ):
            return dumps(("symbol", cls._symbol(value)))
        if not construction:
            return dumps(("instance", cls._symbol(native)))
        module_name = cls._class_namespace(native).get("__module__")
        module = sys.modules.get(module_name) if type(module_name) is str else None
        if type(module) is ModuleType:
            declared = tuple(
                name
                for name, candidate in vars(module).items()
                if type(name) is str and candidate is value
            )
            if declared:
                return dumps(("registered", module_name, sorted(declared)))
        observed: list[t.Pair[str, str]] = []
        ancestry = vars(type)["__mro__"].__get__(native, type(native))
        for owner in ancestry:
            namespace = cls._class_namespace(owner)
            for name, descriptor in sorted(namespace.items()):
                if (
                    type(descriptor) is MemberDescriptorType
                    or (name == "__dict__" and type(descriptor) is GetSetDescriptorType)
                ) and descriptor.__objclass__ is owner:
                    observed.append((
                        f"{cls._symbol(owner)}::{name}",
                        cls._value(
                            descriptor.__get__(value, native), seen, construction=True
                        ),
                    ))
        if observed:
            return dumps(("storage", cls._symbol(native), observed))
        return dumps(("native-symbol", cls._symbol(native)))

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
    def capture(
        cls,
        names: t.StrSequence,
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe the complete native epoch without reconstructing class factories."""
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        origins: dict[str, Path] = {}
        sources: set[t.Triple[str, str, str]] = set()
        evidence: list[m.Infra.NativeBindingEvidence] = []
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
            mutable_globals = set()
            functions = [
                value for value in vars(module).values() if type(value) is FunctionType
            ]
            functions.extend(
                member.__func__
                if type(member) in {classmethod, staticmethod}
                else member
                for value in vars(module).values()
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
                    operands=(("value", cls._value(value)),),
                )
                for key, value in sorted(vars(module).items())
                if type(value) is bool and key not in mutable_globals
            )
            pending.extend(
                (f"{name}::{key}", value, name, "")
                for key, value in sorted(vars(module).items())
                if cls._is_class(value)
                or type(value) in {FunctionType, BuiltinFunctionType, MethodType}
                or type(value) in {property, classmethod, staticmethod}
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
                            ("slots", cls._value(namespace.get("__slots__"))),
                        ),
                    ),
                )
                pending.extend(
                    (f"{binding}.{key}", item, actual_supplier, source)
                    for key, item in sorted(namespace.items())
                    if cls._is_class(item)
                    or type(item) in {FunctionType, BuiltinFunctionType, MethodType}
                    or type(item) in {property, classmethod, staticmethod}
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
            if type(value) in {
                ClassMethodDescriptorType,
                MethodDescriptorType,
                WrapperDescriptorType,
            }:
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
            kind = type(value).__name__
            if type(value) in {classmethod, staticmethod}:
                value = value.__func__
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
                        operands.append((
                            attribute,
                            cls._value(
                                slot.__get__(value, type(value)),
                                construction=True,
                            ),
                        ))
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
                    or type(item) in {FunctionType, BuiltinFunctionType}
                    or cls._native_wrapper_kind(item) is not None
                )
                continue
            if type(value) is not FunctionType:
                if type(value) is not BuiltinFunctionType:
                    # Only genuine C-extension callables carry the native
                    # metadata slots this proof reads; Python wrappers, bound
                    # methods and descriptor objects are classified elsewhere.
                    extension_types = (
                        MethodDescriptorType,
                        ClassMethodDescriptorType,
                        GetSetDescriptorType,
                        MemberDescriptorType,
                    )
                    if type(value) not in extension_types:
                        continue
                home_module = getattr(value, "__module__", None)
            home_root = (
                home_module.split(".")[0]
                if type(home_module) is str
                else ""
            )
                if home_root not in {
                    "flext",
                    "flext_core",
                    "flext_infra",
                    "flext_api",
                    "flext_cli",
                    "ai_hub",
                }:
                    # Ecosystem bindings (typing_inspection, pydantic
                    # internals, ...) are observations of third-party code:
                    # the fleet cannot authenticate their globals and the
                    # walk records nothing it cannot own.
                    continue
                    extension = cls._extension_callback(value)
                    if extension.failure:
                        return r[m.Infra.NativeImportObservation].from_failure(
                            extension
                        )
                    actual_supplier, native_name, qualified = extension.value
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
                            operands=(("native_type", cls._symbol(type(value))),),
                        ),
                    )
                    continue
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
            actual_supplier = value.__globals__.get("__name__")
            if isinstance(actual_supplier, str):
                module = sys.modules.get(actual_supplier)
                if module is None or (
                    not generated and value.__globals__ is not vars(module)
                ):
                    return r[m.Infra.NativeImportObservation].fail(
                        f"producer globals have no native supplier: {binding}",
                    )
            else:
                actual_supplier = supplier
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
                    or type(item) in {FunctionType, BuiltinFunctionType, MethodType}
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
                    ),
                ),
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
            if item.model_dump(exclude={"code", "operational"}) != native.model_dump(
                exclude={"code", "operational"}
            ):
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
            current = u.Cli.atomic_read_binary_file_receipt(
                receipt.path, required=receipt.device is not None
            )
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != receipt:
                return r[bool].fail(f"native source authority changed: {receipt.path}")
        from flext_infra.codegen.codegen_preconditions import (
            FlextInfraCodegenPreconditions,
        )

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
