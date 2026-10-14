"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import marshal
import sys
from base64 import b64decode, b64encode
from inspect import getattr_static, getclosurevars, isbuiltin, isclass, isfunction
from json import dumps
from pathlib import Path
from types import CodeType, MemberDescriptorType, ModuleType

from flext_infra import m, p, r, t


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

    @staticmethod
    def _symbol(value: p.AttributeProbe) -> str:
        if isclass(value):
            module = type.__getattribute__(value, "__module__")
            name = type.__getattribute__(value, "__qualname__")
        elif isfunction(value) or isbuiltin(value):
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
        fields = getattr_static(native, "__dataclass_fields__", None)
        if type(fields) is dict and not isclass(value):
            observed = []
            for name in fields:
                item = getattr_static(value, name)
                if type(item) is MemberDescriptorType:
                    item = item.__get__(value, native)
                observed.append((name, cls._value(item, seen)))
            return dumps(("dataclass", cls._symbol(native), observed))
        # Runtime settings/model instances have their own validation authority.
        # Their identity here is their native type, never a frozen state dump.
        return dumps(("binding", cls._symbol(value)))

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
                if isclass(value)
                or isfunction(value)
                or isbuiltin(value)
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
            if isclass(value):
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
                        ),
                    ),
                )
                pending.extend(
                    (f"{binding}.{key}", item, actual_supplier, source)
                    for key, item in sorted(namespace.items())
                    if isclass(item)
                    or isfunction(item)
                    or isbuiltin(item)
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
            if not isfunction(value):
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
            closure = getclosurevars(value)
            wrapped = vars(value).get("__wrapped__")
            if wrapped is not None and not any(
                item is wrapped
                for item in (*closure.nonlocals.values(), *closure.globals.values())
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
                        ("closure", cls._value(closure.nonlocals)),
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
            ):
                return r[bool].fail(
                    f"producer executed code differs from native import: {item.binding}"
                )
        return r[bool].ok(value=True)
