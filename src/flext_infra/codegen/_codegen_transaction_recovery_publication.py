"""Publication receipt and output-proof mixin for the generation transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import secrets
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenFileLeases,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransactionRecoveryPublicationMixin:
    """Derive, publish, and bind the native receipts of one publication owner."""

    if TYPE_CHECKING:
        _journal_receipts: MutableMapping[Path, m.Cli.AtomicFileState]

        def _live_producer_journal(
            self,
            journal: m.Infra.CodegenTransactionJournal,
        ) -> p.Result[m.Infra.CodegenTransactionJournal]: ...

        def _write_journal(
            self,
            layout: m.Infra.MiseToolchainWorkspaceLayout,
            journal: m.Infra.CodegenTransactionJournal,
            *,
            expected: m.Cli.AtomicFileState,
        ) -> p.Result[m.Cli.AtomicFileState]: ...

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
        evidence = self.publish_outcome(session.plan.layout.scope_root, outcome)
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

    @classmethod
    def publish_outcome(
        cls,
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
        if latest.failure:
            return r[bool].from_failure(latest)
        if surface is not c.Infra.CodegenConformSurface.ALL:
            return r[bool].ok(value=True)
        return cls._retire_partial_receipts(root)

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
        if candidate.completed and (
            not candidate.batches
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
        request: m.Infra.CodegenConformRequest,
        batches: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        scope_roots: t.VariadicTuple[Path],
        operation: m.Infra.CodegenPhaseOutcome | None = None,
        completed: bool = False,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Compose actual native batches without reopening their settled journals.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
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
            scope_roots=scope_roots,
            completed=completed,
            batches=batches,
            written_files=tuple(
                path for item in batches for path in item.written_files
            ),
            issues=tuple(issue for item in batches for issue in item.issues),
        )
        admitted = cls._admitted_operation_receipt(outcome, operation)
        if admitted.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(admitted)
        with FlextInfraCodegenFileLeases.mutation_lease(root):
            if completed:
                current = (
                    FlextInfraMiseArtifactsVerification.publication_outputs_current(
                        batches,
                    )
                )
                if current.failure:
                    return r[m.Infra.CodegenPhaseOutcome].from_failure(current)
            written = cls.publish_outcome(root, outcome)
        if written.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(written)
        return cls._owned_publication_outcome(outcome)

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
        owned = self._publication_journal_current(session)
        if owned.failure:
            return r[m.Infra.CodegenTransactionSession].from_failure(owned)
        outputs = {item.path: item for item in session.journal.outputs}
        if batch_admission is not None:
            if (
                batch_admission.analysis is None
                or batch_admission.analysis.files != plans
                or {item.path for item in batch_admission.outputs}
                != {item.path for item in plans}
            ):
                return r[m.Infra.CodegenTransactionSession].fail(
                    "output proof differs from its native admitted plan",
                )
            outputs.update({item.path: item for item in batch_admission.outputs})
        admitted = {item.before.path: item for item in session.published_files}
        for plan in plans:
            state = self._proof_output_state(session, plan, admitted)
            if state.failure:
                return r[m.Infra.CodegenTransactionSession].from_failure(state)
            record = FlextInfraMiseArtifactsJournal.source_record(
                "output",
                state.value,
                path=plan.path,
            )
            if record.failure:
                return r[m.Infra.CodegenTransactionSession].from_failure(record)
            outputs[plan.path] = record.value
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

    @classmethod
    def _proof_output_state(
        cls,
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
        return cls._observed_proof_state(session, plan)


__all__: list[str] = ["FlextInfraCodegenTransactionRecoveryPublicationMixin"]
