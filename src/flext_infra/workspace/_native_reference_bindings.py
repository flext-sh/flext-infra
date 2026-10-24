"""Capture of classes, descriptors, wrappers and native callables.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from json import dumps
from types import FunctionType, GetSetDescriptorType, MemberDescriptorType, MethodType
from weakref import ReferenceType

from flext_infra import m, p, r, t
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace._native_reference_values import (
    FlextInfraWorkspaceNativeReferenceValuesMixin,
)


class FlextInfraWorkspaceNativeReferenceBindingsMixin(
    FlextInfraWorkspaceNativeReferenceValuesMixin
):
    @classmethod
    def _capture_class_body(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeType,
        binding: str,
        identity: t.Quad[str, str, str, t.MappingKV[str, t.Infra.NativeOperand]],
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Observe a source class body before enqueuing its executable children.

        Returns:
            The first declaration failure or the complete native class evidence.

        """
        supplier, source, qualname, namespace = identity
        declarations = cls._declared_class_names(
            supplier, context.origins[supplier], qualname, namespace, context.compiled
        )
        if declarations.failure:
            return r[bool].from_failure(declarations)
        declaration = cls._class_declaration(namespace, declarations.value)
        writers = cls._class_state_writers(
            value, namespace, frozenset(declaration), instructions
        )
        operational = frozenset(name for _, _, fields in writers for name in fields)
        context.pending.extend(
            (f"{binding}.{name}", writer, supplier, source, "execution")
            for name, writer, _ in writers
        )
        observe_value = partial(
            cls._value,
            context=context,
            binding=context.binding_context,
        )
        # These are compiler outputs under observation, never expected inputs.
        # The isolated import supplies their independent expected values.
        generated_data = tuple(
            (name, observe_value(namespace[name], construction=True))
            for name in ("__dataclass_fields__", "__dataclass_params__")
            if name in namespace
        )
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=binding,
                kind="class",
                supplier=supplier,
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
                            namespace.get("__annotations__", {}), construction=True
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
                    ("generated_data", dumps(generated_data)),
                ),
                operational=tuple(
                    (name, observe_value(declaration[name]))
                    for name in sorted(operational)
                ),
            )
        )
        cls._enqueue_class_members(context, value, binding, identity)
        return r[bool].ok(value=True)

    @classmethod
    def _capture_class(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeType,
        binding: str,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Authenticate a class supplier before observing its source declaration.

        Returns:
            The first supplier failure or a fully observed native class.

        """
        namespace = cls._class_namespace(value)
        supplier = cls._type_attr("__module__", value, type(value))
        if type(supplier) is not str:
            return r[bool].fail(
                f"producer class has no native source supplier: {binding}",
            )
        cls._remember_generated_descriptors(value, supplier, context.generated_owners)
        origin = context.origins.get(supplier)
        if origin is None:
            observed = FlextInfraWorkspaceEnvironmentProvenance.module_source(supplier)
            if observed.failure:
                return r[bool].from_failure(observed)
            origin = context.origins[supplier] = observed.value
        source = str(cls._source_path(origin, context.paths))
        qualname = cls._type_attr("__qualname__", value, type(value))
        if type(qualname) is not str:
            return r[bool].fail(
                f"producer class has no native qualified name: {binding}",
            )
        context.sources.add((f"{supplier}::{qualname}", source, ""))
        return cls._capture_class_body(
            context,
            value,
            binding,
            (supplier, source, qualname, namespace),
            instructions,
        )

    @classmethod
    def _capture_function_binding(
        cls,
        context: m.Infra.NativeObservationContext,
        value: p.Infra.FunctionDescriptor,
    ) -> p.Result[bool]:
        """Observe an exact classmethod or staticmethod and enqueue its function.

        Returns:
            The original category evidence or its first native failure.

        """
        function = value.__func__
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind=cls._type_attr("__name__", type(value), type(type(value))),
                supplier=context.supplier,
                name="",
                qualname="",
                operands=(("function", cls._symbol(function)),),
            ),
        )
        context.pending.append((
            f"{context.binding}.function",
            function,
            context.supplier,
            context.owner_source,
            "execution",
        ))
        return r[bool].ok(value=True)

    @classmethod
    def _capture_bound_method(
        cls,
        context: m.Infra.NativeObservationContext,
        value: MethodType,
    ) -> p.Result[bool]:
        """Observe a bound method before its function and class receiver.

        Returns:
            The original category evidence or its first native failure.

        """
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind="bound_method",
                supplier=context.supplier,
                name=value.__func__.__name__,
                qualname=value.__func__.__qualname__,
                operands=(("receiver", cls._symbol(value.__self__)),),
            )
        )
        context.pending.append((
            f"{context.binding}.function",
            value.__func__,
            context.supplier,
            context.owner_source,
            "execution",
        ))
        if cls._is_class(value.__self__):
            context.pending.append((
                f"{context.binding}.receiver",
                value.__self__,
                context.supplier,
                context.owner_source,
                "execution",
            ))
        return r[bool].ok(value=True)

    @classmethod
    def _capture_property(
        cls,
        context: m.Infra.NativeObservationContext,
        value: property,
    ) -> p.Result[bool]:
        """Observe property accessor presence before queuing actual accessors.

        Returns:
            The original category evidence or its first native failure.

        """
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind="property",
                supplier=context.supplier,
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
        context.pending.extend(
            (
                f"{context.binding}.{name}",
                accessor,
                context.supplier,
                context.owner_source,
                "execution",
            )
            for name, accessor in (
                ("get", value.fget),
                ("set", value.fset),
                ("delete", value.fdel),
            )
            if accessor is not None
        )
        return r[bool].ok(value=True)

    @classmethod
    def _capture_descriptor(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeDescriptor,
    ) -> p.Result[bool]:
        """Authenticate a native descriptor supplier and enqueue its actual owner.

        Returns:
            The original category evidence or its first native failure.

        """
        owner = value.__objclass__
        actual_supplier = cls._type_attr("__module__", owner, type(owner))
        if type(actual_supplier) is not str:
            return r[bool].fail(
                f"native descriptor owner has no source supplier: {context.binding}",
            )
        elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
            actual_supplier,
        )
        if elected.failure:
            return r[bool].from_failure(elected)
        context.sources.add((
            f"{actual_supplier}::{value.__qualname__}",
            str(cls._source_path(elected.value, context.paths)),
            "",
        ))
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind=cls._type_attr("__name__", type(value), type(type(value))),
                supplier=actual_supplier,
                name=value.__name__,
                qualname=value.__qualname__,
                operands=(("receiver", cls._symbol(owner)),),
            ),
        )
        context.pending.append((
            f"{context.binding}.receiver",
            owner,
            actual_supplier,
            context.owner_source,
            "storage_type",
        ))
        return r[bool].ok(value=True)

    @classmethod
    def _capture_generic_alias(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeOperand,
    ) -> p.Result[bool]:
        """Observe native alias construction and its actual executable operands.

        Returns:
            The original category evidence or its first native failure.

        """
        observe_value = partial(
            cls._value, context=context, binding=context.binding_context
        )
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
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
        context.pending.extend(
            (edge, item, context.supplier, context.owner_source, role)
            for edge, item, role in cls._executable_operands(
                context.binding, value, role=context.role
            )
        )
        return r[bool].ok(value=True)

    @classmethod
    def _capture_wrapper(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeOperand,
        kind: str,
        wrapper_kind: str,
    ) -> p.Result[bool]:
        """Authenticate a native wrapper, its storage and its actual wrapped function.

        Returns:
            The original category evidence or its first native failure.

        """
        observe_value = partial(
            cls._value, context=context, binding=context.binding_context
        )
        function = cls._native_wrapper_function(value, wrapper_kind)
        if function.failure:
            return r[bool].from_failure(function)
        namespace = cls._class_namespace(type(value))
        storage = namespace.get("__dict__")
        if not cls._is_native(
            storage, GetSetDescriptorType
        ) or storage.__objclass__ is not type(value):
            return r[bool].fail(
                f"native wrapper has no interpreter-owned attributes: "
                f"{context.binding}",
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
                    return r[bool].fail(
                        f"native partial lacks its {attribute} slot: {context.binding}",
                    )
                operands.append((
                    attribute,
                    observe_value(
                        slot.__get__(value, slot.__objclass__),
                        construction=True,
                        binding=(
                            f"{context.incoming}.{attribute}; body={context.binding}; "
                            f"supplier={context.supplier}; "
                            f"callable={cls._symbol(function.value)}"
                        ),
                    ),
                ))
                stored = slot.__get__(value, slot.__objclass__)
                context.pending.extend(
                    (
                        operand_binding,
                        item,
                        context.supplier,
                        context.owner_source,
                        role,
                    )
                    for operand_binding, item, role in cls._executable_operands(
                        f"{context.binding}.{attribute}",
                        stored,
                    )
                )
        else:
            cache_state = cls._native_cache_state(value)
            if cache_state.failure:
                return r[bool].from_failure(cache_state)
            operational = (("cache", cache_state.value),)
        context.evidence.append(
            m.Infra.NativeBindingEvidence.model_validate({
                "binding": context.binding,
                "kind": f"{kind}:{wrapper_kind}",
                "supplier": "_functools",
                "name": attributes.get("__name__", ""),
                "qualname": attributes.get("__qualname__", ""),
                "operands": tuple(operands),
                "operational": operational,
            }),
        )
        context.pending.append((
            f"{context.binding}.native_function",
            function.value,
            context.supplier,
            context.owner_source,
            "execution",
        ))
        context.pending.extend(
            (
                f"{context.binding}.attributes.{key}",
                item,
                context.supplier,
                context.owner_source,
                "storage_type",
            )
            for key, item in sorted(attributes.items())
            if cls._is_class(item)
            or type(item) is FunctionType
            or cls._native_builtin(item)
            or cls._native_wrapper_kind(item) is not None
            if not context.lexical or key == "__wrapped__"
        )
        return r[bool].ok(value=True)

    @classmethod
    def _capture_native_callable(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeOperand,
        kind: str,
    ) -> p.Result[bool]:
        """Observe native callable storage, registered callbacks and receiver inputs.

        Returns:
            The original category evidence or its first native failure.

        """
        observe_value = partial(
            cls._value, context=context, binding=context.binding_context
        )
        if type(value) is ReferenceType:
            # Calling an exact interpreter weak reference only dereferences it
            # natively; a live executable referent continues the graph as its own
            # edge, while data referents (registries, self references) end here.
            referent = value()
            context.evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=context.binding,
                    kind="weak_reference",
                    supplier="weakref",
                    name="ref",
                    qualname="ReferenceType",
                    operands=(("referent", "dead" if referent is None else "live"),),
                ),
            )
            if referent is not None and cls._executable_binding(referent):
                context.pending.append((
                    f"{context.binding}.referent",
                    referent,
                    context.supplier,
                    context.owner_source,
                    "execution",
                ))
            return r[bool].ok(value=True)
        native_builtin = value if cls._native_builtin(value) else None
        if cls._native_callable_instance(value) or cls._python_callable_instance(value):
            native = type(value)
            context.evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=context.binding,
                    kind="callable_instance",
                    supplier=vars(type)["__module__"].__get__(native, type(native)),
                    name=vars(type)["__name__"].__get__(native, type(native)),
                    qualname=vars(type)["__qualname__"].__get__(native, type(native)),
                    operands=(
                        (
                            "storage",
                            observe_value(value, construction=True),
                        ),
                    ),
                ),
            )
            context.pending.append((
                f"{context.binding}.native_class",
                native,
                context.supplier,
                context.owner_source,
                "execution",
            ))
            return r[bool].ok(value=True)
        if native_builtin is None:
            extension = cls._extension_callback(value, context.binding)
            if extension.failure:
                return r[bool].fail(
                    f"{extension.error}; binding={context.binding}; "
                    f"binding_supplier={context.supplier}; "
                    f"native_type={cls._symbol(type(value))}; "
                    f"native_ancestry={
                        tuple(
                            cls._symbol(owner) for owner in cls._native_mro(type(value))
                        )
                    }"
                )
            actual_supplier, native_name, qualified = extension.value
            origin = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                actual_supplier,
            )
            if origin.failure:
                return r[bool].from_failure(origin)
            context.sources.add((
                f"{actual_supplier}::{qualified}",
                str(cls._source_path(origin.value, context.paths)),
                "",
            ))
        else:
            actual_supplier, _, qualified = cls._symbol(native_builtin).partition("::")
            native_name = native_builtin.__name__
            elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(
                actual_supplier,
            )
            if elected.failure:
                return r[bool].from_failure(elected)
            context.sources.add((
                f"{actual_supplier}::{qualified}",
                str(cls._source_path(elected.value, context.paths)),
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
                context.pending.append((
                    f"{context.binding}.receiver_type",
                    type(receiver),
                    actual_supplier,
                    context.owner_source,
                    "storage_type",
                ))
                context.pending.extend(
                    (edge, item, actual_supplier, context.owner_source, role)
                    for edge, item, role in cls._executable_operands(
                        f"{context.binding}.receiver_inputs", receiver_inputs
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
                                f"{context.binding}; supplier={actual_supplier}; "
                                f"method={native_name}"
                            ),
                        ),
                    ),
                )
        context.evidence.append(
            m.Infra.NativeBindingEvidence(
                binding=context.binding,
                kind=kind,
                supplier=actual_supplier,
                name=native_name,
                qualname=qualified,
                operands=receiver_operands,
                operational=receiver_operational,
            ),
        )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceNativeReferenceBindingsMixin"]
