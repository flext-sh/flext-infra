"""Single extensible transaction coordinator for complete project generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenTransactionGeneration,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMisePublication,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.codegen.staged_package import FlextInfraStagedPackage

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransaction(FlextInfraCodegenTransactionGeneration):
    """Keep every generation phase recoverable until one final fixed point."""

    def preview_sources[T](
        self,
        workspace: Path,
        updates: t.MappingKV[Path, str],
        validator: Callable[[Path, t.MappingKV[Path, Path]], T],
        *,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
        runtime_root: Path | None = None,
    ) -> p.Result[T]:
        """Validate a journal-owned source view without publishing live files.

        Args:
            workspace: The declared source workspace.
            updates: Desired source content keyed by live paths.
            validator: A callable that validates the source view.
            inputs: Original caller source states required to remain unchanged.
            runtime_root: Declared physical runtime for pre-check candidate imports.

        Returns:
            A result wrapping the validation outcome or the first failure encountered.


        """
        if self._source_authority is not None and updates:
            return r[T].fail(
                "cold source authority permits an unchanged reference view only",
            )
        planned = FlextInfraStagedPackage.plan_sources(
            workspace,
            updates,
            inputs=inputs,
        )
        if planned.failure:
            return r[T].from_failure(planned)
        plan = planned.value
        roots = {
            f"@stage-inputs-{index}": root
            for index, root in enumerate(sorted(plan.roots))
        }

        def validate_locked(scope_root: Path) -> p.Result[T]:
            source_barrier = FlextInfraStagedPackage.source_inputs_current(plan)
            if source_barrier.failure:
                return r[T].from_failure(source_barrier)
            started = self.begin_files_locked(scope_root, roots, plan.inputs)
            if started.failure:
                return r[T].from_failure(started)
            session = started.value

            def validate_prepared(
                prepared: m.Infra.CodegenTransactionSession,
            ) -> p.Result[T]:
                participant = next(
                    item
                    for item in prepared.plan.layout.file_participants
                    if item.root == plan.workspace
                )
                view_root = participant.transaction_root / "source-view"
                candidates = {
                    path: view_root / path.relative_to(plan.workspace)
                    for path in plan.updates
                }
                materialized = self._materialize_source_preview(
                    prepared,
                    plan,
                    view_root,
                )
                if materialized.failure:
                    return r[T].from_failure(materialized)
                current_session, manifest = materialized.value
                consumed = self._source_runtime_consumer(plan, view_root, runtime_root)
                if consumed.failure:
                    return r[T].from_failure(consumed)
                value = validator(view_root, candidates)
                barrier = self._source_preview_current(
                    plan,
                    manifest,
                    current_session,
                )
                if barrier.failure:
                    return r[T].from_failure(barrier)
                return self._cleaned_source_preview_value(prepared, value)

            return self.publish_prepared_locked(session, validate_prepared)

        return self.run_files_locked(roots, validate_locked)

    def _cleaned_source_preview_value[T](
        self,
        prepared: m.Infra.CodegenTransactionSession,
        value: T,
    ) -> p.Result[T]:
        """Recover the prepared source preview and release its captured value.

        Args:
            prepared: The prepared session owning the staging layout.
            value: The validated value captured from the live source view.

        Returns:
            The captured value after clean recovery, or the recovery failure
            annotated with its residual cleanup error.

        """
        cleaned = self._recover_prepared(prepared.plan.layout)
        if cleaned.failure:
            return r[T].fail(
                cleaned.error or "source preview staging cleanup failed",
                error_code=cleaned.error_code,
                exception=cleaned.exception,
                error_data={
                    **(cleaned.error_data or {}),
                    "cleanup_error": cleaned.error,
                },
            )
        return r[T].ok(value)

    def _materialize_source_preview(
        self,
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.StageSourcePlan,
        view_root: Path,
    ) -> p.Result[
        t.Pair[m.Infra.CodegenTransactionSession, m.Cli.AtomicPhysicalTreeManifest]
    ]:
        """Record the actual materialized view through the existing journal writer.

        Returns:
            The prepared cursor and its authenticated candidate manifest.

        """
        return self._materialize_package_writes(
            session,
            self._source_preview_writes(plan, view_root),
        ).flat_map(
            lambda current: u.Cli.atomic_inventory_physical_tree(view_root).map(
                lambda manifest: (current, manifest),
            )
        )

    @staticmethod
    def _source_runtime_consumer(
        plan: m.Infra.StageSourcePlan,
        view_root: Path,
        runtime_root: Path | None,
    ) -> p.Result[bool]:
        """Import sealed runtime modules before any candidate check callback.

        Returns:
            Actual native consumer success or its first causal failure.

        """
        if runtime_root is None:
            return r[bool].ok(value=True)
        environment = u.Infra.runtime_environment_dir(
            plan.workspace, runtime_root=runtime_root
        )
        interpreter = u.Infra.runtime_python(plan.workspace, runtime_root=runtime_root)
        if environment.is_symlink() or not environment.is_dir():
            return r[bool].fail(f"candidate runtime must be physical: {environment}")
        observed = u.Cli.atomic_plan_directory_chain(environment)
        if observed.failure:
            return r[bool].from_failure(observed)
        identity = observed.value
        bindings = tuple(
            (
                layout.package_name,
                str(view_root / layout.src_dir.relative_to(plan.workspace)),
            )
            for layout in plan.layouts
        )
        modules = tuple(
            sorted({
                ".".join(
                    (*path.relative_to(layout.src_dir).with_suffix("").parts[:-1],)
                    if path.stem == "__init__"
                    else path.relative_to(layout.src_dir).with_suffix("").parts
                )
                for layout in plan.layouts
                for path in (state.path for state in plan.inputs)
                if path.suffix == c.Infra.EXT_PYTHON
                and path.is_relative_to(layout.package_dir)
            })
        )
        code = (
            "import ast, importlib, importlib.util, sys\n"
            "from importlib.machinery import PathFinder\n"
            "from graphlib import TopologicalSorter\n"
            "from pathlib import Path\n"
            f"if Path(sys.prefix).resolve() != Path({str(environment)!r}).resolve():\n"
            "    raise RuntimeError('candidate interpreter escaped "
            "declared physical runtime')\n"
            f"environment = Path({str(environment)!r})\n"
            f"expected = {(identity.anchor_device, identity.anchor_inode)!r}\n"
            "before = environment.stat()\n"
            "if environment.is_symlink() "
            "or (before.st_dev, before.st_ino) != expected:\n"
            "    raise RuntimeError('candidate physical runtime identity changed')\n"
            f"bindings = {bindings!r}\n"
            "specs = {}\n"
            "dependencies = {}\n"
            "namespaces = {name for name, source in bindings}\n"
            "for name, source in bindings:\n"
            "    if name in sys.modules:\n"
            "        raise ImportError('candidate inherited cached package: ' + name)\n"
            "    spec = PathFinder.find_spec(name, [source])\n"
            "    if spec is None or spec.loader is None:\n"
            "        raise ImportError('unsupported candidate package: ' + name)\n"
            "    sys.modules[name] = importlib.util.module_from_spec(spec)\n"
            "    specs[name] = spec\n"
            "    imports = []\n"
            "    for node in ast.parse(Path(spec.origin).read_text()).body:\n"
            "        if isinstance(node, ast.Import):\n"
            "            imports.extend(alias.name for alias in node.names)\n"
            "        elif (isinstance(node, ast.ImportFrom) "
            "and not node.level and node.module):\n"
            "            imports.append(node.module)\n"
            "    dependencies[name] = {module.split('.')[0] for module in imports}\n"
            "    dependencies[name].intersection_update(namespaces - {name})\n"
            "for name in TopologicalSorter(dependencies).static_order():\n"
            "    spec = specs[name]\n"
            "    spec.loader.exec_module(sys.modules[spec.name])\n"
            f"for name in {modules!r}:\n"
            "    importlib.import_module(name)\n"
            "origins = {name: Path(source) / name for name, source in bindings}\n"
            "for name, module in tuple(sys.modules.items()):\n"
            "    namespace = name.split('.')[0]\n"
            f"    if namespace not in {tuple(plan.workspace_packages)!r}:\n"
            "        continue\n"
            "    root = origins.get(namespace)\n"
            "    origin = getattr(module, '__file__', None)\n"
            "    paths = getattr(module, '__path__', ())\n"
            "    if (root is None or origin is None\n"
            "        or not Path(origin).resolve().is_relative_to(root)\n"
            "        or any(not Path(path).resolve().is_relative_to(root) "
            "for path in paths)):\n"
            "        raise ImportError('unsealed candidate origin: ' "
            "+ name + ': ' + str(origin))\n"
            "after = environment.stat()\n"
            "if environment.is_symlink() or (after.st_dev, after.st_ino) != expected:\n"
            "    raise RuntimeError('candidate physical runtime identity changed')\n"
        )
        output = u.Cli.run_raw(
            [str(interpreter), "-I", "-B", "-W", "error", "-"],
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(
                input_data=code,
                remove_env_keys=(c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,),
            ),
        )
        if output.failure:
            return r[bool].from_failure(output)
        if not u.Cli.process_succeeded(output.value.outcome) or output.value.stderr:
            return r[bool].fail(
                f"candidate runtime consumer failed: {output.value.outcome}:\n"
                f"{output.value.stdout}{output.value.stderr}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _source_preview_current(
        plan: m.Infra.StageSourcePlan,
        manifest: m.Cli.AtomicPhysicalTreeManifest,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[bool]:
        """Bind acceptance to unchanged candidate, live sources and journal.

        Returns:
            Success only while every pre-consumer observation remains current.

        """
        current = u.Cli.atomic_inventory_physical_tree(manifest.root.path)
        if current.failure:
            return r[bool].from_failure(current)
        if current.value != manifest:
            before = {entry.path: entry for entry in (manifest.root, *manifest.entries)}
            after = {
                entry.path: entry
                for entry in (current.value.root, *current.value.entries)
            }
            changed = tuple(
                str(path.relative_to(manifest.root.path))
                for path in sorted(before.keys() | after.keys())
                if before.get(path) != after.get(path)
            )
            return r[bool].fail(
                f"source preview candidate changed during validation: {changed}"
            )
        originals = FlextInfraStagedPackage.source_inputs_current(plan)
        if originals.failure:
            return r[bool].from_failure(originals)
        journal = FlextInfraMiseArtifactsState.unchanged_journal(
            session,
            "source preview journal changed during validation",
        )
        if journal.failure:
            return r[bool].from_failure(journal)
        return r[bool].ok(originals.value)

    @staticmethod
    def _source_preview_writes(
        plan: m.Infra.StageSourcePlan,
        view_root: Path,
    ) -> t.VariadicTuple[tuple[Path, bytes, int]]:
        """Build the staged writes that materialize the previewed source view.

        Returns:
            One (destination, content, mode) write per existing or desired source input.

        """
        writes: list[tuple[Path, bytes, int]] = []
        for before in plan.inputs:
            if not before.path.is_relative_to(plan.workspace):
                continue
            content = (
                plan.updates[before.path].encode(c.DEFAULT_ENCODING)
                if before.path in plan.updates
                else before.content
            )
            if content is None:
                continue
            writes.append((
                view_root / before.path.relative_to(plan.workspace),
                content,
                before.mode if before.mode is not None else c.Infra.CONFIG_SPEC[1],
            ))
        return tuple(writes)

    def run_files_locked[T](
        self,
        roots: t.MappingKV[str, Path],
        operation: Callable[[Path], p.Result[T]],
        *,
        prepare: bool = True,
    ) -> p.Result[T]:
        """Hold Git and shared destination leases before planning or recovery.

        Returns:
            The resulting ``p.Result[T]``.

        """
        identity = self._authorized_run_identity(roots)
        if identity.failure:
            return r[T].from_failure(identity)
        proposed = self._planner.file_layout(
            identity.value.repo_root,
            roots,
            transaction_id=secrets.token_hex(16),
        )
        if proposed.failure:
            return r[T].from_failure(proposed)
        with u.Infra.codegen_transaction_lease(
            self._planner.journal_path(identity.value),
        ):
            participants = self._file_recovery_participants(
                proposed.value,
                prepare=prepare,
            )
            if participants.failure:
                return r[T].from_failure(participants)
            with self._lease_file_participants(
                participants.value,
                held_roots=frozenset({identity.value.repo_root.resolve()}),
            ):
                if not prepare:
                    residue = FlextInfraMiseArtifactsState.transaction_residue(
                        proposed.value,
                    )
                    if residue:
                        return r[T].fail(
                            "unregistered generation staging blocks readiness: "
                            f"{residue[0]}",
                        )
                    u.Cli.info(
                        "stage=file-transaction-readiness "
                        "journal=absent residue=0 leased=true",
                    )
                return self._run_locked_operation(
                    identity.value,
                    prepare=prepare,
                    operation=operation,
                )

    def _authorized_run_identity(
        self,
        roots: t.MappingKV[str, Path],
    ) -> p.Result[m.Infra.GitIdentityReport]:
        """Resolve the scope identity and authorize roots and journal for a run.

        Returns:
            The scope identity report of the transaction scope.

        """
        producer = self._file_session_authority()
        if producer.failure:
            return r[m.Infra.GitIdentityReport].from_failure(producer)
        identity = self._planner.scope_identity()
        if identity.failure:
            return r[m.Infra.GitIdentityReport].from_failure(identity)
        authorized = self._authorize_roots(tuple(roots.values()))
        if authorized.failure:
            return r[m.Infra.GitIdentityReport].from_failure(authorized)
        return identity

    def _file_recovery_participants(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        *,
        prepare: bool,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFileParticipant]]:
        """Authenticate current and recorded participants under the journal lease.

        Returns:
            The ordered participants whose destination leases must be acquired.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFileParticipant]]
        participants = {item.root: item for item in layout.file_participants}
        observed = FlextInfraMiseArtifactsState.journal_state(layout)
        if observed.failure:
            return result_type.from_failure(observed)
        snapshot = FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
        if snapshot is not None and snapshot.content is not None:
            if not prepare:
                return result_type.fail(
                    "pending file generation journal blocks read-only readiness; "
                    "authenticated apply recovery is required",
                )
            loaded = FlextInfraMiseArtifactsJournal.read(layout)
            if loaded.failure:
                return result_type.from_failure(loaded)
            authorized = self._authorize_journal(layout, loaded.value[0])
            if authorized.failure:
                return result_type.from_failure(authorized)
            for participant in loaded.value[0].file_participants:
                current = participants.get(participant.root)
                if current is not None and (current.device, current.inode) != (
                    participant.device,
                    participant.inode,
                ):
                    return result_type.fail(
                        "file capability identity changed before recovery",
                    )
                participants[participant.root] = participant
        return result_type.ok(tuple(participants.values()))

    def begin_files_locked(
        self,
        scope_root: Path,
        roots: t.MappingKV[str, Path],
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Authenticate the producer before creating a durable file-only cursor.

        Authority is re-proven before preparing a layout or opening its journal.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        authority = self._file_session_authority()
        if authority.failure:
            return result_type.from_failure(authority)
        prepared = self._leased_file_layout(scope_root, roots)
        if prepared.failure:
            return result_type.from_failure(prepared)
        layout = prepared.value
        if layout.transaction_id is None:
            return result_type.fail("file session lacks its invocation identity")
        plan = m.Infra.CodegenFileSessionPlan(layout=layout)
        opened = self._open_file_transaction_journal(
            layout,
            plan,
            inputs,
            layout.transaction_id,
        )
        if opened.failure:
            return result_type.from_failure(opened)
        journal, journal_state = opened.value
        return result_type.ok(
            m.Infra.CodegenTransactionSession(
                plan=plan,
                journal=journal,
                journal_state=journal_state,
            ),
        )

    def _leased_file_layout(
        self,
        scope_root: Path,
        roots: t.MappingKV[str, Path],
    ) -> p.Result[m.Infra.MiseToolchainWorkspaceLayout]:
        """Bind one invocation identity to authenticated, leased physical roots.

        This layout proof checks destination leases and their physical identities;
        the publication admission or journal entrypoint owns producer authority.

        Returns:
            The physical participant layout carrying its invocation identity.

        """
        result_type = r[m.Infra.MiseToolchainWorkspaceLayout]
        if set(roots.values()) - self._file_leases.keys():
            return result_type.fail("file session requires every destination lease")
        prepared = self._planner.file_layout(
            scope_root,
            roots,
            transaction_id=secrets.token_hex(16),
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        layout = prepared.value
        mismatch = self._file_lease_mismatch(layout)
        if mismatch is not None:
            return result_type.fail(mismatch)
        return result_type.ok(layout)

    def _file_session_authority(self) -> p.Result[bool]:
        """Resolve the current producer or cold source authority receipt.

        Returns:
            Whether the active authority is current, or its first failure.

        """
        if self._source_authority is not None:
            return FlextInfraCodegenPreconditions.source_authority_current(
                self._source_authority,
            )
        if self._producer.failure:
            return r[bool].from_failure(self._producer)
        return FlextInfraMiseArtifactsVerification.publication_outputs_current(
            self._prior_publications,
            reference=self._producer.value.generator_reference,
        ).flat_map(
            lambda outputs: FlextInfraCodegenPreconditions.producer_current(
                self._producer.value, outputs=outputs
            )
        )

    def _file_lease_mismatch(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> str | None:
        """Describe the first file participant whose identity left its lease.

        Returns:
            The mismatch message, or None when every participant still matches.

        """
        for participant in layout.file_participants:
            leased = self._file_leases[participant.root]
            if (participant.device, participant.inode) != (leased.device, leased.inode):
                return "file capability root changed after lease acquisition"
        return None

    @staticmethod
    def _file_transaction_guard(
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> p.Result[
        t.Pair[t.VariadicTuple[m.Infra.CodegenJournalDirectory], m.Cli.AtomicFileState]
    ]:
        """Require a recovered-absent journal, no residue, and stable inputs.

        Returns:
            The resulting ``p.Result[t.Pair[t.VariadicTuple[
                m.Infra.CodegenJournalDirectory], m.Cli.AtomicFileState]]`` with
            the planned transaction directories and the absent-journal baseline.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[m.Infra.CodegenJournalDirectory],
                m.Cli.AtomicFileState,
            ]
        ]
        observed = FlextInfraMiseArtifactsState.journal_state(layout)
        if observed.failure:
            return result_type.from_failure(observed)
        before = FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
        if before is None or before.content is not None:
            return result_type.fail(
                "file transaction journal is not absent after recovery",
            )
        if FlextInfraMiseArtifactsState.transaction_residue(layout):
            return result_type.fail("file transaction has unowned staging residue")
        directories = FlextInfraMiseArtifactsState.plan_transaction_directories(layout)
        if directories.failure:
            return result_type.from_failure(directories)
        return result_type.ok((directories.value, before))

    def _open_file_transaction_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        plan: m.Infra.CodegenFileSessionPlan,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
        transaction_id: str,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Open, persist, materialize, and durably prepare the file journal.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        guarded = self._file_transaction_guard(layout)
        if guarded.failure:
            return result_type.from_failure(guarded)
        directories, before = guarded.value
        journal = FlextInfraMiseArtifactsJournal.begin(
            plan,
            transaction_id=transaction_id,
            sources=tuple(("docs", source) for source in inputs),
            directories=directories,
            producer=(
                self._source_authority
                if self._source_authority is not None
                else self._producer.value
            ),
        )
        if journal.failure:
            return result_type.from_failure(journal)
        opened = self._materialize_journal(layout, journal.value, expected=before)
        if opened.failure:
            return result_type.from_failure(opened)
        recorded, recorded_state = opened.value
        prepared_journal = FlextInfraMiseArtifactsJournal.append_prepared(
            plan,
            recorded,
            (),
        )
        if prepared_journal.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].from_failure(prepared_journal),
                ),
            )
        ready = self._write_journal(
            layout,
            prepared_journal.value,
            expected=recorded_state,
        )
        if ready.failure:
            return result_type.from_failure(
                self._handle_journal_write_failure(
                    layout,
                    r[bool].from_failure(ready),
                ),
            )
        return result_type.ok((prepared_journal.value, ready.value))

    def publish_file_phase_locked(
        self,
        scope_root: Path,
        roots: t.MappingKV[str, Path],
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: m.Infra.CodegenPhasePublicationPolicy,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Compose file publication through the same durable phase lifecycle.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        result_type = r[t.VariadicTuple[Path]]
        if self._producer.failure:
            return result_type.from_failure(self._producer)
        admitted = FlextInfraMisePublication.admit_batch(
            analysis,
            producer=self._producer.value,
            admission=policy.admission,
            prior_publications=self._prior_publications,
        )
        if admitted.failure:
            return result_type.from_failure(admitted)
        if admitted.value.analysis is None:
            return result_type.fail("publication lacks its admitted producer analysis")
        analysis = admitted.value.analysis
        admission = admitted.value.model_copy(
            update={
                "source_topology": policy.source_topology
                if "source_topology" in policy.model_fields_set
                else admitted.value.source_topology,
                "scope_roots": policy.scope_roots
                if "scope_roots" in policy.model_fields_set
                else admitted.value.scope_roots,
                "source_scope": policy.source_scope
                if "source_scope" in policy.model_fields_set
                else admitted.value.source_scope,
            }
        )
        effect_free = (
            bool(analysis.files)
            and not analysis.issues
            and analysis.exception is None
            and not any(
                u.Infra.codegen_file_requires_effect(file) for file in analysis.files
            )
        )
        if effect_free and not policy.directories and policy.staged_validator is None:
            return self._publish_unchanged_file_phase(
                scope_root,
                roots,
                admission,
                publication_receipts=publication_receipts,
            )
        session = self.begin_files_locked(scope_root, roots, analysis.inputs)
        if session.failure:
            return result_type.from_failure(session)

        def publish(
            started: m.Infra.CodegenTransactionSession,
        ) -> p.Result[t.VariadicTuple[Path]]:
            """Publish the admitted phase under the prepared journal's recovery.

            Returns:
                The committed paths, or the first publication failure.

            """
            bound = self.bind_publication_proof(
                started,
                analysis.files,
                topology=admission,
                phase=analysis.phase,
                batch_admission=admission,
            )
            if bound.failure:
                return result_type.from_failure(bound)
            recorded = self.record_publication(bound.value, phase=analysis.phase)
            if recorded.failure:
                return result_type.from_failure(recorded)
            prepared = self.append_directories_locked(
                recorded.value.model_copy(
                    update={
                        "exception": recorded.value.exception or analysis.exception
                    },
                ),
                analysis.phase,
                policy.directories,
            )
            if prepared.failure:
                return result_type.from_failure(prepared)
            published = self.append_phase_locked(
                prepared.value,
                analysis.phase,
                analysis.files,
                issues=analysis.issues,
                publication_policy=policy.model_copy(update={"admission": admission}),
            )
            return published.flat_map(
                lambda ready: self.commit_locked(
                    ready,
                    publication_receipts=publication_receipts,
                )
            )

        return self.publish_prepared_locked(
            session.value,
            publish,
        )

    def _publish_unchanged_file_phase(
        self,
        scope_root: Path,
        roots: t.MappingKV[str, Path],
        admission: m.Infra.CodegenPhaseOutcome,
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome] | None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish observed no-op outputs without authorizing staging or effects.

        Returns:
            No written paths after the complete admitted observation is proven.


        """
        result_type = r[t.VariadicTuple[Path]]
        prepared = self._leased_file_layout(scope_root, roots)
        if prepared.failure:
            return result_type.from_failure(prepared)
        layout = prepared.value
        outcome = self._file_transaction_guard(layout).flat_map(
            lambda _guarded: FlextInfraMiseArtifactsJournal.observed_outcome(
                layout,
                admission,
                producer=(
                    self._source_authority
                    if self._source_authority is not None
                    else self._producer.value
                ),
            )
        )
        if outcome.failure:
            return result_type.from_failure(outcome)
        reference = self._producer.value.generator_reference
        if reference is None:
            return result_type.fail("observed publication lacks its original producer")
        storage = outcome.value.__pydantic_private__
        if storage is None:
            return result_type.fail(
                "observed publication lacks its declared private storage",
            )
        storage["_publication_birth"] = (
            id(outcome.value),
            id(reference),
            u.Cli.sha256_content(outcome.value.model_dump_json()),
        )
        current = FlextInfraMiseArtifactsVerification.publication_outputs_current(
            (*self._prior_publications, outcome.value),
            reference=self._producer.value.generator_reference,
            destinations=tuple(output.path for output in outcome.value.outputs),
        ).flat_map(lambda _current: self.publish_outcome(scope_root, outcome.value))
        if current.failure:
            return result_type.from_failure(current)
        if publication_receipts is not None:
            publication_receipts.append(outcome.value)
        return result_type.ok(())

    def validate(
        self,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[bool]:
        """Validate a coherent committed Mise snapshot under the generation lock.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return self.run_locked(
            prepare=False,
            operation=lambda scope_root: self.validate_locked(scope_root, config_plans),
        )

    def validate_locked(
        self,
        scope_root: Path,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[bool]:
        """Reject pending recovery/residue, then exercise real Mise consumers.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        selected = self._selected_validate_layout(scope_root, config_plans)
        if selected.failure:
            return r[bool].from_failure(selected)
        layout = selected.value
        journal = FlextInfraMiseArtifactsState.journal_state(layout)
        if journal.failure:
            return r[bool].from_failure(journal)
        journal_snapshot = FlextInfraMiseArtifactsState.journal_snapshot(journal.value)
        if journal_snapshot is not None and journal_snapshot.content is not None:
            return r[bool].fail(
                "pending generation transaction requires apply-mode recovery",
            )
        residue = FlextInfraMiseArtifactsState.transaction_residue(layout)
        if residue:
            return r[bool].fail(
                f"generation staging has no journal authority: {residue[0]}",
            )
        plan = self._planner.snapshot(layout, config_plans)
        if plan.failure:
            return r[bool].from_failure(plan)
        return FlextInfraMiseArtifactsVerification.live(self._owner, plan.value)

    def _selected_validate_layout(
        self,
        scope_root: Path,
        config_plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.MiseToolchainWorkspaceLayout]:
        """Derive the exact topology for a validation pass and select its scope.

        Returns:
            The resulting ``p.Result[m.Infra.MiseToolchainWorkspaceLayout]``.

        """
        layout_result = (
            self._planner.layout_for_config_plans(scope_root, config_plans)
            if config_plans
            else self._planner.layout(scope_root)
        )
        if layout_result.failure:
            return r[m.Infra.MiseToolchainWorkspaceLayout].from_failure(layout_result)
        return self._planner.select_layout(layout_result.value, config_plans)

    @staticmethod
    def validate_phase_analysis_locked(
        analysis: m.Infra.CodegenPhaseAnalysis,
        *,
        session: m.Infra.CodegenTransactionSession | None = None,
    ) -> p.Result[bool]:
        """Validate a published phase from its immutable planning receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return FlextInfraMiseArtifactsVerification.phase_analysis_live(
            analysis, session=session
        )

    def run_locked[T](
        self,
        *,
        prepare: bool,
        operation: Callable[[Path], p.Result[T]],
    ) -> p.Result[T]:
        """Own the shared journal before recovery through final publication cleanup.

        Returns:
            The resulting ``p.Result[T]``.

        """
        identity = self._planner.scope_identity()
        if identity.failure:
            return r[T].from_failure(identity)
        with u.Infra.codegen_transaction_lease(
            self._planner.journal_path(identity.value),
        ):
            return self._run_locked_operation(
                identity.value,
                prepare=prepare,
                operation=operation,
            )

    def _run_locked_operation[T](
        self,
        identity: m.Infra.GitIdentityReport,
        *,
        prepare: bool,
        operation: Callable[[Path], p.Result[T]],
    ) -> p.Result[T]:
        """Reauthenticate and reconcile after the descriptor lock is held.

        Returns:
            The resulting ``p.Result[T]``.

        """
        preflight = self._preflight_journal(identity)
        if preflight.failure:
            return r[T].from_failure(preflight)
        if prepare:
            reconciled = self._reconcile(identity)
            if reconciled.failure:
                return r[T].from_failure(reconciled)
        return operation(identity.repo_root)

    def abort_locked(
        self,
        session: m.Infra.CodegenTransactionSession,
        failure: p.FailureLike,
    ) -> p.Result[bool]:
        """Recover a native failure; reject a success before touching its journal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return self._recover_failure(session.plan.layout, failure)

    def publish_prepared_locked[T](
        self,
        session: m.Infra.CodegenTransactionSession,
        operation: Callable[[m.Infra.CodegenTransactionSession], p.Result[T]],
    ) -> p.Result[T]:
        """Run every phase after ``begin_locked`` without stranding its journal.

        A phase that fails or raises after the journal was prepared recovers
        that journal here, while the lease is still held, and keeps the cause:
        a failure retains its code and cause with cleanup evidence, and an
        exception escapes unchanged with any cleanup failure attached as a note.
        A failure whose owner already attempted or refused cleanup (it carries
        ``cleanup_error``) is returned as-is, never cleaned twice.

        Returns:
            The resulting ``p.Result[T]``.

        """
        layout = session.plan.layout

        try:
            outcome = operation(session)
        except Exception as exc:
            self._recover_failure(layout, r[bool].fail(str(exc), exception=exc))
            raise
        if outcome.failure:
            if outcome.error_data is not None and "cleanup_error" in outcome.error_data:
                return outcome
            return r[T].from_failure(
                self._recover_failure(
                    layout,
                    outcome,
                ),
            )
        return outcome


__all__: list[str] = ["FlextInfraCodegenTransaction"]
