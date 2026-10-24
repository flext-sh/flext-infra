"""Static observations of native imports; never reconstruct class factories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from importlib.machinery import FrozenImporter, ModuleSpec
from pathlib import Path
from types import (
    ClassMethodDescriptorType,
    FunctionType,
    GenericAlias,
    MethodDescriptorType,
    MethodType,
    ModuleType,
    WrapperDescriptorType,
)

from flext_infra import m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace._native_reference_bindings import (
    FlextInfraWorkspaceNativeReferenceBindingsMixin,
)
from flext_infra.workspace._native_reference_functions import (
    FlextInfraWorkspaceNativeReferenceFunctionsMixin,
)


class FlextInfraWorkspaceNativeReference(
    FlextInfraWorkspaceNativeReferenceFunctionsMixin,
    FlextInfraWorkspaceNativeReferenceBindingsMixin,
):
    """Observe code and binding topology without evaluating authored expressions."""

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
        if not cls._is_native(module, str):
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

    @classmethod
    def capture(
        cls,
        names: t.SequenceOf[str | m.Infra.SourceClassReference],
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]] = (),
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe one native epoch using its own physical source witnesses.

        Returns:
            The observation or its first source/provenance failure.

        """
        return cls._capture(names, paths=paths)

    @classmethod
    def _capture_executable(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeOperand,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Dispatch the remaining executable categories in their original order.

        Returns:
            The admitted executable observation or its first native failure.

        """
        kind = cls._type_attr("__name__", type(value), type(type(value)))
        if any(owner is GenericAlias for owner in cls._native_mro(type(value))):
            return cls._capture_generic_alias(context, value)
        wrapper_kind = cls._native_wrapper_kind(value)
        if wrapper_kind is not None:
            return cls._capture_wrapper(context, value, kind, wrapper_kind)
        if not cls._is_native(value, FunctionType):
            return cls._capture_native_callable(context, value, kind)
        return cls._capture_function(context, value, kind, instructions)

    @classmethod
    def _capture_binding(
        cls,
        context: m.Infra.NativeObservationContext,
        value: t.Infra.NativeOperand,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Dispatch each first-visited native identity without changing its queue.

        Returns:
            The original category result before advancing to another identity.

        """
        if cls._is_function_binding(value):
            return cls._capture_function_binding(context, value)
        if cls._is_class(value):
            return cls._capture_class(context, value, context.binding, instructions)
        if cls._is_native(value, MethodType):
            return cls._capture_bound_method(context, value)
        if cls._is_native(value, property):
            return cls._capture_property(context, value)
        if cls._is_descriptor(value) and any(
            cls._is_native(value, kind)
            for kind in (
                ClassMethodDescriptorType,
                MethodDescriptorType,
                WrapperDescriptorType,
            )
        ):
            return cls._capture_descriptor(context, value)
        return cls._capture_executable(context, value, instructions)

    @classmethod
    def _capture_native_suppliers(
        cls, context: m.Infra.NativeObservationContext
    ) -> p.Result[bool]:
        """Elect original interpreter suppliers before accepting any nomination.

        Returns:
            Every original supplier source, or its first physical election failure.

        """
        for supplier in (
            "builtins",
            "_operator",
            "_functools",
            "_typing",
            "operator",
            "functools",
            "typing",
            "types",
            "gc",
        ):
            elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(supplier)
            if elected.failure:
                return r[bool].from_failure(elected)
            context.sources.add((
                supplier,
                str(cls._source_path(elected.value, context.paths)),
                "",
            ))
        return r[bool].ok(value=True)

    @classmethod
    def _capture_nominations(
        cls, names: t.SequenceOf[str | m.Infra.SourceClassReference]
    ) -> p.Result[t.VariadicTuple[m.Infra.SourceClassReference]]:
        """Validate exactly one complete-module or lexical selection contract.

        Returns:
            Original ordered nominations, or the original contract refusal.

        """
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
            return r[t.VariadicTuple[m.Infra.SourceClassReference]].fail(
                "invalid native source selection"
            )
        selected = all(item.attributes for item in nominations)
        if any(item.attributes for item in nominations) and not selected:
            return r[t.VariadicTuple[m.Infra.SourceClassReference]].fail(
                "mixed native selection contracts"
            )
        return r[t.VariadicTuple[m.Infra.SourceClassReference]].ok(nominations)

    @classmethod
    def _capture_next(
        cls,
        context: m.Infra.NativeObservationContext,
        instructions: t.Infra.NativeInstructionFacts,
    ) -> p.Result[bool]:
        """Admit exactly the next native identity after draining registered edges.

        Returns:
            The original alias/body observation or its first graph contradiction.

        """
        for registered, owner in context.references:
            supplier, _, _qualified = cls._symbol(owner).partition("::")
            context.pending.append((
                f"{registered}.native_type",
                owner,
                supplier,
                "",
                "storage_type",
            ))
        context.references.clear()
        incoming, value, supplier, owner_source, role = context.pending.pop()
        captured = context.visited.get(id(value))
        binding = f"@{len(context.visited)}" if captured is None else captured[1]
        previous = context.edges.get(incoming)
        if incoming in context.absent_edges or (
            previous is not None and previous != binding
        ):
            return r[bool].fail(
                f"native edge changed target: {incoming}; supplier={supplier}",
            )
        if previous is None:
            context.edges[incoming] = binding
            context.evidence.append(
                m.Infra.NativeBindingEvidence(
                    binding=incoming,
                    kind="alias",
                    supplier=supplier,
                    name="",
                    qualname="",
                    operands=(("target", binding),),
                )
            )
        context.binding_context = f"{incoming}; body={binding}; supplier={supplier}"
        context.incoming = incoming
        context.binding = binding
        context.supplier = supplier
        context.owner_source = owner_source
        context.role = role
        if captured is not None:
            if (
                role == "execution"
                and cls._is_class(value)
                and id(value) not in context.expanded_classes
            ):
                observed = next(
                    item for item in context.evidence if item.binding == binding
                )
                cls._enqueue_class_members(
                    context,
                    value,
                    binding,
                    (
                        observed.supplier,
                        str(
                            cls._source_path(
                                context.origins[observed.supplier], context.paths
                            )
                        ),
                        observed.qualname,
                        cls._class_namespace(value),
                    ),
                )
            return r[bool].ok(value=True)
        context.visited[id(value)] = (value, binding)
        observed_binding = cls._capture_binding(context, value, instructions)
        if observed_binding.failure:
            return r[bool].from_failure(observed_binding)
        return r[bool].ok(value=True)

    @classmethod
    def _capture(
        cls,
        names: t.SequenceOf[str | m.Infra.SourceClassReference],
        *,
        paths: t.SequenceOf[t.Pair[Path, Path]],
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe nominated modules or lexical entrypoints without running factories.

        Plain module names request complete inventories through the existing
        public API. Typed lexical paths select an invocation's executable graph.

        Returns:
            Native binding evidence and sources, or the first admission failure.

        """
        context = m.Infra.NativeObservationContext(paths=tuple(paths))
        suppliers = cls._capture_native_suppliers(context)
        if suppliers.failure:
            return r[m.Infra.NativeImportObservation].from_failure(suppliers)
        scope = ContextVar[t.Infra.NativeInvocationFacts | None].get(
            cls._compilation_facts
        )
        instructions: t.Infra.NativeInstructionFacts = (
            scope[1] if scope is not None else {}
        )
        selected = cls._capture_nominations(names)
        if selected.failure:
            return r[m.Infra.NativeImportObservation].from_failure(selected)
        nominations = selected.value
        context.lexical = all(item.attributes for item in nominations)
        for nomination in nominations:
            nominated = cls._nominate_module(context, nomination, instructions)
            if nominated.failure:
                return r[m.Infra.NativeImportObservation].from_failure(nominated)
        while context.pending or context.references:
            observed = cls._capture_next(context, instructions)
            if observed.failure:
                return r[m.Infra.NativeImportObservation].from_failure(observed)
        return r[m.Infra.NativeImportObservation].ok(
            m.Infra.NativeImportObservation(
                runtime=Path(sys.executable).resolve(),
                runtime_prefix=Path(sys.prefix).absolute(),
                modules=nominations,
                sources=tuple(sorted(context.sources)),
                bindings=tuple(sorted(context.evidence, key=lambda item: item.binding)),
            )
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
    def _compare_epoch(
        observed: m.Infra.NativeImportObservation,
        reference: m.Infra.NativeImportObservation,
    ) -> p.Result[bool]:
        """Compare runtime, nominations and source elections before graph bodies.

        Returns:
            The first epoch mismatch or the same native import epoch.

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
        return r[bool].ok(value=True)

    @staticmethod
    def _compare_inventory(
        actual: t.MappingKV[str, m.Infra.NativeBindingEvidence],
        expected: t.MappingKV[str, m.Infra.NativeBindingEvidence],
    ) -> p.Result[bool]:
        """Compare the exact elected native binding inventory.

        Returns:
            The first inventory mismatch with its original identity context.

        """
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
        return r[bool].ok(value=True)

    @staticmethod
    def _compare_binding_metadata(
        item: m.Infra.NativeBindingEvidence,
        native: m.Infra.NativeBindingEvidence,
    ) -> p.Result[bool]:
        """Compare every executable binding field before its code witness.

        Returns:
            The first binding mismatch or exactly matching native metadata.

        """
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
        return r[bool].ok(value=True)

    @staticmethod
    def _compare_binding_code(
        observed: m.Infra.NativeImportObservation,
        reference: m.Infra.NativeImportObservation,
        item: m.Infra.NativeBindingEvidence,
        native: m.Infra.NativeBindingEvidence,
    ) -> p.Result[bool]:
        """Compare complete native code witnesses and retain first-delta evidence.

        Returns:
            The first complete compiler mismatch or identical native code.

        """
        if item.code is None or native.code is None:
            if item.code != native.code:
                return r[bool].fail(
                    "producer native code presence differs: "
                    f"{item.binding}; "
                    f"supplier={item.supplier}; qualname={item.qualname}",
                )
            return r[bool].ok(value=True)
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
                f"witness_windows={
                    tuple(
                        witness[max((offset or 0) - 24, 0) : (offset or 0) + 24]
                        for witness in witnesses
                    )
                }; "
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
    def compare(
        observed: m.Infra.NativeImportObservation,
        reference: m.Infra.NativeImportObservation,
    ) -> p.Result[bool]:
        """Compare complete native compiler witnesses without code deserialization.

        Returns:
            The first epoch, binding or compiler mismatch in the original order.

        """
        epoch = FlextInfraWorkspaceNativeReference._compare_epoch(observed, reference)
        if epoch.failure:
            return epoch
        indexes: list[t.DictKV[str, m.Infra.NativeBindingEvidence]] = []
        for snapshot in (observed, reference):
            indexed = FlextInfraWorkspaceNativeReference._binding_index(snapshot)
            if indexed.failure:
                return r[bool].from_failure(indexed)
            indexes.append(indexed.value)
        actual, expected = indexes
        inventory = FlextInfraWorkspaceNativeReference._compare_inventory(
            actual, expected
        )
        if inventory.failure:
            return inventory
        for item in observed.bindings:
            native = expected[item.binding]
            metadata = FlextInfraWorkspaceNativeReference._compare_binding_metadata(
                item, native
            )
            if metadata.failure:
                return metadata
            code = FlextInfraWorkspaceNativeReference._compare_binding_code(
                observed, reference, item, native
            )
            if code.failure:
                return code
        return r[bool].ok(value=True)

    @classmethod
    def authored_sources_current(
        cls,
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
    ) -> p.Result[bool]:
        """Check authored code against pinned bytes without authenticating emissions.

        Generated code remains pending until the source-backed native import and
        complete observation comparison. This check grants no reference or write.

        Returns:
            The authored-code check or its first physical/compiler failure.

        """
        return cls._authored_sources_current(observed, inputs)

    @classmethod
    def _authored_code_units(
        cls,
        binding: m.Infra.NativeBindingEvidence,
        executed: m.Infra.NativeCodeEvidence,
        states: t.MappingKV[Path, m.Cli.AtomicFileReceipt],
        module_spec: ModuleSpec,
    ) -> p.Result[t.VariadicTuple[t.Infra.NativeCode]]:
        """Compile the elected source only after its physical receipt is proved.

        Returns:
            The native root and nested units or the first physical source failure.

        """
        result_type = r[t.VariadicTuple[t.Infra.NativeCode]]
        if module_spec.origin == "frozen":
            root = FrozenImporter.get_code(module_spec.name)
            if root is None:
                return result_type.fail(
                    f"frozen native supplier has no code: {module_spec.name}"
                )
        else:
            receipt = states.get(Path(executed.filename))
            if receipt is None:
                return result_type.fail(
                    f"authored producer source is not pinned: {binding.binding}",
                )
            read = u.Cli.atomic_read_binary_file_state(receipt.path, required=True)
            if read.failure:
                return result_type.from_failure(read)
            state = read.value
            verified = u.Cli.atomic_read_binary_file_receipt(
                receipt.path, required=True
            )
            if verified.failure:
                return result_type.from_failure(verified)
            if verified.value != receipt or state.content is None:
                return result_type.fail(f"authored source changed: {receipt.path}")
            root = compile(
                state.content,
                executed.filename,
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
        return result_type.ok(cls._code_units(root))

    @classmethod
    def _authored_sources_current(
        cls,
        observed: m.Infra.NativeImportObservation,
        inputs: t.SequenceOf[m.Cli.AtomicFileReceipt],
    ) -> p.Result[bool]:
        """Authenticate authored driver code before read-only reference staging.

        Generated units remain pending independent native-import authentication;
        neither this authored subset nor its result grants publication authority.

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
                # A generated unit has no authored module code unit. Only the
                # independent native import can establish its expected emission.
                admitted += 1
                continue
            key = binding.supplier if frozen else executed.filename
            if key not in compiled:
                units = cls._authored_code_units(binding, executed, states, module_spec)
                if units.failure:
                    return r[bool].from_failure(units)
                compiled[key] = units.value
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
                    f"{binding.binding}; supplier={binding.supplier}; "
                    f"qualname={binding.qualname}; filename={executed.filename!r}; "
                    f"name={executed.name!r}; firstlineno={executed.firstlineno}; "
                    f"source_candidates={
                        tuple(
                            (code.co_qualname, code.co_firstlineno)
                            for code in compiled[key]
                            if code.co_name == executed.name
                        )
                    }",
                )
            admitted += 1
        if not admitted:
            return r[bool].fail("cold producer authority has no authored driver code")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceNativeReference"]
