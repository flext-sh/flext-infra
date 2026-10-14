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

from flext_infra import m, p, r, t, u


class FlextInfraWorkspaceNativeReference:
    """Observe code and binding topology without evaluating authored expressions."""

    @staticmethod
    def _class_namespace(value: p.AttributeProbe) -> t.MappingKV[str, p.AttributeProbe]:
        return vars(type)["__dict__"].__get__(value, type(value))

    @classmethod
    def _source_witness(
        cls,
        name: str,
        project: p.Infra.RopeProject,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
    ) -> p.Result[m.Infra.NativeSourceWitness]:
        """Capture and compile each supplier once without importing or replaying it."""
        if name in witnesses:
            return r[m.Infra.NativeSourceWitness].ok(witnesses[name])
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            return r[m.Infra.NativeSourceWitness].fail(
                f"producer source supplier is not registered: {name}",
            )
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        elected = FlextInfraWorkspaceEnvironmentProvenance._module_source(name)
        if elected.failure:
            return r[m.Infra.NativeSourceWitness].from_failure(elected)
        source = elected.value
        if module.__spec__ is not None and module.__spec__.origin == "frozen":
            source = Path(module.__spec__.loader_state.filename).absolute()
        captured = u.Cli.atomic_read_binary_file_state(source, required=True)
        if captured.failure:
            return r[m.Infra.NativeSourceWitness].from_failure(captured)
        state = captured.value
        if state.content is None:
            return r[m.Infra.NativeSourceWitness].fail(
                f"producer captured source bytes are absent: {name}",
            )
        no_project = u.Infra.runtime_callable(
            "rope.base.project",
            "get_no_project",
        )()
        resource = u.Infra.runtime_callable(
            "rope.base.resources",
            "File",
        )(no_project, str(source))
        if not isinstance(resource, p.Infra.RopeFile):
            msg = "Native source resource violates Rope's file contract"
            raise TypeError(msg)
        native = u.Infra.build_string_module(
            project,
            state.content.decode("utf-8"),
            resource=resource,
            force_errors=True,
        )
        if not isinstance(native, p.Infra.RopeSourceModule):
            msg = "Native source module lost its shared Rope graph"
            raise TypeError(msg)
        root = native.get_scope()
        if not isinstance(root, p.Infra.RopeScope):
            msg = "Native source module has no semantic scope"
            raise TypeError(msg)
        scopes: dict[str, p.Infra.RopeScope] = {}
        pending = [(root, "")]
        while pending:
            current, qualified = pending.pop()
            if qualified in scopes:
                return r[m.Infra.NativeSourceWitness].fail(
                    f"producer declaration identity is ambiguous: {name}::{qualified}",
                )
            scopes[qualified] = current
            for child in current.get_scopes():
                component = child.pyobject.get_name()
                prefix = (
                    f"{qualified}.<locals>"
                    if current.get_kind() == "Function"
                    else qualified
                )
                child_name = f"{prefix}.{component}" if prefix else component
                pending.append((child, child_name))
        compiled = compile(state.content, str(source), "exec", dont_inherit=True)
        if module.__spec__ is not None and module.__spec__.origin == "frozen":
            compiled = FrozenImporter.get_code(module.__spec__.name)
        if not isinstance(compiled, CodeType):
            msg = "Native compiler did not return a Python code object"
            raise TypeError(msg)
        witness = m.Infra.NativeSourceWitness(
            source=source,
            state=state,
            module=native,
            code=compiled,
            scopes=scopes,
            statements=u.Infra.logical_statements(native.source_code),
            finder=u.Infra.semantic_finder(native),
        )
        witnesses[name] = witness
        return r[m.Infra.NativeSourceWitness].ok(witness)

    @staticmethod
    def _compiled_function(
        witness: m.Infra.NativeSourceWitness,
        code: p.Infra.NativeCodeIdentity,
    ) -> p.Result[bool]:
        """Compare a physical executable against the captured module compilation."""
        if not isinstance(witness.code, CodeType):
            msg = "Source witness contains no native compiler result"
            raise TypeError(msg)
        pending = [witness.code]
        candidates = []
        while pending:
            current = pending.pop()
            if current.co_qualname == code.co_qualname:
                candidates.append(current)
            pending.extend(
                value for value in current.co_consts if isinstance(value, CodeType)
            )
        if not any(candidate == code for candidate in candidates):
            return r[bool].fail(
                "producer executable differs from captured native compilation: "
                f"{code.co_qualname}; source={witness.source}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _source_binding(
        cls,
        scope: p.Infra.RopeScope,
        expression: str,
        witnesses: t.MutableMappingKV[str, m.Infra.NativeSourceWitness],
        project: p.Infra.RopeProject,
    ) -> p.Result[p.AttributeProbe]:
        """Bridge a native lexical identity to its statically stored runtime value."""
        binding = u.Infra.expression_name(scope, expression)
        if binding is None:
            return r[p.AttributeProbe].fail(
                f"producer has no native lexical source binding: {expression}",
            )
        target = binding.get_object()
        provider = target.get_module()
        if provider is None:
            if isinstance(target, p.Infra.RopeBuiltinClass):
                return r[p.AttributeProbe].ok(target.builtin)
            return r[p.AttributeProbe].fail(
                f"producer binding has no native declaration supplier: {expression}",
            )
        provider_name = provider.get_name()
        registered = sys.modules.get(provider_name)
        if type(registered) is not ModuleType:
            return r[p.AttributeProbe].fail(
                f"producer source binding supplier is not loaded: {provider_name}",
            )
        declaration = target.get_scope()
        if declaration is None:
            if isinstance(target, p.Infra.RopeBuiltinClass):
                return r[p.AttributeProbe].ok(target.builtin)
            return r[p.AttributeProbe].fail(
                f"producer lexical value has no native declaration scope: {expression}",
            )
        components = []
        current = declaration
        while current.parent is not None:
            components.append(current.pyobject.get_name())
            current = current.parent
        value: p.AttributeProbe = registered
        for component in reversed(components):
            namespace = (
                cls._class_namespace(value)
                if cls._is_class(value)
                else vars(value)
                if type(value) is ModuleType
                else None
            )
            if namespace is None or component not in namespace:
                return r[p.AttributeProbe].fail(
                    f"producer source binding has no static runtime slot: {expression}",
                )
            value = namespace[component]
        if cls._is_class(value):
            if type.__getattribute__(value, "__module__") != provider_name:
                return r[p.AttributeProbe].fail(
                    f"producer class supplier differs from native source: {expression}",
                )
        elif type(value) is FunctionType:
            captured = cls._source_witness(provider_name, project, witnesses)
            if captured.failure:
                return r[p.AttributeProbe].from_failure(captured)
            authenticated = cls._compiled_function(captured.value, value.__code__)
            if authenticated.failure:
                return r[p.AttributeProbe].from_failure(authenticated)
        return r[p.AttributeProbe].ok(value)

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

    @staticmethod
    def _code_locations(code: CodeType) -> str:
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
                or FlextInfraWorkspaceNativeReference._code_locations(actual_code)
                != FlextInfraWorkspaceNativeReference._code_locations(expected_code)
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
