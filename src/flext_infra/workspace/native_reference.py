"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import marshal
import sys
from base64 import b64decode, b64encode
from importlib.machinery import FrozenImporter
from json import dumps
from pathlib import Path
from types import (
    BuiltinFunctionType,
    CodeType,
    FunctionType,
    GenericAlias,
    GetSetDescriptorType,
    MemberDescriptorType,
    ModuleType,
    UnionType,
)

from flext_infra import m, p, r, t


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

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
            module = type.__getattribute__(value, "__module__")
            name = type.__getattribute__(value, "__qualname__")
        elif type(value) in {FunctionType, BuiltinFunctionType}:
            module = value.__module__
            name = value.__qualname__
        elif type(value) is ModuleType:
            module, name = value.__name__, ""
        else:
            module = type.__getattribute__(type(value), "__module__")
            name = type.__getattribute__(type(value), "__qualname__")
        return f"{module}::{name}"

    @classmethod
    def _value(
        cls,
        value: p.AttributeProbe | None,
        seen: frozenset[int] = frozenset(),
    ) -> str:
        """Encode native value slots without authored repr/hash/equality callbacks."""
        native = type(value)
        if native in {str, int, bool, type(None)}:
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
        if native in {tuple, list, set, frozenset}:
            items = tuple(cls._value(item, seen) for item in value)
            return dumps((
                native.__name__,
                sorted(items) if native in {set, frozenset} else items,
            ))
        if native is dict:
            return dumps((
                "dict",
                sorted(
                    (cls._value(key, seen), cls._value(item, seen))
                    for key, item in value.items()
                ),
            ))
        if native is CodeType:
            return dumps(("code", b64encode(marshal.dumps(value)).decode("ascii")))
        if native is FunctionType:
            return dumps((
                "function",
                cls._symbol(value),
                cls._value(value.__code__, seen),
                cls._value(value.__defaults__, seen),
                cls._value(value.__kwdefaults__, seen),
                cls._value(
                    tuple(cell.cell_contents for cell in value.__closure__ or ()),
                    seen,
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
        if cls._is_class(value) or native in {BuiltinFunctionType, ModuleType}:
            return dumps(("symbol", cls._symbol(value)))
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
                        cls._value(descriptor.__get__(value, native), seen),
                    ))
        if observed:
            return dumps(("storage", cls._symbol(native), observed))
        for module_name in (type.__getattribute__(native, "__module__"),):
            module = sys.modules.get(module_name)
            if type(module) is ModuleType:
                declared = tuple(
                    name
                    for name, candidate in vars(module).items()
                    if type(name) is str and candidate is value
                )
                if declared:
                    return dumps(("registered", module_name, sorted(declared)))
        raise ValueError(
            "native import operand has no callback-free storage or registered binding: "
            + cls._symbol(native),
        )

    @staticmethod
    def _relocate_code(
        code: CodeType,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> CodeType:
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

    @classmethod
    def capture(
        cls,
        names: t.StrSequence,
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Capture already-imported native definitions once for the complete epoch."""
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
                return r[m.Infra.NativeImportReference].fail(
                    f"native reference lacks an elected module: {name}",
                )
            origin = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
            if origin.failure:
                return r[m.Infra.NativeImportReference].from_failure(origin)
            origins[name] = cls._source_path(origin.value, paths)
            sources.add((name, str(origins[name]), ""))
            pending.extend(
                (f"{name}::{key}", value, name, "")
                for key, value in sorted(vars(module).items())
                if cls._is_class(value)
                or type(value) in {FunctionType, BuiltinFunctionType}
                or type(value) in {property, classmethod, staticmethod}
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
                actual_supplier = type.__getattribute__(value, "__module__")
                origin = origins.get(actual_supplier)
                if origin is None:
                    observed = FlextInfraWorkspaceEnvironmentProvenance._module_source(
                        actual_supplier,
                    )
                    if observed.failure:
                        return r[m.Infra.NativeImportReference].from_failure(observed)
                    origin = origins[actual_supplier] = cls._source_path(
                        observed.value,
                        paths,
                    )
                source = str(origin)
                qualname = type.__getattribute__(value, "__qualname__")
                sources.add((f"{actual_supplier}::{qualname}", source, ""))
                evidence.append(
                    m.Infra.NativeBindingEvidence(
                        binding=binding,
                        kind="class",
                        supplier=actual_supplier,
                        name=type.__getattribute__(value, "__name__"),
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
                                cls._value(namespace.get("__annotations__")),
                            ),
                            (
                                "dataclass_parameters",
                                cls._value(namespace.get("__dataclass_params__")),
                            ),
                            (
                                "dataclass_fields",
                                cls._value(namespace.get("__dataclass_fields__")),
                            ),
                            ("slots", cls._value(namespace.get("__slots__"))),
                        ),
                    ),
                )
                pending.extend(
                    (f"{binding}.{key}", item, actual_supplier, source)
                    for key, item in sorted(namespace.items())
                    if cls._is_class(item)
                    or type(item) in {FunctionType, BuiltinFunctionType}
                    or type(item) in {property, classmethod, staticmethod}
                )
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
            kind = type(value).__name__
            if type(value) in {classmethod, staticmethod}:
                value = value.__func__
            if type(value) is not FunctionType:
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
            code = cls._relocate_code(value.__code__, paths)
            generated = code.co_filename.startswith("<")
            actual_supplier = value.__globals__.get("__name__")
            if isinstance(actual_supplier, str):
                module = sys.modules.get(actual_supplier)
                if module is None or (
                    not generated and value.__globals__ is not vars(module)
                ):
                    return r[m.Infra.NativeImportReference].fail(
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
                    return r[m.Infra.NativeImportReference].from_failure(observed)
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
            wrapped = vars(value).get("__wrapped__")
            if wrapped is not None and not any(
                item is wrapped for item in (*nonlocals.values(), *globals_used)
            ):
                return r[m.Infra.NativeImportReference].fail(
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
                        ("keyword_defaults", cls._value(value.__kwdefaults__)),
                        ("closure", cls._value(nonlocals)),
                        ("wrapped", cls._value(wrapped)),
                    ),
                ),
            )
        return r[m.Infra.NativeImportReference].ok(
            m.Infra.NativeImportReference(
                runtime=Path(sys.executable).resolve(),
                modules=tuple(names),
                sources=tuple(sorted(sources)),
                bindings=tuple(sorted(evidence, key=lambda item: item.binding)),
            ),
        )

    @staticmethod
    def compare(
        observed: m.Infra.NativeImportReference,
        reference: m.Infra.NativeImportReference,
    ) -> p.Result[bool]:
        """Compare executable code using CPython equality, never serialized hashes."""
        if (
            observed.runtime != reference.runtime
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
            ):
                return r[bool].fail(
                    f"producer executed code differs from native import: {item.binding}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def authored_sources_current(
        observed: m.Infra.NativeImportReference,
        inputs: t.SequenceOf[m.Cli.AtomicFileState],
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
                    state = states.get(Path(executed.co_filename))
                    if state is None or state.content is None:
                        return r[bool].fail(
                            f"authored producer source is not pinned: {binding.binding}",
                        )
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
            if not any(code == executed for code in compiled[key]):
                return r[bool].fail(
                    f"authored producer code differs from pinned native source: {binding.binding}",
                )
            admitted += 1
        if not admitted:
            return r[bool].fail("cold producer authority has no authored driver code")
        return r[bool].ok(value=True)
