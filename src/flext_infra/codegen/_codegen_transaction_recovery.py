"""Journal persistence and recovery owner for the generation transaction.

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
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMiseRecovery,
    FlextInfraMiseWorkspacePlanner,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransactionRecovery(FlextInfraCodegenFileLeases):
    """Persist owned journal receipts and recover exactly what they authorize."""

    def __init__(
        self,
        owner: p.Infra.MiseArtifactsOwner,
        *,
        participant_policy: m.Infra.CodegenParticipantPolicy | None = None,
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
        self._producer = (
            r[m.Infra.CodegenPhaseAnalysis].fail(
                "cold source authority cannot authorize project publication",
            )
            if source_authority is not None
            else FlextInfraCodegenPreconditions.capture_producer(
                owner.repository_root,
                entrypoint=type(self).__init__,
            )
            if producer is None
            else r[m.Infra.CodegenPhaseAnalysis].ok(producer)
        )

    @staticmethod
    def record_publication(
        session: m.Infra.CodegenTransactionSession,
        *,
        phase: str | None = None,
        completed: bool = False,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Persist cumulative gains before any subsequent phase can fail.

        Returns:
            The session whose published paths and issues have been recorded.

        """
        derived = FlextInfraCodegenTransactionRecovery.publication_outcome(
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

    @staticmethod
    def publication_outcome(
        session: m.Infra.CodegenTransactionSession,
        *,
        phase: str | None = None,
        completed: bool = False,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Derive the receipt from the exact invocation's native journal state.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseOutcome]``.

        """
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
            generator_reference=session.journal.generator_reference,
            source_topology=topology,
            scope_roots=session.journal.scope_roots,
            source_scope=session.journal.source_scope,
        )
        return r[m.Infra.CodegenPhaseOutcome].ok(outcome)

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
        return FlextInfraCodegenTransactionRecovery._retire_partial_receipts(root)

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
        mismatched = operation is not None and (
            operation.root != root
            or operation.surface != request.what
            or operation.scope != request.scope
            or operation.module != request.module
        )
        if not scope_roots or mismatched:
            return r[m.Infra.CodegenPhaseOutcome].fail(
                "operation receipt differs from its actual request",
            )
        if completed and (
            not batches
            or any(
                not item.completed
                or item.error
                or item.issues
                or item.pending_files
                or item.root is None
                or item.transaction_id is None
                or not (item.outputs or item.batches)
                for item in batches
            )
        ):
            return r[m.Infra.CodegenPhaseOutcome].fail(
                "operation completion requires every actual batch output proof",
            )
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
        with cls.mutation_lease(root):
            if completed:
                current = (
                    FlextInfraMiseArtifactsVerification.publication_states_current(
                        outcome,
                    )
                )
                if current.failure:
                    return r[m.Infra.CodegenPhaseOutcome].from_failure(current)
            written = cls.publish_outcome(root, outcome)
        if written.failure:
            return r[m.Infra.CodegenPhaseOutcome].from_failure(written)
        return r[m.Infra.CodegenPhaseOutcome].ok(outcome)

    def bind_publication_proof(
        self,
        session: m.Infra.CodegenTransactionSession,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        topology: m.Infra.CodegenPhaseOutcome | None = None,
        phase: c.Infra.CodegenStagedFilePhase | None = None,
        batch_admission: m.Infra.CodegenPhaseOutcome | None = None,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Persist the complete native output set without rendering or byte copies.

        ``topology`` names the receipt whose source topology, scope roots and
        source scope the journal adopts; without it the journal keeps its own.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
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
            state = FlextInfraCodegenTransactionRecovery._proof_output_state(
                session, plan, admitted
            )
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
        if not session.journal.generator_sources or not session.journal.generator_trees:
            return r[m.Infra.CodegenTransactionSession].fail(
                "publication has no pre-planning producer authority"
            )
        adopted = topology or session.journal
        journal = session.journal.model_copy(
            update={
                "outputs": tuple(outputs.values()),
                "source_topology": adopted.source_topology
                or session.journal.source_topology,
                "scope_roots": adopted.scope_roots or session.journal.scope_roots,
                "source_scope": adopted.source_scope or session.journal.source_scope,
                "phase": phase or session.journal.phase,
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
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[m.Infra.CodegenParticipantPolicy]:
        """Snapshot the canonical physical topology without creating state.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenParticipantPolicy]``.

        """
        result_type = r[m.Infra.CodegenParticipantPolicy]
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
        identity = self._planner.scope_identity()
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
        identity = self._planner.scope_identity()
        if identity.failure:
            return r[m.Infra.GitIdentityReport].from_failure(identity)
        if identity.value.repo_root != self._participant_policy.scope_root:
            return r[m.Infra.GitIdentityReport].fail(
                "generation authorization coordination root differs",
            )
        return identity

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
        if layout.scope_root != self._participant_policy.scope_root:
            return r[bool].fail("generation authorization coordination root differs")
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
        if identity.repo_root != self._participant_policy.scope_root:
            return r[bool].fail("generation authorization coordination root differs")
        authorized = self._authorize_roots((identity.repo_root,))
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
