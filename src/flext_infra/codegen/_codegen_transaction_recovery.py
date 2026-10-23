"""Journal persistence and recovery owner for the generation transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import secrets
from collections.abc import MutableMapping
from pathlib import Path

from flext_infra import c, codegen, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenFileLeases,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMiseRecovery,
    FlextInfraMiseWorkspacePlanner,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions


class FlextInfraCodegenTransactionRecovery(FlextInfraCodegenFileLeases):
    """Persist owned journal receipts and recover exactly what they authorize."""

    def __init__(
        self,
        owner: p.Infra.MiseArtifactsOwner,
        *,
        participant_policy: p.Infra.CodegenParticipantPolicy | None = None,
        producer: m.Infra.CodegenPhaseAnalysis | None = None,
        source_authority: m.Infra.CodegenSourceAuthority | None = None,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome] = (),
    ) -> None:
        """Initialize journal planning and recovery for one Mise artifact owner.

        Raises:
            ValueError: If reference staging and publication share one
                authority.

        """
        super().__init__(participant_policy)
        self._planner = FlextInfraMiseWorkspacePlanner(owner)
        self._recovery = FlextInfraMiseRecovery()
        self._journal_receipts: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        if source_authority is not None and (
            producer is not None or prior_publications
        ):
            msg = "reference staging and publication require distinct authorities"
            raise ValueError(msg)
        self._source_authority = source_authority
        self._prior_publications = prior_publications
        self._producer = producer

    def record_publication(
        self,
        session: m.Infra.CodegenTransactionSession,
        *,
        phase: str | None = None,
        completed: bool = False,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Persist cumulative gains before any subsequent phase can fail.

        Returns:
            The session whose published paths and issues have been recorded.

        """
        derived = self.publication_outcome(
            session,
            phase=phase,
            completed=completed,
        )
        if derived.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(derived)
        outcome = derived.value
        evidence = FlextInfraCodegenTransactionRecovery.publish_outcome(
            session.plan.layout.scope_root,
            outcome,
        )
        if evidence.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(evidence)
        if completed and outcome.pending_files:
            return r[m.Infra.CodegenTransactionSession].fail(
                "publication accounting is incomplete: "
                + ", ".join(str(path) for path in outcome.pending_files),
                error_code=c.Infra.ToolOutcome.ERROR.value,
            )
        return r[m.Infra.CodegenTransactionSession].ok(session)

    def publication_outcome(
        self,
        session: m.Infra.CodegenTransactionSession,
        *,
        phase: str | None = None,
        completed: bool = False,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Derive the receipt from the exact invocation's native journal state.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        original = self._publication_journal_current(session)
        if original.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(original)
        journal = original.value
        destinations: list[Path] = []
        for entry in session.journal.entries:
            destination = FlextInfraMiseArtifactsFiles.resolve_transaction(
                session.plan.layout,
                entry.path,
                purpose="publication accounting",
            )
            if destination.failure:
                return r[m.Infra.CodegenPhaseOutcome].from_failure(destination)
            destinations.append(destination.value)
        effect_targets = tuple(dict.fromkeys(destinations))
        observed_targets = {
            *session.written_files,
            *session.retained_files,
            *(Path(issue.file) for issue in session.issues),
        }
        attempted_files = tuple(
            path for path in effect_targets if path in observed_targets
        )
        pending_files = tuple(
            path for path in effect_targets if path not in observed_targets
        )
        sources = list(session.journal.sources)
        for publication in session.published_files:
            before = FlextInfraMiseArtifactsJournal.source_record(
                publication.phase,
                publication.before,
            )
            if before.failure:
                return r[m.Infra.CodegenPhaseOutcome].from_failure(before)
            sources.append(before.value)
        if session.journal.phase == c.Infra.CodegenStagedFilePhase.DOCS:
            sources.extend(
                output.model_copy(
                    update={"phase": c.Infra.CodegenStagedFilePhase.DOCS},
                )
                for output in session.journal.outputs
                if output.path in session.written_files
                and u.Infra.docs_source_path_is_input(
                    output.path,
                    session.journal.scope_roots,
                    source_scope=session.journal.source_scope,
                )
            )
        created = {
            item.created.path: item.created
            for item in session.journal.directories
            if item.created is not None
        }
        topology = tuple(
            item.model_copy(
                update={
                    "anchor_path": item.target,
                    "anchor_device": created[item.target].device,
                    "anchor_inode": created[item.target].inode,
                    "anchor_ancestry": (
                        *item.anchor_ancestry,
                        *(
                            (created[path].device, created[path].inode)
                            for path in item.directories
                        ),
                    ),
                    "directories": (),
                }
            )
            if item.directories and all(path in created for path in item.directories)
            else item
            for item in session.journal.source_topology
        )
        outcome = m.Infra.CodegenPhaseOutcome(
            root=session.plan.layout.scope_root,
            transaction_id=session.journal.transaction_id,
            phase=phase or session.journal.phase,
            completed=completed and not pending_files,
            written_files=session.written_files,
            published_files=session.published_files,
            retained_files=session.retained_files,
            effect_targets=effect_targets,
            attempted_files=attempted_files,
            pending_files=pending_files,
            issues=session.issues,
            exception=session.exception,
            sources=tuple(sources),
            outputs=session.journal.outputs,
            generator_sources=session.journal.generator_sources,
            generator_trees=session.journal.generator_trees,
            generator_modules=session.journal.generator_modules,
            generator_reference=journal.generator_reference,
            source_topology=topology,
            source_directories=tuple(
                receipt for _phase, receipt in session.journal.source_directories
            ),
            source_query_topology=tuple(
                receipt for _phase, receipt in session.journal.source_query_topology
            ),
            scope_roots=session.journal.scope_roots,
            source_scope=session.journal.source_scope,
        )
        return self._owned_publication_outcome(outcome)

    @staticmethod
    def _owned_publication_outcome(
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Bind a newly constructed physical receipt to its live writer.

        Returns:
            The exact receipt emitted here, or its storage failure.

        """
        private = outcome.__pydantic_private__
        if private is None:
            return r[m.Infra.CodegenPhaseOutcome].fail(
                "publication receipt has no Pydantic private storage",
            )
        private["_publication_birth"] = (
            id(outcome),
            u.Cli.sha256_content(outcome.model_dump_json()),
        )
        return r[m.Infra.CodegenPhaseOutcome].ok(outcome)

    def _publication_journal_current(
        self,
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Authenticate the exact journal emitted by this publication owner.

        Returns:
            Its exact invocation-owned journal, or the first origin failure.

        """
        result_type = r[m.Infra.CodegenTransactionJournal]
        original = self._live_producer_journal(session.journal)
        if original.failure:
            return result_type.from_failure(original)
        saved = self._journal_receipts.get(session.plan.layout.journal_path)
        if saved is None or saved.content is None:
            return result_type.fail("publication has no invocation-owned journal")
        recorded = m.Infra.CodegenTransactionJournal.model_validate_json(saved.content)
        if recorded.model_dump(exclude={"state"}) != session.journal.model_dump(
            exclude={"state"},
        ):
            return result_type.fail("publication differs from its own journal receipt")
        return original

    @staticmethod
    def publish_outcome(
        root: Path,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Archive every typed native receipt and publish operations by surface.

        ``conform --mode check`` authenticates the latest receipt of its own
        surface. Each operation receipt therefore occupies only its surface's
        slot: a partial publication (setup's runtime bindings, upg's
        pyproject and mise-config) never evicts the generation receipt, and a
        generation retires the partial slots it supersedes. Batch receipts
        carry no surface and stay in the transaction archive only.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if outcome.transaction_id is None or outcome.root != root:
            return r[bool].fail("publication receipt lacks its actual scope identity")
        storage = FlextInfraMiseArtifactsVerification.publication_storage_root(root)
        if storage.failure:
            return r[bool].from_failure(storage)
        path = c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        digest = u.Cli.sha256_content(outcome.model_dump_json())
        archived = u.Infra.publish_refactor_report_evidence(
            root,
            outcome,
            relative_path=c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH
            / outcome.transaction_id
            / f"{digest}{path.suffix}",
        )
        if archived.failure:
            return r[bool].from_failure(archived)
        surface = outcome.surface
        if surface is None:
            return r[bool].ok(value=True)
        latest = u.Infra.publish_refactor_report_evidence(
            root,
            outcome,
            relative_path=FlextInfraMiseArtifactsVerification.publication_receipt(
                surface
            ),
        )
        if latest.failure or surface is not c.Infra.CodegenConformSurface.ALL:
            return latest.map(lambda _value: True)
        return FlextInfraCodegenTransactionRecovery._retire_partial_receipts(
            storage.value
        )

    @staticmethod
    def _retire_partial_receipts(root: Path) -> p.Result[bool]:
        """Remove partial-surface slots a generation receipt now supersedes.

        Returns:
            True once no partial slot remains, or the first read/delete failure.

        """
        for surface in c.Infra.CodegenConformSurface:
            if surface is c.Infra.CodegenConformSurface.ALL:
                continue
            slot = FlextInfraMiseArtifactsFiles.read_state(
                root / FlextInfraMiseArtifactsVerification.publication_receipt(surface),
                required=False,
            )
            if slot.failure:
                return r[bool].from_failure(slot)
            if slot.value.content is None:
                continue
            retired = u.Cli.atomic_delete_binary_file_guarded(slot.value)
            if retired.failure:
                return r[bool].from_failure(retired)
        return r[bool].ok(value=True)

    @staticmethod
    def _admitted_operation_receipt(
        candidate: m.Infra.CodegenPhaseOutcome,
        operation: m.Infra.CodegenPhaseOutcome | None,
    ) -> p.Result[bool]:
        """Admit an operation receipt before it is composed and published.

        The original operation is still born of this invocation and matches
        the actual request, every batch output stays inside the operation
        participants, and a completed operation proves every batch output.

        Returns:
            Success, or the first admission failure.

        """
        if operation is not None:
            original = FlextInfraMiseArtifactsVerification.publication_birth_current(
                operation,
            )
            if original.failure:
                return original
        mismatched = operation is not None and (
            operation.root != candidate.root
            or operation.surface != candidate.surface
            or operation.scope != candidate.scope
            or operation.module != candidate.module
        )
        if not candidate.scope_roots or mismatched:
            return r[bool].fail("operation receipt differs from its actual request")
        pending = list(candidate.batches)
        while pending:
            batch = pending.pop()
            pending.extend(batch.batches)
            outside = tuple(
                output.path
                for output in batch.outputs
                if not any(
                    output.path.is_relative_to(scope) for scope in candidate.scope_roots
                )
            )
            if outside:
                return r[bool].fail(
                    "batch output is outside the operation participants: "
                    + ", ".join(map(str, outside)),
                )
        incomplete = (
            candidate.error
            or candidate.issues
            or candidate.exception is not None
            or not candidate.batches
        )
        if candidate.completed and (
            incomplete
            or any(
                not item.completed
                or item.error
                or item.issues
                or item.pending_files
                or item.root is None
                or item.transaction_id is None
                or not (item.outputs or item.batches)
                for item in candidate.batches
            )
        ):
            return r[bool].fail(
                "operation completion requires every actual batch output proof",
            )
        return r[bool].ok(value=True)

    @classmethod
    def publish_operation_receipt(
        cls,
        request: p.Infra.CodegenConformRequest,
        batches: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        publication: p.Infra.CodegenPublicationOutcome,
        operation: m.Infra.CodegenPhaseOutcome | None = None,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Compose actual native batches without reopening their settled journals.

        Publication supplies accounting state, not authenticated provenance. The
        original operation remains the identity-bearing admission receipt.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
        state = m.Infra.CodegenPhaseOutcome.model_validate(
            publication,
            from_attributes=True,
        )
        root = request.root.expanduser().resolve()
        outcome = m.Infra.CodegenPhaseOutcome(
            root=root,
            transaction_id=(
                operation.transaction_id
                if operation is not None
                else secrets.token_hex(16)
            ),
            phase=c.Infra.CodegenStagedFilePhase.CONFORM,
            surface=request.what,
            scope=request.scope,
            module=request.module,
            scope_roots=state.scope_roots,
            completed=state.completed,
            batches=batches,
            written_files=tuple(
                path for item in batches for path in item.written_files
            ),
            issues=(
                *state.issues,
                *(issue for item in batches for issue in item.issues),
            ),
            exception=state.exception,
            error=str(state.exception) if state.exception is not None else "",
        )
        admitted = cls._admitted_operation_receipt(outcome, operation)
        if admitted.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(admitted)
        if state.completed:
            with cls.mutation_lease(root):
                current = (
                    FlextInfraMiseArtifactsVerification.publication_outputs_current(
                        batches
                    )
                )
            if current.failure:
                return r[m.Infra.CodegenPhaseOutcome].from_failure(current)
            return cls._owned_publication_outcome(outcome).flat_map(
                cls.publish_operation_report
            )
        with cls.mutation_lease(root):
            written = cls.publish_outcome(root, outcome)
        if written.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(written)
        return cls._owned_publication_outcome(outcome)

    @classmethod
    def publish_operation_report(
        cls, outcome: m.Infra.CodegenPhaseOutcome
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Publish the final user reports through the existing native file journal.

        Returns:
            The recorded operation, or its original admission/publication failure.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        admitted = cls._admitted_final_report(outcome)
        if admitted.failure:
            return result_type.from_failure(admitted)
        root, surface = outcome.root, outcome.surface
        if root is None or surface is None or outcome.transaction_id is None:
            return result_type.fail(
                "final report requires its native operation identity"
            )
        planned = cls._operation_report_files(root, surface, outcome)
        if planned.failure:
            return result_type.from_failure(planned)
        plans, inputs = planned.value
        members = tuple(sorted(plan.path for plan in plans))
        plans = tuple(
            plan.model_copy(
                update={
                    "dependency_group": (
                        f"publication-evidence:{outcome.transaction_id}"
                    ),
                    "dependency_members": members,
                }
            )
            for plan in plans
        )
        owner = codegen.FlextInfraCodegenTransaction(
            codegen.FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        phase = c.Infra.CodegenStagedFilePhase.CONFORM
        roots = owner.capability_roots(phase.value, (root,))
        receipts: list[m.Infra.CodegenPhaseOutcome] = []
        published = owner.run_files_locked(
            roots,
            lambda scope: owner.publish_file_phase_locked(
                scope,
                roots,
                m.Infra.CodegenPhaseAnalysis(phase=phase, files=plans, inputs=inputs),
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=tuple(
                        sorted({
                            plan.path.parent
                            for plan in plans
                            if plan.desired_content is not None
                            and isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                        })
                    )
                ),
                publication_receipts=receipts,
            ),
        )
        if published.failure:
            return result_type.from_failure(published)
        recorded = outcome.model_copy(
            update={
                "batches": (*outcome.batches, *receipts),
                "written_files": tuple(
                    dict.fromkeys((*outcome.written_files, *published.value))
                ),
            }
        )
        persisted = cls.publish_outcome(root, recorded)
        if persisted.failure:
            return result_type.from_failure(persisted)
        return cls._owned_publication_outcome(recorded)

    @staticmethod
    def _admitted_final_report(
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[bool]:
        """Require the original complete operation before planning its reports.

        Returns:
            Success, or the first origin, identity, or completion failure.

        """
        born = FlextInfraMiseArtifactsVerification.publication_birth_current(outcome)
        if born.failure:
            return born
        if (
            outcome.root is None
            or outcome.surface is None
            or outcome.transaction_id is None
        ):
            return r[bool].fail("final report requires its native operation identity")
        if not outcome.completed:
            return r[bool].fail("source reports require a completed native operation")
        if not outcome.batches:
            return r[bool].fail("completed operation has no native artifact batch")
        return r[bool].ok(value=True)

    @classmethod
    def _operation_report_files(
        cls,
        root: Path,
        surface: c.Infra.CodegenConformSurface,
        outcome: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Plan report publication and retirement from original native evidence.

        Returns:
            Report file plans and their immutable inputs, or the first failure.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        if outcome.transaction_id is None:
            return result_type.fail(
                "final report requires its native operation identity"
            )
        content = outcome.model_dump_json().encode(c.DEFAULT_ENCODING)
        report = FlextInfraMiseArtifactsVerification.publication_receipt(surface)
        archive = (
            c.Infra.CODEGEN_PUBLICATION_ARCHIVE_RELATIVE_PATH
            / outcome.transaction_id
            / f"{u.Cli.sha256_bytes(content)}{report.suffix}"
        )
        desired: t.MutableMappingKV[Path, bytes | None] = {
            root / archive: content,
            root / report: content,
        }
        inputs: tuple[m.Cli.AtomicFileState, ...] = ()
        if surface is c.Infra.CodegenConformSurface.ALL:
            evidence = cls._retained_plan_evidence(root)
            if evidence.failure:
                return result_type.from_failure(evidence)
            if evidence.value.content is None:
                return result_type.fail(
                    "native planning report lacks its original bytes"
                )
            desired[root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH] = (
                evidence.value.content
            )
            inputs = (evidence.value,)
        plans: list[m.Infra.CodegenFilePlan] = []
        for path, payload in desired.items():
            before = u.Infra.codegen_target_snapshot(path)
            if before.failure:
                return result_type.from_failure(before)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=path,
                    before=before.value,
                    desired_content=payload,
                    desired_mode=config.Infra.codegen.modes.file_default
                    if payload is not None
                    else None,
                    source_states=inputs,
                )
            )
        if surface is c.Infra.CodegenConformSurface.ALL:
            partials = cls._partial_report_retirements(root, inputs)
            if partials.failure:
                return result_type.from_failure(partials)
            plans.extend(partials.value)
        return result_type.ok((tuple(plans), inputs))

    @staticmethod
    def _partial_report_retirements(
        root: Path,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Retire partial receipt slots superseded by a complete operation.

        Returns:
            Deletion plans for existing slots, or the first read failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        plans: list[m.Infra.CodegenFilePlan] = []
        for surface in c.Infra.CodegenConformSurface:
            if surface is c.Infra.CodegenConformSurface.ALL:
                continue
            path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
                surface
            )
            before = FlextInfraMiseArtifactsFiles.read_state(path, required=False)
            if before.failure:
                return result_type.from_failure(before)
            if before.value.content is not None:
                plans.append(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before.value,
                        desired_content=None,
                        desired_mode=None,
                        source_states=inputs,
                    )
                )
        return result_type.ok(tuple(plans))

    @staticmethod
    def _retained_plan_evidence(root: Path) -> p.Result[m.Cli.AtomicFileState]:
        """Retain this operation's bytes before CHECK replaces its mutable slot.

        Returns:
            The immutable native planning report, or the first storage failure.

        """
        storage = FlextInfraMiseArtifactsVerification.publication_storage_root(root)
        if storage.failure:
            return r[m.Cli.AtomicFileState].from_failure(storage)
        evidence = FlextInfraMiseArtifactsFiles.read_state(
            storage.value / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH, required=True
        )
        if evidence.failure:
            return evidence
        retained = u.Infra.publish_mod_native_artifact(
            storage.value, evidence.value.path
        )
        return FlextInfraMiseArtifactsFiles.read_state(retained.path, required=True)

    def bind_publication_proof(
        self,
        session: m.Infra.CodegenTransactionSession,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        topology: m.Infra.CodegenPhaseOutcome | None = None,
        phase: c.Infra.CodegenStagedFilePhase | None = None,
        batch_admission: m.Infra.CodegenPhaseOutcome | None = None,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Bind physical output proof to this writer's original journal.

        ``topology`` names the receipt whose source topology, scope roots and
        source scope the journal adopts; without it the journal keeps its own.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        admitted_plans = u.Infra.codegen_file_publication_admission(plans)
        if admitted_plans.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(admitted_plans)
        owned = self._publication_journal_current(session)
        if owned.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(owned)
        proven = self._proof_outputs(session, plans, batch_admission)
        if proven.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(proven)
        outputs = proven.value
        adopted = topology or session.journal
        native_directories, native_topology = (
            FlextInfraMiseArtifactsJournal.source_query_records(
                session.journal,
                plans,
                phase=batch_admission.phase if batch_admission is not None else phase,
            )
        )
        journal = session.journal.model_copy(
            update={
                "outputs": tuple(outputs.values()),
                "source_topology": adopted.source_topology
                or session.journal.source_topology,
                "scope_roots": adopted.scope_roots or session.journal.scope_roots,
                "source_scope": adopted.source_scope or session.journal.source_scope,
                "phase": phase or session.journal.phase,
                "source_directories": native_directories,
                "source_query_topology": native_topology,
            }
        )
        written = self._write_journal(
            session.plan.layout,
            journal,
            expected=session.journal_state,
        )
        if written.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(written)
        return r[m.Infra.CodegenTransactionSession].ok(
            session.model_copy(
                update={
                    "journal": journal,
                    "journal_state": written.value,
                }
            )
        )

    @staticmethod
    def _proof_outputs(
        session: m.Infra.CodegenTransactionSession,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        batch_admission: m.Infra.CodegenPhaseOutcome | None,
    ) -> p.Result[t.MutableMappingKV[Path, m.Infra.CodegenJournalSource]]:
        """Record each plan's physical output proof over the journal's outputs.

        Returns:
            Journal output records keyed by path, or the first proof failure.

        """
        result_type = r[t.MutableMappingKV[Path, m.Infra.CodegenJournalSource]]
        outputs = {item.path: item for item in session.journal.outputs}
        if batch_admission is not None:
            if (
                batch_admission.analysis is None
                or batch_admission.analysis.files != plans
                or {item.path for item in batch_admission.outputs}
                != {item.path for item in plans}
            ):
                return result_type.fail(
                    "output proof differs from its native admitted plan",
                )
            outputs.update({item.path: item for item in batch_admission.outputs})
        admitted = {item.before.path: item for item in session.published_files}
        for plan in plans:
            state = FlextInfraCodegenTransactionRecovery._proof_output_state(
                session, plan, admitted
            )
            if state.failure:
                return result_type.from_failure(state)
            record = FlextInfraMiseArtifactsJournal.source_record(
                "output", state.value, path=plan.path
            )
            if record.failure:
                return result_type.from_failure(record)
            outputs[plan.path] = record.value
        return result_type.ok(outputs)

    @staticmethod
    def _observed_proof_state(
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]:
        """Prove one unplanned output against its authenticated preimage.

        Args:
            session: Locked transaction session binding the publication.
            plan: The file plan requiring its proof output.

        Returns:
            The observed proof output state, or the first read, binding or
            preimage failure.

        """
        result_type = r[m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]
        observed = FlextInfraMiseArtifactsFiles.read_state(
            plan.path,
            required=(
                isinstance(plan.before, m.Cli.AtomicFileState)
                and plan.before.content is not None
            ),
        )
        if observed.failure:
            return result_type.from_failure(observed)
        expected = (
            m.Cli.AtomicFileState(path=plan.path)
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
            else plan.before
        )
        if expected.parent_device is None and observed.value.parent_device is not None:
            rebound = FlextInfraMiseArtifactsVerification.bind_source_parent(
                expected,
                session.journal,
            )
            if rebound.failure:
                return result_type.from_failure(rebound)
            expected = rebound.value
        if observed.value != expected:
            return result_type.fail(
                "generation output differs from its authenticated preimage: "
                f"{plan.path}",
            )
        return result_type.ok(
            plan.before
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
            and observed.value.parent_device is None
            else observed.value
        )

    @staticmethod
    def _proof_output_state(
        session: m.Infra.CodegenTransactionSession,
        plan: m.Infra.CodegenFilePlan,
        admitted: t.MappingKV[Path, m.Infra.CodegenStagedFile],
    ) -> p.Result[m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]:
        """Resolve one plan's proof output state from its published record.

        Args:
            session: Locked transaction session binding the publication.
            plan: The file plan requiring its proof output.
            admitted: Published files keyed by their original path.

        Returns:
            The proof output state, or the first read or preimage failure.

        """
        result_type = r[m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]
        actual = admitted.get(plan.path)
        if actual is not None and actual.replacement is not None:
            return result_type.ok(actual.replacement)
        if actual is not None:
            absent = FlextInfraMiseArtifactsFiles.read_state(
                plan.path,
                required=False,
            )
            if absent.failure:
                return result_type.from_failure(absent)
            if absent.value.content is not None:
                return result_type.fail(
                    f"published deletion changed before proof: {plan.path}",
                )
            return result_type.ok(absent.value)
        return FlextInfraCodegenTransactionRecovery._observed_proof_state(session, plan)

    def participant_policy(
        self,
        *,
        initial_workspace: p.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[p.Infra.CodegenParticipantPolicy]:
        """Snapshot the canonical physical topology without creating state.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenParticipantPolicy]``.

        """
        result_type = r[p.Infra.CodegenParticipantPolicy]
        layout = self._planner.layout(initial_workspace=initial_workspace)
        if layout.failure:
            return result_type.from_failure(layout)
        roots: list[m.Cli.AtomicDirectoryChainPlan] = []
        for project in layout.value.projects:
            observed = u.Cli.atomic_plan_directory_chain(project.root)
            if observed.failure:
                return result_type.from_failure(observed)
            roots.append(observed.value)
        return result_type.ok(
            m.Infra.CodegenParticipantPolicy(
                scope_root=layout.value.scope_root,
                roots=tuple(roots),
            ),
        )

    def inspect_journal(self) -> p.Result[m.Infra.CodegenFootprint]:
        """Read the typed journal under its lease without recovery or writes.

        Inspects the journal in place; it neither recovers it nor writes any
        destination.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenFootprint]``.

        """
        identity = self._planner.repository_identity()
        if identity.failure:
            return r[m.Infra.CodegenFootprint].from_failure(identity)
        with u.Infra.codegen_transaction_lease(
            self._planner.journal_path(identity.value),
        ):
            return self._inspect_journal(identity.value)

    def validate_footprint(
        self,
        footprint: m.Infra.CodegenFootprint,
    ) -> p.Result[m.Infra.CodegenFootprint]:
        """Authorize the current journal under its lease without recovering it.

        Returns:
            The current authenticated footprint, independent of earlier observations.

        """
        identity = self._coordinated_identity()
        if identity.failure:
            return r[m.Infra.CodegenFootprint].from_failure(identity)
        layout = self._planner.journal_layout(identity.value)
        if layout.failure:
            return r[m.Infra.CodegenFootprint].from_failure(layout)
        if (
            layout.value.journal_path != footprint.journal_path
            or identity.value.repo_root != footprint.scope_root
        ):
            return r[m.Infra.CodegenFootprint].fail(
                "generation footprint journal anchor changed",
            )
        with u.Infra.codegen_transaction_lease(layout.value.journal_path):
            return self._validate_footprint_locked(identity.value)

    def _coordinated_identity(self) -> p.Result[m.Infra.GitIdentityReport]:
        """Resolve the scope identity and hold it against the participant policy.

        Returns:
            The scope identity anchored at the authorized coordination root.

        """
        if self._participant_policy is None:
            return r[m.Infra.GitIdentityReport].fail(
                "footprint validation requires request authorization",
            )
        identity = self._planner.repository_identity()
        if identity.failure:
            return r[m.Infra.GitIdentityReport].from_failure(identity)
        return self._coordination_root_authorized(identity.value.repo_root).map(
            lambda _: identity.value
        )

    def _coordination_root_authorized(self, root: Path) -> p.Result[bool]:
        """Admit the workspace root or one authorized member as journal anchor.

        File journals live in the Git directory of the repository a run writes,
        so the anchor is either the policy scope root or one declared member.

        Returns:
            Success when ``root`` is an authorized coordination anchor.

        """
        policy = self._participant_policy
        if (
            policy is None
            or root == policy.scope_root
            or root in {item.target for item in policy.roots}
        ):
            return r[bool].ok(value=True)
        return r[bool].fail("generation authorization coordination root differs")

    def _validate_footprint_locked(
        self,
        identity: m.Infra.GitIdentityReport,
    ) -> p.Result[m.Infra.CodegenFootprint]:
        """Observe and authorize current journal authority while its lease is held.

        Returns:
            The current footprint or its actual authorization failure.

        """
        observed = self._inspect_journal(identity)
        if observed.failure:
            return r[m.Infra.CodegenFootprint].from_failure(observed)
        layout = self._planner.journal_layout(identity)
        if layout.failure:
            return r[m.Infra.CodegenFootprint].from_failure(layout)
        authorized = (
            self._authorize_journal(layout.value, observed.value.journal)
            if observed.value.journal is not None
            else self._authorize_roots((identity.repo_root,))
        )
        if authorized.failure:
            return r[m.Infra.CodegenFootprint].from_failure(authorized)
        return observed

    def _inspect_journal(
        self,
        identity: m.Infra.GitIdentityReport,
    ) -> p.Result[m.Infra.CodegenFootprint]:
        result_type = r[m.Infra.CodegenFootprint]
        layout = self._planner.journal_layout(identity)
        if layout.failure:
            return result_type.from_failure(layout)
        observed = FlextInfraMiseArtifactsState.journal_state(layout.value)
        if observed.failure:
            return result_type.from_failure(observed)
        snapshot = FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
        if snapshot is None:
            return result_type.fail("generation journal has no physical parent")
        journal: m.Infra.CodegenTransactionJournal | None = None
        if snapshot.content is not None:
            loaded = FlextInfraMiseArtifactsJournal.read(layout.value)
            if loaded.failure:
                return result_type.from_failure(loaded)
            journal, snapshot = loaded.value
        return result_type.ok(
            m.Infra.CodegenFootprint(
                scope_root=identity.repo_root,
                journal_path=layout.value.journal_path,
                snapshot_identity=snapshot.model_dump_json(exclude={"content"}),
                snapshot_sha256=(
                    u.Cli.sha256_bytes(snapshot.content)
                    if snapshot.content is not None
                    else None
                ),
                journal_version=journal.version if journal is not None else None,
                transaction_id=journal.transaction_id if journal is not None else None,
                normalized_journal_sha256=(
                    u.Cli.sha256_bytes(
                        journal.model_dump_json().encode(c.DEFAULT_ENCODING),
                    )
                    if journal is not None
                    else None
                ),
                journal_state=journal.state if journal is not None else "absent",
                pending_roots=(
                    (
                        *(
                            identity.repo_root / project.selector
                            for project in journal.projects
                        ),
                        *(
                            participant.root
                            for participant in journal.file_participants
                        ),
                    )
                    if journal is not None
                    else ()
                ),
                pending_destinations=(
                    tuple(entry.path for entry in journal.entries)
                    if journal is not None
                    else ()
                ),
                pending_directories=(
                    tuple(directory.path for directory in journal.directories)
                    if journal is not None
                    else ()
                ),
                pending_staging=(
                    (
                        *(
                            participant.transaction_root
                            for participant in journal.file_participants
                        ),
                        *(intent.before.path for intent in journal.staging_intents),
                    )
                    if journal is not None
                    else ()
                ),
                journal=journal,
                snapshot=snapshot,
            ),
        )

    def _authorize_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[bool]:
        """Validate every recorded effect before leases, restore, or cleanup.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        roots = (
            *(layout.scope_root / project.selector for project in journal.projects),
            *(participant.root for participant in journal.file_participants),
        )
        authorized = self._authorize_roots(roots)
        if authorized.failure or self._participant_policy is None:
            return authorized
        anchored = self._coordination_root_authorized(layout.scope_root)
        if anchored.failure:
            return anchored
        recorded_layout = layout.model_copy(
            update={"file_participants": journal.file_participants},
        )
        paths: list[Path] = [
            participant.transaction_root for participant in journal.file_participants
        ]
        paths.extend(intent.before.path for intent in journal.staging_intents)
        paths.extend(
            directory.before.path
            for directory in journal.directories
            if directory.before is not None
        )
        paths.extend(
            directory.created.path
            for directory in journal.directories
            if directory.created is not None
        )
        for selector in (
            *(entry.path for entry in journal.entries),
            *(directory.path for directory in journal.directories),
            *(
                selector
                for entry in journal.entries
                for selector in (entry.desired_staging,)
                if selector is not None
            ),
        ):
            resolved = FlextInfraMiseArtifactsFiles.resolve_transaction(
                recorded_layout,
                selector,
                purpose="authorized generation effect",
            )
            if resolved.failure:
                return r[bool].from_failure(resolved)
            paths.append(resolved.value)
        return self._authorize_roots(roots, tuple(paths))

    def _preflight_journal(
        self,
        identity: m.Infra.GitIdentityReport,
    ) -> p.Result[bool]:
        """Refuse foreign pending authority while holding the scope journal lease.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if self._participant_policy is None:
            return r[bool].ok(value=True)
        authorized = self._coordination_root_authorized(identity.repo_root).flat_map(
            lambda _: self._authorize_roots((identity.repo_root,))
        )
        if authorized.failure:
            return authorized
        observed = self._validate_footprint_locked(identity)
        if observed.failure:
            return r[bool].from_failure(observed)
        return r[bool].ok(value=True)

    def _materialize_directories(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Create and durably bind one directory identity at a time.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]
        authorized = self._authorize_journal(layout, journal)
        if authorized.failure:
            return result_type.from_failure(authorized)
        current_journal = journal
        current_state = journal_state
        for intent in current_journal.directories:
            if intent.created is not None:
                continue
            materialized = self._create_and_record_directory(
                layout,
                current_journal,
                current_state,
                intent,
            )
            if materialized.failure:
                return result_type.from_failure(materialized)
            current_journal, current_state = materialized.value
        manifested = FlextInfraMiseArtifactsJournal.record_transaction_manifests(
            layout,
            current_journal,
        )
        if manifested.failure:
            return result_type.from_failure(manifested)
        for previous, recorded in zip(
            current_journal.directories,
            manifested.value.directories,
            strict=True,
        ):
            if (
                previous.manifest is None
                and recorded.manifest is not None
                and recorded.manifest.entries
            ):
                return result_type.fail(
                    f"new transaction tree contains unregistered entries: "
                    f"{recorded.path}",
                )
        persisted = self._write_journal(
            layout,
            manifested.value,
            expected=current_state,
        )
        if persisted.failure:
            return result_type.from_failure(persisted)
        return result_type.ok((manifested.value, persisted.value))

    def _create_and_record_directory(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
        intent: m.Infra.CodegenJournalDirectory,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Create one journaled directory, then record and persist its receipt.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]
        created = FlextInfraMiseArtifactsState.create_journaled_directory(
            layout,
            journal.directories,
            intent,
        )
        if created.failure:
            return result_type.from_failure(
                self._recover_failure(
                    layout,
                    r[bool].from_failure(created),
                ),
            )
        directories = tuple(
            created.value if entry.path == intent.path else entry
            for entry in journal.directories
        )
        recorded = FlextInfraMiseArtifactsJournal.record_directories(
            journal,
            directories,
        )
        if recorded.failure:
            failed = self._compensate_directory_persistence(
                layout,
                created.value,
                r[bool].from_failure(recorded),
                journal_write=False,
            )
            return result_type.from_failure(failed)
        persisted = self._write_journal(
            layout,
            recorded.value,
            expected=journal_state,
        )
        if persisted.failure:
            failed = self._compensate_directory_persistence(
                layout,
                created.value,
                r[bool].from_failure(persisted),
                journal_write=True,
            )
            return result_type.from_failure(failed)
        return result_type.ok((recorded.value, persisted.value))

    def _compensate_directory_persistence(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        created: m.Infra.CodegenJournalDirectory,
        failure: p.FailureLike,
        *,
        journal_write: bool,
        context: str | None = None,
    ) -> p.Result[bool]:
        """Compensate only this invocation's exact empty-directory effect.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        original = r[bool].from_failure(failure)
        compensated = FlextInfraMiseArtifactsState.compensate_created_directory(created)
        if compensated.failure:
            if original.exception is not None:
                original.exception.add_note(
                    f"created-directory compensation failed: {compensated.error}"
                )
            return r[bool].fail(
                original.error,
                exception=original.exception,
                error_code=original.error_code,
                error_data={
                    **(original.error_data or {}),
                    "cleanup_error": compensated.error,
                    "recovery_context": context,
                },
            )
        if journal_write:
            return self._handle_journal_write_failure(layout, original, context=context)
        return self._recover_failure(layout, original, context=context)

    def _recover_prepared(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> p.Result[bool]:
        """Recover only the latest journal receipt written by this transaction.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected = self._journal_receipts.get(layout.journal_path)
        if expected is None:
            observed = FlextInfraMiseArtifactsState.journal_state(layout)
            if observed.failure:
                return r[bool].from_failure(observed)
            snapshot = FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
            if snapshot is not None and snapshot.content is None:
                return r[bool].ok(value=False)
            return r[bool].fail("generation recovery has no invocation journal receipt")
        return self._recover(layout, expected=expected)

    def _reconcile(self, identity: m.Infra.GitIdentityReport) -> p.Result[bool]:

        layout = self._planner.journal_layout(identity)
        if layout.failure:
            return r[bool].from_failure(layout)
        journal = FlextInfraMiseArtifactsState.journal_state(layout.value)
        if journal.failure:
            return r[bool].from_failure(journal)
        journal_snapshot = FlextInfraMiseArtifactsState.journal_snapshot(journal.value)
        if journal_snapshot is not None and journal_snapshot.content is not None:
            return self._recover(layout.value)
        residue = FlextInfraMiseArtifactsState.transaction_residue(layout.value)
        if residue:
            return r[bool].fail(
                f"generation staging has no journal authority: {residue[0]}",
            )
        return r[bool].ok(value=True)

    def _handle_journal_write_failure(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        failure: p.FailureLike,
        *,
        context: str | None = None,
    ) -> p.Result[bool]:
        original = r[bool].from_failure(failure)
        observed = FlextInfraMiseArtifactsState.journal_state(layout)
        if observed.failure:
            secondary = f"journal inspection failed: {observed.error}"
        else:
            observed_snapshot = FlextInfraMiseArtifactsState.journal_snapshot(
                observed.value
            )
            if observed_snapshot is not None and observed_snapshot.content is not None:
                return self._recover_failure(layout, original, context=context)
            secondary = "durable journal disappeared"
        if original.exception is not None:
            original.exception.add_note(secondary)
        return r[bool].fail(
            original.error,
            exception=original.exception,
            error_code=original.error_code,
            error_data={
                **(original.error_data or {}),
                "cleanup_error": secondary,
                "recovery_context": context,
            },
        )

    def _recover_failure(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        failure: p.FailureLike,
        *,
        context: str | None = None,
    ) -> p.Result[bool]:
        original = r[bool].from_failure(failure)
        try:
            recovered = self._recover_prepared(layout)
        except (OSError, ValueError) as cleanup_exception:
            recovered = r[bool].fail_op(
                "finalize failed generation publication",
                cleanup_exception,
            )
        if recovered.failure and original.exception is not None:
            original.exception.add_note(
                f"generation recovery failed: {recovered.error}"
            )
        return r[bool].fail(
            original.error,
            exception=original.exception,
            error_code=original.error_code,
            error_data={
                **(original.error_data or {}),
                "cleanup_error": recovered.error if recovered.failure else None,
                "recovery_context": context,
            },
        )

    def _write_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        expected: m.Cli.AtomicFileState,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Retain the exact owned receipt for in-session failure recovery.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        authorized = self._authorize_journal(layout, journal)
        if authorized.failure:
            return r[m.Cli.AtomicFileState].from_failure(authorized)
        written = FlextInfraMiseArtifactsJournal.write(
            layout,
            journal,
            expected=expected,
        )
        if written.success:
            self._journal_receipts[layout.journal_path] = written.value
        return written

    def _live_producer_journal(
        self,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Bind journal data to the authority explicitly supplied to this writer.

        Returns:
            The original journal, retaining any explicitly supplied reference.

        """
        result_type = r[m.Infra.CodegenTransactionJournal]
        if self._source_authority is not None:
            return result_type.fail(
                "cold source authority cannot authorize project publication",
            )
        if self._producer is None:
            return (
                result_type.ok(journal)
                if journal.generator_reference is None
                else result_type.fail("journal has an unowned producer reference")
            )
        reference = self._producer.generator_reference
        if reference is None or journal.generator_reference is None:
            return result_type.fail("journal lacks its original native producer")
        born = FlextInfraCodegenPreconditions.reference_birth_current(reference)
        if born.failure:
            return result_type.from_failure(born)
        if journal.generator_reference.model_dump() != reference.model_dump():
            return result_type.fail("journal belongs to a different native producer")
        return result_type.ok(
            journal.model_copy(update={"generator_reference": reference}),
        )

    def _recover(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        *,
        expected: m.Cli.AtomicFileState | None = None,
    ) -> p.Result[bool]:
        loaded = FlextInfraMiseArtifactsJournal.read(layout)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        journal, journal_state = loaded.value
        if expected is not None and journal_state != expected:
            return r[bool].fail(
                "generation recovery journal changed from owned receipt",
            )
        authorized = self._authorize_journal(layout, journal)
        if authorized.failure:
            return authorized
        if journal.file_participants:
            return self._recover_file_participants(
                layout,
                journal,
                journal_state,
                owned_receipt=expected is not None,
            )
        return self._recover_project_selectors(layout, journal, journal_state)

    def _recover_file_participants(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
        *,
        owned_receipt: bool,
    ) -> p.Result[bool]:
        """Recover a file-only journal under its participants' leases.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if journal.projects:
            return r[bool].fail(
                "mixed Mise and file-only recovery requires explicit composition",
            )
        if owned_receipt:
            if (
                layout.transaction_id != journal.transaction_id
                or layout.file_participants != journal.file_participants
            ):
                return r[bool].fail(
                    "owned file cleanup layout differs from authenticated journal",
                )
            recovery_layout = layout
        else:
            reconstructed = self._planner.file_layout(
                layout.scope_root,
                {item.selector: item.root for item in journal.file_participants},
                transaction_id=journal.transaction_id,
            )
            if reconstructed.failure:
                return r[bool].from_failure(reconstructed)
            recovery_layout = reconstructed.value
        if recovery_layout.journal_path != layout.journal_path:
            return r[bool].fail("file journal identity changed during recovery")
        with self._lease_file_participants(journal.file_participants):
            recovered = self._recovery.execute(
                recovery_layout,
                journal,
                journal_state,
            )
        return self._settle_recovery(layout, recovered)

    def _recover_project_selectors(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Recover a Mise journal through its recorded project selectors.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        selectors = tuple(project.selector for project in journal.projects)
        recovery_layout = self._planner.layout_from_selectors(
            layout.scope_root,
            selectors,
            transaction_id=journal.transaction_id,
        )
        if recovery_layout.failure:
            return r[bool].from_failure(recovery_layout)
        if recovery_layout.value.journal_path != layout.journal_path:
            return r[bool].fail("generation journal identity changed during recovery")
        recovered = self._recovery.execute(
            recovery_layout.value,
            journal,
            journal_state,
        )
        return self._settle_recovery(layout, recovered)

    def _settle_recovery(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        recovered: p.Result[bool],
    ) -> p.Result[bool]:
        """Drop the owned receipt once a recovery fully succeeded.

        Returns:
            The recovery outcome.

        """
        if recovered.success:
            self._journal_receipts.pop(layout.journal_path, None)
        return recovered


__all__: list[str] = ["FlextInfraCodegenTransactionRecovery"]
