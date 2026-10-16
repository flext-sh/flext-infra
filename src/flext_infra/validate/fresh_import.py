"""Verify published exports and real entrypoints in fresh child processes.

The ``fresh-import`` check gate runs this guard in the checkout's provisioned
runtime. File-facade generation also uses its authenticated staged-view consumer.
Each entrypoint loads before any package smoke so cached imports cannot hide
consumer-order defects. Imported workspace modules must belong to this checkout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_infra import FlextInfraServiceBase, c, config, m, p, r, settings, t, u
from flext_infra.codegen import (
    FlextInfraCodegenPreconditions,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._mise_artifacts_state import FlextInfraMiseArtifactsState
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference


class FlextInfraValidateFreshImport(FlextInfraServiceBase[bool]):
    """Verify consumers and publication contracts without inherited import state."""

    packages: Annotated[
        t.StrSequence,
        m.Field(description="Packages to validate in fresh subprocesses"),
    ] = (c.Infra.PKG_CORE_UNDERSCORE, "flext_infra", "flext_tests")
    runtime_root: Annotated[
        Path | None,
        m.Field(
            description=(
                "Declared runtime root whose environment runs the probes; "
                "undeclared, the target checkout's own environment"
            ),
        ),
    ] = m.Field(
        default_factory=lambda: type(settings).fetch_global().Infra.runtime_root
    )
    _NATIVE_REFERENCE_LOADER: ClassVar[str] = """
from importlib.machinery import (
    BuiltinImporter, FrozenImporter, PathFinder, SourceFileLoader, ExtensionFileLoader
)
_native_trace = {}
_native_atomic = None
for _native_name in tuple(sys.modules):
    _native_namespace = _native_name.partition('.')[0]
    if (
        _native_namespace in _native_roots
        and _native_namespace not in sys.stdlib_module_names
    ):
        raise ImportError(
            'producer was imported before its source loader: ' + _native_name
        )

def _native_source_path(fullname, filename):
    path = Path(filename).absolute()
    physical = path.resolve()
    namespace = fullname.partition('.')[0]
    root = _native_roots.get(namespace)
    if root is not None:
        allowed = (
            physical.is_relative_to(root.resolve())
            if root.is_dir() else physical == root.resolve()
        )
    else:
        allowed = (
            physical.is_relative_to(_native_standard)
            and not any(physical.is_relative_to(root) for root in _native_packages)
        )
    if not allowed:
        raise ImportError(
            'source has no elected physical provider: '
            + fullname + ': ' + str(path)
        )
    return path

def _native_before_load(fullname, filename, source):
    path = _native_source_path(fullname, filename)
    if _native_atomic is None:
        if path not in _native_receipts or (source and path not in _native_payloads):
            raise ImportError(
                'source is not pinned before atomic-reader bootstrap: ' + str(path)
            )
        encoded = _native_receipts[path]
        content = _native_payloads[path] if source else None
    else:
        receipt_reader, file_reader, receipt_model = _native_atomic
        receipt = receipt_reader(path, required=True).unwrap()
        previous = _native_trace.get(path, _native_receipts.get(path))
        if (
            previous is not None
            and receipt != receipt_model.model_validate_json(previous)
        ):
            raise ImportError('native source changed before compilation: ' + str(path))
        encoded = receipt.model_dump_json()
        content = None
        if source:
            if receipt.size is None:
                raise ImportError('native source receipt has no size: ' + str(path))
            with file_reader(receipt) as reader:
                content = reader.read_range(0, receipt.size)
    _native_trace[path] = encoded
    return content

class _NativeSourceLoader(SourceFileLoader):
    def get_code(self, fullname):
        filename = self.get_filename(fullname)
        content = _native_before_load(fullname, filename, True)
        return self.source_to_code(content, filename, _optimize=sys.flags.optimize)

class _NativeExtensionLoader(ExtensionFileLoader):
    def create_module(self, spec):
        _native_before_load(spec.name, self.path, False)
        return super().create_module(spec)

class _NativeSourceFinder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        native = BuiltinImporter.find_spec(fullname)
        if native is not None:
            return native
        native = FrozenImporter.find_spec(fullname)
        if native is not None:
            return native
        native = PathFinder.find_spec(fullname, path, target)
        if native is None:
            raise ModuleNotFoundError(
                'native import has no elected module: ' + fullname, name=fullname
            )
        if native.origin is None:
            if native.submodule_search_locations is None:
                raise ImportError(
                    'native module has neither source nor namespace portions: '
                    + fullname
                )
            for portion in native.submodule_search_locations:
                _native_source_path(fullname, portion)
            return native
        _native_source_path(fullname, native.origin)
        if type(native.loader) is SourceFileLoader:
            native.loader = _NativeSourceLoader(fullname, native.origin)
        elif type(native.loader) is ExtensionFileLoader:
            native.loader = _NativeExtensionLoader(fullname, native.origin)
        else:
            raise ImportError(
                'native source loader cannot prove compilation: ' + fullname
            )
        return native

sys.meta_path.insert(0, _NativeSourceFinder)
from flext_cli import m as _native_cli_models, u as _native_cli_utilities
_native_atomic = (
    _native_cli_utilities.Cli.atomic_read_binary_file_receipt,
    _native_cli_utilities.Cli.atomic_binary_file_reader,
    _native_cli_models.Cli.AtomicFileReceipt,
)
"""

    @classmethod
    def capture_producer(
        cls,
        repository_root: Path,
        *,
        entrypoint: p.AttributeProbe,
        collaborators: t.SequenceOf[p.AttributeProbe] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Authenticate the loaded producer against its cold physical authority.

        Returns:
            The authenticated producer phase analysis snapshot.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        selection = FlextInfraWorkspaceNativeReference.producer_selections(
            entrypoint,
            collaborators,
        )
        if selection.failure:
            return result_type.from_failure(selection)
        names = selection.value
        environment = Path(sys.prefix).absolute()
        if (
            environment.name != c.Infra.ENVIRONMENT_DIRECTORY
            or environment.is_symlink()
        ):
            return result_type.fail(
                f"producer runtime is not a physical managed environment: {environment}"
            )
        runtime_root = environment.parent
        reference = cls.capture_producer_reference(repository_root, runtime_root, names)
        if reference.failure:
            return result_type.from_failure(reference)
        consumed = FlextInfraCodegenPreconditions.authority_inputs(
            reference.value.source_authority
        )
        if consumed.failure:
            return result_type.from_failure(consumed)
        authority = reference.value.source_authority
        snapshot = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(),
            inputs=consumed.value,
            generator_trees=authority.generator_trees,
            generator_modules=authority.generator_modules,
            generator_reference=reference.value,
        )
        return FlextInfraCodegenPreconditions.producer_current(snapshot).map(
            lambda _current: snapshot
        )

    @classmethod
    def capture_producer_reference(
        cls,
        repository_root: Path,
        runtime_root: Path,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Bind one elected source epoch to its independent native import.

        Returns:
            The live admitted reference or the first source/import failure.

        """
        result_type = r[m.Infra.NativeImportReference]
        u.Cli.info(
            f"stage=native-source-authority selections={len(names)} "
            f"runtime={runtime_root}",
        )
        sealed = FlextInfraCodegenPreconditions.observed_source_authority(
            runtime_root, names
        )
        if sealed.failure:
            return result_type.from_failure(sealed)
        authority, observation = sealed.value
        u.Cli.info(
            f"stage=native-source-authority-complete "
            f"providers={len(authority.generator_modules)} "
            f"inputs={len(authority.inputs)}",
        )
        inputs = FlextInfraCodegenPreconditions.authority_inputs(authority)
        if inputs.failure:
            return result_type.from_failure(inputs)
        # The authority already observed these exact selections; capturing the
        # loaded producer again could only repeat that observation.
        return cls._observed_native_reference(
            m.Infra.NativeImportRequest(
                repository_root=repository_root,
                runtime_root=runtime_root,
                modules=names,
                inputs=inputs.value,
                source_authority=authority,
                import_roots=tuple(
                    dict.fromkeys(
                        root.parent for _name, root in authority.generator_modules
                    )
                ),
            ),
            observation,
        )

    @classmethod
    def _observed_native_reference(
        cls,
        request: m.Infra.NativeImportRequest,
        snapshot: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Prove one loaded-producer observation against a cold native import.

        Returns:
            The sealed reference, or the first source or runtime failure.

        """
        return FlextInfraWorkspaceNativeReference.capture(request.modules).flat_map(
            lambda observed: cls._observed_native_reference(request, observed)
        )

    @classmethod
    def _observed_native_reference(
        cls,
        request: m.Infra.NativeImportRequest,
        snapshot: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Compare one loaded observation with its independently imported producer.

        Returns:
            The live reference after the original source and cold import proofs.

        """
        result_type = r[m.Infra.NativeImportReference]
        observed = FlextInfraWorkspaceNativeReference.authored_sources_current(
            snapshot, request.source_authority.inputs
        ).map(lambda _: snapshot)
        if observed.failure:
            return result_type.from_failure(observed)
        cold = cls._cold_native_observation(request)
        if cold.failure:
            return result_type.from_failure(cold)
        return FlextInfraCodegenPreconditions.admit_native_reference(
            request, observed.value, cold.value
        )

    @classmethod
    def _cold_native_observation(
        cls,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Read the complete original child outcome before decoding its evidence.

        Returns:
            The original native import observation or process failure.

        """
        result_type = r[m.Infra.NativeImportObservation]
        consumer = cls(
            repository_root=request.repository_root,
            runtime_root=request.runtime_root,
        )
        output = consumer.native_reference_probe(request)
        if output.failure:
            return result_type.from_failure(output)
        if not u.Cli.process_succeeded(output.value.outcome) or output.value.stderr:
            return result_type.fail(
                f"cold native source import failed: {output.value.outcome}\n"
                f"stdout:\n{output.value.stdout}\nstderr:\n{output.value.stderr}",
            )
        imported = m.Infra.NativeImportObservation.model_validate_json(
            output.value.stdout
        )
        private = imported.__pydantic_private__
        if private is None:
            return result_type.fail(
                "native observation has no Pydantic private storage"
            )
        private["_import_birth"] = (
            id(imported),
            u.Cli.sha256_bytes(imported.model_dump_json().encode(c.DEFAULT_ENCODING)),
        )
        return result_type.ok(imported)

    def native_reference_probe(
        self,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Consume the authenticated import selections in the isolated interpreter.

        Returns:
            The real native import output, preserving its original failure.

        """
        admitted = FlextInfraCodegenPreconditions.native_inputs_current(request)
        if admitted.failure:
            return r[p.Cli.CommandOutput].from_failure(admitted)
        roots = tuple(dict.fromkeys(request.import_roots))
        imports = tuple(map(str, roots))
        selections = tuple(item.model_dump_json() for item in request.modules)
        origins = tuple(
            (namespace, str(source))
            for namespace, source in request.source_authority.generator_modules
            if source.is_dir()
        )
        receipts = {
            receipt.path: receipt.model_dump_json()
            for receipt in request.source_authority.inputs
        }
        payloads = {
            state.path: state.content
            for state in request.inputs
            if state.path.suffix == c.Infra.EXT_PYTHON and state.content is not None
        }
        standard = FlextInfraWorkspaceEnvironmentProvenance.standard_library_root()
        packages = tuple(
            map(
                str,
                FlextInfraWorkspaceEnvironmentProvenance.standard_library_package_roots(),
            )
        )
        elected_roots = tuple(
            (name, str(root))
            for name, root in request.source_authority.generator_modules
        )
        code = (
            "import importlib, sys\nfrom pathlib import Path\n"
            f"_native_roots = {{name: Path(root) for name, root in "
            f"{elected_roots!r}}}\n"
            f"_native_standard = Path({str(standard)!r})\n"
            f"_native_packages = tuple(Path(root) for root in {packages!r})\n"
            f"_native_receipts = {{Path(path): receipt for path, receipt in "
            f"{tuple((str(path), receipt) for path, receipt in receipts.items())!r}}}\n"
            f"_native_payloads = {{Path(path): content for path, content in "
            f"{tuple((str(path), content) for path, content in payloads.items())!r}}}\n"
            f"sys.path[:0] = tuple(root for root in {imports!r} "
            "if root not in sys.path)\n"
            + self._NATIVE_REFERENCE_LOADER
            + "from flext_infra import m\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n" + "selections = tuple("
            "m.Infra.SourceClassReference.model_validate_json(item)"
            f" for item in {selections!r})\n"
            "for item in selections: importlib.import_module(item.target)\n"
            + c.Infra.FRESH_IMPORT_ORIGIN_CODE.replace(
                c.Infra.FRESH_IMPORT_ORIGINS_PLACEHOLDER, repr(origins)
            )
            + "reference = native.capture(selections).unwrap()\n"
            "reference = reference.model_copy(update={'executed_sources': tuple("
            "m.Cli.AtomicFileReceipt.model_validate_json(receipt) "
            "for path, receipt in sorted(_native_trace.items()))})\n"
            "sys.stdout.write(reference.model_dump_json())\n"
        )
        return self.execute_probe(
            m.Infra.FreshImportProbe(subject="native reference", code=code),
            cwd=request.repository_root,
            source_roots=roots,
            isolated=True,
        )

    def build_report(
        self,
        packages: t.StrSequence = (),
        *,
        publications: t.SequenceOf[m.Infra.LazyInitPlan] = (),
        repository_roots: t.SequenceOf[Path] = (),
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate complete publications, stopping at the first causal failure.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        layouts_result = self._project_layouts(repository_roots)
        if layouts_result.failure:
            return r[m.Infra.ValidationReport].from_failure(layouts_result)
        layouts = layouts_result.value
        origin_code = self._origin_code(layouts)
        probes: t.MutableSequenceOf[m.Infra.FreshImportProbe] = []
        for layout in layouts:
            built = self._layout_probes(layout, origin_code, publications)
            if built.failure:
                return r[m.Infra.ValidationReport].from_failure(built)
            probes.extend(built.value)
        packaged = self._package_probes(packages, origin_code)
        if packaged.failure:
            return r[m.Infra.ValidationReport].from_failure(packaged)
        probes.extend(packaged.value)
        if not probes:
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=True,
                    violations=(),
                    summary="0 fresh-import probe(s) passed",
                ),
            )
        return self._execute_probes(probes, layouts)

    def _stage_journal_authority(
        self,
        view: m.Infra.StagePackageView,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Verify journal authority, containment and finalized intentions in order.

        Returns:
            The destination proof or the first journal authority failure.

        """
        authority = FlextInfraMiseArtifactsState.unchanged_journal(
            session, "staged view journal authority changed"
        )
        if authority.failure:
            return r[bool].from_failure(authority)
        topology = FlextInfraMiseArtifactsVerification.journal_topology(
            session.plan.layout, session.journal
        )
        if topology.failure:
            return r[bool].from_failure(topology)
        if not any(
            view.root.is_relative_to(participant.transaction_root)
            and view.root != participant.transaction_root
            for participant in session.plan.layout.file_participants
        ):
            return r[bool].fail(
                "candidate view escapes registered participant transaction roots"
            )
        receipts = {
            intent.before.path: intent.created
            for intent in session.journal.staging_intents
        }
        if any(
            entry.kind == "file" and receipts.get(entry.path) != entry
            for entry in view.manifest.entries
        ):
            return r[bool].fail(
                "candidate file has no durable finalized staging intention"
            )
        return self._stage_target_current(view, session)

    @staticmethod
    def _stage_target_current(
        view: m.Infra.StagePackageView,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Bind the staged target hash to its canonical live destination.

        Returns:
            Success only for the matching destination journal entry.

        """
        original_layout = next(
            (
                layout
                for layout in view.plan.layouts
                if layout.package_name == view.plan.package
            ),
            None,
        )
        if original_layout is None:
            return r[bool].fail(
                "candidate selected package has no pinned original layout"
            )
        original_target = original_layout.src_dir / Path(
            *view.plan.module.split(".")
        ).with_suffix(c.Infra.EXT_PYTHON)
        target_entry: m.Infra.CodegenJournalEntry | None = None
        for entry in session.journal.entries:
            resolved = FlextInfraMiseArtifactsFiles.resolve_transaction(
                session.plan.layout,
                entry.path,
                purpose="staged public facade destination",
            )
            if resolved.failure:
                return r[bool].from_failure(resolved)
            if resolved.value == original_target:
                target_entry = entry
        if target_entry is None or target_entry.desired_sha256 != view.target.sha256:
            return r[bool].fail(
                "candidate target hash has no matching live-destination journal entry"
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _stage_sources_current(
        plan: m.Infra.StagePackagePlan,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Re-prove each pinned source against its original journal record.

        Returns:
            Success or the first missing, unreadable or changed source authority.

        """
        for source in plan.inputs:
            previous = next(
                (item for item in session.journal.sources if item.path == source.path),
                None,
            )
            if previous is None:
                return r[bool].fail(
                    f"candidate input is not journal-bound: {source.path}"
                )
            record = FlextInfraMiseArtifactsJournal.source_record(
                previous.phase, source, previous
            )
            if record.failure:
                return r[bool].from_failure(record)
            if record.value != previous:
                return r[bool].fail(
                    f"candidate source authority differs: {source.path}"
                )
        return r[bool].ok(value=True)

    def _authenticate_stage_view(
        self,
        view: m.Infra.StagePackageView,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.StagePackageView]:
        """Authenticate the existing view before constructing its consumer.

        Returns:
            The unchanged view only after every pre-consumer proof succeeds.

        """
        authority = self._stage_journal_authority(view, session)
        if authority.failure:
            return r[m.Infra.StagePackageView].from_failure(authority)
        sources = self._stage_sources_current(view.plan, session)
        if sources.failure:
            return r[m.Infra.StagePackageView].from_failure(sources)
        before = u.Cli.atomic_inventory_physical_tree(view.root)
        if before.failure:
            return r[m.Infra.StagePackageView].from_failure(before)
        if before.value != view.manifest or view.target not in view.manifest.entries:
            return r[m.Infra.StagePackageView].fail(
                "candidate tree differs from authenticated view manifest",
            )
        originals = self._stage_inputs_current(view.plan)
        if originals.failure:
            return r[m.Infra.StagePackageView].from_failure(originals)
        return r[m.Infra.StagePackageView].ok(view)

    def validate_stage_view(
        self,
        view: m.Infra.StagePackageView,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Consume actual candidate public exports in a cache-free child process.

        The package view is a materialized journal artifact, not a sys.path alias
        for the old checkout. Every candidate module origin and target hash is
        checked, and original inputs/tree identities are re-proven afterward.

        Returns:
            Success only after authentication, import and post-consumer barriers.

        """
        authenticated = self._authenticate_stage_view(view, session)
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        view = authenticated.value
        plan = view.plan
        code = (
            c.Infra.FRESH_IMPORT_PRELUDE
            + (
                "from hashlib import sha256\n"
                f"if {plan.package!r} in sys.modules "
                f"or {plan.module!r} in sys.modules:\n"
                "    raise ImportError('staged consumer inherited a cached package')\n"
                f"public = importlib.import_module({plan.package!r})\n"
                f"facade = getattr(public, 't')\n"
                f"published = getattr(public, {plan.classname!r})\n"
                f"candidate = importlib.import_module({plan.module!r})\n"
                f"owner = getattr(importlib.import_module({plan.owner_module!r}), "
                f"{plan.classname!r})\n"
                "if Path(candidate.__file__).resolve() != "
                f"Path({str(view.target.path)!r}):\n"
                "    raise ImportError('public facade did not originate "
                "in the candidate target')\n"
                "if sha256(Path(candidate.__file__).read_bytes()).hexdigest() != "
                f"{view.target.sha256!r}:\n"
                "    raise ImportError('candidate facade bytes differ "
                "from desired hash')\n"
                f"if facade is not published or facade.__module__ != {plan.module!r} "
                "or facade.__bases__ != (owner,):\n"
                "    raise ImportError('public t/full-owner identity "
                "contract differs')\n"
                f"for module_name, name in {tuple(plan.upstream)!r}:\n"
                "    upstream = getattr(importlib.import_module(module_name), name)\n"
                "    if upstream not in owner.__bases__ "
                "or not issubclass(facade, upstream):\n"
                "        raise ImportError('canonical upstream type identity "
                "differs')\n"
                f"for name in {tuple(plan.members)!r}:\n"
                "    if getattr(facade, name) is not getattr(owner, name):\n"
                "        raise ImportError('public facade changed "
                "an owner declaration')\n"
                f"sealed = {tuple(layout.package_name for layout in view.layouts)!r}\n"
                "for loaded_name in tuple(sys.modules):\n"
                "    if loaded_name.split('.')[0] in "
                f"{tuple(plan.workspace_packages)!r} "
                "and loaded_name.split('.')[0] not in sealed:\n"
                "        raise ImportError('unsealed workspace runtime dependency: ' "
                "+ loaded_name)\n"
            )
            + self._origin_code(view.layouts)
        )
        probe = m.Infra.FreshImportProbe(
            subject=f"staged {plan.module}: public t/{plan.classname}", code=code
        )
        report = self._execute_probes((probe,), view.layouts)
        if report.failure:
            return r[bool].from_failure(report)
        if not report.value.passed:
            return r[bool].fail(
                "\n".join((report.value.summary, *report.value.violations))
            )
        barrier = self._stage_consumer_barrier(view, session)
        if barrier.failure:
            return r[bool].from_failure(barrier)
        u.Cli.info(
            f"staged-consumer passed: {plan.module} origin={view.target.path} "
            f"sha256={view.target.sha256}",
        )
        return r[bool].ok(value=True)

    def _stage_consumer_barrier(
        self,
        view: m.Infra.StagePackageView,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Re-prove the staged tree, journal and original inputs after import.

        Returns:
            Success only if the consumer changed none of its authenticated inputs.

        """
        after = u.Cli.atomic_inventory_physical_tree(view.root)
        if after.failure:
            return r[bool].from_failure(after)
        if after.value != view.manifest:
            return r[bool].fail("candidate tree identity changed during public import")
        journal_barrier = FlextInfraMiseArtifactsState.unchanged_journal(
            session, "staged view journal changed during consumer"
        )
        if journal_barrier.failure:
            return r[bool].from_failure(journal_barrier)
        return self._stage_inputs_current(view.plan)

    @staticmethod
    def _stage_inputs_current(plan: m.Infra.StagePackagePlan) -> p.Result[bool]:
        """Reject source changes and additions to the sealed package/resource set.

        Returns:
            Success only when source states and every inventory remain pinned.

        """
        states = FlextInfraMiseArtifactsVerification.states_current(plan.inputs)
        if states.failure:
            return states
        for layout in plan.layouts:
            roots = (
                layout.package_dir,
                layout.project_root / c.Infra.CODEGEN_CONFIG_DIR,
            )
            expected = {
                state.path
                for state in plan.inputs
                if state.content is not None
                and any(state.path.is_relative_to(root) for root in roots)
            }
            actual = FlextInfraValidateFreshImport._stage_source_inventory(roots)
            if actual.failure:
                return r[bool].from_failure(actual)
            if actual.value != expected:
                return r[bool].fail(
                    f"candidate source inventory changed: {layout.package_name}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _stage_source_inventory(roots: t.SequenceOf[Path]) -> p.Result[set[Path]]:
        """Collect physical source files without accepting symlinked originals.

        Returns:
            The observed inventory or the first symlink failure.

        """
        actual: set[Path] = set()
        for root in roots:
            if root.is_symlink():
                return r[set[Path]].fail(
                    f"candidate original directory became a symlink: {root}",
                )
            if not root.is_dir():
                continue
            files = FlextInfraValidateFreshImport._stage_root_files(root)
            if files.failure:
                return files
            actual.update(files.value)
        return r[set[Path]].ok(actual)

    @staticmethod
    def _stage_root_files(root: Path) -> p.Result[set[Path]]:
        """Collect one source directory's physical files, refusing any symlink.

        Returns:
            The directory's files outside bytecode caches, or the first symlink.

        """
        files: set[Path] = set()
        for path in root.rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                return r[set[Path]].fail(
                    f"candidate original path became a symlink: {path}",
                )
            if path.is_file():
                files.add(path)
        return r[set[Path]].ok(files)

    @staticmethod
    def _project_layouts(
        repository_roots: t.SequenceOf[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.RopeProjectLayout]]:
        """Resolve one Rope layout per requested repository root.

        Returns:
            The resulting project layouts.

        """
        layouts: t.MutableSequenceOf[m.Infra.RopeProjectLayout] = []
        for root in repository_roots:
            layout = u.Infra.layout(root)
            if layout is None:
                return r[t.VariadicTuple[m.Infra.RopeProjectLayout]].fail(
                    f"fresh-import has no Python layout for {root}",
                )
            layouts.append(layout)
        return r[t.VariadicTuple[m.Infra.RopeProjectLayout]].ok(tuple(layouts))

    @staticmethod
    def _origin_code(layouts: t.SequenceOf[m.Infra.RopeProjectLayout]) -> str:
        """Render the origin-containment guard code for the probed layouts.

        Returns:
            The origin guard source injected into every probe.

        """
        origins = tuple(
            (layout.package_name, str(layout.package_dir.resolve()))
            for layout in layouts
        )
        return c.Infra.FRESH_IMPORT_ORIGIN_CODE.replace(
            c.Infra.FRESH_IMPORT_ORIGINS_PLACEHOLDER,
            repr(origins),
        )

    def _layout_probes(
        self,
        layout: m.Infra.RopeProjectLayout,
        origin_code: str,
        publications: t.SequenceOf[m.Infra.LazyInitPlan],
    ) -> p.Result[t.MutableSequenceOf[m.Infra.FreshImportProbe]]:
        """Build one layout's entry-point and export probes.

        Returns:
            The resulting probes for the layout.

        """
        source = u.Cli.files_read_text(layout.project_root / c.PYPROJECT_FILENAME)
        if source.failure:
            return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].from_failure(source)
        payload = u.Cli.toml_mapping_from_text(source.value)
        if payload is None:
            return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].fail(
                f"invalid published pyproject in {layout.project_root}",
            )
        metadata = m.Infra.FreshImportMetadata.model_validate(payload).project
        probes = self._entry_point_probes(layout, metadata, origin_code)
        export = self._export_probe(layout, origin_code, publications)
        if export.failure:
            return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].from_failure(export)
        probes.append(export.value)
        return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].ok(probes)

    def _entry_point_probes(
        self,
        layout: m.Infra.RopeProjectLayout,
        metadata: m.Infra.FreshImportEntryPoints,
        origin_code: str,
    ) -> t.MutableSequenceOf[m.Infra.FreshImportProbe]:
        """Build one probe per declared console, GUI, and entry point.

        Returns:
            The entry-point probes of the layout.

        """
        groups: list[t.Pair[str, t.StrMapping]] = []
        if metadata.scripts is not None:
            groups.append(("console_scripts", metadata.scripts))
        if metadata.gui_scripts is not None:
            groups.append(("gui_scripts", metadata.gui_scripts))
        if metadata.entry_points is not None:
            groups.extend(metadata.entry_points.items())
        probes: t.MutableSequenceOf[m.Infra.FreshImportProbe] = []
        for group, entries in groups:
            for name, value in entries.items():
                probes.append(
                    m.Infra.FreshImportProbe(
                        subject=f"{layout.package_name}: {group}/{name}={value}",
                        code=(
                            c.Infra.FRESH_IMPORT_PRELUDE + f"EntryPoint(name={name!r}, "
                            f"value={value!r}, group={group!r}).load()\n" + origin_code
                        ),
                    ),
                )
        return probes

    def _export_probe(
        self,
        layout: m.Infra.RopeProjectLayout,
        origin_code: str,
        publications: t.SequenceOf[m.Infra.LazyInitPlan],
    ) -> p.Result[m.Infra.FreshImportProbe]:
        """Build one layout's public-export probe from its plan contract.

        A publication plan is the generation transaction's own receipt for a
        package it rewrote. The lazy-init planner only covers the packages of
        a single Rope workspace index, so a workspace root plans its own
        packages while a transaction that also declares member repositories
        leaves those members planless (their initializers are owned by their
        own self-scoped runs). A layout no plan claims is therefore verified
        against its real on-disk contract: import it in the fresh runtime and
        resolve the exports it declares. A plan that does claim the layout
        must still carry an importable, non-removal contract, and a
        broken live package fails on its import or on a declared name that
        cannot resolve.

        Returns:
            The resulting export probe of the layout.

        """
        layout_plans = tuple(
            plan
            for plan in publications
            if plan.context.pkg_dir.is_relative_to(layout.package_dir)
        )
        if layout_plans:
            owned = tuple(
                plan
                for plan in layout_plans
                if plan.context.importable
                and plan.action is not c.Infra.LazyInitAction.REMOVE
            )
            if not any(plan.context.pkg_dir == layout.package_dir for plan in owned):
                return r[m.Infra.FreshImportProbe].fail(
                    f"missing public export contract for {layout.package_name}",
                )
            body = "".join(
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=plan.context.current_pkg
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(
                    exports=tuple(plan.exports)
                )
                for plan in owned
            )
        else:
            body = (
                c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(
                    package=layout.package_name
                )
                + origin_code
                + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(exports=())
            )
        return r[m.Infra.FreshImportProbe].ok(
            m.Infra.FreshImportProbe(
                subject=layout.package_name,
                code=c.Infra.FRESH_IMPORT_PRELUDE + body + origin_code,
            ),
        )

    def _package_probes(
        self,
        packages: t.StrSequence,
        origin_code: str,
    ) -> p.Result[t.MutableSequenceOf[m.Infra.FreshImportProbe]]:
        """Build one whole-package import probe per declared package name.

        Returns:
            The resulting package probes.

        """
        probes: t.MutableSequenceOf[m.Infra.FreshImportProbe] = []
        for package in packages:
            if not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(package):
                return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].fail(
                    f"{package}: not a valid Python package name",
                )
            probes.append(
                m.Infra.FreshImportProbe(
                    subject=package,
                    code=c.Infra.FRESH_IMPORT_PRELUDE
                    + c.Infra.FRESH_IMPORT_EXPORT_IMPORT_CODE.format(package=package)
                    + origin_code
                    + c.Infra.FRESH_IMPORT_EXPORT_RESOLVE_CODE.format(exports=()),
                ),
            )
        return r[t.MutableSequenceOf[m.Infra.FreshImportProbe]].ok(probes)

    def _execute_probes(
        self,
        probes: t.SequenceOf[m.Infra.FreshImportProbe],
        layouts: t.SequenceOf[m.Infra.RopeProjectLayout],
    ) -> p.Result[m.Infra.ValidationReport]:
        """Run every probe in the declared runtime and judge the outcomes.

        The probes execute the target checkout's code, so they run in the
        declared runtime root's environment (the generated Makefile's
        RUNTIME_ROOT), never the one hosting this tool: probing with the
        host's dependency set would grade the target against packages it
        does not install.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        workers = config.Infra.codegen.fresh_import_workers
        u.Cli.info(f"fresh-import: running {len(probes)} probes with {workers} workers")

        # Each source travels on stdin because the workspace export probe may
        # exceed the kernel's single-argument limit. map preserves report order.
        # ``-B``: a validator never writes into the checkout it validates, so
        # the probed sources leave no bytecode cache behind.
        def run_probe(probe: m.Infra.FreshImportProbe) -> p.Result[p.Cli.CommandOutput]:
            return self.execute_probe(
                probe,
                source_roots=tuple(layout.src_dir for layout in layouts),
            )

        with ThreadPoolExecutor(max_workers=workers) as executor:
            outcomes = tuple(executor.map(run_probe, probes))
        for probe, smoke in zip(probes, outcomes, strict=True):
            if smoke.failure:
                return r[m.Infra.ValidationReport].from_failure(smoke)
            output = smoke.value
            if u.Cli.process_succeeded(output.outcome):
                continue
            outcome = m.Cli.ProcessOutcome.model_validate(
                output.outcome,
                from_attributes=True,
            )
            detail = (
                f"{probe.subject}: {outcome.model_dump_json()}\n"
                f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}"
            )
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=False,
                    violations=(detail,),
                    summary=f"fresh-import failed: {probe.subject}",
                ),
            )
        summary = f"{len(probes)} fresh-import probe(s) passed"
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(passed=True, violations=(), summary=summary),
        )

    def execute_probe(
        self,
        probe: m.Infra.FreshImportProbe,
        *,
        cwd: Path | None = None,
        source_roots: t.SequenceOf[Path] = (),
        isolated: bool = False,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run the selected native consumer in its declared physical runtime.

        Returns:
            Result carrying the consumer's command output, or a failure when
            the runtime is not a physical directory or the interpreter is
            missing.

        """
        interpreter = u.Infra.runtime_python(
            self.repository_root,
            runtime_root=self.runtime_root,
        )
        environment = u.Infra.runtime_environment_dir(
            self.repository_root,
            runtime_root=self.runtime_root,
        )
        if environment.is_symlink() or not environment.is_dir():
            return r[p.Cli.CommandOutput].fail(
                f"fresh-import runtime must be physical: {environment}",
            )
        if not interpreter.is_file():
            return r[p.Cli.CommandOutput].fail(
                f"fresh-import target interpreter is missing: {interpreter}; "
                "make setup provisions it",
            )
        return u.Cli.run_raw(
            [
                str(interpreter),
                *("-O",) * sys.flags.optimize,
                *(("-I",) if isolated else ()),
                "-B",
                "-W",
                "error",
                "-",
            ],
            cwd=self.repository_root if cwd is None else cwd,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(
                env=self._workspace_import_env(source_roots),
                input_data=probe.code,
            ),
        )

    def _workspace_import_env(
        self,
        source_roots: t.SequenceOf[Path] = (),
    ) -> t.StrMapping:
        """Prefer the complete candidate fleet over inherited editable installs.

        Returns:
            The resulting ``t.StrMapping``.

        """
        inherited_env = u.Cli.process_env()
        import_roots = (
            *(str(root) for root in source_roots),
            str(self.repository_root),
            str(self.repository_root / c.Infra.DEFAULT_SRC_DIR),
        )
        existing = inherited_env.get(c.Infra.ORCHESTRATOR_ENV_PYTHONPATH, "")
        pythonpath = c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
            part for part in (*import_roots, existing) if part
        )
        return u.Cli.process_env(
            overrides={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: pythonpath},
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the same guard used by managed publication.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result = self.build_report(packages=self.packages)
        if result.failure:
            return r[bool].from_failure(result)
        report = result.value
        return (
            r[bool].ok(value=True)
            if report.passed
            else r[bool].fail("\n".join((report.summary, *report.violations)))
        )


__all__: t.StrSequence = ("FlextInfraValidateFreshImport",)
