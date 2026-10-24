"""Immutable source and journal preconditions for generation transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsComparison,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournalRelocation,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._codegen_preconditions_capture import (
    FlextInfraCodegenPreconditionsCaptureMixin,
)
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraCodegenPreconditions(FlextInfraCodegenPreconditionsCaptureMixin):
    """Validate source consistency and receipt ownership before publishing."""

    @classmethod
    def _bootstrap_source_paths(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[frozenset[Path]]:
        """Bind bootstrap buffers to original receipts without rereading candidates.

        Returns:
            Candidate paths outside protected runtime and resource inventories.

        """
        result_type = r[frozenset[Path]]
        if authority.bootstrap_sources:
            private = authority.__pydantic_private__
            if type(authority) is not m.Infra.CodegenSourceAuthority or (
                private is None
                or private.get("_source_birth")
                != (
                    id(authority),
                    u.Cli.sha256_bytes(
                        authority.model_dump_json().encode(c.DEFAULT_ENCODING)
                    ),
                )
            ):
                return result_type.fail(
                    "bootstrap source authority lacks its original capture "
                    "identity and payload"
                )
        sources = cls.unique_states(authority.bootstrap_sources)
        if sources.failure:
            return result_type.from_failure(sources)
        by_path = {source.path: source for source in sources.value}
        matched = cls._authenticated_receipt_files(by_path, authority.inputs)
        if matched.failure:
            return result_type.from_failure(matched)
        if matched.value != set(by_path):
            return result_type.fail("bootstrap source lacks its original receipt")
        protected = {
            authority.runtime,
            *(tree.root.path for tree in authority.generator_trees),
            *(
                entry.path
                for tree in authority.generator_trees
                for entry in tree.entries
            ),
        }
        return result_type.ok(frozenset(by_path).difference(protected))

    @classmethod
    @override
    def source_authority_current(
        cls, authority: m.Infra.CodegenSourceAuthority
    ) -> p.Result[bool]:
        """Re-prove cold election and physical state without executing providers.

        Returns:
            Success only for an unchanged capturing runtime, module election,
            pinned inputs and resource trees.

        """
        modules = cls._authority_modules_current(authority)
        if modules.failure:
            return r[bool].from_failure(modules)
        return cls._authority_inputs_current(authority)

    @classmethod
    def _authority_modules_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[bool]:
        """Re-prove the runtime, optimization and module election identities.

        Returns:
            Success only for the capturing runtime and unchanged elections.

        """
        result_type = r[bool]
        if authority.runtime != Path(sys.executable).resolve():
            return result_type.fail("cold producer runtime changed")
        if authority.optimize != sys.flags.optimize:
            return result_type.fail("cold producer compiler optimization changed")
        for namespace, root in authority.generator_modules:
            elected = cls._elect_namespace(namespace)
            if elected.failure:
                return result_type.from_failure(elected)
            if elected.value != root:
                return result_type.fail("cold producer module election changed")
        return result_type.ok(value=True)

    @classmethod
    def _authority_inputs_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[bool]:
        """Re-prove producer receipts and every captured resource tree.

        Returns:
            Success for unchanged producer inputs and inventories; bootstrap
            candidates retain their original buffered identities until consumed.

        """
        result_type = r[bool]
        bootstrap = cls._bootstrap_source_paths(authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        for expected in authority.inputs:
            if expected.path in bootstrap.value:
                continue
            observed = u.Cli.atomic_read_binary_file_receipt(
                expected.path,
                required=expected.device is not None,
            )
            if observed.failure:
                return result_type.from_failure(observed)
            if observed.value != expected:
                return result_type.fail(
                    f"cold producer source changed: {expected.path}"
                )
        for tree in authority.generator_trees:
            observed = u.Cli.atomic_inventory_physical_tree(tree.root.path)
            if observed.failure:
                return result_type.from_failure(observed)
            if observed.value != tree:
                previous = {entry.path: entry for entry in tree.entries}
                current = {entry.path: entry for entry in observed.value.entries}
                changed = sorted(
                    path
                    for path in previous.keys() | current.keys()
                    if previous.get(path) != current.get(path)
                )
                return result_type.fail(
                    f"cold producer resource tree changed: {tree.root.path}; "
                    f"root_changed={tree.root != observed.value.root} "
                    f"changed_count={len(changed)} first={changed[:3]}"
                )
        return result_type.ok(value=True)

    @classmethod
    def authority_inputs(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read producer payloads and retain original bootstrap candidate buffers.

        Returns:
            Protected inputs read through their authenticated descriptors and
            candidate inputs carrying their original authenticated bytes.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileState]]
        bootstrap = cls._bootstrap_source_paths(authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        buffered = {
            source.path: source
            for source in authority.bootstrap_sources
            if source.path in bootstrap.value
        }
        states: list[m.Cli.AtomicFileState] = []
        for receipt in authority.inputs:
            if receipt.path in buffered:
                states.append(buffered[receipt.path])
                continue
            if receipt.device is None:
                current = u.Cli.atomic_read_binary_file_receipt(receipt.path)
                if current.failure:
                    return result_type.from_failure(current)
                if current.value != receipt:
                    return result_type.fail(
                        f"cold producer absent input changed: {receipt.path}",
                    )
                content = None
            elif receipt.size is not None:
                with u.Cli.atomic_binary_file_reader(receipt) as reader:
                    content = reader.read_range(0, receipt.size)
            else:
                return result_type.fail(
                    f"cold producer pinned input has no physical size: {receipt.path}",
                )
            states.append(
                m.Cli.AtomicFileState.model_validate({
                    **receipt.model_dump(
                        include=set(m.Cli.AtomicFileState.model_fields),
                    ),
                    "content": content,
                }),
            )
        return result_type.ok(tuple(states))

    @classmethod
    def admit_native_reference(
        cls,
        request: m.Infra.NativeImportRequest,
        original: m.Infra.NativeImportObservation,
        imported: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Seal an imported reference only after complete executable and input proof.

        Returns:
            The live reference after trace, binding, source and runtime admission.

        """
        result_type = r[m.Infra.NativeImportReference]
        if imported.modules != request.modules:
            return result_type.fail(
                "native observation differs from its requested producer selections"
            )
        private = imported.__pydantic_private__
        if type(imported) is not m.Infra.NativeImportObservation or (
            private is None
            or private.get("_import_birth")
            != (
                id(imported),
                u.Cli.sha256_bytes(
                    imported.model_dump_json().encode(c.DEFAULT_ENCODING)
                ),
            )
        ):
            return result_type.fail(
                "native observation lacks its original cold import identity and payload"
            )
        consumed = cls._executed_source_authority(request, imported, original)
        if consumed.failure:
            return result_type.from_failure(consumed)
        return (
            FlextInfraWorkspaceNativeReference
            .compare(original, imported)
            .flat_map(
                lambda _: FlextInfraWorkspaceNativeReference.authored_sources_current(
                    imported, consumed.value.inputs
                )
            )
            .flat_map(lambda _: cls._native_runtime_current(request))
            .flat_map(lambda _: cls.source_authority_current(consumed.value))
            .flat_map(lambda _: cls._seal_native_reference(imported, consumed.value))
        )

    @staticmethod
    def _seal_native_reference(
        reference: m.Infra.NativeImportObservation,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Issue one live reference after full physical and executable admission.

        Returns:
            The exact reference with its Pydantic-owned private birth storage.

        """
        admitted = m.Infra.NativeImportReference(
            **reference.model_dump(),
            source_authority=authority,
        )
        private = admitted.__pydantic_private__
        if private is None:
            return r[m.Infra.NativeImportReference].fail(
                "native admission has no Pydantic private storage"
            )
        private["_native_birth"] = (
            id(admitted),
            u.Cli.sha256_bytes(admitted.model_dump_json().encode(c.DEFAULT_ENCODING)),
        )
        return r[m.Infra.NativeImportReference].ok(admitted)

    @staticmethod
    def reference_birth_current(
        reference: m.Infra.NativeImportReference,
    ) -> p.Result[bool]:
        """Require the exact live reference emitted by complete native admission.

        Returns:
            Its original live identity and payload, never reconstructed authority.

        """
        private = reference.__pydantic_private__
        if type(reference) is not m.Infra.NativeImportReference or (
            private is None
            or private.get("_native_birth")
            != (
                id(reference),
                u.Cli.sha256_bytes(
                    reference.model_dump_json().encode(c.DEFAULT_ENCODING)
                ),
            )
        ):
            return r[bool].fail(
                "native reference lacks its original admission identity and payload"
            )
        return r[bool].ok(value=True)

    @classmethod
    def reference_current(
        cls,
        reference: m.Infra.NativeImportReference,
    ) -> p.Result[bool]:
        """Re-prove a native reference's admission by value.

        Historical and reconstructed evidence stays admitted while its sealed
        authority still names this capturing runtime, compiler optimization
        and module election; only ``reference_birth_current`` grants a live
        operation's capability. Pinned input bytes are not re-read here: a
        transaction legitimately publishes its own producer inputs (a
        self-hosted pyproject or lazy init), so physical currency belongs to
        ``authority_current``, which authenticates those effects against the
        journal's recorded outputs.

        Returns:
            Success only while the reference's runtime and election hold.

        """
        if type(reference) is not m.Infra.NativeImportReference:
            return r[bool].fail("native reference is not an admitted native import")
        return cls._authority_modules_current(reference.source_authority)

    @classmethod
    def _executed_source_authority(
        cls,
        request: m.Infra.NativeImportRequest,
        observed: m.Infra.NativeImportObservation,
        original: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.CodegenSourceAuthority]:
        """Bind pre-execution child receipts to the original elected providers.

        Returns:
            The complete input authority after physical and execution-trace proof.

        """
        result_type = r[m.Infra.CodegenSourceAuthority]
        if not observed.executed_sources:
            return result_type.fail(
                "cold native import has no executed-source receipts"
            )
        consumed = cls._executed_sources_current(
            request.source_authority, observed.executed_sources
        )
        if consumed.failure:
            return result_type.from_failure(consumed)
        bootstrap = cls._bootstrap_source_paths(request.source_authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        executed = {receipt.path for receipt in observed.executed_sources}
        for supplier, origin, declaration in observed.sources:
            if supplier.partition("::")[0].partition(".")[0] in sys.stdlib_module_names:
                continue
            for source in (origin, declaration):
                if (
                    source
                    and Path(source).suffix == c.Infra.EXT_PYTHON
                    and Path(source) not in executed
                ):
                    return result_type.fail(
                        f"cold producer source was not compiled by its loader: {source}"
                    )
        graph_sources = {
            Path(source)
            for snapshot in (original, observed)
            for _, origin, declaration in snapshot.sources
            for source in (origin, declaration)
            if source
        }
        required = graph_sources | executed
        authority = request.source_authority.model_copy(
            update={
                "inputs": tuple(
                    receipt
                    for receipt in consumed.value
                    if receipt.path not in bootstrap.value or receipt.path in required
                ),
                "bootstrap_sources": (),
            }
        )
        return cls.source_authority_current(authority).map(lambda _: authority)

    @staticmethod
    def _executed_sources_current(
        authority: m.Infra.CodegenSourceAuthority,
        receipts: t.VariadicTuple[m.Cli.AtomicFileReceipt],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileReceipt]]:
        """Authenticate every child receipt within the original physical election.

        Returns:
            The original and newly consumed receipts with unchanged physical bytes.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileReceipt]]
        standard = FlextInfraWorkspaceEnvironmentProvenance.standard_library_root()
        packages = (
            FlextInfraWorkspaceEnvironmentProvenance.standard_library_package_roots()
        )
        roots = tuple(root for _, root in authority.generator_modules)
        pinned = {receipt.path: receipt for receipt in authority.inputs}
        executed: t.MutableMappingKV[Path, m.Cli.AtomicFileReceipt] = {}
        for receipt in receipts:
            path = receipt.path
            physical = path.resolve()
            runtime_source = physical.is_relative_to(standard) and not any(
                physical.is_relative_to(root) for root in packages
            )
            if not (
                runtime_source
                or any(
                    physical.is_relative_to(root.resolve())
                    if root.is_dir()
                    else physical == root.resolve()
                    for root in roots
                )
            ):
                return result_type.fail(
                    f"cold source escaped its elected provider: {path}"
                )
            previous = executed.get(path, pinned.get(path))
            if previous is not None and previous != receipt:
                return result_type.fail(f"cold source input changed: {path}")
            current = u.Cli.atomic_read_binary_file_receipt(path, required=True)
            if current.failure:
                return result_type.from_failure(current)
            if current.value != receipt:
                return result_type.fail(f"cold executed source changed: {path}")
            executed[path] = receipt
        return result_type.ok(tuple({**pinned, **executed}.values()))

    @classmethod
    def native_inputs_current(
        cls,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[bool]:
        """Recheck the pinned inputs and the executing physical runtime.

        Returns:
            Success when source, environment and interpreter identities agree.

        """
        if request.modules != request.source_authority.selections or (
            request.import_roots
            != tuple(
                dict.fromkeys(
                    root.parent
                    for _, root in request.source_authority.generator_modules
                )
            )
        ):
            return r[bool].fail(
                "native import request differs from its elected source authority"
            )
        bootstrap = cls._bootstrap_source_paths(request.source_authority)
        if bootstrap.failure:
            return r[bool].from_failure(bootstrap)
        states = cls.unique_states(request.inputs)
        if states.failure:
            return r[bool].from_failure(states)
        by_path = {state.path: state for state in states.value}
        matched = cls._authenticated_receipt_files(
            by_path, request.source_authority.inputs
        )
        if matched.failure:
            return r[bool].from_failure(matched)
        if matched.value != set(by_path) or matched.value != {
            receipt.path for receipt in request.source_authority.inputs
        }:
            return r[bool].fail(
                "native import inputs differ from their complete captured receipts"
            )
        return (
            cls
            .source_authority_current(request.source_authority)
            .flat_map(
                lambda _: FlextInfraMiseArtifactsVerification.states_current(
                    tuple(
                        state
                        for state in request.inputs
                        if state.path not in bootstrap.value
                    )
                )
            )
            .flat_map(lambda _: cls._native_runtime_current(request))
        )

    @staticmethod
    def _native_runtime_current(
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[bool]:
        """Re-prove the request's original physical environment and interpreter.

        Returns:
            Success only for unchanged environment, prefix and compiler mode.

        """
        environment = u.Infra.runtime_environment_dir(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        runtime = u.Infra.runtime_python(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        actual_environment = environment.absolute()
        actual_prefix = Path(sys.prefix).absolute()
        actual_runtime = runtime.resolve()
        if (
            environment.is_symlink()
            or actual_environment != actual_prefix
            or not runtime.is_file()
            or actual_runtime != request.source_authority.runtime
            or sys.flags.optimize != request.source_authority.optimize
        ):
            return r[bool].fail(
                "native reference runtime authority differs: "
                f"environment={actual_environment} symlink={environment.is_symlink()} "
                f"prefix={actual_prefix} runtime={actual_runtime} "
                f"runtime_file={runtime.is_file()} "
                f"expected_runtime={request.source_authority.runtime} "
                f"optimize={sys.flags.optimize} "
                f"expected_optimize={request.source_authority.optimize}"
            )
        return r[bool].ok(value=True)

    @classmethod
    def producer_current(
        cls,
        producer: m.Infra.CodegenPhaseAnalysis,
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Authenticate the original epoch and relevant invocation-owned effects.

        Returns:
            Success only for unchanged inputs and native code, with changed
            physical sources accounted for by authenticated own outputs.

        """
        if not producer.inputs or producer.generator_reference is None:
            return r[bool].fail("producer context lacks authenticated source closure")
        birth = cls.reference_birth_current(producer.generator_reference)
        if birth.failure:
            return birth
        states = cls.unique_states(producer.inputs)
        if states.failure:
            return r[bool].from_failure(states)
        by_path = {state.path: state for state in states.value}
        authority = producer.generator_reference.source_authority
        source_paths = {item.path for item in authority.inputs}
        own_outputs = tuple(
            output
            for output in outputs
            if output.path in source_paths
            or any(
                output.path.is_relative_to(tree.root.path)
                for tree in authority.generator_trees
            )
        )
        output_paths = {output.path for output in own_outputs}
        authenticated = cls._authenticated_receipt_files(by_path, authority.inputs)
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        # The native authority physically reauthenticates every matching receipt.
        # Extra planner inputs retain their own immediate snapshot proof.
        retained = tuple(
            state
            for state in states.value
            if state.path not in output_paths and state.path not in authenticated.value
        )
        current = FlextInfraMiseArtifactsComparison.states_current(retained)
        if current.failure:
            return current
        return cls.producer_trees_current(
            producer.generator_trees,
            own_outputs,
            modules=producer.generator_modules,
            reference=producer.generator_reference,
        )

    @staticmethod
    @override
    def _authenticated_receipt_files(
        by_path: t.MappingKV[Path, m.Cli.AtomicFileState],
        receipts: t.VariadicTuple[m.Cli.AtomicFileReceipt],
    ) -> p.Result[set[Path]]:
        """Bind buffered inputs to receipts before their native physical proof.

        Args:
            by_path: Captured states indexed by their physical path.
            receipts: Original authority receipts, including owned output preimages.

        Returns:
            Paths whose exact buffered state agrees with its original receipt.

        """
        result_type = r[set[Path]]
        covered: set[Path] = set()
        identity_fields = set(m.Cli.AtomicFileIdentity.model_fields)
        for receipt in receipts:
            state = by_path.get(receipt.path)
            if state is None:
                continue
            content = state.content
            if (
                state.model_dump(include=identity_fields),
                len(content) if content is not None else None,
                u.Cli.sha256_bytes(content) if content is not None else None,
            ) != (
                receipt.model_dump(include=identity_fields),
                receipt.size,
                receipt.sha256,
            ):
                return result_type.fail(
                    f"producer input differs from captured receipt: {state.path}"
                )
            covered.add(state.path)
        return result_type.ok(covered)

    @staticmethod
    def producer_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
        *,
        modules: t.VariadicTuple[t.Pair[str, Path]],
        reference: m.Infra.NativeImportReference | None = None,
    ) -> p.Result[bool]:
        """Check the original native epoch without minting namespace-local proofs.

        Returns:
            Success only for the unchanged native epoch, its membership and
            its re-captured loaded bindings.

        """
        if reference is None:
            return r[bool].fail("producer closure lacks its pre-planning native epoch")
        birth = FlextInfraCodegenPreconditions.reference_current(reference)
        if birth.failure:
            return birth
        if (
            tuple(trees) != reference.source_authority.generator_trees
            or modules != reference.source_authority.generator_modules
        ):
            return r[bool].fail("producer native epoch belongs to another election")

        current = FlextInfraCodegenPreconditions.authority_current(
            reference.source_authority, outputs=outputs
        )
        if current.failure:
            return current
        observed = FlextInfraWorkspaceNativeReference.capture(reference.modules)
        if observed.failure:
            return r[bool].from_failure(observed)
        return FlextInfraWorkspaceNativeReference.compare(observed.value, reference)

    @staticmethod
    def source_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
        *,
        modules: t.VariadicTuple[t.Pair[str, Path]],
    ) -> p.Result[bool]:
        """Reauthenticate whole trees, then compare source membership and identity.

        Interpreter bytecode is derived, not a source input. It is excluded only
        after native inventory has authenticated all physical entries. Native
        output receipts, never path guesses, authorize publication membership.

        Returns:
            Success only for unchanged trees, election and executing sources.

        """
        for tree in trees:
            current = FlextInfraCodegenPreconditions._producer_tree_current(
                tree, outputs
            )
            if current.failure:
                return current
        if not modules:
            return r[bool].fail("producer module election changed after capture")
        for namespace, root in modules:
            elected = FlextInfraCodegenPreconditions._elect_namespace(namespace)
            if elected.failure:
                return r[bool].from_failure(elected)
            if elected.value != root:
                return r[bool].fail("producer module election changed after capture")
        return r[bool].ok(value=True)

    @staticmethod
    def _authorized_outputs_current(
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Authenticate every physical effect before permitting source substitution.

        Returns:
            The first physical mismatch or the exact recorded effects.

        """
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
        return r[bool].ok(value=True)

    @classmethod
    def authority_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
        *,
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Validate physical source authority and only authenticated own effects.

        Returns:
            The original input/election proof, without creating execution authority.

        """
        modules = cls._authority_modules_current(authority)
        if modules.failure:
            return modules
        if not authority.inputs or authority.runtime not in {
            item.path for item in authority.inputs
        }:
            return r[bool].fail(
                "native source authority lacks its physical interpreter"
            )
        published = cls._authorized_outputs_current(outputs)
        if published.failure:
            return published
        output_paths = {item.path for item in outputs}
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
        return cls.source_trees_current(
            authority.generator_trees,
            tuple(outputs),
            modules=authority.generator_modules,
        )

    @classmethod
    def _producer_tree_current(
        cls,
        tree: m.Cli.AtomicPhysicalTreeManifest,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Authenticate physical inventory before directory and file proof.

        Returns:
            Success only for this tree's native identities and journaled effects.

        """
        inventory = u.Cli.atomic_inventory_physical_tree(tree.root.path)
        if inventory.failure:
            return r[bool].from_failure(inventory)
        if not FlextInfraMiseArtifactsComparison.same_directory_identity(
            tree.root, inventory.value.root
        ):
            return r[bool].fail(f"producer root identity changed: {tree.root.path}")
        if any(item.kind == "symlink" for item in inventory.value.entries):
            return r[bool].fail(
                f"producer resource has a physical alias: {tree.root.path}"
            )
        own = {
            item.path: item
            for item in outputs
            if item.path.is_relative_to(tree.root.path)
        }
        directories = {
            item.path: item
            for item in tree.entries
            if item.kind == "directory"
            and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        live = {
            item.path: item
            for item in inventory.value.entries
            if item.kind == "directory"
            and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        admitted = {
            parent
            for path, item in own.items()
            if item.sha256 is not None
            for parent in path.parents
            if parent.is_relative_to(tree.root.path) and parent != tree.root.path
        }
        if set(live) != set(directories) | admitted:
            return r[bool].fail(
                f"producer directory membership changed: {tree.root.path}"
            )
        for path, before in directories.items():
            if not FlextInfraMiseArtifactsComparison.same_directory_identity(
                before, live[path]
            ):
                return r[bool].fail(f"producer directory identity changed: {path}")
        return cls._producer_files_current(tree, inventory.value, own)

    @staticmethod
    def _producer_files_current(
        tree: m.Cli.AtomicPhysicalTreeManifest,
        inventory: m.Cli.AtomicPhysicalTreeManifest,
        own: t.MappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Verify source files and every admitted effect against native receipts.

        Returns:
            Success for exact membership, byte, mode and physical identities.

        """
        expected = {
            item.path: item
            for item in tree.entries
            if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        observed = {
            item.path: item
            for item in inventory.entries
            if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        if set(observed) != (set(expected) - set(own)) | {
            path for path, item in own.items() if item.sha256 is not None
        }:
            return r[bool].fail(
                f"producer resource membership changed: {tree.root.path}"
            )
        for path, receipt in own.items():
            if receipt.sha256 is None:
                continue
            after = observed[path]
            if (
                after.sha256,
                after.mode,
                after.device,
                after.inode,
                after.parent_device,
                after.parent_inode,
            ) != (
                receipt.sha256,
                receipt.mode,
                receipt.device,
                receipt.inode,
                receipt.parent_device,
                receipt.parent_inode,
            ):
                return r[bool].fail(f"producer effect receipt changed: {path}")
        for path, before in expected.items():
            if path not in own and observed[path] != before:
                return r[bool].fail(f"producer resource identity changed: {path}")
        return r[bool].ok(value=True)

    @staticmethod
    def rendering_engine(repository_root: Path) -> p.Result[bool]:
        """Prove the executing engine is the flext-infra the target's lock pins.

        Editable bindings and targets without an engine pin use their own tree.

        Returns:
            Success only for the declared rendering origin and registry version.

        """
        result_type = r[bool]
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return result_type.from_failure(context)
        lock_path = context.value.lock_path
        if not lock_path.is_file():
            return result_type.ok(value=True)
        distribution_name = config.Infra.codegen.infra_repository.distribution
        matches = u.installed_distributions(name=distribution_name)
        if len(matches) != 1:
            return result_type.fail(
                f"rendering engine distribution count mismatch: "
                f"distribution={distribution_name} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        direct_url = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        receipt: m.Infra.DirectUrlReceipt | None = None
        if direct_url is not None:
            parsed = r[m.Infra.DirectUrlReceipt].create_from_callable(
                partial(m.Infra.DirectUrlReceipt.model_validate_json, direct_url)
            )
            if parsed.failure:
                return result_type.from_failure(parsed)
            receipt = parsed.value
        if (
            receipt is not None
            and receipt.dir_info is not None
            and receipt.dir_info.editable
        ):
            return result_type.ok(value=True)
        return (
            u.Cli
            .toml_read_json(lock_path)
            .flat_map(
                lambda payload: r[m.Infra.LockedEnvironment].create_from_callable(
                    partial(m.Infra.LockedEnvironment.model_validate, payload)
                )
            )
            .flat_map(
                partial(
                    FlextInfraCodegenPreconditions._locked_engine_current,
                    distribution,
                    direct_url,
                    distribution_name=distribution_name,
                )
            )
        )

    @staticmethod
    def _locked_engine_current(
        distribution: Distribution,
        direct_url: str | None,
        locked: m.Infra.LockedEnvironment,
        *,
        distribution_name: str,
    ) -> p.Result[bool]:
        """Compare the installed engine to the unique typed committed pin.

        Returns:
            Success for an unpinned/editable engine or its exact artifact origin.

        """
        result_type = r[bool]
        pinned = tuple(
            item for item in locked.package if item.name == distribution_name
        )
        if not pinned:
            return result_type.ok(value=True)
        if len(pinned) != 1:
            return result_type.fail(
                "rendering engine has ambiguous committed lock entries"
            )
        item = pinned[0]
        if item.source.editable is not None:
            return result_type.ok(value=True)
        origin = FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict(
            distribution_name, item, direct_url
        )
        if origin.failure:
            return origin
        if item.source.registry is not None and distribution.version != item.version:
            return result_type.fail(
                f"rendering engine {distribution_name}@{distribution.version} "
                f"is not the locked pin {distribution_name}@{item.version}: "
                "the environment is stale — cure: make setup (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        return result_type.ok(value=True)

    @staticmethod
    def phase_sources(
        phase: str,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]]]:
        """Reject conflicting observations and tag each source with its phase.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[str,
                m.Cli.AtomicFileState]]]``.

        """
        return FlextInfraCodegenPreconditions.unique_states(
            tuple(source for plan in plans for source in plan.source_states)
        ).map(lambda sources: tuple((phase, source) for source in sources))

    @classmethod
    def bind_producer_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        producer: m.Infra.CodegenPhaseAnalysis,
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Bind the original producer epoch to the current admitted planner inputs.

        Returns:
            The planner's exact inputs and files with authenticated producer metadata.

        """
        current = cls.producer_current(producer, outputs=outputs)
        if current.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(current)
        return cls.compose_producer_analysis(analysis, producer, outputs=outputs)

    @classmethod
    def compose_producer_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        producer: m.Infra.CodegenPhaseAnalysis,
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Compose snapshots and producer metadata without granting authority.

        Returns:
            The planner analysis with its original producer metadata, or a
            conflicting snapshot failure.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        # Earlier owned publications may replace producer source bytes. Planner
        # inputs still agree among themselves; the native epoch is never rewritten.
        output_paths = {output.path for output in outputs}
        sources = cls.unique_states((
            *(state for state in producer.inputs if state.path not in output_paths),
            *analysis.inputs,
            *(source for plan in analysis.files for source in plan.source_states),
        ))
        if sources.failure:
            return result_type.from_failure(sources)
        return result_type.ok(
            analysis.model_copy(
                update={
                    "generator_trees": producer.generator_trees,
                    "generator_modules": producer.generator_modules,
                    "generator_reference": producer.generator_reference,
                }
            )
        )

    @staticmethod
    @override
    def unique_states(
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Preserve the first identity per path and refuse conflicting snapshots.

        Returns:
            The authenticated ordered union or its first identity conflict.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        by_path: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        for file_state in states:
            previous = by_path.setdefault(file_state.path, file_state)
            if previous != file_state:
                first_hash = (
                    u.Cli.sha256_bytes(previous.content)
                    if previous.content is not None
                    else None
                )
                observed_hash = (
                    u.Cli.sha256_bytes(file_state.content)
                    if file_state.content is not None
                    else None
                )
                details = (
                    f" first={previous.model_dump_json(exclude={'content'})}"
                    f" observed={file_state.model_dump_json(exclude={'content'})}"
                    f" first_sha256={first_hash}"
                    f" observed_sha256={observed_hash}"
                )
                if previous.model_dump() == file_state.model_dump():
                    details += (
                        f" first_type={type(previous).__module__}."
                        f"{type(previous).__qualname__}"
                        f" observed_type={type(file_state).__module__}."
                        f"{type(file_state).__qualname__}"
                    )
                return result_type.fail(
                    f"planner observed two states for {file_state.path};{details}"
                )
        return result_type.ok(tuple(by_path.values()))


__all__: list[str] = ["FlextInfraCodegenPreconditions"]
